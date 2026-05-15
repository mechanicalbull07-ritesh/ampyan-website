from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import current_user, login_required

from models.models import db, Post, News, Car, User, MechanicProfile, MechanicReview, MarketplaceListing, MarketplaceMessage, Video
from services.car_health_engine import calculate_car_health
from services.garage_network_service import (
    calculate_trust_profile_score,
    trust_level_from_score,
    refresh_mechanic_reputation,
)
from services.india_car_catalog import catalog_image_path

main_bp = Blueprint("main", __name__)


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
    # AMPYAN HOME PAGE REDESIGN START

    cars = []
    default_car = None

    if current_user.is_authenticated:

        cars = Car.query.filter_by(owner_id=current_user.id).all()

        default_car = Car.query.filter_by(
            owner_id=current_user.id,
            is_default=True
        ).first()

        if default_car:
            default_car.health = calculate_car_health(default_car)

    latest_news_records = News.query.order_by(News.created_at.desc()).limit(6).all()
    latest_news = [
        {
            "title": news.title,
            "summary": (news.content or "Read the latest AMPYAN automotive update.")[:120],
            "url": f"/news/{news.id}",
            "image_url": url_for("static", filename=f"news_images/{news.image}") if news.image else None,
            "meta": news.created_at.strftime("%d %b %Y") if news.created_at else "AMPYAN News",
        }
        for news in latest_news_records
    ]

    if not latest_news:
        latest_news = [
            {"title": "What to check before a long highway drive", "summary": "Tyres, fluids, lights and service history should be checked before a long trip.", "url": "/news", "image_url": None, "meta": "Ownership Guide"},
            {"title": "Understanding service estimate line items", "summary": "Learn which workshop items are routine and which should be approved only after inspection.", "url": "/news", "image_url": None, "meta": "Service Awareness"},
            {"title": "Used car checklist for city buyers", "summary": "Documents, accident signs, tyres, clutch feel and maintenance records matter before purchase.", "url": "/news", "image_url": None, "meta": "Used Car Guide"},
        ]

    recent_post_records = Post.query.order_by(Post.created_at.desc()).limit(8).all()
    community_threads = [
        {
            "title": post.title,
            "summary": (post.content or "Community discussion on AMPYAN.")[:120],
            "url": f"/post/{post.id}",
            "image_url": url_for("static", filename=f"post_images/{post.image}") if post.image else None,
            "meta": post.created_at.strftime("%d %b") if post.created_at else "Community",
        }
        for post in recent_post_records
    ]

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
        "Keep service bills and odometer readings in My Garage.",
        "Do not approve add-on cleaning jobs without a clear reason.",
        "Inspect battery health before summer and long trips.",
    ]

    upcoming_service = None
    if default_car:
        vehicle_name = f"{default_car.brand or 'Your car'} {default_car.model or ''}".strip()
        if default_car.next_service_km and default_car.current_km:
            km_left = max(default_car.next_service_km - default_car.current_km, 0)
            upcoming_service = f"{vehicle_name}: {km_left} km to next service"
        elif default_car.next_service_date:
            upcoming_service = f"{vehicle_name}: service due on {default_car.next_service_date.strftime('%d %b %Y')}"

    # AMPYAN HOME PAGE REDESIGN END
    return render_template(
        "home.html",
        cars=cars,
        default_car=default_car,
        recent_posts=recent_post_records,
        latest_news=latest_news,
        community_threads=community_threads,
        trending_problems=trending_problems,
        popular_problems=popular_problems,
        service_tips=service_tips,
        upcoming_service=upcoming_service
    )


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


@main_bp.route("/garage-network")
def garage_network():

    city = (request.args.get("city") or "").strip()
    city_mode = (request.args.get("view") or "list").strip()

    query = MechanicProfile.query.filter_by(is_verified=True).order_by(
        MechanicProfile.is_featured.desc(),
        MechanicProfile.trust_score.desc(),
        MechanicProfile.id.desc()
    )

    if city:
        query = query.filter(MechanicProfile.city.ilike(f"%{city}%"))

    mechanics = query.all()

    for mechanic in mechanics:
        refresh_mechanic_reputation(mechanic)

    city_groups = {}
    for mechanic in mechanics:
        city_groups.setdefault(mechanic.city, []).append(mechanic)

    return render_template(
        "garage_network.html",
        mechanics=mechanics,
        selected_city=city,
        city_mode=city_mode,
        city_groups=city_groups
    )


@main_bp.route("/garage-network/<int:mechanic_id>")
def garage_profile(mechanic_id):

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)

    if not mechanic.is_verified and (not current_user.is_authenticated or current_user.role != "admin"):
        flash("This garage profile is awaiting admin approval.")
        return redirect(url_for("main.garage_network"))

    metrics = refresh_mechanic_reputation(mechanic)
    existing_review = None

    if current_user.is_authenticated:
        existing_review = MechanicReview.query.filter_by(
            mechanic_id=mechanic.id,
            user_id=current_user.id
        ).first()

    return render_template(
        "garage_profile.html",
        mechanic=mechanic,
        review_count=metrics["review_count"],
        average_rating=metrics["average_rating"],
        existing_review=existing_review
    )


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
            is_featured=True if current_user.is_authenticated and current_user.role == "admin" else False
        )

        if current_user.is_authenticated:
            current_user.role = "mechanic"

        db.session.add(profile)
        refresh_mechanic_reputation(profile)
        db.session.commit()

        flash("Garage registered successfully. Your profile is now waiting for admin approval.")
        return redirect(url_for("main.garage_network"))

    return render_template("register_garage.html")
