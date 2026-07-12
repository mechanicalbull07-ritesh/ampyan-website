import os
from urllib.parse import urlparse

from flask import Blueprint, current_app, jsonify, render_template, request, redirect, flash, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, inspect as sqlalchemy_inspect, or_
from sqlalchemy.orm import load_only
from werkzeug.utils import secure_filename

from models.models import db, Post, News, Car, User, MechanicProfile, MechanicReview, MarketplaceListing, MarketplaceMessage, Video
from routes.auth_routes import ADMIN_EMAIL_SET
from services.car_health_engine import calculate_car_health
from services.garage_network_service import (
    calculate_trust_profile_score,
    trust_level_from_score,
    refresh_mechanic_reputation,
)
from services.app_api_sync import sync_garage_to_app
from services.india_car_catalog import catalog_image_path

main_bp = Blueprint("main", __name__)
PUBLIC_SEED_OWNER_NAME = "Listing Owner Not Provided"


def _is_admin_account(user):
    return (
        user.is_authenticated
        and (user.email or "").strip().lower() in ADMIN_EMAIL_SET
    )


def _isoformat(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _split_services(value):
    return [
        item.strip()
        for item in (value or "").replace("|", ",").split(",")
        if item.strip()
    ]


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return min(maximum, max(minimum, parsed))


def _boolish(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _garage_image_url(mechanic, columns=None):
    image_value = _mechanic_value(mechanic, "image_url", columns=columns)
    parsed = urlparse(image_value or "")
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return image_value
    if image_value:
        return url_for("static", filename=image_value.lstrip("/"), _external=True)
    return url_for("static", filename="images/logo.png", _external=True)


def _listing_status(mechanic, columns=None):
    columns = columns if columns is not None else _mechanic_profile_columns()
    if "listing_status" in columns:
        return _mechanic_value(mechanic, "listing_status", columns=columns) or "pending_review"
    if _mechanic_value(mechanic, "is_verified", False, columns):
        return "listed"
    if _mechanic_value(mechanic, "owner_name", None, columns) == PUBLIC_SEED_OWNER_NAME:
        return "public_unverified"
    return "pending_review"


def _is_public_garage_listing(mechanic, columns=None):
    return bool(_mechanic_value(mechanic, "is_verified", False, columns)) or _listing_status(mechanic, columns) == "public_unverified"


def _mechanic_profile_columns():
    try:
        inspector = sqlalchemy_inspect(db.engine)
        if not inspector.has_table("mechanic_profile"):
            return set()
        return {column["name"] for column in inspector.get_columns("mechanic_profile")}
    except Exception:
        current_app.logger.exception("mechanic_profile_column_inspection_failed")
        return {column.name for column in MechanicProfile.__table__.columns}


def _mechanic_query():
    columns = _mechanic_profile_columns()
    mapped_columns = {column.name for column in MechanicProfile.__table__.columns}
    loadable_columns = sorted(columns & mapped_columns)
    query = MechanicProfile.query
    if loadable_columns:
        query = query.options(load_only(*(getattr(MechanicProfile, name) for name in loadable_columns)))
    return query, columns


def _mechanic_value(mechanic, name, default=None, columns=None):
    if columns is None:
        columns = _mechanic_profile_columns()
    if columns and name not in columns:
        return default
    try:
        value = getattr(mechanic, name)
    except Exception:
        current_app.logger.exception("mechanic_profile_value_unavailable", extra={"column": name})
        return default
    return default if value is None else value


def _garage_order_by(query, columns):
    order_columns = []
    if "is_featured" in columns:
        order_columns.append(MechanicProfile.is_featured.desc())
    if "trust_score" in columns:
        order_columns.append(MechanicProfile.trust_score.desc())
    order_columns.append(MechanicProfile.id.desc())
    return query.order_by(*order_columns)


def _mechanic_metrics(mechanic, columns, include_reviews=False):
    trust_score = _mechanic_value(mechanic, "trust_score", 30, columns)
    trust_level = _mechanic_value(
        mechanic,
        "trust_level",
        trust_level_from_score(trust_score),
        columns,
    )
    if not include_reviews:
        return {
            "review_count": 0,
            "average_rating": 0,
            "trust_score": trust_score,
            "trust_level": trust_level,
        }

    try:
        review_count = len(mechanic.reviews)
        average_rating = (
            sum(review.rating for review in mechanic.reviews) / review_count
            if review_count else 0
        )
    except Exception:
        current_app.logger.exception("mechanic_profile_reviews_unavailable")
        review_count = 0
        average_rating = 0

    return {
        "review_count": review_count,
        "average_rating": round(average_rating, 1) if review_count else 0,
        "trust_score": trust_score,
        "trust_level": trust_level,
    }


def _serialize_mechanic(mechanic, include_reviews=False, columns=None):
    columns = columns if columns is not None else _mechanic_profile_columns()
    metrics = _mechanic_metrics(mechanic, columns, include_reviews=include_reviews)
    service_types = _mechanic_value(mechanic, "service_types", "", columns)
    specialties = _mechanic_value(mechanic, "specialties", "", columns)
    is_verified = bool(_mechanic_value(mechanic, "is_verified", False, columns))
    services = _split_services(service_types or specialties)
    area = (
        _mechanic_value(mechanic, "area", None, columns)
        or _mechanic_value(mechanic, "state", None, columns)
        or _mechanic_value(mechanic, "pincode", None, columns)
    )
    image_url = _garage_image_url(mechanic, columns)
    listing_status = _listing_status(mechanic, columns)
    listing_label = "AMPYAN Verified" if is_verified else "Listed for discovery"
    verification_label = "AMPYAN Verified" if is_verified else "Not verified by AMPYAN yet"
    description = _mechanic_value(mechanic, "about", None, columns) or "Public garage information listed for discovery on AMPYAN. Verification can be completed by the business owner."
    average_rating = metrics["average_rating"] if is_verified else None
    payload = {
        "id": _mechanic_value(mechanic, "id", None, columns),
        "business_name": _mechanic_value(mechanic, "business_name", "Garage", columns),
        "name": _mechanic_value(mechanic, "business_name", None, columns) or "Garage",
        "owner_name": _mechanic_value(mechanic, "owner_name", None, columns),
        "owner": _mechanic_value(mechanic, "owner_name", None, columns),
        "email": _mechanic_value(mechanic, "email", None, columns),
        "phone": _mechanic_value(mechanic, "phone", None, columns),
        "city": _mechanic_value(mechanic, "city", None, columns),
        "area": area,
        "state": _mechanic_value(mechanic, "state", None, columns),
        "country": _mechanic_value(mechanic, "country", "India", columns),
        "pincode": _mechanic_value(mechanic, "pincode", None, columns),
        "address": _mechanic_value(mechanic, "address", None, columns),
        "specialties": specialties,
        "service_types": service_types,
        "services": services,
        "experience_years": _mechanic_value(mechanic, "experience_years", 0, columns),
        "about": _mechanic_value(mechanic, "about", None, columns),
        "description": description,
        "trust_score": metrics["trust_score"] if is_verified else None,
        "trust_level": metrics["trust_level"] if is_verified else "Listed for discovery",
        "is_featured": bool(_mechanic_value(mechanic, "is_featured", False, columns)),
        "is_verified": is_verified,
        "is_ampyan_verified": is_verified,
        "accepts_emergency": bool(_mechanic_value(mechanic, "accepts_emergency", False, columns)),
        "pickup_drop_available": bool(_mechanic_value(mechanic, "pickup_drop_available", False, columns)),
        "latitude": _mechanic_value(mechanic, "latitude", None, columns),
        "longitude": _mechanic_value(mechanic, "longitude", None, columns),
        "image_url": image_url,
        "image": image_url,
        "listing_status": listing_status,
        "listing_label": listing_label,
        "verification_label": verification_label,
        "claim_cta": "Own this garage? Claim this listing.",
        "claim_url": url_for("main.register_garage", _external=True),
        "source": _mechanic_value(mechanic, "source", None, columns) or "website",
        "created_at": _isoformat(_mechanic_value(mechanic, "created_at", None, columns)),
        "review_count": metrics["review_count"] if is_verified else 0,
        "average_rating": average_rating,
        "rating": average_rating,
    }
    if include_reviews:
        try:
            payload["reviews"] = [
                {
                    "id": review.id,
                    "rating": review.rating,
                    "review_text": review.review_text,
                    "created_at": _isoformat(review.created_at),
                    "author": {
                        "id": review.user_id,
                        "name": review.author.username if review.author else "Member",
                    },
                }
                for review in mechanic.reviews
            ]
        except Exception:
            current_app.logger.exception("mechanic_profile_reviews_serialize_failed")
            payload["reviews"] = []
    return payload


def _garage_query_from_request():
    query, columns = _mechanic_query()
    city = (request.args.get("city") or "").strip()
    service = (request.args.get("service") or request.args.get("service_type") or "").strip()
    search = (request.args.get("search") or request.args.get("q") or "").strip()
    include_unverified = _is_admin_account(current_user) and request.args.get("include_unverified") == "true"

    if not include_unverified:
        public_filters = []
        if "is_verified" in columns:
            public_filters.append(MechanicProfile.is_verified.is_(True))
        if "listing_status" in columns:
            public_filters.append(MechanicProfile.listing_status == "public_unverified")
        elif "owner_name" in columns:
            public_filters.append(MechanicProfile.owner_name == PUBLIC_SEED_OWNER_NAME)
        if public_filters:
            query = query.filter(or_(*public_filters))
    if city:
        city_filters = []
        if "city" in columns:
            city_filters.append(MechanicProfile.city.ilike(f"%{city}%"))
        if "area" in columns:
            city_filters.append(MechanicProfile.area.ilike(f"%{city}%"))
        if city_filters:
            query = query.filter(or_(*city_filters))
    if service:
        service_filters = []
        if "service_types" in columns:
            service_filters.append(MechanicProfile.service_types.ilike(f"%{service}%"))
        if "specialties" in columns:
            service_filters.append(MechanicProfile.specialties.ilike(f"%{service}%"))
        if service_filters:
            query = query.filter(or_(*service_filters))
    if search:
        pattern = f"%{search}%"
        search_filters = []
        for column_name in ("business_name", "owner_name", "city", "area", "address", "specialties", "service_types"):
            if column_name in columns:
                search_filters.append(getattr(MechanicProfile, column_name).ilike(pattern))
        if search_filters:
            query = query.filter(or_(*search_filters))

    return query, columns


def _static_image_url_if_exists(folder, filename, fallback=None):
    parsed = urlparse(filename or "")
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return filename

    if filename:
        candidates = []
        for candidate in (filename, secure_filename(filename)):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        for candidate in candidates:
            relative_path = os.path.join(folder, candidate)
            absolute_path = os.path.join(current_app.static_folder, relative_path)
            if os.path.isfile(absolute_path):
                return url_for("static", filename=relative_path.replace(os.sep, "/"))

            if folder == "news_images":
                upload_folder = current_app.config.get("UPLOAD_FOLDER")
                if upload_folder and os.path.isabs(upload_folder):
                    upload_path = os.path.join(upload_folder, candidate)
                    if os.path.isfile(upload_path):
                        return url_for("uploaded_news_image", filename=candidate)

    return url_for("static", filename=fallback) if fallback else None


def _safe_int(value):
    try:
        parsed = int(value or 0)
        return parsed or None
    except (TypeError, ValueError):
        return None


def _attach_listing_catalog_image(listing):
    listing.catalog_image_path = catalog_image_path(listing.brand, listing.model)
    return listing


# ================= HOME PAGE =================

@main_bp.route("/")
def home():
    default_news_image = "news_images/AMPYAN_-_Powering_Intelligent_Mobility.png"
    fallback_news_image = url_for("static", filename=default_news_image)

    cars = []
    default_car = None
    recent_post_records = []
    latest_videos = []
    upcoming_service = None

    try:
        if current_user.is_authenticated:

            cars = Car.query.filter_by(owner_id=current_user.id).all()

            default_car = Car.query.filter_by(
                owner_id=current_user.id,
                is_default=True
            ).first()

            if default_car:
                default_car.health = calculate_car_health(default_car)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("home_section_error=garage error=%s", exc.__class__.__name__)
        cars = []
        default_car = None

    try:
        latest_news_records = News.query.order_by(News.created_at.desc()).limit(6).all()
        latest_news = [
            {
                "title": news.title,
                "summary": (news.content or "Read the latest AMPYAN automotive update.")[:120],
                "url": f"/news/{news.id}",
                "image_url": _static_image_url_if_exists(
                    "news_images",
                    news.image,
                    fallback=default_news_image
                ),
                "meta": news.created_at.strftime("%d %b %Y") if news.created_at else "AMPYAN News",
            }
            for news in latest_news_records
        ]
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("home_section_error=news error=%s", exc.__class__.__name__)
        latest_news = []

    if not latest_news:
        latest_news = [
            {"title": "What to check before a long highway drive", "summary": "Tyres, fluids, lights and service history should be checked before a long trip.", "url": "/news", "image_url": fallback_news_image, "meta": "Ownership Guide"},
            {"title": "Understanding service estimate line items", "summary": "Learn which workshop items are routine and which should be approved only after inspection.", "url": "/news", "image_url": fallback_news_image, "meta": "Service Awareness"},
            {"title": "Used car checklist for city buyers", "summary": "Documents, accident signs, tyres, clutch feel and maintenance records matter before purchase.", "url": "/news", "image_url": fallback_news_image, "meta": "Used Car Guide"},
        ]

    try:
        recent_post_records = Post.query.order_by(Post.created_at.desc()).limit(8).all()
        community_threads = [
            {
                "title": post.title,
                "summary": (post.content or "Community discussion on AMPYAN.")[:120],
                "url": f"/post/{post.id}",
                "image_url": _static_image_url_if_exists(
                    "post_images",
                    post.image,
                    fallback=default_news_image
                ),
                "meta": post.created_at.strftime("%d %b") if post.created_at else "Community",
            }
            for post in recent_post_records
        ]
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("home_section_error=community error=%s", exc.__class__.__name__)
        recent_post_records = []
        community_threads = []

    if not community_threads:
        community_threads = [
            {"title": "Engine vibration at idle after service", "summary": "Owners discuss mounts, plugs, idle RPM and recent service checks.", "url": "/create-post", "image_url": None, "meta": "Start discussion"},
            {"title": "Brake noise after monsoon driving", "summary": "A practical thread about dust, pads, discs and when inspection is needed.", "url": "/create-post", "image_url": None, "meta": "Community"},
            {"title": "Best maintenance routine for daily city use", "summary": "Compare real owner routines for tyres, fluids, filters and battery care.", "url": "/create-post", "image_url": None, "meta": "Community"},
        ]

    trending_problems = [
        "Engine vibration at idle",
        "AC cooling weak in traffic",
        "Brake noise while slowing",
        "Low pickup on acceleration",
        "Battery drain overnight",
        "Steering vibration at speed",
        "Mileage dropped suddenly",
        "Warning light after service",
    ][:8]

    popular_problems = [
        {"title": "Engine misfire or rough idle", "url": "/tools/ai-diagnosis"},
        {"title": "Clutch slip and burning smell", "url": "/tools/ai-diagnosis"},
        {"title": "Suspension thud on bad roads", "url": "/tools/ai-diagnosis"},
        {"title": "Overheating in slow traffic", "url": "/tools/ai-diagnosis"},
    ]

    service_tips = [
        "Check tyre pressure monthly and before highway drives.",
        "Keep service bills and odometer readings in My Car Health.",
        "Do not approve add-on cleaning jobs without a clear reason.",
        "Inspect battery health before summer and long trips.",
    ]

    try:
        latest_videos = Video.query.order_by(Video.created_at.desc()).limit(2).all()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("home_section_error=videos error=%s", exc.__class__.__name__)
        latest_videos = []

    try:
        if default_car:
            vehicle_name = f"{default_car.brand or 'Your car'} {default_car.model or ''}".strip()
            if default_car.next_service_km and default_car.current_km:
                km_left = max(default_car.next_service_km - default_car.current_km, 0)
                upcoming_service = f"{vehicle_name}: {km_left} km to next service"
            elif default_car.next_service_date:
                upcoming_service = f"{vehicle_name}: service due on {default_car.next_service_date.strftime('%d %b %Y')}"
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("home_section_error=garage error=%s", exc.__class__.__name__)
        upcoming_service = None

    # AMPYAN HOME PAGE REDESIGN END
    response = render_template(
        "home.html",
        cars=cars,
        default_car=default_car,
        recent_posts=recent_post_records,
        latest_news=latest_news,
        community_threads=community_threads,
        trending_problems=trending_problems,
        popular_problems=popular_problems,
        service_tips=service_tips,
        latest_videos=latest_videos,
        upcoming_service=upcoming_service
    )
    current_app.logger.info("home_page_rendered")
    return response


@main_bp.route("/marketplace")
def marketplace():
    listing_type = (request.args.get("type") or "all").strip().lower()
    query = MarketplaceListing.query.filter_by(is_active=True).order_by(MarketplaceListing.created_at.desc())
    if listing_type in {"buy", "sell"}:
        query = query.filter_by(listing_type=listing_type)

    return render_template(
        "marketplace.html",
        listings=[_attach_listing_catalog_image(listing) for listing in query.all()],
        listing_type=listing_type,
    )


@main_bp.route("/marketplace/create", methods=["GET", "POST"])
@login_required
def create_marketplace_listing():
    if request.method == "POST":
        listing_type = (request.form.get("listing_type") or "sell").strip().lower()
        if listing_type not in {"buy", "sell"}:
            listing_type = "sell"

        title = (request.form.get("title") or "").strip()
        if not title:
            flash("Listing title is required.")
            return redirect(url_for("main.create_marketplace_listing"))

        listing = MarketplaceListing(
            listing_type=listing_type,
            title=title,
            description=(request.form.get("description") or "").strip(),
            brand=(request.form.get("brand") or "").strip(),
            model=(request.form.get("model") or "").strip(),
            year=_safe_int(request.form.get("year")),
            price=_safe_int(request.form.get("price")),
            location=(request.form.get("location") or current_user.city or "").strip(),
            contact_phone=(request.form.get("contact_phone") or current_user.mobile or "").strip(),
            user_id=current_user.id,
        )
        db.session.add(listing)
        db.session.commit()
        flash("Marketplace listing created.")
        return redirect(url_for("main.marketplace_listing_detail", listing_id=listing.id))

    return render_template("marketplace_create.html")


@main_bp.route("/marketplace/<int:listing_id>")
def marketplace_listing_detail(listing_id):
    listing = MarketplaceListing.query.get_or_404(listing_id)
    _attach_listing_catalog_image(listing)
    return render_template("marketplace_detail.html", listing=listing)


@main_bp.route("/marketplace/<int:listing_id>/message", methods=["POST"])
@login_required
def send_marketplace_message(listing_id):
    listing = MarketplaceListing.query.get_or_404(listing_id)
    if listing.user_id == current_user.id:
        flash("This is your own listing.")
        return redirect(url_for("main.marketplace_listing_detail", listing_id=listing.id))

    message_text = (request.form.get("message") or "").strip()
    if not message_text:
        flash("Message is required.")
        return redirect(url_for("main.marketplace_listing_detail", listing_id=listing.id))

    db.session.add(MarketplaceMessage(
        listing_id=listing.id,
        sender_id=current_user.id,
        receiver_id=listing.user_id,
        message=message_text,
    ))
    db.session.commit()
    flash("Message sent to the listing owner.")
    return redirect(url_for("main.marketplace_listing_detail", listing_id=listing.id))


@main_bp.route("/marketplace/inbox")
@login_required
def marketplace_inbox():
    messages = (
        MarketplaceMessage.query
        .filter((MarketplaceMessage.receiver_id == current_user.id) | (MarketplaceMessage.sender_id == current_user.id))
        .order_by(MarketplaceMessage.created_at.desc())
        .all()
    )
    return render_template("marketplace_inbox.html", messages=messages)


@main_bp.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(
        User.reputation.desc(),
        User.helpful_answers.desc(),
        User.posts_count.desc(),
        User.id.asc()
    ).limit(50).all()

    return render_template("leaderboard.html", users=users)


@main_bp.route("/garages")
@main_bp.route("/garage-network")
def garage_network():

    city = (request.args.get("city") or "").strip()
    city_mode = (request.args.get("view") or "list").strip()

    query, columns = _garage_query_from_request()
    query = _garage_order_by(query, columns)

    mechanics = query.all()
    serialized_mechanics = [_serialize_mechanic(mechanic, columns=columns) for mechanic in mechanics]

    city_groups = {}
    for mechanic in serialized_mechanics:
        city_groups.setdefault(mechanic.get("city") or "Unknown", []).append(mechanic)

    return render_template(
        "garage_network.html",
        mechanics=serialized_mechanics,
        selected_city=city,
        city_mode=city_mode,
        city_groups=city_groups
    )


@main_bp.route("/api/garages")
@main_bp.route("/api/nearby-garages")
def api_garages():
    page = _bounded_int(request.args.get("page"), 1, 1, 10_000)
    per_page = _bounded_int(request.args.get("per_page") or request.args.get("limit"), 20, 1, 100)
    query, columns = _garage_query_from_request()
    total = query.order_by(None).with_entities(func.count(MechanicProfile.id)).scalar() or 0

    mechanics = (
        _garage_order_by(query, columns)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return jsonify({
        "success": True,
        "status": "success",
        "garages": [_serialize_mechanic(mechanic, columns=columns) for mechanic in mechanics],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page if per_page else 0,
        },
    })


@main_bp.route("/api/garages/<int:mechanic_id>")
def api_garage_detail(mechanic_id):
    query, columns = _mechanic_query()
    mechanic = query.filter(MechanicProfile.id == mechanic_id).first_or_404()
    if not _is_public_garage_listing(mechanic, columns) and not _is_admin_account(current_user):
        return jsonify({"status": "error", "message": "garage not found"}), 404

    return jsonify({
        "success": True,
        "status": "success",
        "garage": _serialize_mechanic(mechanic, include_reviews=True, columns=columns),
    })


@main_bp.route("/api/garages/register", methods=["POST"])
def api_register_garage():
    data = request.get_json(silent=True) or request.form
    form_data = {
        "business_name": (data.get("business_name") or data.get("name") or "").strip(),
        "owner_name": (data.get("owner_name") or data.get("owner") or "").strip(),
        "email": (data.get("email") or "").strip().lower(),
        "phone": (data.get("phone") or "").strip(),
        "city": (data.get("city") or "").strip(),
        "area": (data.get("area") or "").strip(),
        "state": (data.get("state") or "").strip(),
        "country": (data.get("country") or "India").strip(),
        "pincode": (data.get("pincode") or "").strip(),
        "address": (data.get("address") or "").strip(),
        "specialties": (data.get("specialties") or "").strip(),
        "service_types": (data.get("service_types") or "").strip(),
        "experience_years": data.get("experience_years") or 0,
        "about": (data.get("about") or data.get("description") or "").strip(),
        "image_url": (data.get("image_url") or data.get("image") or "").strip(),
        "accepts_emergency": _boolish(data.get("accepts_emergency")),
        "pickup_drop_available": _boolish(data.get("pickup_drop_available")),
    }
    if not form_data["service_types"] and isinstance(data.get("services"), list):
        form_data["service_types"] = ", ".join(str(item).strip() for item in data.get("services") if str(item).strip())

    missing = [field for field in ("business_name", "phone", "city") if not form_data.get(field)]
    if missing:
        return jsonify({
            "success": False,
            "status": "error",
            "message": "Business name, phone and city are required.",
            "missing": missing,
        }), 400

    trust_score = calculate_trust_profile_score(form_data)
    profile = MechanicProfile(
        user_id=current_user.id if current_user.is_authenticated else None,
        business_name=form_data["business_name"],
        owner_name=form_data["owner_name"] or "Not provided",
        email=form_data["email"] or None,
        phone=form_data["phone"],
        city=form_data["city"],
        area=form_data["area"] or None,
        state=form_data["state"] or None,
        country=form_data["country"] or "India",
        pincode=form_data["pincode"] or None,
        address=form_data["address"] or None,
        specialties=form_data["specialties"] or None,
        service_types=form_data["service_types"] or None,
        experience_years=_bounded_int(form_data["experience_years"], 0, 0, 80),
        about=form_data["about"] or None,
        image_url=form_data["image_url"] or None,
        listing_status="pending_review",
        source="api",
        trust_score=trust_score,
        trust_level=trust_level_from_score(trust_score),
        accepts_emergency=form_data["accepts_emergency"],
        pickup_drop_available=form_data["pickup_drop_available"],
        is_verified=False,
        is_featured=False,
    )
    db.session.add(profile)
    refresh_mechanic_reputation(profile)
    db.session.commit()
    return jsonify({
        "success": True,
        "status": "success",
        "message": "Garage registered and pending review.",
        "garage": _serialize_mechanic(profile),
    }), 201


@main_bp.route("/garages/<int:mechanic_id>")
@main_bp.route("/garage-network/<int:mechanic_id>")
def garage_profile(mechanic_id):

    query, columns = _mechanic_query()
    mechanic = query.filter(MechanicProfile.id == mechanic_id).first_or_404()

    if not _is_public_garage_listing(mechanic, columns) and not _is_admin_account(current_user):
        flash("This garage profile is awaiting admin approval.")
        return redirect(url_for("main.garage_network"))

    metrics = _mechanic_metrics(mechanic, columns)
    mechanic_payload = _serialize_mechanic(mechanic, include_reviews=True, columns=columns)
    existing_review = None

    if current_user.is_authenticated:
        existing_review = MechanicReview.query.filter_by(
            mechanic_id=_mechanic_value(mechanic, "id", mechanic_id, columns),
            user_id=current_user.id
        ).first()

    return render_template(
        "garage_profile.html",
        mechanic=mechanic_payload,
        review_count=metrics["review_count"],
        average_rating=metrics["average_rating"],
        existing_review=existing_review
    )


@main_bp.route("/garages/<int:mechanic_id>/review", methods=["POST"])
@main_bp.route("/garage-network/<int:mechanic_id>/review", methods=["POST"])
@login_required
def submit_garage_review(mechanic_id):

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)

    if current_user.role == "mechanic":
        flash("Mechanic accounts cannot review garage listings.")
        return redirect(url_for("main.garage_profile", mechanic_id=mechanic_id))

    rating = int(request.form.get("rating") or 0)
    review_text = (request.form.get("review_text") or "").strip()

    if rating < 1 or rating > 5:
        flash("Please choose a rating between 1 and 5.")
        return redirect(url_for("main.garage_profile", mechanic_id=mechanic_id))

    existing_review = MechanicReview.query.filter_by(
        mechanic_id=mechanic.id,
        user_id=current_user.id
    ).first()

    if existing_review:
        existing_review.rating = rating
        existing_review.review_text = review_text
    else:
        existing_review = MechanicReview(
            mechanic_id=mechanic.id,
            user_id=current_user.id,
            rating=rating,
            review_text=review_text
        )
        db.session.add(existing_review)

    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Your review has been saved.")
    return redirect(url_for("main.garage_profile", mechanic_id=mechanic_id))


@main_bp.route("/dashboard")
@login_required
def dashboard_router():

    if current_user.role == "mechanic":
        return redirect(url_for("main.mechanic_dashboard"))

    return redirect("/profile")


@main_bp.route("/mechanic-dashboard")
@login_required
def mechanic_dashboard():

    if current_user.role != "mechanic":
        return redirect("/profile")

    profile = MechanicProfile.query.filter_by(user_id=current_user.id).order_by(MechanicProfile.id.desc()).first()

    if not profile:
        flash("Create your garage profile to unlock the mechanic dashboard.")
        return redirect(url_for("main.register_garage"))

    metrics = refresh_mechanic_reputation(profile)
    db.session.commit()

    return render_template(
        "mechanic_dashboard.html",
        mechanic=profile,
        review_count=metrics["review_count"],
        average_rating=metrics["average_rating"]
    )


@main_bp.route("/garages/register", methods=["GET", "POST"])
@main_bp.route("/garage-network/register", methods=["GET", "POST"])
def register_garage():

    if request.method == "POST":
        form_data = {
            "business_name": (request.form.get("business_name") or "").strip(),
            "owner_name": (request.form.get("owner_name") or "").strip(),
            "email": (request.form.get("email") or "").strip().lower(),
            "phone": (request.form.get("phone") or "").strip(),
            "city": (request.form.get("city") or "").strip(),
            "state": (request.form.get("state") or "").strip(),
            "country": (request.form.get("country") or "India").strip(),
            "pincode": (request.form.get("pincode") or "").strip(),
            "address": (request.form.get("address") or "").strip(),
            "specialties": (request.form.get("specialties") or "").strip(),
            "service_types": (request.form.get("service_types") or "").strip(),
            "experience_years": request.form.get("experience_years") or 0,
            "about": (request.form.get("about") or "").strip(),
            "accepts_emergency": True if request.form.get("accepts_emergency") else False,
            "pickup_drop_available": True if request.form.get("pickup_drop_available") else False
        }

        required_fields = ["business_name", "owner_name", "phone", "city"]
        missing = [field for field in required_fields if not form_data.get(field)]

        if missing:
            flash("Business name, owner name, phone and city are required.")
            return redirect(url_for("main.register_garage"))

        trust_score = calculate_trust_profile_score(form_data)

        profile = MechanicProfile(
            user_id=current_user.id if current_user.is_authenticated else None,
            business_name=form_data["business_name"],
            owner_name=form_data["owner_name"],
            email=form_data["email"] or None,
            phone=form_data["phone"],
            city=form_data["city"],
            state=form_data["state"] or None,
            country=form_data["country"] or "India",
            pincode=form_data["pincode"] or None,
            address=form_data["address"] or None,
            specialties=form_data["specialties"] or None,
            service_types=form_data["service_types"] or None,
            experience_years=int(form_data["experience_years"] or 0),
            about=form_data["about"] or None,
            trust_score=trust_score,
            trust_level=trust_level_from_score(trust_score),
            accepts_emergency=form_data["accepts_emergency"],
            pickup_drop_available=form_data["pickup_drop_available"],
            is_verified=False,
            is_featured=True if _is_admin_account(current_user) else False
        )

        if current_user.is_authenticated and not _is_admin_account(current_user):
            current_user.role = "mechanic"

        db.session.add(profile)
        refresh_mechanic_reputation(profile)
        db.session.commit()
        sync_garage_to_app(profile)

        flash("Garage registered successfully. Your profile is now waiting for admin approval.")
        return redirect(url_for("main.garage_network"))

    return render_template("register_garage.html")
