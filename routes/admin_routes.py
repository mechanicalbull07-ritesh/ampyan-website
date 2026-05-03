from collections import Counter, defaultdict
from datetime import datetime, time, timedelta

from flask import Blueprint, render_template, redirect, flash
from flask_login import login_required, current_user
from models.models import db, User, Post, Comment, News, WebsiteVisit, WebsiteEvent, MechanicProfile, MechanicReview, Car
from services.garage_network_service import refresh_mechanic_reputation

admin_bp = Blueprint("admin", __name__)


def _count_by_hour(visits):
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    buckets = {
        (now - timedelta(hours=index)).strftime("%d %b %H:00"): 0
        for index in range(23, -1, -1)
    }
    for visit in visits:
        if visit.visit_time:
            key = visit.visit_time.replace(minute=0, second=0, microsecond=0).strftime("%d %b %H:00")
            if key in buckets:
                buckets[key] += 1
    return list(buckets.items())


def _count_by_day(visits, days=30):
    today = datetime.utcnow().date()
    buckets = {
        (today - timedelta(days=index)).strftime("%d %b"): 0
        for index in range(days - 1, -1, -1)
    }
    for visit in visits:
        if visit.visit_time:
            key = visit.visit_time.date().strftime("%d %b")
            if key in buckets:
                buckets[key] += 1
    return list(buckets.items())


def _count_by_month(visits):
    buckets = defaultdict(int)
    for visit in visits:
        if visit.visit_time:
            buckets[visit.visit_time.strftime("%b %Y")] += 1
    return list(buckets.items())[-12:]


def _referrer_source(referrer):
    if not referrer:
        return "Direct"
    lowered = referrer.lower()
    if "google." in lowered:
        return "Google"
    if "instagram." in lowered:
        return "Instagram"
    if "youtube." in lowered or "youtu.be" in lowered:
        return "YouTube"
    if "ampyan.com" in lowered:
        return "Internal"
    return referrer.split("/")[2] if "://" in referrer else referrer[:40]


# ================= ADMIN DASHBOARD =================

@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return "Access Denied", 403

    users = User.query.order_by(User.id.desc()).all()
    posts = Post.query.order_by(Post.id.desc()).all()
    comments = Comment.query.order_by(Comment.id.desc()).all()
    news = News.query.order_by(News.id.desc()).all()
    mechanics = MechanicProfile.query.order_by(
        MechanicProfile.is_verified.asc(),
        MechanicProfile.is_featured.desc(),
        MechanicProfile.id.desc()
    ).all()
    reviews = MechanicReview.query.order_by(MechanicReview.id.desc()).limit(10).all()
    cars = Car.query.order_by(Car.created_at.desc()).all()

    total_ai_usage = db.session.query(db.func.sum(User.ai_uses_today)).scalar() or 0
    now = datetime.utcnow()
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    yesterday_start = today_start - timedelta(days=1)
    last_24h = now - timedelta(hours=24)
    last_30d = now - timedelta(days=30)
    last_365d = now - timedelta(days=365)
    tracked_visits = WebsiteVisit.query.filter_by(is_page_view=True)
    visit_count = tracked_visits.count()
    today_page_views = tracked_visits.filter(WebsiteVisit.visit_time >= today_start).count()
    yesterday_page_views = tracked_visits.filter(
        WebsiteVisit.visit_time >= yesterday_start,
        WebsiteVisit.visit_time < today_start
    ).count()
    traffic_delta_today = today_page_views - yesterday_page_views
    total_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None)
    ).scalar() or 0
    today_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        WebsiteVisit.visit_time >= today_start
    ).scalar() or 0
    logged_in_views = tracked_visits.filter_by(is_authenticated=True).count()
    guest_views = tracked_visits.filter_by(is_authenticated=False).count()
    top_pages = db.session.query(
        WebsiteVisit.path,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.path.isnot(None)
    ).group_by(WebsiteVisit.path).order_by(db.func.count(WebsiteVisit.id).desc()).limit(8).all()
    device_breakdown = db.session.query(
        WebsiteVisit.device_type,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.device_type.isnot(None)
    ).group_by(WebsiteVisit.device_type).order_by(db.func.count(WebsiteVisit.id).desc()).all()
    total_users = User.query.count()
    banned_users_count = User.query.filter_by(is_banned=True).count()
    admin_users_count = User.query.filter_by(role="admin").count()
    pending_garages_count = MechanicProfile.query.filter_by(is_verified=False).count()
    approved_garages_count = MechanicProfile.query.filter_by(is_verified=True).count()
    featured_garages_count = MechanicProfile.query.filter_by(is_featured=True).count()
    recent_visit_rows = tracked_visits.filter(WebsiteVisit.visit_time >= last_365d).all()
    visits_24h = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_24h]
    visits_30d = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_30d]
    hourly_traffic = _count_by_hour(visits_24h)
    daily_traffic = _count_by_day(visits_30d)
    monthly_traffic = _count_by_month(recent_visit_rows)

    click_events = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d
    ).order_by(WebsiteEvent.event_time.desc()).all()
    security_events = WebsiteEvent.query.filter_by(event_type="security").filter(
        WebsiteEvent.event_time >= last_30d
    ).order_by(WebsiteEvent.event_time.desc()).all()
    security_events_24h = [
        event for event in security_events
        if event.event_time and event.event_time >= last_24h
    ]

    click_counter = Counter((event.label or event.target_url or "Click") for event in click_events)
    top_clicks = click_counter.most_common(10)
    click_page_counter = Counter((event.path or "Unknown") for event in click_events)
    top_click_pages = click_page_counter.most_common(8)
    referrer_counter = Counter(_referrer_source(visit.referrer) for visit in visits_30d)
    top_referrers = referrer_counter.most_common(8)

    page_metrics = []
    for page in top_pages:
        page_visits = [visit for visit in visits_30d if visit.path == page.path]
        page_clicks = sum(1 for event in click_events if event.path == page.path)
        page_metrics.append({
            "path": page.path or "Unknown",
            "views": page.views,
            "unique": len({visit.visitor_id for visit in page_visits if visit.visitor_id}),
            "logged_in": sum(1 for visit in page_visits if visit.is_authenticated),
            "guest": sum(1 for visit in page_visits if not visit.is_authenticated),
            "clicks": page_clicks,
            "last_visit": max((visit.visit_time for visit in page_visits if visit.visit_time), default=None),
        })

    suspicious_ip_counter = Counter(event.ip_address or "Unknown" for event in security_events_24h)
    suspicious_ips = suspicious_ip_counter.most_common(6)
    safety_alerts = []
    if security_events_24h:
        safety_alerts.append({
            "severity": "High",
            "title": "Sensitive or abusive requests blocked",
            "detail": f"{len(security_events_24h)} blocked security event(s) in the last 24 hours.",
        })
    if suspicious_ips and suspicious_ips[0][1] >= 5:
        safety_alerts.append({
            "severity": "Medium",
            "title": "Repeated requests from one source",
            "detail": f"{suspicious_ips[0][0]} triggered {suspicious_ips[0][1]} security event(s).",
        })
    if yesterday_page_views and today_page_views > yesterday_page_views * 2:
        safety_alerts.append({
            "severity": "Info",
            "title": "Traffic spike",
            "detail": f"Today has {today_page_views} views vs {yesterday_page_views} yesterday.",
        })
    if not safety_alerts:
        safety_alerts.append({
            "severity": "Good",
            "title": "No major safety alerts",
            "detail": "No unusual security pattern detected from tracked events.",
        })

    total_cars = len(cars)
    car_owner_count = db.session.query(db.func.count(db.func.distinct(Car.owner_id))).scalar() or 0
    today = datetime.utcnow().date()
    service_due_cars = [
        car for car in cars
        if car.next_service_km and car.current_km and car.current_km >= car.next_service_km
    ]
    service_soon_cars = [
        car for car in cars
        if car.next_service_km and car.current_km and 0 <= (car.next_service_km - car.current_km) <= 500
    ]
    insurance_expired_cars = [
        car for car in cars
        if car.insurance_expiry and car.insurance_expiry < today
    ]
    pollution_expired_cars = [
        car for car in cars
        if car.pollution_expiry and car.pollution_expiry < today
    ]

    for mechanic in mechanics:
        refresh_mechanic_reputation(mechanic)

    pending_mechanics = [mechanic for mechanic in mechanics if not mechanic.is_verified]
    approved_mechanics = [mechanic for mechanic in mechanics if mechanic.is_verified][:8]
    recent_users = users[:10]
    recent_posts = posts[:8]
    recent_cars = cars[:12]
    banned_users = [user for user in users if user.is_banned][:8]

    return render_template(
        "admin.html",
        users=users,
        posts=posts,
        comments=comments,
        news=news,
        mechanics=mechanics,
        reviews=reviews,
        total_users=total_users,
        total_ai_usage=total_ai_usage,
        visit_count=visit_count,
        today_page_views=today_page_views,
        yesterday_page_views=yesterday_page_views,
        traffic_delta_today=traffic_delta_today,
        total_unique_visitors=total_unique_visitors,
        today_unique_visitors=today_unique_visitors,
        logged_in_views=logged_in_views,
        guest_views=guest_views,
        top_pages=top_pages,
        page_metrics=page_metrics,
        device_breakdown=device_breakdown,
        hourly_traffic=hourly_traffic,
        daily_traffic=daily_traffic,
        monthly_traffic=monthly_traffic,
        top_clicks=top_clicks,
        top_click_pages=top_click_pages,
        top_referrers=top_referrers,
        security_events=security_events[:12],
        security_events_24h=security_events_24h,
        suspicious_ips=suspicious_ips,
        safety_alerts=safety_alerts,
        click_events_count=len(click_events),
        banned_users_count=banned_users_count,
        admin_users_count=admin_users_count,
        pending_garages_count=pending_garages_count,
        approved_garages_count=approved_garages_count,
        featured_garages_count=featured_garages_count,
        total_cars=total_cars,
        car_owner_count=car_owner_count,
        service_due_cars=service_due_cars,
        service_soon_cars=service_soon_cars,
        insurance_expired_cars=insurance_expired_cars,
        pollution_expired_cars=pollution_expired_cars,
        pending_mechanics=pending_mechanics,
        approved_mechanics=approved_mechanics,
        recent_users=recent_users,
        recent_posts=recent_posts,
        recent_cars=recent_cars,
        banned_users=banned_users
    )


# ================= DELETE USER =================

@admin_bp.route("/admin/delete-user/<int:user_id>")
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    # admin खुद को delete नहीं कर सकता
    if user.id == current_user.id:
        flash("You cannot delete yourself")
        return redirect("/admin")

    # पहले user के posts delete
    Post.query.filter_by(user_id=user.id).delete()

    # user के comments delete
    Comment.query.filter_by(user_id=user.id).delete()

    # अब user delete
    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully")

    return redirect("/admin")


# ================= BAN USER =================

@admin_bp.route("/admin/ban-user/<int:user_id>")
@login_required
def ban_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = True
    db.session.commit()

    return redirect("/admin")


# ================= UNBAN USER =================

@admin_bp.route("/admin/unban-user/<int:user_id>")
@login_required
def unban_user(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = False
    db.session.commit()

    return redirect("/admin")


# ================= REMOVE ADMIN =================

@admin_bp.route("/admin/remove-admin/<int:user_id>")
@login_required
def remove_admin(user_id):

    if current_user.role != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.role = "user"
    db.session.commit()

    return redirect("/admin")


@admin_bp.route("/admin/approve-garage/<int:mechanic_id>")
@login_required
def approve_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = True
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage approved successfully.")
    return redirect("/admin")


@admin_bp.route("/admin/reject-garage/<int:mechanic_id>")
@login_required
def reject_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = False
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage moved back to pending state.")
    return redirect("/admin")


@admin_bp.route("/admin/feature-garage/<int:mechanic_id>")
@login_required
def feature_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_featured = True
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage featured on the network.")
    return redirect("/admin")


@admin_bp.route("/admin/unfeature-garage/<int:mechanic_id>")
@login_required
def unfeature_garage(mechanic_id):

    if current_user.role != "admin":
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage removed from featured list.")
    return redirect("/admin")
