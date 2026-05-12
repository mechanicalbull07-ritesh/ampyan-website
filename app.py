print("STEP 1 START")

# ================= ENV LOAD =================
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("ENV loaded")
except Exception:
    print("ENV load skipped")

# ================= DIAGNOSTIC ENGINE =================
# from ai_engine.diagnostic_engine import diagnose_vehicle
print("Diagnostic engine loaded")

# ================= FAILURE DATABASE =================
from failure_database import FAILURE_DATABASE
print("Failure database loaded")

# ================= FLASK =================
from flask import Flask, Response, g, render_template, request, redirect, flash, url_for, jsonify
from sqlalchemy import func, inspect, text
print("Flask core loaded")

# ================= MODELS =================
from models.models import db, User, Post, Comment, Vote, News, NewsReply, Video, VideoReply, DiagnosticLearning, HelpReport, Car, CarCommunity, WebsiteVisit, WebsiteEvent
print("Models loaded")

# ================= SECURITY =================
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
print("Security modules loaded")

# ================= ROUTES =================
from routes.auth_routes import auth_bp
print("Auth routes loaded")

from routes.community_routes import community_bp
print("Community routes loaded")

from routes.ai_routes import ai_bp
print("AI routes loaded")

from routes.admin_routes import admin_bp
print("Admin routes loaded")

# ================= SERVICES =================
from services.email_service import send_email
print("Email service loaded")

# ================= OTHER IMPORTS =================
from flask import session
import os
from PIL import Image
from collections import defaultdict, deque
import re
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from authlib.integrations.flask_client import OAuth
from routes.main_routes import main_bp
from routes.garage_routes import garage_bp
from routes.tools_routes import tools_bp
from routes.user_routes import user_bp
from routes.auth_routes import ADMIN_EMAILS
from ai_engine.diagnostic_engine import diagnose_vehicle
from ai_engine.response_formatter import enrich_diagnosis_results

print("All imports completed")



import secrets

def ai_diagnose(problem, car):

    problem = problem.lower()

    results = []

    # Brake vibration
    if "vibration" in problem and "brake" in problem:

        results.append({
            "issue": "Brake Disc Warp",
            "confidence": 78,
            "reason": "Vibration during braking often indicates warped brake discs."
        })

        results.append({
            "issue": "Brake Pad Wear",
            "confidence": 52,
            "reason": "Uneven brake pad wear can cause vibration."
        })

        results.append({
            "issue": "Wheel Balancing",
            "confidence": 31,
            "reason": "Improper wheel balance may create vibration."
        })

    # Engine vibration
    elif "vibration" in problem:

        results.append({
            "issue": "Engine Mount Damage",
            "confidence": 70,
            "reason": "Engine mounts absorb vibration."
        })

        results.append({
            "issue": "Wheel Balancing",
            "confidence": 45,
            "reason": "Wheel imbalance can cause vibration."
        })

    # Noise issues
    elif "noise" in problem or "sound" in problem:

        results.append({
            "issue": "Suspension Wear",
            "confidence": 65,
            "reason": "Suspension components often produce noise."
        })

        results.append({
            "issue": "Bearing Damage",
            "confidence": 50,
            "reason": "Wheel bearings may create humming noise."
        })

    # Overheating
    elif "overheat" in problem or "temperature" in problem:

        results.append({
            "issue": "Low Coolant",
            "confidence": 75,
            "reason": "Low coolant commonly causes overheating."
        })

        results.append({
            "issue": "Radiator Blockage",
            "confidence": 40,
            "reason": "Blocked radiator reduces cooling."
        })

    else:

        results.append({
            "issue": "Unknown Issue",
            "confidence": 20,
            "reason": "Problem needs manual inspection."
        })

    return results

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
IS_PRODUCTION = os.environ.get("ENV", "").lower() == "production" or os.environ.get("RENDER", "").lower() == "true"

app.register_blueprint(auth_bp)
app.register_blueprint(community_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(main_bp)
app.register_blueprint(garage_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(user_bp)

print("Motrnoix AMPYAN server booting...")

# ================= FILE SIZE LIMIT =================
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# ================= ALLOWED IMAGE TYPES =================

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
IMAGE_FORMATS = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}

def compress_image(image_path):

    try:

        with Image.open(image_path) as img:
            image_format = IMAGE_FORMATS.get(image_path.rsplit(".", 1)[-1].lower(), img.format)
            if image_format == "JPEG":
                img = img.convert("RGB")
            elif image_format == "PNG" and img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")

            img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

            save_options = {"optimize": True}
            if image_format in {"JPEG", "WEBP"}:
                save_options["quality"] = 78

            img.save(image_path, format=image_format, **save_options)

    except Exception as e:
        app.logger.warning("Image compression failed: %s", e.__class__.__name__)

def safe_image_check(file_path):

    try:
        img = Image.open(file_path)
        img.verify()

        if img.format.lower() not in ["jpeg","png","webp"]:
            return False

        return True

    except:
        return False

def save_uploaded_image(image_file, folder, prefix):
    if not image_file or image_file.filename == "":
        return None

    original_filename = secure_filename(image_file.filename)
    if not allowed_file(original_filename):
        return None

    extension = original_filename.rsplit(".", 1)[1].lower()
    filename = f"{prefix}_{secrets.token_hex(8)}.{extension}"
    upload_path = os.path.join(folder, filename)
    image_file.save(upload_path)

    if not safe_image_check(upload_path):
        try:
            os.remove(upload_path)
        except OSError:
            pass
        return None

    compress_image(upload_path)
    return filename
ADMIN_EMAILS = [
"dabasdeepak676@gmail.com",
"riteshsingh1609@gmail.com",
"channelspeed16@gmail.com",
"mechanicalbull@gmail.com",
"mechanicalbull07@gmail.com"
]
@app.context_processor
def inject_admin_emails():
    return dict(ADMIN_EMAILS=ADMIN_EMAILS)

def static_image_url_if_exists(folder, filename):
    if not filename:
        return None

    candidates = []
    for candidate in (filename, secure_filename(filename)):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        relative_path = os.path.join(folder, candidate)
        absolute_path = os.path.join(app.static_folder, relative_path)
        if os.path.isfile(absolute_path):
            return url_for("static", filename=relative_path.replace(os.sep, "/"))

    return None

@app.context_processor
def inject_image_helpers():
    return dict(
        news_image_url=lambda filename: static_image_url_if_exists("news_images", filename)
    )
    
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = ("Motrnoix AMPYAN", os.environ.get("MAIL_FROM"))

mail = Mail(app)

# csrf = CSRFProtect(app)

# ===============================
# DATABASE CONFIG (LOCAL + PROD)
# ===============================
@app.route("/test-email")
def test_email():
    if IS_PRODUCTION:
        return "Not found", 404

    send_email(
        mail,
        "YOUR_EMAIL@gmail.com",
        "Motrnoix AMPYAN Test Email",
        "SMTP working!"
    )

    return "Email sent"
database_url = os.environ.get("DATABASE_URL")

# Render PostgreSQL compatibility fix
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

secret_key = os.environ.get("SECRET_KEY")
if IS_PRODUCTION and not secret_key:
    raise RuntimeError("SECRET_KEY is required in production")

app.secret_key = secret_key or "local-dev-secret"
app.config["SECRET_KEY"] = app.secret_key
app.config["PREFERRED_URL_SCHEME"] = "https" if IS_PRODUCTION else "http"
app.config["DEBUG"] = False
app.config["PROPAGATE_EXCEPTIONS"] = False

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# 🔐 Production Security Settings
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
if IS_PRODUCTION:
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = True

oauth = OAuth(app)
GOOGLE_PRODUCTION_REDIRECT_URI = "https://ampyan.com/google/callback"
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


UPLOAD_FOLDER = "static/news_images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# POST IMAGE UPLOAD FOLDER

POST_IMAGE_UPLOAD = "static/post_images"
app.config["POST_IMAGE_UPLOAD"] = POST_IMAGE_UPLOAD



if not os.path.exists(POST_IMAGE_UPLOAD):
    os.makedirs(POST_IMAGE_UPLOAD)


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):

    return "." in filename and \
    filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

if not os.path.exists(POST_IMAGE_UPLOAD):
    os.makedirs(POST_IMAGE_UPLOAD)

PROFILE_UPLOAD = "static/profile_images"
app.config["PROFILE_UPLOAD"] = PROFILE_UPLOAD

if not os.path.exists(PROFILE_UPLOAD):
    os.makedirs(PROFILE_UPLOAD)


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

conversation_memory = defaultdict(list)
database_init_lock = threading.Lock()
database_initialized = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

from email.header import Header

# ================= VIDEOS =================

def get_youtube_embed_url(youtube_url):
    parsed_url = urlparse(youtube_url.strip())
    host = parsed_url.netloc.lower().replace("www.", "")
    path_parts = [part for part in parsed_url.path.split("/") if part]

    video_id = None

    if host == "youtu.be" and path_parts:
        video_id = path_parts[0]
    elif host in {"youtube.com", "m.youtube.com"}:
        if parsed_url.path == "/watch":
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        elif path_parts and path_parts[0] in {"shorts", "embed"} and len(path_parts) > 1:
            video_id = path_parts[1]

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{6,20}", video_id):
        return None

    return f"https://www.youtube.com/embed/{video_id}"

@app.route("/videos", methods=["GET", "POST"])
def videos():
    is_admin = current_user.is_authenticated and current_user.role == "admin"

    if request.method == "POST":
        if not is_admin:
            flash("Only admin can add videos.", "error")
            return redirect(url_for("videos"))

        title = request.form.get("title", "").strip()
        youtube_url = request.form.get("youtube_url", "").strip()
        embed_url = get_youtube_embed_url(youtube_url)

        if not title or not youtube_url:
            flash("Please enter both video title and YouTube link.", "error")
            return redirect(url_for("videos"))

        if not embed_url:
            flash("Please enter a valid YouTube video link.", "error")
            return redirect(url_for("videos"))

        video = Video(title=title, youtube_url=youtube_url, embed_url=embed_url)
        db.session.add(video)
        db.session.commit()
        flash("Video added successfully.", "success")
        return redirect(url_for("videos"))

    videos = Video.query.order_by(Video.created_at.desc()).all()
    for video in videos:
        video.reply_threads = [reply for reply in video.replies if reply.parent_id is None]
        video.reply_count = len(video.replies)

    return render_template(
        "videos.html",
        videos=videos,
        is_admin=is_admin
    )


@app.route("/videos/<int:video_id>/edit", methods=["GET", "POST"])
@login_required
def edit_video(video_id):
    if current_user.role != "admin":
        return "Access Denied"

    video = Video.query.get_or_404(video_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        youtube_url = request.form.get("youtube_url", "").strip()
        embed_url = get_youtube_embed_url(youtube_url)

        if not title or not youtube_url:
            flash("Please enter both video title and YouTube link.", "error")
            return redirect(url_for("edit_video", video_id=video.id))

        if not embed_url:
            flash("Please enter a valid YouTube video link.", "error")
            return redirect(url_for("edit_video", video_id=video.id))

        video.title = title
        video.youtube_url = youtube_url
        video.embed_url = embed_url
        db.session.commit()
        flash("Video updated successfully.", "success")
        return redirect(url_for("videos"))

    return render_template("edit_video.html", video=video)


@app.route("/videos/<int:video_id>/delete", methods=["POST"])
@login_required
def delete_video(video_id):
    if current_user.role != "admin":
        return "Access Denied"

    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash("Video deleted successfully.", "success")
    return redirect(url_for("videos"))


@app.route("/videos/<int:video_id>/reply", methods=["POST"])
@login_required
def add_video_reply(video_id):
    video = Video.query.get_or_404(video_id)
    content = (request.form.get("content") or "").strip()
    parent_id = request.form.get("parent_id") or None

    if content:
        if parent_id and not VideoReply.query.filter_by(id=parent_id, video_id=video.id).first():
            parent_id = None
        db.session.add(
            VideoReply(
                content=content,
                user_id=current_user.id,
                video_id=video.id,
                parent_id=parent_id,
            )
        )
        db.session.commit()

    return redirect(f"{url_for('videos')}#video-{video.id}")


@app.route("/videos/reply/<int:reply_id>/edit", methods=["GET", "POST"])
@login_required
def edit_video_reply(reply_id):
    reply = VideoReply.query.get_or_404(reply_id)
    if reply.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    if request.method == "POST":
        reply.content = (request.form.get("content") or "").strip()
        db.session.commit()
        return redirect(f"{url_for('videos')}#video-{reply.video_id}")

    return render_template("edit_comment.html", comment=reply)


@app.route("/videos/reply/<int:reply_id>/delete", methods=["POST"])
@login_required
def delete_video_reply(reply_id):
    reply = VideoReply.query.get_or_404(reply_id)
    if reply.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    video_id = reply.video_id
    db.session.delete(reply)
    db.session.commit()
    return redirect(f"{url_for('videos')}#video-{video_id}")


# ================= AUTOHIVE KNOWLEDGE BASE =================

KNOWLEDGE_BASE = {

    "buying": {
        "city": "For city driving choose compact car, light steering, good visibility and automatic transmission.",
        "highway": "For highway choose stable chassis, strong braking, minimum 4-star safety and refined engine.",
        "default": "Choose car based on usage: City → Hatchback, Highway → Sedan, Bad roads → Compact SUV. Always check service cost and resale."
    },

    "service": {
        "default": "Service warning ⚠️ Always ask for old parts back. Avoid unnecessary throttle cleaning and early brake replacement."
    },

    "gear": {
        "morning": "Morning hard gear shift usually happens due to cold transmission oil. If it improves after 5–10 min, it's normal.",
        "default": "Hard gear shift can be due to clutch wear or low transmission oil. Avoid half-clutch driving."
    },

    "engine": {
        "vibration": "Engine vibration may indicate mounting issue, misfire or fuel quality problem. Do not ignore.",
        "default": "Engine noise can be due to low oil, timing belt wear or tappet issue."
    },

    "ev": {
        "default": "EV is best for city usage. Check 8-year battery warranty and charging availability in your area."
    }

}

# ================= REPUTATION SYSTEM =================

def update_user_reputation(user):

    user.reputation = user.posts_count * 5 + user.helpful_answers * 10

    if user.reputation >= 1000:
        user.badge = "Master Mechanic"

    elif user.reputation >= 500:
        user.badge = "Car Expert"

    elif user.reputation >= 200:
        user.badge = "Car Enthusiast"

    elif user.reputation >= 50:
        user.badge = "Contributor"

    else:
        user.badge = "Member"


def build_unique_username(base_username):

    candidate = re.sub(r"[^a-zA-Z0-9_]", "", (base_username or "").strip()) or "user"
    suffix = 1
    unique_candidate = candidate

    while User.query.filter_by(username=unique_candidate).first():
        suffix += 1
        unique_candidate = f"{candidate}{suffix}"

    return unique_candidate


def commit_new_user_with_id_fallback(user):
    try:
        db.session.add(user)
        db.session.commit()
        return
    except Exception as exc:
        db.session.rollback()
        app.logger.warning("Google user insert needed id fallback: %s", exc.__class__.__name__)
        message = str(exc).lower()
        if "null value" not in message or "id" not in message:
            raise

        next_id = (db.session.query(func.max(User.id)).scalar() or 0) + 1
        user.id = next_id
        db.session.add(user)
        db.session.commit()

# ================= LOGIN =================

@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user:
        return user
    return None

# ================= ROUTES =================

@app.route("/login/google")
def google_login():
    missing_env = [
        key for key in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "SECRET_KEY")
        if not os.environ.get(key)
    ]
    if missing_env:
        app.logger.error("Google login is missing required environment variables")
        flash("Google login is not configured yet. Please check server configuration.")
        return redirect(url_for("auth.login"))

    redirect_uri = GOOGLE_PRODUCTION_REDIRECT_URI

    try:
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.warning("Google login redirect failed: %s", e.__class__.__name__)
        flash("Google login could not start. Please check Google OAuth redirect settings.")
        return redirect(url_for("auth.login"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/vision")
def vision():
    return render_template("vision.html")

@app.route("/speed16")
def speed16():
    return render_template("speed16.html")


@app.route("/yaanix")
def yaanix():
    return render_template("yaanix.html")

@app.route("/platform")
def platform():
    return render_template("platform.html")
 

@app.route("/google/callback")
def google_callback():
    try:
        token = google.authorize_access_token()

        user_info = token.get("userinfo") if isinstance(token, dict) else None

        if not user_info:
            user_info = google.get("userinfo").json()

        if not user_info:
            app.logger.warning("Google callback missing user profile data")
            flash("Google login failed. Please try again.")
            return redirect(url_for("auth.login"))

        email = (user_info.get("email") or "").strip().lower()

        if not email:
            app.logger.warning("Google callback missing email field")
            flash("Google login failed. Please try again.")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                username=build_unique_username(email.split("@")[0]),
                mobile="",
                email=email,
                password=generate_password_hash(secrets.token_urlsafe(16)),
                role="user",
                is_banned=False,
                email_verified=True,
                reputation=0,
                posts_count=0,
                helpful_answers=0,
                contributor_score=0,
                badge="New Member",
            )
            commit_new_user_with_id_fallback(user)

        # ✅ Admin assignment after user exists
        if user.email in ADMIN_EMAILS:
            user.role = "admin"
            db.session.commit()

        login_user(user)

        return redirect("/community")
    except Exception as e:
        db.session.rollback()
        app.logger.warning("Google callback failed: %s", e.__class__.__name__)
        flash("Google login failed. Please try again.")
        return redirect(url_for("auth.login"))


# ================= SECURITY BASICS =================

SENSITIVE_PATHS = {
    "/.env",
    "/.git",
    "/.git/config",
    "/config",
    "/phpinfo",
    "/_environment",
    "/webroot",
    "/debug",
    "/console",
    "/server-status",
    "/wp-admin",
    "/wp-login.php",
    "/vendor",
    "/composer.json",
    "/package.json",
    "/node_modules",
}

RATE_LIMIT_RULES = {
    "/login": (20, 60),
    "/register": (12, 60),
    "/forgot-password": (8, 60),
    "/login/google": (20, 60),
    "/google/callback": (30, 60),
    "/tools/ai-diagnosis": (30, 60),
    "/tools/ai-diagnosis-followup": (30, 60),
    "/api/help-report": (12, 60),
    "/submit_feedback": (20, 60),
}
rate_limit_hits = defaultdict(deque)
rate_limit_lock = threading.Lock()


def client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()


def wants_json_response():
    return request.path.startswith("/api") or "application/json" in request.headers.get("Accept", "")


def security_path_matches(path):
    normalized = (path or "").rstrip("/") or "/"
    return normalized in SENSITIVE_PATHS or any(normalized.startswith(f"{prefix}/") for prefix in ("/.git", "/vendor", "/node_modules"))


def sanitize_event_text(value, max_length=160):
    cleaned = re.sub(r"\s+", " ", (value or "").strip())
    return cleaned[:max_length]


def normalize_event_url(value):
    parsed = urlparse((value or "").strip())
    if parsed.netloc and parsed.netloc not in {"ampyan.com", "www.ampyan.com"}:
        return parsed.netloc[:500]
    path = parsed.path or "/"
    return path[:500]


def record_website_event(event_type, label="", target_url="", severity="info", path=None):
    try:
        if not database_initialized:
            initialize_database()
        visitor_id = request.cookies.get("ampyan_visitor_id") or getattr(g, "set_visitor_cookie", None)
        event = WebsiteEvent(
            event_type=sanitize_event_text(event_type, 40),
            label=sanitize_event_text(label, 160),
            path=(path or request.path or "")[:500],
            target_url=normalize_event_url(target_url),
            visitor_id=visitor_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=client_ip()[:50],
            referrer=(request.referrer or "")[:500],
            user_agent=(request.headers.get("User-Agent", "") or "")[:500],
            device_type=detect_device_type(request.headers.get("User-Agent", "")),
            is_authenticated=current_user.is_authenticated,
            severity=sanitize_event_text(severity, 20) or "info",
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        db.session.rollback()


def rate_limited(path):
    rule = RATE_LIMIT_RULES.get(path)
    if not rule:
        return False
    max_hits, window_seconds = rule
    key = (client_ip(), path)
    now = time.time()
    with rate_limit_lock:
        hits = rate_limit_hits[key]
        while hits and now - hits[0] > window_seconds:
            hits.popleft()
        if len(hits) >= max_hits:
            return True
        hits.append(now)
    return False


@app.before_request
def security_guard():
    forwarded_proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    if (
        IS_PRODUCTION
        and forwarded_proto == "http"
        and request.host in {"ampyan.com", "www.ampyan.com"}
    ):
        return redirect(f"https://ampyan.com{request.full_path.rstrip('?')}", code=301)

    if IS_PRODUCTION and request.host == "www.ampyan.com":
        return redirect(f"https://ampyan.com{request.full_path.rstrip('?')}", code=301)

    if security_path_matches(request.path):
        record_website_event(
            "security",
            label="Blocked sensitive path",
            target_url=request.path,
            severity="high",
            path=request.path,
        )
        return "Not found", 404

    content_length = request.content_length or 0
    if content_length > app.config["MAX_CONTENT_LENGTH"]:
        return jsonify({"status": "error", "message": "Request too large"}), 413

    if rate_limited(request.path):
        record_website_event(
            "security",
            label="Rate limit triggered",
            target_url=request.path,
            severity="medium",
            path=request.path,
        )
        if wants_json_response():
            return jsonify({"status": "error", "message": "Too many requests. Please try again soon."}), 429
        return "Too many requests. Please try again soon.", 429

# ================= WEBSITE VISIT TRACKER =================

def should_track_page_visit():
    if request.method != "GET":
        return False

    excluded_prefixes = (
        "/static",
        "/api",
        "/admin",
        "/login",
        "/logout",
        "/register",
        "/google",
        "/healthz",
        "/version",
        "/symptom-suggest",
        "/favicon",
    )

    if request.path.startswith(excluded_prefixes):
        return False

    if "." in request.path.rsplit("/", 1)[-1]:
        return False

    return True


def detect_device_type(user_agent):
    ua = (user_agent or "").lower()
    if any(token in ua for token in ["iphone", "android", "mobile"]):
        return "mobile"
    if any(token in ua for token in ["ipad", "tablet"]):
        return "tablet"
    return "desktop"


@app.before_request
def track_visit():

    try:

        if not should_track_page_visit():
            return

        if not database_initialized:
            initialize_database()

        visitor_id = request.cookies.get("ampyan_visitor_id")

        if not visitor_id:
            visitor_id = secrets.token_urlsafe(24)
            g.set_visitor_cookie = visitor_id

        user_agent = request.headers.get("User-Agent", "")

        visit = WebsiteVisit(
            ip_address=request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip(),
            visitor_id=visitor_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            path=request.path,
            method=request.method,
            referrer=request.referrer,
            user_agent=user_agent[:500],
            device_type=detect_device_type(user_agent),
            is_authenticated=current_user.is_authenticated,
            is_page_view=True
        )

        db.session.add(visit)
        db.session.commit()

    except Exception as e:

        db.session.rollback()


@app.after_request
def attach_visitor_cookie(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://www.instagram.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data: https:; "
        "frame-src https://www.youtube.com https://www.youtube-nocookie.com https://www.instagram.com; "
        "connect-src 'self' https://ampyan-api.onrender.com https://api.ampyan.com; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
    )

    visitor_id = getattr(g, "set_visitor_cookie", None)
    if visitor_id:
        response.set_cookie(
            "ampyan_visitor_id",
            visitor_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="Lax",
            secure=request.is_secure,
        )
    return response

@app.before_request
def reset_ai_usage():

    if not current_user.is_authenticated:
        return

    today = datetime.utcnow().date()

    if not current_user.ai_last_reset or current_user.ai_last_reset.date() != today:

        current_user.ai_uses_today = 0
        current_user.ai_last_reset = datetime.utcnow()

        try:
            db.session.commit()
        except:
            db.session.rollback()


# ================= AI DIAGNOSE =================

@app.route("/tools/ai-diagnosis", methods=["GET","POST"])
def diagnose():

    # ===== Load cars =====
    if current_user.is_authenticated:
        cars = Car.query.filter_by(owner_id=current_user.id).all()
        default_car = next((c for c in cars if c.is_default), None)
    else:
        cars = []
        default_car = None

    # ===== POST =====
    if request.method == "POST":

        problem = request.form.get("problem", "")
        car_id = request.form.get("car_id")

        car = Car.query.get(car_id)

        if not car:
            flash("Please select a car.")
            return redirect("/tools/ai-diagnosis")

        # ✅ AI ENGINE
        results, questions = diagnose_vehicle(problem, car=car)

        app.logger.info("AI diagnosis completed with %s result(s)", len(results or []))

        # ✅ SAVE
        if results:
            learning = DiagnosticLearning(
                user_id=current_user.id if current_user.is_authenticated else None,
                problem_text=problem,
                predicted_issue=results[0]["issue"],
                confidence=results[0]["confidence"]
            )
            db.session.add(learning)
            db.session.commit()

        # ✅ FINAL OUTPUT PAGE
        diagnosis_view = enrich_diagnosis_results(results, problem)
        return render_template(
            "diagnosis_result.html",
            results=diagnosis_view["results"],
            ui_text=diagnosis_view["ui_text"],
            response_language=diagnosis_view["language_code"],
            response_language_name=diagnosis_view["language_name"],
            questions=questions,
            problem=problem,
            car=car
        )

    # ===== GET =====
    return render_template(
        "ai_diagnosis.html",
        cars=cars,
        default_car=default_car
    )

    # ================= MAIN AI ENGINE =================


    # ================= SAVE =================

    if results:

        learning = DiagnosticLearning(
            user_id=current_user.id if current_user.is_authenticated else None,
            problem_text=problem,
            predicted_issue=results[0]["issue"],
            confidence=results[0]["confidence"]
        )

        db.session.add(learning)
        db.session.commit()

    return render_template(
    "diagnosis_result.html",
    results=results,
    questions=questions,
    problem=problem,
    car=car
)

    # ===== Guest limit =====
    if not current_user.is_authenticated:

        guest_uses = session.get("guest_uses", 0)

        if guest_uses >= 1:
            flash("Please login to continue diagnosing your car.")
            return redirect("/login")

        session["guest_uses"] = guest_uses + 1

    # ===== Load cars =====
    if current_user.is_authenticated:
        cars = Car.query.filter_by(owner_id=current_user.id).all()
    else:
        cars = []

    # ===== Form submit =====
    if request.method == "POST":

        problem = request.form.get("problem")
        car_id = request.form.get("car_id")

        car = Car.query.get(car_id)

        if not car:
            flash("Please select a car.")
            return redirect("/tools/ai-diagnosis")



        # ===== Save diagnosis history =====
        if results:

            learning = DiagnosticLearning(
                user_id=current_user.id if current_user.is_authenticated else None,
                problem_text=problem,
                predicted_issue=results[0]["issue"],
                confidence=results[0]["confidence"]
            )

            db.session.add(learning)
            db.session.commit()

        return render_template(
    "ai_diagnosis.html",
    results=results,
    questions=questions,
    problem=problem,
    car=car,
    cars=cars,
    default_car=default_car
)
@app.route("/tools/ai-diagnosis-followup", methods=["POST"])
def diagnosis_followup():

    problem = request.form.get("problem")
    car_id = request.form.get("car_id")

    answers = dict(request.form)

    # Basic refinement logic
    final_results = []

    if answers.get("steering_vibration") == "yes":
        final_results.append({
            "issue": "Brake Disc Warp",
            "confidence": 90,
            "reason": "Steering vibration strongly indicates disc warp."
        })

    else:
        final_results.append({
            "issue": "Brake Pad Wear",
            "confidence": 65,
            "reason": "Less likely disc warp, more likely pad wear."
        })

    car = Car.query.get(car_id)

    diagnosis_view = enrich_diagnosis_results(final_results, problem)

    return render_template(
        "diagnosis_result.html",
        results=diagnosis_view["results"],
        ui_text=diagnosis_view["ui_text"],
        response_language=diagnosis_view["language_code"],
        response_language_name=diagnosis_view["language_name"],
        questions=[],
        problem=problem,
        car=car
    )





# ================= CREATE POST =================

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():

    if request.method == "POST":

        post = Post(
            title=request.form["title"],
            content=request.form["content"],
            user_id=current_user.id
        )

        db.session.add(post)

        current_user.posts_count += 1
        current_user.reputation += 5
        update_user_reputation(current_user)

        db.session.commit()

        return redirect("/community")

    return render_template("create.html")


# ================= SYMPTOM SUGGESTION =================

@app.route("/symptom-suggest")
def symptom_suggest():

    query = request.args.get("q","").lower().strip()

    if not query:
        return jsonify({"suggestions":[]})

    suggestions = []

    for failure in FAILURE_DATABASE:

        # problem match
        problem = failure.get("problem","").lower()

        if query in problem:
            suggestions.append(problem)

        # match individual words
        for word in problem.split():

            if query in word:
                suggestions.append(problem)

        # search symptoms
        for symptom in failure.get("symptoms",[]):

            s = symptom.lower()

            if query in s:
                suggestions.append(s)

            for w in s.split():

                if query in w:
                    suggestions.append(s)

    # remove duplicates
    suggestions = list(set(suggestions))

    # limit suggestions
    suggestions = suggestions[:10]

    return jsonify({"suggestions":suggestions})

# ================= NEWS =================

@app.route("/news")
def news_list():
    news_items = News.query.order_by(News.id.desc()).all()
    return render_template("news.html", news_items=news_items)


@app.route("/news/<int:news_id>")
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    news.reply_threads = [reply for reply in news.replies if reply.parent_id is None]
    news.reply_count = len(news.replies)
    return render_template("news_detail.html", news=news)


@app.route("/news/<int:news_id>/reply", methods=["POST"])
@login_required
def add_news_reply(news_id):
    news = News.query.get_or_404(news_id)
    content = (request.form.get("content") or "").strip()
    parent_id = request.form.get("parent_id") or None

    if content:
        if parent_id and not NewsReply.query.filter_by(id=parent_id, news_id=news.id).first():
            parent_id = None
        db.session.add(
            NewsReply(
                content=content,
                user_id=current_user.id,
                news_id=news.id,
                parent_id=parent_id,
            )
        )
        db.session.commit()

    return redirect(url_for("news_detail", news_id=news.id))


@app.route("/news/reply/<int:reply_id>/edit", methods=["GET", "POST"])
@login_required
def edit_news_reply(reply_id):
    reply = NewsReply.query.get_or_404(reply_id)
    if reply.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    if request.method == "POST":
        reply.content = (request.form.get("content") or "").strip()
        db.session.commit()
        return redirect(url_for("news_detail", news_id=reply.news_id))

    return render_template("edit_comment.html", comment=reply)


@app.route("/news/reply/<int:reply_id>/delete", methods=["POST"])
@login_required
def delete_news_reply(reply_id):
    reply = NewsReply.query.get_or_404(reply_id)
    if reply.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    news_id = reply.news_id
    db.session.delete(reply)
    db.session.commit()
    return redirect(url_for("news_detail", news_id=news_id))


@app.route("/admin/news/create", methods=["GET", "POST"])
@login_required
def create_news():
    if current_user.role != "admin":
        return "Access Denied"

    if request.method == "POST":

        image_file = request.files.get("image")
        filename = None

        if image_file and image_file.filename != "":
            filename = save_uploaded_image(image_file, app.config["UPLOAD_FOLDER"], "news")
            if not filename:
                flash("Please upload a valid PNG, JPG, JPEG or WebP image.", "error")
                return redirect(url_for("create_news"))

        news = News(
            title=request.form["title"],
            content=request.form["content"],
            image=filename
        )

        db.session.add(news)
        db.session.commit()

        return redirect("/news")

    return render_template("create_news.html")


import requests
# ================= EDIT NEWS =================

@app.route("/admin/news/edit/<int:news_id>", methods=["GET","POST"])
@login_required
def edit_news(news_id):

    if current_user.role != "admin":
        return "Access Denied"

    news = News.query.get_or_404(news_id)

    if request.method == "POST":

        news.title = request.form["title"]
        news.content = request.form["content"]

        image_file = request.files.get("image")

        if image_file and image_file.filename != "":
            filename = save_uploaded_image(image_file, app.config["UPLOAD_FOLDER"], f"news_{news.id}")
            if not filename:
                flash("Please upload a valid PNG, JPG, JPEG or WebP image.", "error")
                return redirect(url_for("edit_news", news_id=news.id))
            news.image = filename

        db.session.commit()

        return redirect("/news")

    return render_template("edit_news.html", news=news)
# ================= DELETE NEWS =================

@app.route("/admin/news/delete/<int:news_id>")
@login_required
def delete_news(news_id):

    if current_user.role != "admin":
        return "Access Denied"

    news = News.query.get_or_404(news_id)

    db.session.delete(news)
    db.session.commit()

    return redirect("/news")
# ================= LEGAL PAGES =================

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/help", methods=["GET", "POST"])
def help_center():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        category = request.form.get("category", "").strip()
        page_url = request.form.get("page_url", "").strip()
        message = request.form.get("message", "").strip()

        if not category or not message:
            flash("Please select a category and describe the issue.")
            return redirect("/help")

        report = HelpReport(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=name or (current_user.username if current_user.is_authenticated else None),
            email=email or (current_user.email if current_user.is_authenticated else None),
            category=category,
            page_url=page_url,
            message=message,
        )
        db.session.add(report)
        db.session.commit()
        flash("Thanks. Your report has been submitted to AMPYAN support.")
        return redirect("/help")

    return render_template("help.html")


@app.route("/api/help-report", methods=["POST"])
def api_help_report():
    payload = request.get_json(silent=True) or request.form
    category = (payload.get("category") or "").strip()
    message = (payload.get("message") or "").strip()
    email = (payload.get("email") or "").strip()

    if not category or not message:
        return jsonify({"status": "error", "message": "category and message are required"}), 400
    if len(message) > 2000:
        return jsonify({"status": "error", "message": "message is too long"}), 400
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"status": "error", "message": "valid email is required"}), 400

    report = HelpReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        name=(payload.get("name") or "").strip() or (current_user.username if current_user.is_authenticated else None),
        email=email or (current_user.email if current_user.is_authenticated else None),
        category=category,
        page_url=(payload.get("page_url") or payload.get("screen") or "").strip(),
        message=message,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"status": "success", "report_id": report.id})


@app.route("/api/track-event", methods=["POST"])
def api_track_event():
    payload = request.get_json(silent=True) or {}
    event_type = sanitize_event_text(payload.get("event_type") or "click", 40)

    if event_type != "click":
        return jsonify({"status": "error", "message": "unsupported event type"}), 400

    label = sanitize_event_text(payload.get("label") or "Click", 120)
    target_url = normalize_event_url(payload.get("target_url") or "")
    source_path = normalize_event_url(payload.get("path") or request.path)

    if not label and not target_url:
        return jsonify({"status": "error", "message": "event label or target is required"}), 400

    record_website_event(
        "click",
        label=label,
        target_url=target_url,
        severity="info",
        path=source_path,
    )
    return jsonify({"status": "success"})
# ================= FORGOT PASSWORD =================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Please enter a valid email address.")
            return redirect(url_for("forgot_password"))

        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(minutes=15)

            user.reset_token = token
            user.reset_token_expiry = expiry
            db.session.commit()

            reset_link = url_for("reset_password", token=token, _external=True)

            send_email(
    mail,
    email,
    "Reset your Motrnoix AMPYAN password",
    f"Click this link to reset your password:\n\n{reset_link}"
)

            flash("Reset link sent to your email.")
        else:
            flash("Email not found.")

    return render_template("forgot_password.html")



# ================= EDIT COMMENT =================

@app.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    if request.method == "POST":
        comment.content = request.form["content"]
        db.session.commit()
        return redirect(url_for("post_detail", post_id=comment.post_id))

    return render_template("edit_comment.html", comment=comment)


# ================= DELETE COMMENT =================

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id and current_user.role != "admin":
        return "Unauthorized"

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()

    return redirect(url_for("community.post_detail", post_id=post_id))

# ================= EMAIL VERIFICATION =================

@app.route("/verify-email/<token>")
def verify_email(token):

    user = User.query.filter_by(verification_token=token).first()

    if not user:
        return "Invalid or expired verification link."

    if user.verification_token_expiry < datetime.utcnow():
        return "Verification link expired."

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expiry = None

    db.session.commit()

    flash("Email verified successfully. You can now login.")

    return redirect(url_for("auth.login"))

# ================= RESET PASSWORD =================

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return "Invalid or expired token."

    if user.reset_token_expiry < datetime.utcnow():
        return "Token expired."

    if request.method == "POST":

        new_password = request.form.get("password")

        if not new_password or len(new_password) < 8:
            flash("Password should be at least 8 characters.")
            return redirect(request.url)

        user.password = generate_password_hash(new_password)

        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        flash("Password reset successful. Please login.")

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")

# ================= CREATE DB TABLES =================

def ensure_user_schema():
    """Add auth/profile columns that older databases may be missing."""
    inspector = inspect(db.engine)
    if not inspector.has_table("user"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("user")}
    dialect = db.engine.dialect.name
    string_type = "VARCHAR"
    datetime_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    bool_type = "BOOLEAN" if dialect == "postgresql" else "BOOLEAN"

    column_definitions = {
        "mobile": f"{string_type}(20)",
        "role": f"{string_type}(20) DEFAULT 'user'",
        "ai_uses_today": "INTEGER DEFAULT 0",
        "ai_last_reset": datetime_type,
        "email_verified": f"{bool_type} DEFAULT FALSE",
        "is_banned": f"{bool_type} DEFAULT FALSE",
        "reset_token": f"{string_type}(200)",
        "reset_token_expiry": datetime_type,
        "verification_token": f"{string_type}(200)",
        "verification_token_expiry": datetime_type,
        "profile_photo": f"{string_type}(200)",
        "city": f"{string_type}(100)",
        "state": f"{string_type}(100)",
        "country": f"{string_type}(100)",
        "pincode": f"{string_type}(20)",
        "reputation": "INTEGER DEFAULT 0",
        "posts_count": "INTEGER DEFAULT 0",
        "helpful_answers": "INTEGER DEFAULT 0",
        "contributor_score": "INTEGER DEFAULT 0",
        "badge": f"{string_type}(50) DEFAULT 'New Member'",
    }

    for column_name, column_definition in column_definitions.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_definition}'))

    if dialect == "postgresql":
        required_user_columns = {"id", "username", "email", "password"}
        for column in inspect(db.engine).get_columns("user"):
            column_name = column["name"]
            if column_name in required_user_columns or column.get("nullable", True):
                continue
            safe_column = column_name.replace('"', '""')
            db.session.execute(text(f'ALTER TABLE "user" ALTER COLUMN "{safe_column}" DROP NOT NULL'))

        db.session.execute(text('CREATE SEQUENCE IF NOT EXISTS user_id_seq OWNED BY "user".id'))
        db.session.execute(text("SELECT setval('user_id_seq', COALESCE((SELECT MAX(id) FROM \"user\"), 0) + 1, false)"))
        db.session.execute(text("ALTER TABLE \"user\" ALTER COLUMN id SET DEFAULT nextval('user_id_seq')"))

    db.session.commit()


def ensure_car_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table("car"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("car")}
    dialect = db.engine.dialect.name
    date_type = "DATE"

    column_definitions = {
        "insurance_expiry": date_type,
        "pollution_expiry": date_type,
    }

    for column_name, column_definition in column_definitions.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f"ALTER TABLE car ADD COLUMN {column_name} {column_definition}"))

    db.session.commit()


def ensure_website_visit_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table("website_visit"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("website_visit")}
    dialect = db.engine.dialect.name
    string_type = "VARCHAR"
    bool_type = "BOOLEAN" if dialect == "postgresql" else "BOOLEAN"

    column_definitions = {
        "visitor_id": f"{string_type}(80)",
        "user_id": "INTEGER",
        "path": f"{string_type}(500)",
        "method": f"{string_type}(10)",
        "referrer": f"{string_type}(500)",
        "user_agent": f"{string_type}(500)",
        "device_type": f"{string_type}(30)",
        "is_authenticated": f"{bool_type} DEFAULT FALSE",
        "is_page_view": f"{bool_type} DEFAULT TRUE",
    }

    for column_name, column_definition in column_definitions.items():
        if column_name in existing_columns:
            continue
        db.session.execute(text(f"ALTER TABLE website_visit ADD COLUMN {column_name} {column_definition}"))

    db.session.commit()


def ensure_reply_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table("comment"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("comment")}
    if "parent_id" not in existing_columns:
        db.session.execute(text("ALTER TABLE comment ADD COLUMN parent_id INTEGER"))

    db.session.commit()


def ensure_post_schema():
    inspector = inspect(db.engine)
    if not inspector.has_table("post"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("post")}
    if "community_id" not in existing_columns:
        db.session.execute(text("ALTER TABLE post ADD COLUMN community_id INTEGER"))

    db.session.commit()


def ensure_car_community_seed():
    seed_communities = [
        ("General Owners", "General car ownership questions, buying advice and everyday driving help."),
        ("Swift Community", "Swift owners discussing mileage, service, parts and city use."),
        ("Creta Community", "Creta owners comparing features, maintenance, tyres and road trips."),
        ("Thar Community", "Thar owners sharing off-road, modification and service experience."),
        ("Honda City Community", "Honda City owners discussing comfort, petrol CVT and long-term reliability."),
        ("EV Owners India", "EV owners talking charging, range, batteries and daily use."),
        ("Diesel Owners", "Diesel owners discussing DPF, mileage, turbo and service habits."),
    ]

    for name, description in seed_communities:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if not CarCommunity.query.filter_by(slug=slug).first():
            db.session.add(CarCommunity(name=name, slug=slug, description=description))

    db.session.commit()


def ensure_demo_community_seed():
    demo_authors = [
        ("AmanService", "demo.aman.service@example.com", "Service Guide", 84),
        ("CityDriver", "demo.city.driver@example.com", "Daily Driver", 62),
        ("HighwayRaj", "demo.highway.raj@example.com", "Road Tripper", 71),
        ("NehaAuto", "demo.neha.auto@example.com", "Helpful Member", 58),
        ("RaviGarage", "demo.ravi.garage@example.com", "Garage Expert", 92),
        ("MechVikas", "demo.mech.vikas@example.com", "Helpful Member", 56),
        ("MileageManoj", "demo.mileage.manoj@example.com", "Mileage Tracker", 64),
        ("BatteryBhai", "demo.battery.bhai@example.com", "Electrical Helper", 67),
        ("TyreTalks", "demo.tyre.talks@example.com", "Tyre Advisor", 59),
        ("FamilyCarNisha", "demo.family.nisha@example.com", "Family Driver", 61),
        ("DieselDev", "demo.diesel.dev@example.com", "Diesel Owner", 69),
        ("EVKaran", "demo.ev.karan@example.com", "EV Learner", 53),
    ]

    demo_posts = [
        {
            "user": ("AmanService", "demo.aman.service@example.com", "Service Guide", 84),
            "title": "Morning start ke time engine thoda rough idle karta hai",
            "content": "Petrol car cold start par 30-40 second RPM fluctuate karta hai. Warm hone ke baad normal ho jata hai. Kya injector cleaning karani chahiye?",
            "replies": [
                ("NehaAuto", "demo.neha.auto@example.com", "Pehle throttle body aur air filter check karao. Agar sirf cold start par hai to battery voltage aur spark plugs bhi scan me dekhna useful hoga."),
                ("RaviGarage", "demo.ravi.garage@example.com", "Injector cleaning tabhi karana jab misfire code ya fuel trim abnormal aaye. Basic scan se start karo."),
            ],
        },
        {
            "user": ("CityDriver", "demo.city.driver@example.com", "Daily Driver", 62),
            "title": "Mileage achanak 16 se 11 kmpl ho gaya",
            "content": "Same route aur same fuel pump hai. Tyre pressure normal lag raha hai. Service 2 mahine pehle hui thi.",
            "replies": [
                ("AmanService", "demo.aman.service@example.com", "Tyre pressure gauge se verify karo, air filter box properly locked hai ya nahi dekho, aur brake drag test karao."),
                ("MechVikas", "demo.mech.vikas@example.com", "Agar AC zyada use hua ya city traffic badha hai to drop normal ho sakta hai, but OBD fuel trim check best rahega."),
            ],
        },
        {
            "user": ("HighwayRaj", "demo.highway.raj@example.com", "Road Tripper", 71),
            "title": "Long trip se pehle kya maintenance checklist follow karu?",
            "content": "800 km highway run plan hai. Car 48,000 km par hai aur last service ko 6 months ho gaye.",
            "replies": [
                ("NehaAuto", "demo.neha.auto@example.com", "Engine oil level, coolant, brake fluid, spare tyre, jack, wiper blades aur all lights check karo."),
                ("RaviGarage", "demo.ravi.garage@example.com", "48k par brake pads aur tyres ka visual inspection zaroor karao. Wheel alignment bhi highway trip se pehle helpful hota hai."),
            ],
        },
    ]

    topics = [
        ("engine", "Engine light blink kar rahi hai aur pickup low lag raha hai", "Check engine light kabhi kabhi blink karti hai. Acceleration par car heavy feel hoti hai. Pehle scanner lagwana chahiye ya service center jana chahiye?"),
        ("mileage", "City mileage suddenly drop ho gaya", "Same route par mileage kam aa raha hai. Fuel pump same hai aur tyre pressure normal hai. Common checks kya honge?"),
        ("battery", "Battery morning me weak feel hoti hai", "Self start slow ho gaya hai, din me car normal start hoti hai. Battery test karwana better hai ya alternator check?"),
        ("brake", "Brake dabane par halka vibration aa raha hai", "High speed braking par steering me vibration feel hota hai. Disc skimming, pad replacement ya wheel balancing me se kya pehle check karu?"),
        ("tyre", "Tyre wear one side zyada ho raha hai", "Front tyre ka inner side zyada ghis raha hai. Alignment regular karata hu phir bhi issue repeat hota hai."),
        ("ac", "AC cooling traffic me weak ho jati hai", "Highway par AC thik hai but traffic me cooling low ho jati hai. Fan, gas ya condenser cleaning kya check karna chahiye?"),
        ("service", "Service bill me extra items add ho rahe hain", "Workshop throttle body cleaning, injector cleaning aur AC disinfectant add kar raha hai. Kaun se items avoid kar sakta hu?"),
        ("suspension", "Bad road par khatak sound aa raha hai", "Left side se khatak khatak sound aata hai. Speed breaker par zyada clear hota hai. Link rod ya shocker issue ho sakta hai?"),
        ("clutch", "Clutch pedal heavy ho gaya hai", "Traffic me clutch heavy lagta hai aur gear shift bhi thoda hard hai. Cable, hydraulic ya clutch plate ka sign hai?"),
        ("buying", "Daily city use ke liye used car advice chahiye", "Budget limited hai aur daily 35 km city run hai. Petrol automatic lena sahi rahega ya CNG manual?"),
    ]

    reply_bank = [
        "Basic scan se start karo. Error code milne ke baad unnecessary part replacement avoid ho jayega.",
        "Pehle simple checks karo: fluid level, tyre pressure, battery voltage aur recent service history.",
        "Agar issue safety related hai to long drive avoid karo aur trusted mechanic se inspection karao.",
        "Same symptom ke multiple reasons ho sakte hain. Video ya exact condition mention karoge to diagnosis better hoga.",
        "Workshop se old parts wapas maango aur estimate written me lo. Isse extra billing control hoti hai.",
        "Agar warning light aa rahi hai to OBD scan ka screenshot community me share karo.",
    ]

    while len(demo_posts) < 100:
        index = len(demo_posts)
        topic, title, content = topics[index % len(topics)]
        author = demo_authors[index % len(demo_authors)]
        responder_one = demo_authors[(index + 3) % len(demo_authors)]
        responder_two = demo_authors[(index + 5) % len(demo_authors)]
        demo_posts.append(
            {
                "user": author,
                "title": f"{title} #{index + 1}",
                "content": f"{content} Context: {topic} issue, car daily use me hai aur owner practical advice chahta hai.",
                "replies": [
                    (responder_one[0], responder_one[1], reply_bank[index % len(reply_bank)]),
                    (responder_two[0], responder_two[1], reply_bank[(index + 2) % len(reply_bank)]),
                ],
            }
        )

    created_users = {}
    for post_data in demo_posts:
        people = [post_data["user"]] + [(name, email, "Helpful Member", 50) for name, email, _ in post_data["replies"]]
        for username, email, badge, reputation in people:
            if email in created_users:
                continue
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    username=build_unique_username(username),
                    email=email,
                    password=generate_password_hash(secrets.token_urlsafe(16)),
                    role="user",
                    email_verified=True,
                    badge=badge,
                    reputation=reputation,
                    posts_count=0,
                )
                db.session.add(user)
                db.session.flush()
            created_users[email] = user

    for post_data in demo_posts:
        _, author_email, _, _ = post_data["user"]
        existing_post = Post.query.filter_by(title=post_data["title"]).first()
        if existing_post:
            continue

        author = created_users[author_email]
        post = Post(title=post_data["title"], content=post_data["content"], user_id=author.id)
        db.session.add(post)
        db.session.flush()

        parent_comment = None
        for index, reply_data in enumerate(post_data["replies"]):
            _, reply_email, content = reply_data
            comment = Comment(
                content=content,
                user_id=created_users[reply_email].id,
                post_id=post.id,
                parent_id=parent_comment.id if index == 1 and parent_comment else None,
            )
            db.session.add(comment)
            db.session.flush()
            if parent_comment is None:
                parent_comment = comment

    for user in created_users.values():
        posts_count = Post.query.filter_by(user_id=user.id).count()
        comments_count = Comment.query.filter_by(user_id=user.id).count()
        user.posts_count = posts_count
        user.reputation = max(user.reputation or 0, (posts_count * 5) + (comments_count * 2))

    db.session.commit()


def initialize_database():
    global database_initialized
    if database_initialized:
        return

    with database_init_lock:
        if database_initialized:
            return

        db.create_all()
        ensure_user_schema()
        ensure_car_schema()
        ensure_website_visit_schema()
        ensure_reply_schema()
        ensure_post_schema()
        ensure_car_community_seed()
        ensure_demo_community_seed()

        admin_users = User.query.filter(User.email.in_(ADMIN_EMAILS)).all()
        changed = False

        for admin_user in admin_users:
            if admin_user.role != "admin":
                admin_user.role = "admin"
                changed = True

        if changed:
            db.session.commit()

        database_initialized = True


@app.before_request
def ensure_database_ready():
    if request.endpoint in {"healthz", "version"} or request.path in {"/healthz", "/version"}:
        return

    try:
        initialize_database()
    except Exception as e:
        db.session.rollback()
        app.logger.warning("Database initialization skipped: %s", e.__class__.__name__)


@app.errorhandler(404)
def handle_not_found(error):
    if wants_json_response():
        return jsonify({"status": "error", "message": "Not found"}), 404
    return "Not found", 404


@app.errorhandler(500)
def handle_server_error(error):
    db.session.rollback()
    if wants_json_response():
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return "Something went wrong. Please try again later.", 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error
    db.session.rollback()
    app.logger.exception(
        "Unhandled server error on %s %s",
        request.method,
        request.path,
    )
    if wants_json_response():
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return "Something went wrong. Please try again later.", 500


@app.route("/robots.txt")
def robots_txt():
    return Response(
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: https://ampyan.com/sitemap.xml\n",
        mimetype="text/plain",
    )


@app.route("/sitemap.xml")
def sitemap_xml():
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ampyan.com/</loc>
  </url>
  <url>
    <loc>https://ampyan.com/login</loc>
  </url>
  <url>
    <loc>https://ampyan.com/community</loc>
  </url>
  <url>
    <loc>https://ampyan.com/diagnosis</loc>
  </url>
  <url>
    <loc>https://ampyan.com/mygarage</loc>
  </url>
</urlset>
"""
    return Response(sitemap, mimetype="application/xml")


@app.route("/diagnosis")
def diagnosis_alias():
    return redirect("/tools/ai-diagnosis", code=301)


@app.route("/mygarage")
def mygarage_alias():
    return redirect("/garage-dashboard", code=301)


@app.route("/healthz")
def healthz():
    return "ok"


@app.route("/version")
def version():
    return os.environ.get("RENDER_GIT_COMMIT", "local")

# ================= START SERVER =================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    print("Starting Motrnoix AMPYAN server on port:", port)

    app.run(host="0.0.0.0", port=port)
