from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
import secrets

from flask import Blueprint, current_app, jsonify, render_template, redirect, flash, request, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from models.models import db, User, Post, Comment, News, WebsiteVisit, WebsiteEvent, MechanicProfile, MechanicReview, Car, CarCommunity
from routes.auth_routes import ADMIN_EMAILS, ADMIN_EMAIL_SET
from services.garage_network_service import refresh_mechanic_reputation
from services.app_api_sync import delete_garage_from_app, sync_garage_to_app, sync_news_to_app
from services.analytics_service import safe_live_summary
from routes.community_routes import (
    _find_remote_post_id_for_website_post,
    _get_or_create_car_community,
    _safe_remote_call,
    _sync_user_profile,
    refresh_author_stats,
)

admin_bp = Blueprint("admin", __name__)
IST_OFFSET = timedelta(hours=5, minutes=30)


@admin_bp.before_request
def ensure_whitelisted_admin_role():
    if not current_user.is_authenticated:
        return

    email = (current_user.email or "").strip().lower()
    if email not in ADMIN_EMAIL_SET:
        if current_user.role == "admin":
            try:
                current_user.role = "user"
                db.session.commit()
                current_app.logger.warning("Removed admin role before admin route: %s", email)
            except Exception as exc:
                db.session.rollback()
                current_app.logger.warning("Admin route cleanup skipped: %s", exc.__class__.__name__)
        return

    if current_user.role == "admin":
        return

    try:
        current_user.role = "admin"
        db.session.commit()
        current_app.logger.info("Restored admin role before admin route: %s", email)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Admin route role restore skipped: %s", exc.__class__.__name__)


def _to_ist(value):
    if not value:
        return None
    return value + IST_OFFSET


def _format_ist(value, fallback="N/A"):
    ist_value = _to_ist(value)
    if not ist_value:
        return fallback
    return ist_value.strftime("%d %b %Y, %I:%M %p IST")


def _frequency_options():
    return [
        ("24h", "Last 24 hours", timedelta(hours=24)),
        ("7d", "Last 7 days", timedelta(days=7)),
        ("30d", "Last 30 days", timedelta(days=30)),
        ("90d", "Last 90 days", timedelta(days=90)),
        ("all", "All time", None),
    ]


def _frequency_start(filter_key):
    now = datetime.utcnow()
    for key, label, delta in _frequency_options():
        if key == filter_key:
            return (now - delta) if delta else None, label
    return now - timedelta(days=30), "Last 30 days"


def _ist_day_start_utc(days_back=0):
    ist_now = _to_ist(datetime.utcnow())
    ist_start = datetime.combine((ist_now - timedelta(days=days_back)).date(), time.min)
    return ist_start - IST_OFFSET


def _visitor_key(visit):
    if visit.user_id:
        return f"user-{visit.user_id}"
    if visit.visitor_id:
        return f"visitor-{visit.visitor_id}"
    return f"ip-{visit.ip_address or visit.id}"


def _analytics_path(value):
    value = (value or "").strip()
    return value if value else "Legacy tracked page"


def _period_user_stats(visits, period_start):
    period_visits = [visit for visit in visits if visit.visit_time and visit.visit_time >= period_start]
    visitor_counts = Counter(_visitor_key(visit) for visit in period_visits)
    first_seen = {}
    for visit in visits:
        key = _visitor_key(visit)
        if visit.visit_time and (key not in first_seen or visit.visit_time < first_seen[key]):
            first_seen[key] = visit.visit_time
    new_visitors = [key for key, value in first_seen.items() if value >= period_start]
    logged_in_users = {visit.user_id for visit in period_visits if visit.user_id}
    return {
        "views": len(period_visits),
        "unique": len(visitor_counts),
        "repeated": sum(1 for count in visitor_counts.values() if count > 1),
        "new": len(new_visitors),
        "logged_in": len(logged_in_users),
    }


def _count_by_hour(visits):
    now = _to_ist(datetime.utcnow()).replace(minute=0, second=0, microsecond=0)
    buckets = {
        (now - timedelta(hours=index)).strftime("%d %b %H:00"): 0
        for index in range(23, -1, -1)
    }
    for visit in visits:
        if visit.visit_time:
            key = _to_ist(visit.visit_time).replace(minute=0, second=0, microsecond=0).strftime("%d %b %H:00")
            if key in buckets:
                buckets[key] += 1
    return list(buckets.items())


def _count_by_day(visits, days=30):
    today = _to_ist(datetime.utcnow()).date()
    buckets = {
        (today - timedelta(days=index)).strftime("%d %b"): 0
        for index in range(days - 1, -1, -1)
    }
    for visit in visits:
        if visit.visit_time:
            key = _to_ist(visit.visit_time).date().strftime("%d %b")
            if key in buckets:
                buckets[key] += 1
    return list(buckets.items())


def _count_by_month(visits):
    buckets = defaultdict(int)
    for visit in visits:
        if visit.visit_time:
            buckets[_to_ist(visit.visit_time).strftime("%b %Y")] += 1
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


def _require_admin():
    if not current_user.is_authenticated:
        return False
    email = (current_user.email or "").strip().lower()
    return email in ADMIN_EMAIL_SET


def _slugify_persona_username(value):
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in (value or "").strip())
    return cleaned.strip("_-")[:80]


def _commit_new_user_with_id_fallback(user):
    try:
        db.session.add(user)
        db.session.commit()
        return
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Managed persona insert needed id fallback: %s", exc.__class__.__name__)
        message = str(exc).lower()
        if "null value" not in message or "id" not in message:
            raise

        next_id = (db.session.query(db.func.max(User.id)).scalar() or 0) + 1
        user.id = next_id
        db.session.add(user)
        db.session.commit()


def _managed_persona_or_none(user_id):
    if not user_id:
        return None
    return User.query.filter_by(id=user_id, is_managed_persona=True).first()


def _empty_admin_analytics_context(section="overview"):
    empty_period = {"views": 0, "unique": 0, "repeated": 0, "new": 0, "logged_in": 0}
    return {
        "analytics_degraded": True,
        "live_analytics": safe_live_summary(),
        "section": section,
        "frequency_filter": request.args.get("frequency", "30d"),
        "frequency_label": "Temporarily unavailable",
        "frequency_options": _frequency_options(),
        "user_rows": [],
        "active_user_rows": [],
        "inactive_user_count": 0,
        "user_frequency_summary": {
            "hour": dict(empty_period),
            "day": dict(empty_period),
            "week": dict(empty_period),
            "month": dict(empty_period),
        },
        "admin_activity": {
            "views_30d": 0,
            "views_24h": 0,
            "clicks_30d": 0,
            "clicks_24h": 0,
            "unique_admins_30d": 0,
        },
        "visit_count": 0,
        "today_page_views": 0,
        "yesterday_page_views": 0,
        "traffic_delta_today": 0,
        "total_unique_visitors": 0,
        "today_unique_visitors": 0,
        "logged_in_views": 0,
        "guest_views": 0,
        "page_metrics": [],
        "device_breakdown": [],
        "hourly_traffic": [],
        "daily_traffic": [],
        "monthly_traffic": [],
        "top_clicks": [],
        "top_click_pages": [],
        "top_referrers": [],
        "security_events": [],
        "security_events_24h": [],
        "suspicious_ips": [],
        "safety_alerts": [{
            "severity": "Info",
            "title": "Analytics is warming up",
            "detail": "Traffic data is temporarily limited while analytics storage becomes ready.",
        }],
        "click_events_count": 0,
        "total_cars": 0,
        "car_owner_count": 0,
        "service_due_cars": [],
        "service_soon_cars": [],
        "insurance_expired_cars": [],
        "pollution_expired_cars": [],
        "recent_cars": [],
    }


def _build_admin_analytics_context(section="overview"):
    now = datetime.utcnow()
    today_start = _ist_day_start_utc()
    yesterday_start = _ist_day_start_utc(1)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    last_365d = now - timedelta(days=365)
    admin_user_ids = [user.id for user in User.query.filter_by(role="admin").all()]

    tracked_visits = WebsiteVisit.query.filter_by(is_page_view=True)
    public_visits_query = tracked_visits.filter(
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    )
    admin_visits_query = tracked_visits.filter(WebsiteVisit.user_id.in_(admin_user_ids)) if admin_user_ids else tracked_visits.filter(False)
    visit_count = public_visits_query.count()
    today_page_views = public_visits_query.filter(WebsiteVisit.visit_time >= today_start).count()
    yesterday_page_views = public_visits_query.filter(
        WebsiteVisit.visit_time >= yesterday_start,
        WebsiteVisit.visit_time < today_start
    ).count()
    total_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0
    today_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        WebsiteVisit.visit_time >= today_start,
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0

    device_breakdown = db.session.query(
        WebsiteVisit.device_type,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.device_type.isnot(None),
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).group_by(WebsiteVisit.device_type).order_by(db.func.count(WebsiteVisit.id).desc()).all()

    recent_visit_rows = public_visits_query.filter(WebsiteVisit.visit_time >= last_365d).order_by(
        WebsiteVisit.visit_time.desc()
    ).limit(5000).all()
    all_public_visit_rows = (
        public_visits_query
        .order_by(WebsiteVisit.visit_time.desc())
        .limit(5000)
        .all()
    )
    total_unique_visitors = len({_visitor_key(visit) for visit in all_public_visit_rows})
    today_unique_visitors = len({
        _visitor_key(visit)
        for visit in all_public_visit_rows
        if visit.visit_time and visit.visit_time >= today_start
    })
    admin_visit_rows = admin_visits_query.filter(WebsiteVisit.visit_time >= last_30d).order_by(
        WebsiteVisit.visit_time.desc()
    ).limit(2000).all()
    visits_24h = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_24h]
    visits_30d = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_30d]
    hourly_traffic = _count_by_hour(visits_24h)
    daily_traffic = _count_by_day(visits_30d)
    monthly_traffic = _count_by_month(recent_visit_rows)

    public_click_query = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d,
        (WebsiteEvent.user_id.is_(None)) | (~WebsiteEvent.user_id.in_(admin_user_ids))
    )
    admin_click_query = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d,
        WebsiteEvent.user_id.in_(admin_user_ids)
    ) if admin_user_ids else WebsiteEvent.query.filter(False)
    click_events = public_click_query.order_by(WebsiteEvent.event_time.desc()).limit(5000).all()
    admin_click_events = admin_click_query.order_by(WebsiteEvent.event_time.desc()).limit(2000).all()
    security_events = WebsiteEvent.query.filter_by(event_type="security").filter(
        WebsiteEvent.event_time >= last_30d
    ).order_by(WebsiteEvent.event_time.desc()).limit(2000).all()
    security_events_24h = [
        event for event in security_events
        if event.event_time and event.event_time >= last_24h
    ]

    click_counter = Counter((event.label or event.target_url or "Click") for event in click_events)
    top_clicks = click_counter.most_common(20)
    click_page_counter = Counter((event.path or "Unknown") for event in click_events)
    top_click_pages = click_page_counter.most_common(20)
    referrer_counter = Counter(_referrer_source(visit.referrer) for visit in visits_30d)
    top_referrers = referrer_counter.most_common(20)

    page_metrics = []
    page_visit_groups = defaultdict(list)
    for visit in all_public_visit_rows:
        page_visit_groups[_analytics_path(visit.path)].append(visit)
    page_click_groups = Counter(_analytics_path(event.path) for event in click_events)
    for path, page_visits in sorted(page_visit_groups.items(), key=lambda item: len(item[1]), reverse=True)[:20]:
        page_visits_30d = [visit for visit in page_visits if visit.visit_time and visit.visit_time >= last_30d]
        page_metrics.append({
            "path": path,
            "views": len(page_visits),
            "views_30d": len(page_visits_30d),
            "unique": len({_visitor_key(visit) for visit in page_visits}),
            "logged_in": sum(1 for visit in page_visits if visit.is_authenticated),
            "guest": sum(1 for visit in page_visits if not visit.is_authenticated),
            "clicks": page_click_groups[path],
            "last_visit": _to_ist(max((visit.visit_time for visit in page_visits if visit.visit_time), default=None)),
        })

    suspicious_ip_counter = Counter(event.ip_address or "Unknown" for event in security_events_24h)
    suspicious_ips = suspicious_ip_counter.most_common(10)
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

    cars = Car.query.order_by(Car.created_at.desc()).limit(1000).all()
    today = now.date()
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

    frequency_filter = request.args.get("frequency", "30d")
    frequency_start, frequency_label = _frequency_start(frequency_filter)
    user_rows = []
    for user in User.query.order_by(User.id.desc()).limit(500).all():
        user_visits_query = WebsiteVisit.query.filter(
            WebsiteVisit.user_id == user.id,
            WebsiteVisit.is_page_view.is_(True)
        )
        if frequency_start:
            user_visits_query = user_visits_query.filter(WebsiteVisit.visit_time >= frequency_start)
        user_visits = user_visits_query.order_by(WebsiteVisit.visit_time.desc()).limit(1000).all()
        latest_visit = user_visits[0] if user_visits else (
            WebsiteVisit.query.filter_by(user_id=user.id, is_page_view=True)
            .order_by(WebsiteVisit.visit_time.desc())
            .first()
        )
        user_cars = sorted(user.cars, key=lambda car: car.created_at or datetime.min, reverse=True)
        primary_car = next((car for car in user_cars if car.is_default), user_cars[0] if user_cars else None)
        user_events_query = WebsiteEvent.query.filter(WebsiteEvent.user_id == user.id)
        if frequency_start:
            user_events_query = user_events_query.filter(WebsiteEvent.event_time >= frequency_start)
        user_rows.append({
            "user": user,
            "cars": user_cars,
            "primary_car": primary_car,
            "visit_count": len(user_visits),
            "event_count": user_events_query.count(),
            "last_seen": _format_ist(latest_visit.visit_time) if latest_visit else "No visit tracked",
            "last_path": latest_visit.path if latest_visit else "N/A",
        })
    user_rows.sort(key=lambda row: (row["visit_count"], row["event_count"], row["user"].id), reverse=True)
    active_user_rows = [row for row in user_rows if row["visit_count"] > 0]
    user_frequency_summary = {
        "hour": _period_user_stats(all_public_visit_rows, now - timedelta(hours=1)),
        "day": _period_user_stats(all_public_visit_rows, today_start),
        "week": _period_user_stats(all_public_visit_rows, last_7d),
        "month": _period_user_stats(all_public_visit_rows, last_30d),
    }
    admin_activity = {
        "views_30d": len(admin_visit_rows),
        "views_24h": sum(1 for visit in admin_visit_rows if visit.visit_time and visit.visit_time >= last_24h),
        "clicks_30d": len(admin_click_events),
        "clicks_24h": sum(1 for event in admin_click_events if event.event_time and event.event_time >= last_24h),
        "unique_admins_30d": len({visit.user_id for visit in admin_visit_rows if visit.user_id}),
    }

    return {
        "live_analytics": safe_live_summary(),
        "section": section,
        "frequency_filter": frequency_filter,
        "frequency_label": frequency_label,
        "frequency_options": _frequency_options(),
        "user_rows": user_rows,
        "active_user_rows": active_user_rows,
        "inactive_user_count": max(0, len(user_rows) - len(active_user_rows)),
        "user_frequency_summary": user_frequency_summary,
        "admin_activity": admin_activity,
        "visit_count": visit_count,
        "today_page_views": today_page_views,
        "yesterday_page_views": yesterday_page_views,
        "traffic_delta_today": today_page_views - yesterday_page_views,
        "total_unique_visitors": total_unique_visitors,
        "today_unique_visitors": today_unique_visitors,
        "logged_in_views": public_visits_query.filter_by(is_authenticated=True).count(),
        "guest_views": public_visits_query.filter_by(is_authenticated=False).count(),
        "page_metrics": page_metrics,
        "device_breakdown": device_breakdown,
        "hourly_traffic": hourly_traffic,
        "daily_traffic": daily_traffic,
        "monthly_traffic": monthly_traffic,
        "top_clicks": top_clicks,
        "top_click_pages": top_click_pages,
        "top_referrers": top_referrers,
        "security_events": security_events[:50],
        "security_events_24h": security_events_24h,
        "suspicious_ips": suspicious_ips,
        "safety_alerts": safety_alerts,
        "click_events_count": len(click_events),
        "total_cars": len(cars),
        "car_owner_count": db.session.query(db.func.count(db.func.distinct(Car.owner_id))).scalar() or 0,
        "service_due_cars": service_due_cars,
        "service_soon_cars": service_soon_cars,
        "insurance_expired_cars": insurance_expired_cars,
        "pollution_expired_cars": pollution_expired_cars,
        "recent_cars": cars[:30],
    }


@admin_bp.route("/admin/analytics")
@admin_bp.route("/admin/analytics/<section>")
@login_required
def admin_analytics(section="overview"):
    if not _require_admin():
        return "Access Denied", 403

    allowed_sections = {"overview", "traffic", "engagement", "safety", "vehicles", "users"}
    if section not in allowed_sections:
        return redirect("/admin/analytics/overview")

    try:
        context = _build_admin_analytics_context(section)
        context["analytics_degraded"] = False
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning(
            "admin_analytics_degraded section=%s error=%s",
            section,
            exc.__class__.__name__,
        )
        context = _empty_admin_analytics_context(section)
    return render_template("admin_analytics.html", **context)


@admin_bp.route("/admin/analytics/live")
@login_required
def admin_analytics_live():
    if not _require_admin():
        return jsonify({"status": "error"}), 403
    try:
        return jsonify({"status": "success", "analytics": safe_live_summary()})
    except Exception:
        current_app.logger.warning("admin_analytics_live_failed", exc_info=True)
        return jsonify({"status": "success", "analytics": {}})


# ================= ADMIN DASHBOARD =================

@admin_bp.route("/admin")
@login_required
def admin_dashboard():
    if not _require_admin():
        return "Access Denied", 403

    users = User.query.order_by(User.id.desc()).limit(300).all()
    posts = Post.query.order_by(Post.id.desc()).limit(300).all()
    comments = Comment.query.order_by(Comment.id.desc()).limit(300).all()
    news = News.query.order_by(News.id.desc()).limit(300).all()
    mechanics = MechanicProfile.query.order_by(
        MechanicProfile.is_verified.asc(),
        MechanicProfile.is_featured.desc(),
        MechanicProfile.id.desc()
    ).limit(500).all()
    reviews = MechanicReview.query.order_by(MechanicReview.id.desc()).limit(10).all()
    cars = Car.query.order_by(Car.created_at.desc()).limit(500).all()

    total_ai_usage = db.session.query(db.func.sum(User.ai_uses_today)).scalar() or 0
    now = datetime.utcnow()
    today_start = _ist_day_start_utc()
    yesterday_start = _ist_day_start_utc(1)
    last_24h = now - timedelta(hours=24)
    last_30d = now - timedelta(days=30)
    last_365d = now - timedelta(days=365)
    admin_user_ids = [user.id for user in User.query.filter_by(role="admin").all()]
    tracked_visits = WebsiteVisit.query.filter_by(is_page_view=True)
    public_visits_query = tracked_visits.filter(
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    )
    visit_count = public_visits_query.count()
    today_page_views = public_visits_query.filter(WebsiteVisit.visit_time >= today_start).count()
    yesterday_page_views = public_visits_query.filter(
        WebsiteVisit.visit_time >= yesterday_start,
        WebsiteVisit.visit_time < today_start
    ).count()
    traffic_delta_today = today_page_views - yesterday_page_views
    total_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0
    today_unique_visitors = db.session.query(db.func.count(db.func.distinct(WebsiteVisit.visitor_id))).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.visitor_id.isnot(None),
        WebsiteVisit.visit_time >= today_start,
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).scalar() or 0
    logged_in_views = public_visits_query.filter_by(is_authenticated=True).count()
    guest_views = public_visits_query.filter_by(is_authenticated=False).count()
    device_breakdown = db.session.query(
        WebsiteVisit.device_type,
        db.func.count(WebsiteVisit.id).label("views")
    ).filter(
        WebsiteVisit.is_page_view.is_(True),
        WebsiteVisit.device_type.isnot(None),
        WebsiteVisit.is_bot.isnot(True),
        WebsiteVisit.is_internal.isnot(True),
        WebsiteVisit.is_admin.isnot(True),
        (WebsiteVisit.user_id.is_(None)) | (~WebsiteVisit.user_id.in_(admin_user_ids))
    ).group_by(WebsiteVisit.device_type).order_by(db.func.count(WebsiteVisit.id).desc()).all()
    total_users = User.query.count()
    banned_users_count = User.query.filter_by(is_banned=True).count()
    admin_users_count = User.query.filter_by(role="admin").count()
    pending_garages_count = MechanicProfile.query.filter_by(is_verified=False).count()
    approved_garages_count = MechanicProfile.query.filter_by(is_verified=True).count()
    featured_garages_count = MechanicProfile.query.filter_by(is_featured=True).count()
    recent_visit_rows = public_visits_query.filter(WebsiteVisit.visit_time >= last_365d).order_by(
        WebsiteVisit.visit_time.desc()
    ).limit(5000).all()
    all_public_visit_rows = (
        public_visits_query
        .order_by(WebsiteVisit.visit_time.desc())
        .limit(5000)
        .all()
    )
    total_unique_visitors = len({_visitor_key(visit) for visit in all_public_visit_rows})
    today_unique_visitors = len({
        _visitor_key(visit)
        for visit in all_public_visit_rows
        if visit.visit_time and visit.visit_time >= today_start
    })
    visits_24h = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_24h]
    visits_30d = [visit for visit in recent_visit_rows if visit.visit_time and visit.visit_time >= last_30d]
    hourly_traffic = _count_by_hour(visits_24h)
    daily_traffic = _count_by_day(visits_30d)
    monthly_traffic = _count_by_month(recent_visit_rows)

    click_events = WebsiteEvent.query.filter_by(event_type="click").filter(
        WebsiteEvent.event_time >= last_30d,
        (WebsiteEvent.user_id.is_(None)) | (~WebsiteEvent.user_id.in_(admin_user_ids))
    ).order_by(WebsiteEvent.event_time.desc()).limit(5000).all()
    security_events = WebsiteEvent.query.filter_by(event_type="security").filter(
        WebsiteEvent.event_time >= last_30d
    ).order_by(WebsiteEvent.event_time.desc()).limit(2000).all()
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
    page_visit_groups = defaultdict(list)
    for visit in all_public_visit_rows:
        page_visit_groups[_analytics_path(visit.path)].append(visit)
    page_click_groups = Counter(_analytics_path(event.path) for event in click_events)
    for path, page_visits in sorted(page_visit_groups.items(), key=lambda item: len(item[1]), reverse=True)[:8]:
        page_visits_30d = [visit for visit in page_visits if visit.visit_time and visit.visit_time >= last_30d]
        page_metrics.append({
            "path": path,
            "views": len(page_visits),
            "views_30d": len(page_visits_30d),
            "unique": len({_visitor_key(visit) for visit in page_visits}),
            "logged_in": sum(1 for visit in page_visits if visit.is_authenticated),
            "guest": sum(1 for visit in page_visits if not visit.is_authenticated),
            "clicks": page_click_groups[path],
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
    managed_personas = (
        User.query
        .filter_by(is_managed_persona=True)
        .order_by(User.id.desc())
        .limit(60)
        .all()
    )
    car_communities = CarCommunity.query.order_by(CarCommunity.name.asc()).all()

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
        top_pages=page_metrics,
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
        banned_users=banned_users,
        managed_personas=managed_personas,
        car_communities=car_communities
    )


# ================= COMMUNITY STUDIO =================

@admin_bp.route("/admin/community/personas", methods=["POST"])
@login_required
def create_managed_persona():
    if not _require_admin():
        return "Access Denied", 403

    username = _slugify_persona_username(request.form.get("username"))
    city = (request.form.get("city") or "").strip()[:100]
    badge = (request.form.get("badge") or "Community Member").strip()[:50]
    note = (request.form.get("managed_note") or "").strip()[:255]
    email = (request.form.get("email") or "").strip().lower()

    if not username:
        flash("Persona username is required.")
        return redirect(url_for("admin.admin_dashboard"))

    if User.query.filter_by(username=username).first():
        flash("That username already exists.")
        return redirect(url_for("admin.admin_dashboard"))

    if not email:
        email_slug = username.lower().replace("_", "-")
        email = f"{email_slug}-{secrets.token_hex(4)}@community.ampyan.local"
    if User.query.filter_by(email=email).first():
        flash("That persona email already exists.")
        return redirect(url_for("admin.admin_dashboard"))

    persona = User(
        username=username,
        email=email,
        mobile="",
        password=generate_password_hash(secrets.token_urlsafe(32)),
        role="user",
        email_verified=True,
        is_banned=False,
        city=city,
        badge=badge or "Community Member",
        reputation=0,
        posts_count=0,
        helpful_answers=0,
        contributor_score=0,
        is_managed_persona=True,
        managed_by_admin_id=current_user.id,
        managed_note=note,
    )

    try:
        _commit_new_user_with_id_fallback(persona)
        flash(f"Managed community persona '{persona.username}' created.")
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Managed persona create failed: %s", exc.__class__.__name__)
        flash("Persona could not be created.")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/community/post-as", methods=["POST"])
@login_required
def admin_create_post_as_persona():
    if not _require_admin():
        return "Access Denied", 403

    author = _managed_persona_or_none(request.form.get("persona_id", type=int))
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    community_id = request.form.get("community_id", type=int)
    new_community_name = (request.form.get("new_community_name") or "").strip()

    if not author:
        flash("Select a managed persona first.")
        return redirect(url_for("admin.admin_dashboard"))
    if not title or not content:
        flash("Post title and content are required.")
        return redirect(url_for("admin.admin_dashboard"))

    car_community = None
    if new_community_name:
        car_community = _get_or_create_car_community(new_community_name, user=current_user)
    elif community_id:
        car_community = CarCommunity.query.get(community_id)

    try:
        post = Post(
            title=title[:200],
            content=content,
            user_id=author.id,
            community_id=car_community.id if car_community else None,
        )
        db.session.add(post)
        db.session.flush()
        refresh_author_stats(author)
        _sync_user_profile(author)
        _safe_remote_call(
            "/community/posts",
            method="POST",
            payload={
                "source": "website",
                "external_id": f"web-post-{post.id}",
                "email": author.email,
                "fullName": author.username,
                "mobile": author.mobile or "",
                "location": author.city or "Website",
                "text": f"{post.title}\n\n{post.content}",
                "community": car_community.name if car_community else "General Community",
            },
        )
        db.session.commit()
        flash(f"Post published as {author.username}.")
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Admin persona post failed: %s", exc.__class__.__name__)
        flash("Post could not be published.")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/admin/community/reply-as", methods=["POST"])
@login_required
def admin_reply_as_persona():
    if not _require_admin():
        return "Access Denied", 403

    author = _managed_persona_or_none(request.form.get("persona_id", type=int))
    post_id = request.form.get("post_id", type=int)
    parent_id = request.form.get("parent_id", type=int)
    content = (request.form.get("content") or "").strip()

    post = Post.query.get(post_id) if post_id else None
    if not author:
        flash("Select a managed persona first.")
        return redirect(url_for("admin.admin_dashboard"))
    if not post:
        flash("Select a valid post.")
        return redirect(url_for("admin.admin_dashboard"))
    if not content:
        flash("Reply text is required.")
        return redirect(url_for("admin.admin_dashboard"))

    if parent_id and not Comment.query.filter_by(id=parent_id, post_id=post.id).first():
        parent_id = None

    try:
        comment = Comment(content=content, user_id=author.id, post_id=post.id, parent_id=parent_id)
        db.session.add(comment)
        db.session.flush()
        refresh_author_stats(author)
        _sync_user_profile(author)

        remote_post_id = _find_remote_post_id_for_website_post(post.id)
        if remote_post_id:
            _safe_remote_call(
                f"/community/posts/{remote_post_id}/replies",
                method="POST",
                payload={
                    "source": "website",
                    "external_id": f"web-reply-{comment.id}",
                    "email": author.email,
                    "fullName": author.username,
                    "mobile": author.mobile or "",
                    "location": author.city or "Website",
                    "text": content,
                },
            )

        db.session.commit()
        flash(f"Reply added as {author.username}.")
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Admin persona reply failed: %s", exc.__class__.__name__)
        flash("Reply could not be added.")
    return redirect(url_for("admin.admin_dashboard"))


# ================= DELETE USER =================

@admin_bp.route("/admin/delete-user/<int:user_id>")
@login_required
def delete_user(user_id):

    if not _require_admin():
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

    if not _require_admin():
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = True
    db.session.commit()

    return redirect("/admin")


# ================= UNBAN USER =================

@admin_bp.route("/admin/unban-user/<int:user_id>")
@login_required
def unban_user(user_id):

    if not _require_admin():
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_banned = False
    db.session.commit()

    return redirect("/admin")


# ================= REMOVE ADMIN =================

@admin_bp.route("/admin/remove-admin/<int:user_id>")
@login_required
def remove_admin(user_id):

    if not _require_admin():
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.role = "user"
    db.session.commit()

    return redirect("/admin")


@admin_bp.route("/admin/approve-garage/<int:mechanic_id>")
@login_required
def approve_garage(mechanic_id):

    if not _require_admin():
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = True
    refresh_mechanic_reputation(mechanic)
    db.session.commit()
    sync_garage_to_app(mechanic)

    flash("Garage approved successfully.")
    return redirect("/admin")


@admin_bp.route("/admin/reject-garage/<int:mechanic_id>")
@login_required
def reject_garage(mechanic_id):

    if not _require_admin():
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_verified = False
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()
    delete_garage_from_app(mechanic.id)

    flash("Garage moved back to pending state.")
    return redirect("/admin")


@admin_bp.route("/admin/sync-app-content")
@login_required
def sync_app_content():
    if not _require_admin():
        return "Access Denied"

    news_items = News.query.order_by(News.id.asc()).all()
    verified_mechanics = MechanicProfile.query.filter_by(is_verified=True).all()

    news_synced = sum(1 for item in news_items if sync_news_to_app(item))
    garages_synced = sum(1 for mechanic in verified_mechanics if sync_garage_to_app(mechanic))

    flash(
        f"App sync completed: {news_synced}/{len(news_items)} news, "
        f"{garages_synced}/{len(verified_mechanics)} garages."
    )
    return redirect("/admin")


@admin_bp.route("/admin/feature-garage/<int:mechanic_id>")
@login_required
def feature_garage(mechanic_id):

    if not _require_admin():
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

    if not _require_admin():
        return "Access Denied"

    mechanic = MechanicProfile.query.get_or_404(mechanic_id)
    mechanic.is_featured = False
    refresh_mechanic_reputation(mechanic)
    db.session.commit()

    flash("Garage removed from featured list.")
    return redirect("/admin")
