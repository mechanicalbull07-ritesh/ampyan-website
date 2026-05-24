from datetime import datetime, timedelta
import json
import os
import secrets
import re
from urllib import request as urllib_request

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from models.models import User, db
from services.email_service import send_email

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8

ADMIN_EMAILS = [
    "mechanicalbull07@gmail.com",
]
ADMIN_EMAIL_SET = {email.lower() for email in ADMIN_EMAILS}


def _ampyan_api_base_url():
    return (os.environ.get("AMPYAN_API_BASE_URL") or "https://api.ampyan.com").rstrip("/")


def _email_verification_required():
    return os.environ.get("REQUIRE_EMAIL_VERIFICATION", "").strip().lower() == "true"


def _sync_profile(name, email, phone=""):
    payload = json.dumps({"name": name, "email": email, "phone": phone, "user_email": email}).encode("utf-8")
    req = urllib_request.Request(
        f"{_ampyan_api_base_url()}/profile/sync",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=3):
            return True
    except Exception as exc:
        current_app.logger.warning("AMPYAN auth/profile sync failed: %s", exc)
        return False


def _apply_admin_policy(user):
    email = (user.email or "").strip().lower()
    if email in ADMIN_EMAIL_SET:
        user.role = "admin"
        return True
    if user.role == "admin":
        user.role = "user"
        return True
    return False


def _api_user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "mobile": user.mobile,
        "role": user.role,
        "city": user.city,
        "state": user.state,
        "country": user.country,
        "pincode": user.pincode,
        "badge": user.badge,
        "reputation": user.reputation,
        "posts_count": user.posts_count,
        "email_verified": user.email_verified,
        "profile_photo": user.profile_photo,
    }


def _commit_new_user_with_id_fallback(user):
    try:
        db.session.add(user)
        db.session.commit()
        return
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("User insert needed id fallback: %s", exc.__class__.__name__)
        message = str(exc).lower()
        if "null value" not in message or "id" not in message:
            raise

        next_id = (db.session.query(func.max(User.id)).scalar() or 0) + 1
        user.id = next_id
        db.session.add(user)
        db.session.commit()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = (request.form.get("username") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password")

            if not username or not email or not password:
                flash("Username, email and password are required.")
                return redirect(url_for("auth.register"))
            if not EMAIL_RE.match(email):
                flash("Please enter a valid email address.")
                return redirect(url_for("auth.register"))
            if len(password) < MIN_PASSWORD_LENGTH:
                flash("Password should be at least 8 characters.")
                return redirect(url_for("auth.register"))

            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                flash("Username already exists.")
                return redirect(url_for("auth.register"))

            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash("Email already registered.")
                return redirect(url_for("auth.register"))

            hashed_password = generate_password_hash(password)
            require_verification = _email_verification_required()
            token = secrets.token_urlsafe(32) if require_verification else None
            expiry = datetime.utcnow() + timedelta(minutes=30) if require_verification else None

            new_user = User(
                username=username,
                mobile="",
                email=email,
                password=hashed_password,
                role="user",
                is_banned=False,
                email_verified=not require_verification,
                verification_token=token,
                verification_token_expiry=expiry,
                reputation=0,
                posts_count=0,
                helpful_answers=0,
                contributor_score=0,
                badge="New Member",
            )

            _commit_new_user_with_id_fallback(new_user)
            _sync_profile(username, email, new_user.mobile or "")

            if require_verification:
                verification_link = url_for("verify_email", token=token, _external=True)
                mail = current_app.extensions.get("mail")
                send_email(
                    mail,
                    email,
                    "Verify your Motrnoix AMPYAN account",
                    f"Click this link to verify your account:\n\n{verification_link}",
                )
                flash("Account created. Please verify your email.")
            else:
                flash("Account created. You can login now.")
            return redirect(url_for("auth.login"))
        except Exception as exc:
            db.session.rollback()
            current_app.logger.warning("Registration failed: %s", exc.__class__.__name__)
            flash(f"Registration failed: {exc.__class__.__name__}")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next")

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Username/email and password are required.")
            return redirect(url_for("auth.login"))

        user = User.query.filter((User.username == username) | (User.email == username.lower())).first()

        if user and check_password_hash(user.password, password):
            if getattr(user, "is_managed_persona", False):
                flash("This account is managed by AMPYAN admin and cannot login directly.")
                return redirect(url_for("auth.login"))

            if _apply_admin_policy(user):
                db.session.commit()

            if user.is_banned:
                flash("Your account has been banned.")
                return redirect(url_for("auth.login"))

            if _email_verification_required() and not user.email_verified:
                flash("Please verify your email before logging in.")
                return redirect(url_for("auth.login"))

            login_user(user)
            _sync_profile(user.username, user.email, user.mobile or "")

            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect("/community")

        flash("Invalid credentials")

    return render_template("auth.html")


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or request.form
    username = (payload.get("username") or payload.get("email") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify({"status": "error", "message": "username/email and password are required"}), 400

    user = User.query.filter((User.username == username) | (User.email == username.lower())).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"status": "error", "message": "invalid credentials"}), 401

    if getattr(user, "is_managed_persona", False):
        return jsonify({"status": "error", "message": "managed personas cannot login directly"}), 403

    if _apply_admin_policy(user):
        db.session.commit()

    if user.is_banned:
        return jsonify({"status": "error", "message": "account banned"}), 403

    if _email_verification_required() and not user.email_verified:
        return jsonify({"status": "error", "message": "email verification required"}), 403

    login_user(user)
    _sync_profile(user.username, user.email, user.mobile or "")
    return jsonify({
        "status": "success",
        "authenticated": True,
        "user": _api_user_payload(user),
    })


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    logout_user()
    return jsonify({"status": "success", "authenticated": False})


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect("/")
