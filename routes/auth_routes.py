from datetime import datetime, timedelta
import json
import os
import secrets
import traceback
from urllib import request as urllib_request

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from models.models import User, db
from services.email_service import send_email

auth_bp = Blueprint("auth", __name__)

ADMIN_EMAILS = [
    "dabasdeepak676@gmail.com",
    "riteshsingh1609@gmail.com",
    "channelspeed16@gmail.com",
    "mechanicalbull@gmail.com",
    "mechanicalbull07@gmail.com",
]


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
        with urllib_request.urlopen(req, timeout=8):
            return True
    except Exception as exc:
        current_app.logger.warning("AMPYAN auth/profile sync failed: %s", exc)
        return False


def _commit_new_user_with_id_fallback(user):
    try:
        db.session.add(user)
        db.session.commit()
        return
    except Exception as exc:
        db.session.rollback()
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
                email=email,
                password=hashed_password,
                role="user",
                email_verified=not require_verification,
                verification_token=token,
                verification_token_expiry=expiry,
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
            print("REGISTER ERROR:", str(exc))
            traceback.print_exc()
            flash("Registration failed. Please try again.")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next")

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter((User.username == username) | (User.email == username.lower())).first()

        if user and check_password_hash(user.password, password):
            if user.email in ADMIN_EMAILS:
                user.role = "admin"
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


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect("/")
