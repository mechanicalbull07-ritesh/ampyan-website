import json
import hashlib
import hmac
import os
import queue
import re
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import current_app, g, has_request_context, request, session
from flask_login import current_user
from sqlalchemy import inspect, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import OperationalError, ProgrammingError

from models.models import AnalyticsDedupeClaim, AnalyticsEvent, ApiRequestMetric, WebsiteVisit, db
from services.analytics_contract import (
    ALLOWED_EVENT_TYPES, CANONICAL_EVENTS, EVENT_PARAMETERS, FEATURE_VALUES,
    CONTENT_VALUES, METHOD_VALUES, SCREEN_VALUES, SCHEMA_VERSION,
    CANONICAL_FEATURE, CANONICAL_CONTENT,
)


EXCLUDED_PAGE_PATHS = {"/health", "/healthz", "/ready"}
CONTEXT_FIELDS = frozenset({"event_type", "session_id", "path", "referrer", "utm_source", "utm_medium", "utm_campaign", "source", "traffic_type", "platform", "trigger", "event_id"})
LEGACY_PARAMETERS = {"api_error": {"status_code"}, "login_failure": {"reason"}, "login_success": {"method"}, "scroll_depth": {"depth"}, "screen_view": {"screen"}}
CRITICAL_DEDUPE_EVENTS = frozenset({
    "sign_up", "login", "vehicle_added", "vehicle_updated",
    "diagnosis_started", "diagnosis_completed", "garage_contact_clicked", "share_clicked",
})
DEDUPE_WINDOW_SECONDS = 5


def action_event_id(token):
    """Turn a per-submission random form token into an opaque collector ID."""
    if not re.fullmatch(r"[0-9a-f]{32}|[0-9a-f-]{36}", str(token or ""), re.I):
        return None
    secret = current_app.secret_key.encode("utf-8") if isinstance(current_app.secret_key, str) else current_app.secret_key
    return hmac.new(secret, ("analytics-action:" + str(token)).encode(), hashlib.sha256).hexdigest()[:32]


class InvalidAnalyticsEvent(ValueError):
    pass


def safe_path(value):
    """Retain a path only; never retain query strings or URL credentials."""
    parsed = urlparse(str(value or ""))
    path = parsed.path or "/"
    if not path.startswith("/") or any(ord(char) < 32 for char in path):
        return "/"
    static = {"/", "/about", "/tools", "/tools/ai-diagnosis", "/tools/ai-diagnosis-followup",
        "/tools/fuel-cost", "/tools/emi-calculator", "/tools/depreciation-calculator",
        "/tools/maintenance-cost", "/community", "/news", "/garages", "/marketplace",
        "/videos", "/login", "/register", "/garage", "/garage-dashboard", "/app",
        "/my-car-health", "/add-car", "/create-post", "/privacy", "/contact", "/help"}
    if path in static:
        return path
    if path in {"/post/:id", "/news/:id", "/garages/:id", "/edit-car/:id", "/marketplace/:id"}:
        return path
    if path.startswith("/app/") and path[5:] in SCREEN_VALUES:
        return path
    for pattern, replacement in ((r"/post/\d+", "/post/:id"), (r"/news/\d+", "/news/:id"),
                                 (r"/garages/\d+", "/garages/:id"), (r"/edit-car/\d+", "/edit-car/:id"),
                                 (r"/marketplace/\d+", "/marketplace/:id")):
        if re.fullmatch(pattern, path):
            return replacement
    return "/other"


def safe_referrer(value):
    parsed = urlparse(str(value or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    return f"{parsed.scheme}://{parsed.hostname.lower()}/"


def _attribution(value):
    value = str(value or "").strip().lower()
    return value if re.fullmatch(r"[a-z0-9_-]{1,60}", value) and re.search(r"[a-z]", value) else ""


def validate_event(event_type, payload):
    if event_type not in ALLOWED_EVENT_TYPES:
        raise InvalidAnalyticsEvent("unsupported_event")
    if not isinstance(payload, dict) or payload.get("metadata") is not None:
        raise InvalidAnalyticsEvent("invalid_parameters")
    allowed = CONTEXT_FIELDS | EVENT_PARAMETERS.get(event_type, LEGACY_PARAMETERS.get(event_type, set()))
    if set(payload) - allowed:
        raise InvalidAnalyticsEvent("invalid_parameters")
    if any(not isinstance(value, (str, int, float, bool, type(None))) for value in payload.values()):
        raise InvalidAnalyticsEvent("invalid_parameters")
    if "traffic_type" in payload and payload["traffic_type"] not in {"web", "app"}:
        raise InvalidAnalyticsEvent("invalid_parameters")
    if "session_id" in payload and not re.fullmatch(r"[0-9a-f]{32}|[0-9a-f-]{36}", str(payload["session_id"]), re.I):
        raise InvalidAnalyticsEvent("invalid_parameters")
    if "event_id" in payload and not re.fullmatch(r"[0-9a-f]{32}|[0-9a-f-]{36}", str(payload["event_id"]), re.I):
        raise InvalidAnalyticsEvent("invalid_parameters")
    for field, values in (("feature", FEATURE_VALUES), ("content_type", CONTENT_VALUES), ("method", METHOD_VALUES), ("screen", SCREEN_VALUES)):
        if field in payload and payload[field] not in values:
            raise InvalidAnalyticsEvent("invalid_parameters")
    if "reason" in payload and payload["reason"] not in {"missing_credentials", "invalid_credentials"}:
        raise InvalidAnalyticsEvent("invalid_parameters")
    if "status_code" in payload and (not isinstance(payload["status_code"], int) or payload["status_code"] < 400 or payload["status_code"] > 599):
        raise InvalidAnalyticsEvent("invalid_parameters")
    if "depth" in payload and payload["depth"] not in {25, 50, 75, 100}:
        raise InvalidAnalyticsEvent("invalid_parameters")
    if event_type in CANONICAL_EVENTS:
        expected = EVENT_PARAMETERS[event_type]
        if expected and not expected.issubset(payload):
            raise InvalidAnalyticsEvent("invalid_parameters")
        if event_type in CANONICAL_FEATURE and payload["feature"] != CANONICAL_FEATURE[event_type]:
            raise InvalidAnalyticsEvent("invalid_parameters")
        if event_type in CANONICAL_CONTENT and payload["content_type"] not in CANONICAL_CONTENT[event_type]:
            raise InvalidAnalyticsEvent("invalid_parameters")
        if event_type in {"sign_up", "login"} and payload["method"] not in {"email", "google"}:
            raise InvalidAnalyticsEvent("invalid_parameters")
    if len(json.dumps(payload)) > 4096:
        raise InvalidAnalyticsEvent("invalid_parameters")
    return True
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


def analytics_consent_granted():
    return has_request_context() and request.cookies.get("ampyan_analytics_consent") == "granted"


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
    if host == "ampyan.com" or host.endswith(".ampyan.com"):
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
    referrer = safe_referrer(payload.get("referrer") or (request.referrer if has_request_context() else ""))
    attribution_cookie = (getattr(g, "analytics_attribution_cookie", None) or request.cookies.get("ampyan_analytics_attribution", "")) if has_request_context() else ""
    stored_attribution = attribution_cookie.split(".") if attribution_cookie.count(".") == 2 else ["", "", ""]
    query_source = request.args.get("utm_source", "") if has_request_context() else ""
    query_medium = request.args.get("utm_medium", "") if has_request_context() else ""
    query_campaign = request.args.get("utm_campaign", "") if has_request_context() else ""
    source = _attribution(payload.get("utm_source") or payload.get("source") or query_source or stored_attribution[0])
    medium = _attribution(payload.get("utm_medium") or query_medium or stored_attribution[1])
    campaign = _attribution(payload.get("utm_campaign") or query_campaign or stored_attribution[2])
    is_admin = is_admin_user or (has_request_context() and request.path.startswith("/admin"))
    return {
        "session_id": _clean(payload.get("session_id") or getattr(g, "analytics_session_id", ""), 100) if re.fullmatch(r"[0-9a-f]{32}|[0-9a-f-]{36}", str(payload.get("session_id") or getattr(g, "analytics_session_id", "")), re.I) else "",
        "source": _referrer_source(referrer, source),
        "utm_medium": medium,
        "utm_campaign": campaign,
        "path": safe_path(payload.get("path") or (request.path if has_request_context() else "")),
        "referrer": referrer,
        "country": (request.headers.get("CF-IPCountry", "").upper()
                    if has_request_context() and re.fullmatch(r"[A-Za-z]{2}", request.headers.get("CF-IPCountry", ""))
                    else ""),
        "city": "",
        "device_type": _clean(payload.get("device_type") or device, 30),
        "browser": _clean(payload.get("browser") or browser, 80),
        "os_name": _clean(payload.get("os") or payload.get("os_name") or os_name, 80),
        "traffic_type": _clean(payload.get("traffic_type") or traffic_type, 30),
        "is_bot": _is_bot(user_agent),
        "is_internal": _is_internal(ip_address) or _bool(payload.get("is_internal")),
        "is_admin": is_admin,
        "user_id": None,
        "ip_address": "",
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
            AnalyticsDedupeClaim.__table__.create(db.engine, checkfirst=True)
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
        dedupe_key = payload.pop("_dedupe_key", None)
        if dedupe_key:
            now = datetime.utcnow()
            expires = now + timedelta(seconds=DEDUPE_WINDOW_SECONDS)
            dialect = db.engine.dialect.name
            if dialect == "postgresql":
                statement = pg_insert(AnalyticsDedupeClaim).values(key=dedupe_key, expires_at=expires)
            elif dialect == "sqlite":
                statement = sqlite_insert(AnalyticsDedupeClaim).values(key=dedupe_key, expires_at=expires)
            else:
                raise RuntimeError("unsupported_analytics_dedupe_dialect")
            statement = statement.on_conflict_do_update(
                index_elements=[AnalyticsDedupeClaim.key],
                set_={"expires_at": expires},
                where=AnalyticsDedupeClaim.expires_at <= now,
            ).returning(AnalyticsDedupeClaim.key)
            if db.session.execute(statement).scalar_one_or_none() is None:
                db.session.commit()
                return False
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
        payload = payload or {}
        validate_event(event_type, payload)
        if not analytics_enabled() or (traffic_type == "web" and not analytics_consent_granted()):
            return False
        context = request_context(payload, traffic_type=traffic_type)
        approved = EVENT_PARAMETERS.get(event_type, LEGACY_PARAMETERS.get(event_type, set()))
        metadata = {key: payload[key] for key in approved if key in payload}
        metadata["schema_version"] = SCHEMA_VERSION
        # Only identical submission IDs are duplicates; a new action is never
        # suppressed merely because it occurs in the same session or five seconds.
        dedupe_key = None
        if event_type in CRITICAL_DEDUPE_EVENTS and payload.get("event_id"):
            dedupe_key = hashlib.sha256(f"{event_type}:{payload['event_id']}".encode()).hexdigest()
        accepted = _enqueue({
            "_kind": "event",
            "event_type": event_type,
            **context,
            "_dedupe_key": dedupe_key,
            "metadata_json": json.dumps(metadata, separators=(",", ":"))[:4000],
        })
        if accepted and event_type in CANONICAL_EVENTS and event_type != "car_health_viewed" and traffic_type == "web" and has_request_context():
            pending = list(session.get("_analytics_pending", []))[-9:]
            pending.append({"name": event_type, "parameters": {field: metadata[field] for field in approved if field in metadata}})
            session["_analytics_pending"] = pending
        return accepted
    except Exception:
        return False


def safe_track_page_visit():
    try:
        if not analytics_consent_granted():
            return False
        context = request_context(traffic_type="web")
        return _enqueue({
            "_kind": "visit",
            "ip_address": "",
            "visitor_id": "",
            "user_id": context["user_id"],
            "path": context["path"],
            "method": request.method,
            "referrer": context["referrer"],
            "user_agent": "",
            "device_type": context["device_type"],
            "session_id": context["session_id"],
            "source": context["source"],
            "utm_medium": context["utm_medium"],
            "utm_campaign": context["utm_campaign"],
            "country": context["country"],
            "city": "",
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
            "path": safe_path(path),
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
