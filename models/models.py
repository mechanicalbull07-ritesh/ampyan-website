from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ================= USER =================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    mobile = db.Column(db.String(20))

    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="user")

    # AI usage
    ai_uses_today = db.Column(db.Integer, default=0)
    ai_last_reset = db.Column(db.DateTime)

    # account status
    email_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)

    # password reset
    reset_token = db.Column(db.String(200))
    reset_token_expiry = db.Column(db.DateTime)

    # email verification
    verification_token = db.Column(db.String(200))
    verification_token_expiry = db.Column(db.DateTime)

    # profile
    profile_photo = db.Column(db.String(200))

    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    pincode = db.Column(db.String(20))

    # community stats
    reputation = db.Column(db.Integer, default=0)
    posts_count = db.Column(db.Integer, default=0)
    helpful_answers = db.Column(db.Integer, default=0)

    # contributor system
    contributor_score = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50), default="New Member")


# ================= MECHANIC / GARAGE =================

class MechanicProfile(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    business_name = db.Column(db.String(150), nullable=False)
    owner_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30), nullable=False)

    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default="India")
    pincode = db.Column(db.String(20))
    address = db.Column(db.String(255))

    specialties = db.Column(db.String(255))
    service_types = db.Column(db.String(255))
    experience_years = db.Column(db.Integer, default=0)

    about = db.Column(db.Text)

    trust_score = db.Column(db.Integer, default=30)
    trust_level = db.Column(db.String(50), default="Starter Garage")

    is_featured = db.Column(db.Boolean, default=False)
    accepts_emergency = db.Column(db.Boolean, default=False)
    pickup_drop_available = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="mechanic_profiles")


class MechanicReview(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    mechanic_id = db.Column(db.Integer, db.ForeignKey("mechanic_profile.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    mechanic = db.relationship("MechanicProfile", backref="reviews")
    author = db.relationship("User", backref="mechanic_reviews")


# ================= POSTS =================

class CarCommunity(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref="created_car_communities")


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    image = db.Column(db.String(200))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey("car_community.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User", backref="posts")
    car_community = db.relationship("CarCommunity", backref="posts")

    comments = db.relationship(
        "Comment",
        backref="post",
        cascade="all, delete",
        lazy=True
    )

    votes = db.relationship(
        "Vote",
        backref="post",
        cascade="all, delete",
        lazy=True
    )


# ================= VOTES =================

class Vote(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)


# ================= COMMENTS =================

class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="comments")
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete",
        lazy=True,
    )


# ================= NEWS =================

class News(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    category = db.Column(db.String(40), default="auto-news")

    image = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship(
        "NewsReply",
        backref="news",
        cascade="all, delete",
        lazy=True,
    )


class NewsReply(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey("news.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("news_reply.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="news_replies")
    replies = db.relationship(
        "NewsReply",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete",
        lazy=True,
    )


# ================= MARKETPLACE =================

class MarketplaceListing(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    listing_type = db.Column(db.String(20), nullable=False, default="sell")
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    price = db.Column(db.Integer)
    location = db.Column(db.String(140))
    contact_phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="marketplace_listings")


class MarketplaceMessage(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("marketplace_listing.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    listing = db.relationship("MarketplaceListing", backref="messages")
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_marketplace_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_marketplace_messages")


# ================= VIDEOS =================

class Video(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    embed_url = db.Column(db.String(500), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship(
        "VideoReply",
        backref="video",
        cascade="all, delete",
        lazy=True,
    )


class VideoReply(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("video_reply.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="video_replies")
    replies = db.relationship(
        "VideoReply",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete",
        lazy=True,
    )


# =============================
# 🔥 DIAGNOSTIC LEARNING MODEL
# =============================

class DiagnosticLearning(db.Model):
    __tablename__ = "diagnostic_learning"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=True)

    problem = db.Column(db.String(255))
    answers = db.Column(db.Text)
    final_issue = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# =============================
# 🔥 AI FEEDBACK MODEL (NEW)
# =============================

class AIFeedback(db.Model):
    __tablename__ = "ai_feedback"

    id = db.Column(db.Integer, primary_key=True)

    issue = db.Column(db.String(255))
    feedback = db.Column(db.String(10))  # yes / no

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# ================= HELP / REPORTS =================

class HelpReport(db.Model):
    __tablename__ = "help_report"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(150))
    category = db.Column(db.String(80), nullable=False)
    page_url = db.Column(db.String(500))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="open")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="help_reports")


# ================= USER CARS =================

class Car(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
   
    fuel_type = db.Column(db.String(50))
    mileage = db.Column(db.Integer)

    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", backref="cars")


    # SMART GARAGE
    current_km = db.Column(db.Integer, default=0)
    last_service_km = db.Column(db.Integer)
    next_service_km = db.Column(db.Integer)

    last_service_date = db.Column(db.DateTime)
    next_service_date = db.Column(db.DateTime)
    insurance_expiry = db.Column(db.Date)
    pollution_expiry = db.Column(db.Date)
    
    daily_km = db.Column(db.Integer)

    # COMPONENT REPLACEMENT TRACKING
    brake_replaced_km = db.Column(db.Integer)
    tyre_replaced_km = db.Column(db.Integer)
    clutch_replaced_km = db.Column(db.Integer)
    battery_replaced_year = db.Column(db.Integer)


# ================= WEBSITE VISITS =================

class WebsiteVisit(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    visit_time = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    ip_address = db.Column(db.String(50))
    visitor_id = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    path = db.Column(db.String(500))
    method = db.Column(db.String(10))
    referrer = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    device_type = db.Column(db.String(30))
    is_authenticated = db.Column(db.Boolean, default=False)
    is_page_view = db.Column(db.Boolean, default=True)

    user = db.relationship("User", backref="website_visits")


class WebsiteEvent(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    event_time = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    event_type = db.Column(db.String(40), nullable=False)
    label = db.Column(db.String(160))
    path = db.Column(db.String(500))
    target_url = db.Column(db.String(500))
    visitor_id = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    ip_address = db.Column(db.String(50))
    referrer = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    device_type = db.Column(db.String(30))
    is_authenticated = db.Column(db.Boolean, default=False)
    severity = db.Column(db.String(20), default="info")

    user = db.relationship("User", backref="website_events")
