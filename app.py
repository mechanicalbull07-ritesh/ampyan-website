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
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from sqlalchemy import func, inspect, text
print("Flask core loaded")

# ================= MODELS =================
from models.models import db, User, Post, Comment, Vote, News, DiagnosticLearning, Car, WebsiteVisit
print("Models loaded")

# ================= SECURITY =================
from werkzeug.security import generate_password_hash, check_password_hash
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
import traceback
from PIL import Image
from collections import defaultdict
import re
import threading
from datetime import datetime, timedelta
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
def compress_image(image_path):

    try:

        img = Image.open(image_path)

        img = img.convert("RGB")

        img.save(
            image_path,
            format="JPEG",
            quality=70,
            optimize=True
        )

    except Exception as e:

        print("Image compression error:", e)

def safe_image_check(file_path):

    try:
        img = Image.open(file_path)
        img.verify()

        if img.format.lower() not in ["jpeg","png","webp"]:
            return False

        return True

    except:
        return False
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

app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")
app.config["SECRET_KEY"] = app.secret_key
app.config["PREFERRED_URL_SCHEME"] = "https" if os.environ.get("ENV") == "production" else "http"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# 🔐 Production Security Settings
if os.environ.get("ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True

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

@app.route("/videos")
def videos():

    youtube_videos = [
        "https://www.youtube.com/embed/VIDEO_ID_1",
        "https://www.youtube.com/embed/VIDEO_ID_2",
        "https://www.youtube.com/embed/VIDEO_ID_3"
    ]

    instagram_posts = [
        "https://www.instagram.com/p/POST_ID_1/embed",
        "https://www.instagram.com/p/POST_ID_2/embed"
    ]

    return render_template(
        "videos.html",
        youtube_videos=youtube_videos,
        instagram_posts=instagram_posts
    )

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
        print("GOOGLE USER INSERT ERROR:", repr(exc))
        traceback.print_exc()
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
        print("Google login missing environment variables:", ", ".join(missing_env))
        flash("Google login is not configured yet. Please check server configuration.")
        return redirect(url_for("auth.login"))

    redirect_uri = GOOGLE_PRODUCTION_REDIRECT_URI

    try:
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        print("Google login redirect error:", e)
        traceback.print_exc()
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
            print("Google callback missing userinfo. Token keys:", list(token.keys()) if isinstance(token, dict) else type(token))
            return "Google login failed", 500

        email = (user_info.get("email") or "").strip().lower()

        if not email:
            print("Google callback missing email. User info keys:", list(user_info.keys()))
            return "Google login failed", 500

        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                username=build_unique_username(email.split("@")[0]),
                email=email,
                password=generate_password_hash(secrets.token_urlsafe(16)),
                role="user",
                email_verified=True,
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
        print("GOOGLE CALLBACK ERROR:", str(e))
        traceback.print_exc()
        return "Google login failed", 500

# ================= WEBSITE VISIT TRACKER =================

@app.before_request
def track_visit():

    try:

        if request.path.startswith("/static"):
            return

        if request.path.startswith("/login") or request.path.startswith("/google"):
            return

        visit = WebsiteVisit(
            ip_address=request.remote_addr
        )

        db.session.add(visit)
        db.session.commit()

    except Exception as e:

        db.session.rollback()

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

        print("RESULTS:", results)
        print("QUESTIONS:", questions)

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

    print("🔥 RETURNING RESULT PAGE")
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
    return render_template("news_detail.html", news=news)


@app.route("/admin/news/create", methods=["GET", "POST"])
@login_required
def create_news():
    if current_user.role != "admin":
        return "Access Denied"

    if request.method == "POST":

        image_file = request.files.get("image")
        filename = None

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)

            image_file.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )

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
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
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
# ================= FORGOT PASSWORD =================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

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
        db.session.execute(text('CREATE SEQUENCE IF NOT EXISTS user_id_seq OWNED BY "user".id'))
        db.session.execute(text("SELECT setval('user_id_seq', COALESCE((SELECT MAX(id) FROM \"user\"), 0) + 1, false)"))
        db.session.execute(text("ALTER TABLE \"user\" ALTER COLUMN id SET DEFAULT nextval('user_id_seq')"))

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
    try:
        initialize_database()
    except Exception as e:
        db.session.rollback()
        print("Database initialization skipped:", e)
        traceback.print_exc()


@app.route("/healthz")
def healthz():
    return "ok"

# ================= START SERVER =================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    print("Starting Motrnoix AMPYAN server on port:", port)

    app.run(host="0.0.0.0", port=port)
