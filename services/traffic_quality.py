"""Anonymous counts of public, origin-served HTML document responses."""

from datetime import datetime, timedelta

from flask import current_app, g, request
from flask_login import current_user
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from models.models import TrafficMetric, db
from services.analytics_service import _client_ip, _is_internal


# Review public GET endpoints when routes change. Unlisted routes are private by default.
PUBLIC_CONTENT_ENDPOINTS = frozenset({
    "main.home", "about", "vision", "speed16", "yaanix", "platform",
    "privacy", "terms", "disclaimer", "contact", "help_center",
    "news_list", "news_detail", "news_story", "post_story", "videos",
    "main.marketplace", "main.marketplace_listing_detail", "main.leaderboard",
    "main.garage_network", "main.garage_profile",
    "community.community", "community.post_detail", "community.remote_post_detail",
    "website_blogs.index", "website_blogs.index_slash", "website_blogs.detail",
    "tools.tools", "tools.fuel_cost", "tools.emi_calculator",
    "tools.depreciation_calculator", "tools.maintenance_cost",
    "tools.car_suggestion", "tools.ai_diagnosis_page", "diagnose",
})
BOT_MARKERS = (
    "bot", "crawler", "spider", "slurp", "bingpreview", "facebookexternalhit",
    "headless", "lighthouse", "monitor", "uptime", "curl/", "wget/",
    "python-requests", "scrapy", "selenium", "playwright", "puppeteer",
)
def eligible_response(response):
    if request.method != "GET" or response.status_code != 200:
        return False
    if not response.mimetype == "text/html" or request.url_rule is None:
        return False
    if request.endpoint not in PUBLIC_CONTENT_ENDPOINTS:
        return False
    if current_user.is_authenticated and current_user.role == "admin":
        return False
    if _is_internal(_client_ip()):
        return False
    if any(token in request.headers.get("Purpose", "").lower() for token in ("prefetch", "prerender")):
        return False
    if any(token in request.headers.get("Sec-Purpose", "").lower() for token in ("prefetch", "prerender")):
        return False
    if request.headers.get("Sec-Fetch-Dest", "").lower() not in {"", "document"}:
        return False
    if request.headers.get("Sec-Fetch-Mode", "").lower() not in {"", "navigate"}:
        return False
    return True


def classify_request():
    ua = request.headers.get("User-Agent", "").lower()
    if any(marker in ua for marker in BOT_MARKERS):
        return "likely_bot"
    accept = request.headers.get("Accept", "").lower()
    document_navigation = (
        "text/html" in accept
        and request.headers.get("Sec-Fetch-Dest", "").lower() == "document"
        and request.headers.get("Sec-Fetch-Mode", "").lower() == "navigate"
    )
    chrome = "chrome/" in ua and "applewebkit/" in ua and "safari/" in ua
    firefox = "firefox/" in ua and "gecko/" in ua
    safari = "version/" in ua and "safari/" in ua and "applewebkit/" in ua
    if document_navigation and (chrome or firefox or safari):
        return "human_like"
    return "unknown"


def count_response(response):
    try:
        if getattr(g, "traffic_quality_counted", False) or not eligible_response(response):
            return response
        g.traffic_quality_counted = True
        quality = classify_request()
        hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        table = TrafficMetric.__table__
        if db.engine.dialect.name == "postgresql":
            statement = pg_insert(table).values(hour_start_utc=hour, quality=quality, count=1)
        elif db.engine.dialect.name == "sqlite":
            statement = sqlite_insert(table).values(hour_start_utc=hour, quality=quality, count=1)
        else:
            raise RuntimeError("TrafficMetric requires PostgreSQL or SQLite")
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.hour_start_utc, table.c.quality],
            set_={"count": table.c.count + 1},
        )
        # Separate transaction: never commit or roll back unrelated route work.
        with db.engine.begin() as connection:
            connection.execute(statement)
    except Exception as exc:
        try:
            current_app.logger.warning("traffic_metric_failed error=%s", exc.__class__.__name__)
        except Exception:
            pass
    return response


def traffic_quality_summary():
    """Return aggregate-only counts for the trailing 24 UTC hours."""
    cutoff = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
    rows = (TrafficMetric.query.filter(TrafficMetric.hour_start_utc >= cutoff)
            .order_by(TrafficMetric.hour_start_utc).all())
    totals = {"human_like": 0, "likely_bot": 0, "unknown": 0}
    hourly = {}
    for row in rows:
        totals[row.quality] += row.count
        hour = row.hour_start_utc.strftime("%Y-%m-%d %H:00 UTC")
        hourly[hour] = hourly.get(hour, 0) + row.count
    return {"total": sum(totals.values()), "totals": totals, "hourly": list(hourly.items())}
