import json
import os
from types import SimpleNamespace
from urllib import error, request as urllib_request

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request
from flask_login import current_user, login_required
from flask import current_app
from werkzeug.utils import secure_filename
from models.models import Car, Post, db
from services.car_health_engine import calculate_car_health
from services.maintenance_engine import get_maintenance_suggestions
from services.automotive_knowledge_engine import analyze_vehicle
from services.failure_prediction_engine import predict_component_failure
from services.service_timeline_engine import generate_service_timeline
from services.driving_pattern_engine import analyze_driving_pattern
from services.service_schedule_engine import get_service_schedule
from services.component_health_engine import get_component_health
import os

user_bp = Blueprint("user", __name__)


def _ampyan_api_base_url():
    return (os.environ.get("AMPYAN_API_BASE_URL") or "https://api.ampyan.com").rstrip("/")


def _remote_request(path, method="GET", payload=None, timeout=8):
    url = f"{_ampyan_api_base_url()}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except Exception as exc:
        current_app.logger.warning("AMPYAN profile sync failed for %s: %s", path, exc)
        return None


def _sync_current_user_profile():
    return _remote_request(
        "/profile/sync",
        method="POST",
        payload={
            "name": current_user.username,
            "email": current_user.email,
            "phone": current_user.mobile or "",
            "user_email": current_user.email,
        },
    )


def _load_remote_profile_posts():
    payload = _remote_request("/community/export?include_replies=true")
    if not payload:
        return []

    posts = []
    for post in payload.get("posts") or []:
        user = post.get("user") or {}
        email = (user.get("email") or "").strip().lower()
        if email != (current_user.email or "").strip().lower():
            continue
        if (post.get("source") or "").lower() == "website":
            continue
        text = post.get("text") or ""
        title = text.splitlines()[0][:80] if text else "Shared Community Post"
        posts.append(
            SimpleNamespace(
                id=f"remote-{post.get('id')}",
                title=title,
                content=text,
                detail_url=f"/community/remote/{post.get('id')}",
            )
        )
    return posts


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "mobile": user.mobile,
        "city": user.city,
        "state": user.state,
        "country": user.country,
        "pincode": user.pincode,
        "role": user.role,
        "badge": user.badge,
        "reputation": user.reputation,
        "posts_count": user.posts_count,
        "helpful_answers": user.helpful_answers,
        "ai_uses_today": user.ai_uses_today,
        "email_verified": user.email_verified,
        "profile_photo": user.profile_photo,
    }


def serialize_car(car):
    return {
        "id": car.id,
        "brand": car.brand,
        "model": car.model,
        "year": car.year,
        "fuel_type": car.fuel_type,
        "mileage": car.mileage,
        "current_km": car.current_km,
        "last_service_km": car.last_service_km,
        "next_service_km": car.next_service_km,
        "daily_km": car.daily_km,
        "is_default": car.is_default,
        "created_at": car.created_at.isoformat() if car.created_at else None,
    }


@user_bp.route("/profile")
@login_required
def profile():
    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:
        car.health = calculate_car_health(car)
        car.analysis = analyze_vehicle(car)
        car.maintenance = get_maintenance_suggestions(car)
        car.failure_prediction = predict_component_failure(car)
        car.timeline = generate_service_timeline(car)
        car.driving_pattern = analyze_driving_pattern(car)
        car.service_schedule = get_service_schedule(car)
        car.components = get_component_health(car)

    local_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.id.desc()).all()
    remote_posts = _load_remote_profile_posts()
    profile_posts = list(local_posts[:5]) + remote_posts[:5]

    return render_template(
        "profile.html",
        cars=cars,
        posts=local_posts,
        profile_posts=profile_posts[:5],
        cars_count=len(cars),
        posts_count=len(local_posts) + len(remote_posts),
        ai_used=current_user.ai_uses_today,
        reputation=current_user.reputation,
        badge=current_user.badge,
    )


@user_bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    current_user.city = request.form.get("city")
    current_user.state = request.form.get("state")
    current_user.country = request.form.get("country")
    current_user.pincode = request.form.get("pincode")
    current_user.mobile = request.form.get("mobile")

    photo = request.files.get("profile_photo")
    if photo and photo.filename != "":
        filename = secure_filename(photo.filename)
        save_path = os.path.join(current_app.config["PROFILE_UPLOAD"], filename)
        os.makedirs("static/profile_images", exist_ok=True)
        photo.save(save_path)
        current_user.profile_photo = filename

    db.session.commit()
    _sync_current_user_profile()
    flash("Profile updated successfully")
    return redirect("/profile")


@user_bp.route("/api/session")
def api_session():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "user": None, "cars": []})

    cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.id.desc()).all()
    return jsonify({
        "authenticated": True,
        "user": serialize_user(current_user),
        "cars": [serialize_car(car) for car in cars],
    })


@user_bp.route("/api/profile", methods=["GET", "POST"])
@login_required
def api_profile():
    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        current_user.mobile = payload.get("mobile")
        current_user.city = payload.get("city")
        current_user.state = payload.get("state")
        current_user.country = payload.get("country")
        current_user.pincode = payload.get("pincode")
        db.session.commit()
        _sync_current_user_profile()

    return jsonify({"status": "success", "user": serialize_user(current_user)})


@user_bp.route("/api/cars")
@login_required
def api_cars():
    cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.id.desc()).all()
    return jsonify({"status": "success", "cars": [serialize_car(car) for car in cars]})
