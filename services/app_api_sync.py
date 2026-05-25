import os
from urllib.parse import urlparse

import requests
from flask import current_app, url_for


APP_API_BASE_URL = os.environ.get(
    "APP_API_BASE_URL",
    "https://ampyan-api.onrender.com",
).rstrip("/")
APP_API_TIMEOUT_SECONDS = float(os.environ.get("APP_API_TIMEOUT_SECONDS", "3"))
APP_NEWS_ID_OFFSET = int(os.environ.get("APP_NEWS_ID_OFFSET", "100000"))
APP_GARAGE_ID_OFFSET = int(os.environ.get("APP_GARAGE_ID_OFFSET", "100000"))
NEWS_CATEGORY_LABELS = {
    "auto-news": "Auto News",
    "car-review": "Car Review",
    "tips-and-tricks": "Tips and Tricks",
}


def _infer_news_category(news):
    text_value = f"{getattr(news, 'title', '')} {getattr(news, 'content', '')}".lower()
    if any(keyword in text_value for keyword in ("review", "road test", "test drive", "pros and cons", "ownership review")):
        return "car-review"
    if any(keyword in text_value for keyword in ("tip", "tips", "trick", "guide", "checklist", "how to", "maintenance", "mileage", "save petrol", "fuel bills", "cooling")):
        return "tips-and-tricks"
    return "auto-news"


def _effective_news_category(news):
    category = getattr(news, "category", None) or "auto-news"
    if category == "auto-news":
        return _infer_news_category(news)
    return category


def _request(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            f"{APP_API_BASE_URL}{path}",
            timeout=APP_API_TIMEOUT_SECONDS,
            **kwargs,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        current_app.logger.warning(
            "App API sync skipped path=%s error=%s",
            path,
            exc,
        )
        return False


def _absolute_static_url(folder, filename, fallback=None):
    parsed = urlparse(filename or "")
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return filename

    if not filename and fallback:
        filename = fallback
    if not filename:
        return ""
    return url_for("static", filename=f"{folder}/{filename}", _external=True)


def sync_news_to_app(news):
    app_article_id = APP_NEWS_ID_OFFSET + int(news.id)
    body = news.content or ""
    summary = body[:220].strip()
    if len(body) > 220:
        summary = f"{summary}..."
    payload = {
        "title": news.title or "",
        "summary": summary,
        "body": body,
        "category": NEWS_CATEGORY_LABELS.get(_effective_news_category(news), "Auto News"),
        "source": "AMPYAN",
        "image_url": _absolute_static_url(
            "news_images",
            news.image,
            fallback="AMPYAN_-_Powering_Intelligent_Mobility.png",
        ),
        "website_url": url_for("news_detail", news_id=news.id, _external=True),
        "published_at": news.created_at.isoformat() + "Z" if news.created_at else "",
    }
    return _request(
        "PUT",
        f"/news/articles/{app_article_id}",
        json=payload,
        headers={"X-AMPYAN-ROLE": "admin"},
    )


def delete_news_from_app(news_id):
    app_article_id = APP_NEWS_ID_OFFSET + int(news_id)
    return _request(
        "DELETE",
        f"/news/articles/{app_article_id}",
        headers={"X-AMPYAN-ROLE": "admin"},
    )


def delete_garage_from_app(mechanic_id):
    app_garage_id = APP_GARAGE_ID_OFFSET + int(mechanic_id)
    return _request("DELETE", f"/api/nearby-garages/{app_garage_id}")


def sync_garage_to_app(mechanic):
    if not mechanic.is_verified:
        return False
    services = [
        item.strip()
        for item in ((mechanic.service_types or mechanic.specialties or "").split(","))
        if item.strip()
    ]
    payload = {
        "id": APP_GARAGE_ID_OFFSET + int(mechanic.id),
        "name": mechanic.business_name or "Garage",
        "city": mechanic.city or "",
        "area": mechanic.state or mechanic.pincode or "",
        "address": mechanic.address or "",
        "phone": mechanic.phone or "",
        "rating": getattr(mechanic, "average_rating", None) or 0,
        "services": services,
        "latitude": None,
        "longitude": None,
        "source": "website",
    }
    return _request("POST", "/api/nearby-garages", json=payload)
