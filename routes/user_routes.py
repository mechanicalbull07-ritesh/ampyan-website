import json
import os
from datetime import datetime
from types import SimpleNamespace
from urllib import error, request as urllib_request

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request
from flask_login import current_user, login_required
from flask import current_app
from models.models import Car, Post, db
from services.car_health_engine import calculate_car_health
from services.maintenance_engine import get_maintenance_suggestions
from services.automotive_knowledge_engine import analyze_vehicle
from services.failure_prediction_engine import predict_component_failure
from services.service_timeline_engine import generate_service_timeline
from services.driving_pattern_engine import analyze_driving_pattern
from services.service_schedule_engine import get_service_schedule
from services.component_health_engine import get_component_health
from services.garage_summary import enrich_car_for_garage, serialize_garage_car
from services.public_image_storage import public_image_url, store_public_image
import os

user_bp = Blueprint("user", __name__)


def _ampyan_api_base_url():
    return (os.environ.get("AMPYAN_API_BASE_URL") or "https://api.ampyan.com").rstrip("/")


def _remote_request(path, method="GET", payload=None, timeout=3):
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
    profile_url = public_image_url("profile_images", current_user.profile_photo) if current_user.profile_photo else ""
    if profile_url and profile_url.startswith("/"):
        profile_url = f"{request.url_root.rstrip('/')}{profile_url}"
    return _remote_request(
        "/profile/sync",
        method="POST",
        payload={
            "name": current_user.username,
            "email": current_user.email,
            "phone": current_user.mobile or "",
            "user_email": current_user.email,
            "profile_photo": profile_url,
            "profile_image": profile_url,
            "avatar_url": profile_url,
        },
    )


def _safe_int(value, default=None):
    try:
        if value in [None, ""]:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_date(value):
    try:
        if not value:
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _payload_value(payload, *names, default=None):
    for name in names:
        value = payload.get(name)
        if value not in [None, ""]:
            return value
    return default


def _apply_car_payload(car, payload):
    service_interval = 10000

    car.brand = _payload_value(payload, "brand", default=car.brand)
    car.model = _payload_value(payload, "model", default=car.model)
    car.year = _safe_int(_payload_value(payload, "year", default=car.year))
    car.fuel_type = _payload_value(payload, "fuel_type", "fuel", default=car.fuel_type)
    car.mileage = _safe_int(_payload_value(payload, "mileage", default=car.mileage))
    car.current_km = _safe_int(_payload_value(payload, "current_km", default=car.current_km), 0)
    car.last_service_km = _safe_int(_payload_value(payload, "last_service_km", default=car.last_service_km))
    car.daily_km = _safe_int(_payload_value(payload, "daily_km", default=car.daily_km))
    car.brake_replaced_km = _safe_int(_payload_value(payload, "brake_replaced_km", default=car.brake_replaced_km))
    car.tyre_replaced_km = _safe_int(_payload_value(payload, "tyre_replaced_km", default=car.tyre_replaced_km))
    car.clutch_replaced_km = _safe_int(_payload_value(payload, "clutch_replaced_km", default=car.clutch_replaced_km))
    car.battery_replaced_year = _safe_int(_payload_value(payload, "battery_replaced_year", default=car.battery_replaced_year))

    if "insurance_expiry" in payload:
        car.insurance_expiry = _safe_date(payload.get("insurance_expiry"))
    if "pollution_expiry" in payload:
        car.pollution_expiry = _safe_date(payload.get("pollution_expiry"))
    if "last_service_date" in payload:
        car.last_service_date = _safe_date(payload.get("last_service_date"))
    if "next_service_date" in payload:
        car.next_service_date = _safe_date(payload.get("next_service_date"))

    car.next_service_km = car.last_service_km + service_interval if car.last_service_km else None
    return car


def _require_api_auth():
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "authentication required"}), 401
    return None


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
    profile_url = public_image_url("profile_images", user.profile_photo) if user.profile_photo else ""
    if profile_url and profile_url.startswith("/"):
        profile_url = f"{request.url_root.rstrip('/')}{profile_url}"
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
        "profile_photo_url": profile_url,
        "profile_image": profile_url,
        "avatar_url": profile_url,
    }


def serialize_car(car):
    return serialize_garage_car(enrich_car_for_garage(car))


@user_bp.route("/profile")
@login_required
def profile():
    cars = Car.query.filter_by(owner_id=current_user.id).all()

    for car in cars:
        enrich_car_for_garage(car)

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
        upload_result = store_public_image(photo, "profile", current_app.config["PROFILE_UPLOAD"])
        if upload_result.get("ok"):
            current_user.profile_photo = upload_result["stored_value"]
        else:
            current_app.logger.warning("profile_photo_upload_failed reason=%s", upload_result.get("reason"))
            flash("Profile photo could not be uploaded. Other profile details were saved.")

    db.session.commit()
    _sync_current_user_profile()
    flash("Profile updated successfully")
    return redirect("/profile")


@user_bp.route("/api/session")
def api_session():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "user": None, "cars": [], "support": {"help_report_url": "/api/help-report"}})

    cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.id.desc()).all()
    return jsonify({
        "authenticated": True,
        "user": serialize_user(current_user),
        "cars": [serialize_car(car) for car in cars],
        "support": {"help_report_url": "/api/help-report"},
    })


@user_bp.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    auth_error = _require_api_auth()
    if auth_error:
        return auth_error

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


@user_bp.route("/api/cars", methods=["GET", "POST"])
def api_cars():
    auth_error = _require_api_auth()
    if auth_error:
        return auth_error

    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        if not (payload.get("brand") or payload.get("model")):
            return jsonify({"status": "error", "message": "brand or model is required"}), 400

        car = Car(owner_id=current_user.id)
        _apply_car_payload(car, payload)
        if payload.get("is_default") or not Car.query.filter_by(owner_id=current_user.id).first():
            Car.query.filter_by(owner_id=current_user.id).update({"is_default": False})
            car.is_default = True

        db.session.add(car)
        db.session.commit()
        return jsonify({"status": "success", "car": serialize_car(car)}), 201

    cars = Car.query.filter_by(owner_id=current_user.id).order_by(Car.id.desc()).all()
    return jsonify({"status": "success", "cars": [serialize_car(car) for car in cars]})


@user_bp.route("/api/cars/<int:car_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def api_car_detail(car_id):
    auth_error = _require_api_auth()
    if auth_error:
        return auth_error

    car = Car.query.get_or_404(car_id)
    if car.owner_id != current_user.id:
        return jsonify({"status": "error", "message": "car not found"}), 404

    if request.method == "GET":
        return jsonify({"status": "success", "car": serialize_car(car)})

    if request.method in {"PUT", "PATCH"}:
        payload = request.get_json(silent=True) or request.form
        _apply_car_payload(car, payload)
        db.session.commit()
        return jsonify({"status": "success", "car": serialize_car(car)})

    db.session.delete(car)
    db.session.commit()
    return jsonify({"status": "success"})


@user_bp.route("/api/cars/<int:car_id>/default", methods=["POST"])
def api_set_default_car(car_id):
    auth_error = _require_api_auth()
    if auth_error:
        return auth_error

    car = Car.query.get_or_404(car_id)
    if car.owner_id != current_user.id:
        return jsonify({"status": "error", "message": "car not found"}), 404

    Car.query.filter_by(owner_id=current_user.id).update({"is_default": False})
    car.is_default = True
    db.session.commit()
    return jsonify({"status": "success", "car": serialize_car(car)})
