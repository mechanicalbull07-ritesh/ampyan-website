from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import current_user, login_required

from models.models import db, Post, News, Car, User, MechanicProfile, MechanicReview, Video
from services.car_health_engine import calculate_car_health
from services.garage_network_service import (
    calculate_trust_profile_score,
    trust_level_from_score,
    refresh_mechanic_reputation,
)

main_bp = Blueprint("main", __name__)


# ================= HOME PAGE =================

@main_bp.route("/")
def home():

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

    # COMMUNITY POSTS
    recent_posts = Post.query.order_by(Post.id.desc()).limit(5).all()

    # NEWS
    latest_news = News.query.order_by(News.id.desc()).limit(5).all()

    # VIDEOS
    latest_videos = Video.query.order_by(Video.created_at.desc()).limit(3).all()

    # ACTIVITY FEED
    activity_items = []
    for post in Post.query.order_by(Post.created_at.desc()).limit(4).all():
        activity_items.append({
            "type": "Community",
            "icon": "fa-solid fa-message",
            "title": post.title,
            "meta": f"{post.author.username if post.author else 'Member'} started a discussion",
            "url": f"/post/{post.id}",
            "created_at": post.created_at,
        })

    for car in Car.query.order_by(Car.created_at.desc()).limit(3).all():
        activity_items.append({
            "type": "Garage",
            "icon": "fa-solid fa-car-side",
            "title": f"{car.brand or 'Vehicle'} {car.model or ''}".strip(),
            "meta": "New vehicle added to AMPYAN garage",
            "url": "/garage-dashboard",
            "created_at": car.created_at,
        })

    for video in latest_videos:
        activity_items.append({
            "type": "Video",
            "icon": "fa-brands fa-youtube",
            "title": video.title,
            "meta": "New AMPYAN video available",
            "url": "/videos",
            "created_at": video.created_at,
        })

    recent_activity = sorted(
        activity_items,
        key=lambda item: item.get("created_at") or 0,
        reverse=True
    )[:6]

    # LEADERBOARD
    top_contributors = User.query.order_by(User.reputation.desc()).limit(5).all()

    # GARAGE NETWORK
    nearby_mechanics = []
    mechanic_query = MechanicProfile.query.filter_by(is_verified=True).order_by(
        MechanicProfile.is_featured.desc(),
        MechanicProfile.trust_score.desc(),
        MechanicProfile.id.desc()
    )

    if current_user.is_authenticated and current_user.city:
        nearby_mechanics = mechanic_query.filter_by(city=current_user.city).limit(4).all()

    if not nearby_mechanics:
        nearby_mechanics = mechanic_query.limit(4).all()

    for mechanic in nearby_mechanics:
        refresh_mechanic_reputation(mechanic)

    ecosystem_stats = {
        "owners": User.query.filter(User.role != "mechanic").count(),
        "mechanics": MechanicProfile.query.count(),
        "posts": Post.query.count(),
        "diagnostics": len(recent_activity),
        "reviews": MechanicReview.query.count(),
        "car_profiles": Car.query.count()
    }

    return render_template(
        "home.html",
        cars=cars,
        default_car=default_car,
        recent_posts=recent_posts,
        latest_news=latest_news,
        latest_videos=latest_videos,
        recent_activity=recent_activity,
        top_contributors=top_contributors,
        nearby_mechanics=nearby_mechanics,
        ecosystem_stats=ecosystem_stats
    )


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
