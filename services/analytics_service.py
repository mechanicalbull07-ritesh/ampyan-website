import json
import os
import queue
import re
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import current_app, g, has_request_context, request
from flask_login import current_user
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from models.models import AnalyticsEvent, ApiRequestMetric, WebsiteVisit, db


ALLOWED_EVENT_TYPES = {
    "api_error",
    "app_open",
    "click",
    "community_opened",
    "diagnosis_completed",
    "diagnosis_started",
    "garage_added",
    "login_failure",
    "login_success",
    "news_opened",
    "page_view",
    "screen_view",
    "scroll_depth",
}
EXCLUDED_PAGE_PATHS = {"/health", "/healthz", "/ready"}
_queue = queue.Queue(maxsize=1000)
_worker_lock = threading.Lock()
_worker_started = False
_live_cache_lock = threading.Lock()
_live_cache = {"expires_at": 0.0, "value": None}
_storage_retry_after = 0.0
_last_storage_error = None
_last_storage_error_at = None
_last_storage_error_detail = None
_schema_lock = threading.Lock()
_schema_retry_after = 0.0


def analytics_enabled():
    return os.environ.get("ANALYTICS_ENABLED", "false").lower() == "true"


def _clean(value, limit=500):
    return re.sub(r"\s+", " ", str(value or "").strip())[:limit]


def _bool(value):
    return str(value or "").lower() in {"1", "true", "yes", "on"}


def _client_ip():
    if not has_request_context():
        return ""
    return _clean(request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0], 50)


def _is_bot(user_agent):
    if os.environ.get("BOT_FILTER_ENABLED", "true").lower() != "true":
        return False
    ua = (user_agent or "").lower()
    return any(token in ua for token in (
        "bot", "crawler", "spider", "slurp", "bingpreview", "facebookexternalhit",
        "headless", "lighthouse", "monitor", "uptime", "curl/", "wget/",
    ))


def _is_internal(ip_address):
    configured = {
        item.strip()
        for item in os.environ.get("ANALYTICS_INTERNAL_IPS", "").split(",")
        if item.strip()
    }
    return bool(ip_address and ip_address in configured)


def _user_agent_parts(user_agent):
    ua = user_agent or ""
    lowered = ua.lower()
    if any(token in lowered for token in ("iphone", "android", "mobile")):
        device = "mobile"
    elif any(token in lowered for token in ("ipad", "tablet")):
        device = "tablet"
    else:
        device = "desktop"

    if "edg/" in lowered:
        browser = "Edge"
    elif "opr/" in lowered or "opera" in lowered:
        browser = "Opera"
    elif "chrome/" in lowered:
        browser = "Chrome"
    elif "firefox/" in lowered:
        browser = "Firefox"
    elif "safari/" in lowered:
        browser = "Safari"
    else:
        browser = "Other"

    if "android" in lowered:
        os_name = "Android"
    elif "iphone" in lowered or "ipad" in lowered or "ios" in lowered:
        os_name = "iOS"
    elif "windows" in lowered:
        os_name = "Windows"
    elif "mac os" in lowered or "macintosh" in lowered:
        os_name = "macOS"
    elif "linux" in lowered:
        os_name = "Linux"
    else:
        os_name = "Other"
    return device, browser, os_name


def _referrer_source(referrer, utm_source=""):
    if utm_source:
        return _clean(utm_source, 120)
    parsed = urlparse(referrer or "")
    host = (parsed.netloc or "").lower()
    if not host:
        return "direct"
    if "ampyan.com" in host:
        return "internal"
    return _clean(host, 120)


def _source_bucket(source):
    value = (source or "direct").strip().lower()
    if not value or value == "direct":
        return "Direct"
    if "google" in value:
        return "Google"
    if "instagram" in value:
        return "Instagram"
    if "facebook" in value or value == "fb":
        return "Facebook"
    if "youtube" in value or "youtu.be" in value:
        return "YouTube"
    if "whatsapp" in value or "wa.me" in value:
        return "WhatsApp"
    if "ampyan" in value or value == "internal":
        return "Internal"
    return _clean(source, 120) or "Direct"


def _feature_bucket(path, event_type=""):
    value = (path or "").strip().lower()
    if value in {"", "/"}:
        return "Home"
    if value.startswith("/login") or event_type in {"login_success", "login_failure"}:
        return "Login"
    if value.startswith("/community") or event_type == "community_opened":
        return "Community"
    if value.startswith("/news") or event_type == "news_opened":
        return "News"
    if value.startswith("/garage") or value.startswith("/my-car-health") or event_type == "garage_added":
        return "Garage"
    if "diagnosis" in value or event_type in {"diagnosis_started", "diagnosis_completed"}:
        return "Diagnosis"
    if "nearby" in value:
        return "Nearby Garage"
    return value[:80] or "Other"


def _current_user_parts():
    try:
        if current_user.is_authenticated:
            return current_user.id, current_user.role == "admin"
    except Exception:
        pass
    return None, False


def request_context(payload=None, traffic_type="web"):
    payload = payload or {}
    user_agent = request.headers.get("User-Agent", "") if has_request_context() else ""
    ip_address = _client_ip()
    device, browser, os_name = _user_agent_parts(user_agent)
    user_id, is_admin_user = _current_user_parts()
    referrer = _clean(payload.get("referrer") or (request.referrer if has_request_context() else ""), 500)
    is_admin = is_admin_user or (has_request_context() and request.path.startswith("/admin"))
    return {
        "session_id": _clean(payload.get("session_id"), 100),
        "source": _referrer_source(referrer, payload.get("utm_source") or payload.get("source")),
        "path": _clean(payload.get("path") or (request.path if has_request_context() else ""), 500),
        "referrer": referrer,
        "country": _clean(
            payload.get("country")
            or (request.headers.get("CF-IPCountry", "") if has_request_context() else "")
            or (request.headers.get("X-Country", "") if has_request_context() else ""),
            100,
        ),
        "city": _clean(
            payload.get("city")
            or (request.headers.get("CF-IPCity", "") if has_request_context() else "")
            or (request.headers.get("X-City", "") if has_request_context() else ""),
            120,
        ),
        "device_type": _clean(payload.get("device_type") or device, 30),
        "browser": _clean(payload.get("browser") or browser, 80),
        "os_name": _clean(payload.get("os") or payload.get("os_name") or os_name, 80),
        "traffic_type": _clean(payload.get("traffic_type") or traffic_type, 30),
        "is_bot": _is_bot(user_agent),
        "is_internal": _is_internal(ip_address) or _bool(payload.get("is_internal")),
        "is_admin": is_admin,
        "user_id": user_id,
        "ip_address": ip_address,
    }


def _fallback_log(item):
    try:
        path = os.environ.get("ANALYTICS_FALLBACK_LOG", "/tmp/ampyan_analytics_fallback.jsonl")
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, default=str, separators=(",", ":")) + "\n")
    except Exception:
        pass


def _db_error_detail(exc, limit=320):
    original = getattr(exc, "orig", None)
    parts = [exc.__class__.__name__]
    if original is not None:
        parts.append(original.__class__.__name__)
        message = str(original)
    else:
        message = str(exc)
    message = re.sub(r"\s+", " ", message or "").strip()
    if message:
        parts.append(message[:limit])
    return ": ".join(parts)


def _column_type(column):
    dialect = db.engine.dialect.name
    if dialect == "postgresql":
        return str(column.type.compile(dialect=db.engine.dialect))
    return str(column.type.compile(dialect=db.engine.dialect))


def _add_missing_columns(table):
    inspector = inspect(db.engine)
    if not inspector.has_table(table.name):
        return

    existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
    for column in table.columns:
        if column.name in existing_columns:
            continue
        default = ""
        if column.default is not None and column.default.is_scalar:
            default = f" DEFAULT {column.default.arg!r}"
        safe_table = table.name.replace('"', '""')
        safe_column = column.name.replace('"', '""')
        db.session.execute(
            text(f'ALTER TABLE "{safe_table}" ADD COLUMN "{safe_column}" {_column_type(column)}{default}')
        )


def _create_indexes():
    indexes = {
        "website_visit": {
            "ix_website_visit_visit_time": "visit_time",
            "ix_website_visit_session_id": "session_id",
            "ix_website_visit_source": "source",
            "ix_website_visit_country": "country",
            "ix_website_visit_is_bot": "is_bot",
            "ix_website_visit_is_internal": "is_internal",
        },
        "analytics_event": {
            "ix_analytics_event_created_at": "created_at",
            "ix_analytics_event_event_type": "event_type",
            "ix_analytics_event_session_id": "session_id",
            "ix_analytics_event_source": "source",
            "ix_analytics_event_country": "country",
            "ix_analytics_event_is_bot": "is_bot",
            "ix_analytics_event_is_internal": "is_internal",
        },
        "api_request_metric": {
            "ix_api_request_metric_created_at": "created_at",
            "ix_api_request_metric_path": "path",
            "ix_api_request_metric_status_code": "status_code",
            "ix_api_request_metric_is_bot": "is_bot",
            "ix_api_request_metric_is_internal": "is_internal",
        },
    }
    inspector = inspect(db.engine)
    for table_name, table_indexes in indexes.items():
        if not inspector.has_table(table_name):
            continue
        safe_table = table_name.replace('"', '""')
        for index_name, column_name in table_indexes.items():
            safe_index = index_name.replace('"', '""')
            safe_column = column_name.replace('"', '""')
            db.session.execute(text(f'CREATE INDEX IF NOT EXISTS "{safe_index}" ON "{safe_table}" ("{safe_column}")'))


def ensure_analytics_schema(reason=None):
    """Additively create/repair analytics storage without touching core tables."""
    global _schema_retry_after
    if time.monotonic() < _schema_retry_after:
        return False

    with _schema_lock:
        if time.monotonic() < _schema_retry_after:
            return False
        try:
            WebsiteVisit.__table__.create(db.engine, checkfirst=True)
            AnalyticsEvent.__table__.create(db.engine, checkfirst=True)
            ApiRequestMetric.__table__.create(db.engine, checkfirst=True)
            _add_missing_columns(WebsiteVisit.__table__)
            _add_missing_columns(AnalyticsEvent.__table__)
            _add_missing_columns(ApiRequestMetric.__table__)
            _create_indexes()
            db.session.commit()
            _schema_retry_after = 0.0
            if reason is not None:
                current_app.logger.info(
                    "analytics_schema_repaired reason=%s",
                    _db_error_detail(reason),
                )
            return True
        except Exception as exc:
            db.session.rollback()
            _schema_retry_after = time.monotonic() + 300
            current_app.logger.warning(
                "analytics_schema_repair_failed error=%s detail=%s",
                exc.__class__.__name__,
                _db_error_detail(exc),
                exc_info=True,
            )
            return False


def _insert_payload(item):
    payload = dict(item)
    kind = payload.pop("_kind", "")
    if kind == "event":
        db.session.add(AnalyticsEvent(**payload))
    elif kind == "visit":
        db.session.add(WebsiteVisit(**payload))
    elif kind == "api_metric":
        db.session.add(ApiRequestMetric(**payload))
    else:
        return False
    db.session.commit()
    return True


def _persist(item):
    global _last_storage_error, _last_storage_error_at, _last_storage_error_detail
    global _storage_retry_after
    retry_seconds = max(5, min(int(os.environ.get("ANALYTICS_STORAGE_RETRY_SECONDS", "30")), 300))
    if time.monotonic() < _storage_retry_after:
        _fallback_log(item)
        return

    try:
        _insert_payload(item)
        _storage_retry_after = 0.0
    except (ProgrammingError, OperationalError) as exc:
        db.session.rollback()
        if ensure_analytics_schema(reason=exc):
            try:
                _insert_payload(item)
                _storage_retry_after = 0.0
                return
            except Exception as retry_exc:
                db.session.rollback()
                exc = retry_exc
        _storage_retry_after = time.monotonic() + retry_seconds
        _last_storage_error = exc.__class__.__name__
        _last_storage_error_detail = _db_error_detail(exc)
        _last_storage_error_at = datetime.utcnow()
        current_app.logger.warning(
            "analytics_storage_degraded retry_seconds=%s kind=%s error=%s detail=%s",
            retry_seconds,
            item.get("_kind", "unknown"),
            exc.__class__.__name__,
            _last_storage_error_detail,
            exc_info=True,
        )
        _fallback_log(item)
    except Exception as exc:
        db.session.rollback()
        _storage_retry_after = time.monotonic() + retry_seconds
        _last_storage_error = exc.__class__.__name__
        _last_storage_error_detail = _db_error_detail(exc)
        _last_storage_error_at = datetime.utcnow()
        current_app.logger.warning(
            "analytics_storage_degraded retry_seconds=%s kind=%s error=%s detail=%s",
            retry_seconds,
            item.get("_kind", "unknown"),
            exc.__class__.__name__,
            _last_storage_error_detail,
            exc_info=True,
        )
        _fallback_log(item)


def _worker(app):
    while True:
        item = _queue.get()
        try:
            with app.app_context():
                _persist(item)
        except Exception:
            _fallback_log(item)
        finally:
            _queue.task_done()


def start_worker(app):
    global _worker_started
    if not analytics_enabled():
        return
    with _worker_lock:
        if _worker_started:
            return
        threading.Thread(target=_worker, args=(app,), daemon=True, name="ampyan-analytics").start()
        _worker_started = True


def _enqueue(item):
    if not analytics_enabled():
        return False
    try:
        start_worker(current_app._get_current_object())
        _queue.put_nowait(item)
        return True
    except Exception:
        _fallback_log(item)
        return False


def safe_track_event(event_type, payload=None, traffic_type="web"):
    try:
        event_type = _clean(event_type, 60)
        if event_type not in ALLOWED_EVENT_TYPES:
            return False
        payload = payload or {}
        context = request_context(payload, traffic_type=traffic_type)
        metadata = {
            key: _clean(value, 300)
            for key, value in payload.items()
            if key not in context and key not in {"metadata", "referrer"}
        }
        supplied_metadata = payload.get("metadata")
        if isinstance(supplied_metadata, dict):
            metadata.update({str(key)[:80]: _clean(value, 300) for key, value in supplied_metadata.items()})
        return _enqueue({
            "_kind": "event",
            "event_type": event_type,
            **context,
            "metadata_json": json.dumps(metadata, separators=(",", ":"))[:4000],
        })
    except Exception:
        return False


def safe_track_page_visit():
    try:
        context = request_context(traffic_type="web")
        return _enqueue({
            "_kind": "visit",
            "ip_address": context["ip_address"],
            "visitor_id": _clean(request.cookies.get("ampyan_visitor_id") or getattr(g, "set_visitor_cookie", ""), 80),
            "user_id": context["user_id"],
            "path": context["path"],
            "method": request.method,
            "referrer": context["referrer"],
            "user_agent": _clean(request.headers.get("User-Agent", ""), 500),
            "device_type": context["device_type"],
            "session_id": context["session_id"],
            "source": context["source"],
            "country": context["country"],
            "city": context["city"],
            "browser": context["browser"],
            "os_name": context["os_name"],
            "is_bot": context["is_bot"],
            "is_internal": context["is_internal"],
            "is_admin": context["is_admin"],
            "traffic_type": "web",
            "is_authenticated": context["user_id"] is not None,
            "is_page_view": True,
        })
    except Exception:
        return False


def safe_track_api_request(path, method, status_code, response_time_ms):
    try:
        if not path.startswith("/api") or path == "/api/track-event":
            return False
        context = request_context(traffic_type="api")
        _enqueue({
            "_kind": "api_metric",
            "path": _clean(path, 500),
            "method": _clean(method, 10),
            "status_code": int(status_code),
            "response_time_ms": max(0, min(int(response_time_ms), 3_600_000)),
            "traffic_type": "api",
            "is_bot": context["is_bot"],
            "is_internal": context["is_internal"],
            "is_admin": context["is_admin"],
        })
        if int(status_code) >= 500:
            safe_track_event("api_error", {"path": path, "status_code": status_code}, traffic_type="api")
        return True
    except Exception:
        return False


def analytics_storage_status():
    fallback_active = time.monotonic() < _storage_retry_after
    return {
        "fallback_active": fallback_active,
        "last_error": _last_storage_error,
        "last_error_detail": _last_storage_error_detail,
        "last_error_at": _last_storage_error_at.isoformat() if _last_storage_error_at else None,
    }


def live_summary():
    now_monotonic = time.monotonic()
    cache_seconds = max(10, min(int(os.environ.get("ADMIN_ANALYTICS_CACHE_SECONDS", "60")), 600))
    with _live_cache_lock:
        if _live_cache["value"] is not None and _live_cache["expires_at"] > now_monotonic:
            return _live_cache["value"]

    now = datetime.utcnow()
    since = now - timedelta(hours=24)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    human_filter = (
        AnalyticsEvent.created_at >= since,
        AnalyticsEvent.is_bot.is_(False),
        AnalyticsEvent.is_internal.is_(False),
        AnalyticsEvent.is_admin.is_(False),
    )
    events = AnalyticsEvent.query.filter(*human_filter).order_by(AnalyticsEvent.created_at.desc()).limit(2000).all()
    api_rows = ApiRequestMetric.query.filter(ApiRequestMetric.created_at >= since).order_by(ApiRequestMetric.created_at.desc()).limit(1000).all()
    today_events = [event for event in events if event.created_at and event.created_at >= today_start]
    sessions = {event.session_id for event in events if event.session_id}
    today_sessions = {event.session_id for event in today_events if event.session_id}
    event_counts = Counter(event.event_type for event in events)
    today_event_counts = Counter(event.event_type for event in today_events)
    slow_counter = Counter(row.path for row in api_rows if (row.response_time_ms or 0) >= 2000)
    hourly_page_views = Counter()
    hourly_sessions = {}
    hourly_app_events = Counter()
    hourly_api_errors = Counter()
    for event in events:
        if not event.created_at:
            continue
        hour_key = event.created_at.replace(minute=0, second=0, microsecond=0).strftime("%H:00")
        if event.event_type == "page_view":
            hourly_page_views[hour_key] += 1
        if event.session_id:
            hourly_sessions.setdefault(hour_key, set()).add(event.session_id)
        if event.traffic_type == "app" or event.event_type in {"app_open", "screen_view"}:
            hourly_app_events[hour_key] += 1
    for row in api_rows:
        if not row.created_at or (row.status_code or 0) < 500:
            continue
        hour_key = row.created_at.replace(minute=0, second=0, microsecond=0).strftime("%H:00")
        hourly_api_errors[hour_key] += 1
    hour_labels = [
        (now - timedelta(hours=index)).replace(minute=0, second=0, microsecond=0).strftime("%H:00")
        for index in range(23, -1, -1)
    ]
    hourly_24h = [
        {
            "hour": label,
            "page_views": hourly_page_views[label],
            "sessions": len(hourly_sessions.get(label, set())),
            "app_events": hourly_app_events[label],
            "api_errors": hourly_api_errors[label],
        }
        for label in hour_labels
    ]
    storage_status = analytics_storage_status()
    value = {
        "db_status": "OK",
        "analytics_fallback_active": storage_status["fallback_active"],
        "last_analytics_error": storage_status["last_error"] or "None",
        "last_analytics_error_at": storage_status["last_error_at"],
        "human_page_views_today": today_event_counts["page_view"],
        "human_sessions_today": len(today_sessions),
        "app_opens_today": today_event_counts["app_open"],
        "new_events_today": len(today_events),
        "api_errors_today": sum(1 for row in api_rows if row.created_at and row.created_at >= today_start and (row.status_code or 0) >= 500),
        "human_sessions_24h": len(sessions),
        "page_views_24h": event_counts["page_view"],
        "app_opens_24h": event_counts["app_open"],
        "api_errors_24h": sum(1 for row in api_rows if (row.status_code or 0) >= 500),
        "failed_logins_24h": event_counts["login_failure"],
        "hourly_24h": hourly_24h,
        "feature_usage_24h": dict(event_counts),
        "top_sources": Counter(_source_bucket(event.source) for event in events).most_common(10),
        "top_features": Counter(_feature_bucket(event.path, event.event_type) for event in events).most_common(10),
        "top_countries": Counter(event.country or "Unknown" for event in events).most_common(10),
        "top_cities": Counter(event.city or "Unknown" for event in events).most_common(10),
        "devices": Counter(event.device_type or "Unknown" for event in events).most_common(10),
        "browsers": Counter(event.browser or "Unknown" for event in events).most_common(10),
        "operating_systems": Counter(event.os_name or "Unknown" for event in events).most_common(10),
        "referrers": Counter(event.source or "direct" for event in events).most_common(10),
        "slow_endpoints": slow_counter.most_common(10),
        "bot_events_24h": AnalyticsEvent.query.filter(AnalyticsEvent.created_at >= since, AnalyticsEvent.is_bot.is_(True)).count(),
        "internal_events_24h": AnalyticsEvent.query.filter(AnalyticsEvent.created_at >= since, AnalyticsEvent.is_internal.is_(True)).count(),
        "admin_events_24h": AnalyticsEvent.query.filter(AnalyticsEvent.created_at >= since, AnalyticsEvent.is_admin.is_(True)).count(),
    }
    with _live_cache_lock:
        _live_cache["value"] = value
        _live_cache["expires_at"] = now_monotonic + cache_seconds
    return value


def safe_live_summary():
    try:
        return live_summary()
    except Exception:
        db.session.rollback()
        return {
            "db_status": "Limited",
            "analytics_fallback_active": True,
            "last_analytics_error": "Analytics summary unavailable",
            "last_analytics_error_at": None,
            "human_page_views_today": 0,
            "human_sessions_today": 0,
            "app_opens_today": 0,
            "new_events_today": 0,
            "api_errors_today": 0,
            "human_sessions_24h": 0,
            "page_views_24h": 0,
            "app_opens_24h": 0,
            "api_errors_24h": 0,
            "failed_logins_24h": 0,
            "hourly_24h": [],
            "feature_usage_24h": {},
            "top_sources": [],
            "top_features": [],
            "top_countries": [],
            "top_cities": [],
            "devices": [],
            "browsers": [],
            "operating_systems": [],
            "referrers": [],
            "slow_endpoints": [],
            "bot_events_24h": 0,
            "internal_events_24h": 0,
            "admin_events_24h": 0,
        }
