"""Aggregate traffic quality stays independent of consented analytics."""

import pytest
from sqlalchemy import inspect

import app as website
from services import traffic_quality as traffic
from models.models import TrafficMetric, db
from services.traffic_quality import count_response


BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36", "Accept": "text/html", "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate"}


@pytest.fixture(autouse=True)
def isolated_counts(monkeypatch):
    monkeypatch.setattr(website, "safe_track_page_visit", lambda: True)
    with website.app.app_context():
        TrafficMetric.__table__.create(db.engine, checkfirst=True)
        db.session.query(TrafficMetric).delete()
        db.session.commit()
    yield
    with website.app.app_context():
        db.session.query(TrafficMetric).delete()
        db.session.commit()


def counts():
    with website.app.app_context():
        return {row.quality: row.count for row in TrafficMetric.query.all()}


def test_normal_browser_and_consent_choices_count_once():
    client = website.app.test_client()
    for consent in ("denied", "granted"):
        client.set_cookie("ampyan_analytics_consent", consent)
        assert client.get("/about", headers=BROWSER).status_code == 200
    assert counts() == {"human_like": 2}


def test_obvious_bot_and_ambiguous_signals():
    client = website.app.test_client()
    assert client.get("/about", headers={**BROWSER, "User-Agent": "Googlebot/2.1"}).status_code == 200
    assert client.get("/about", headers={"Accept": "text/html"}).status_code == 200
    assert counts() == {"likely_bot": 1, "unknown": 1}


@pytest.mark.parametrize("ua", [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36 Edg/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
])
def test_representative_browsers_are_human_like(ua):
    with website.app.test_request_context("/about", headers={**BROWSER, "User-Agent": ua}):
        assert traffic.classify_request() == "human_like"


@pytest.mark.parametrize("ua", [
    "curl/8.0", "Wget/1.21", "Mozilla/5.0 HeadlessChrome/120.0 Safari/537.36",
    "Googlebot/2.1", "bingbot/2.0", "python-requests/2.31",
])
def test_obvious_automation_is_likely_bot(ua):
    with website.app.test_request_context("/about", headers={**BROWSER, "User-Agent": ua}):
        assert traffic.classify_request() == "likely_bot"


@pytest.mark.parametrize("headers", [
    {**BROWSER, "User-Agent": "Mozilla/5.0"},
    {**BROWSER, "User-Agent": "Mozilla/5.0 SomeBrowser/1.0"},
    {**BROWSER, "Sec-Fetch-Mode": ""},
    {**BROWSER, "Sec-Fetch-Dest": ""},
    {**BROWSER, "Accept": "*/*"},
])
def test_ambiguous_or_incomplete_browser_signals_are_unknown(headers):
    with website.app.test_request_context("/about", headers=headers):
        assert traffic.classify_request() == "unknown"


def test_browser_without_document_signal_is_unknown():
    headers = {key: value for key, value in BROWSER.items() if key != "Sec-Fetch-Dest"}
    assert website.app.test_client().get("/about", headers=headers).status_code == 200
    assert counts() == {"unknown": 1}


@pytest.mark.parametrize("path", [
    "/login", "/register", "/logout", "/forgot-password",
    "/reset-password/synthetic", "/verify-email/synthetic", "/admin/analytics",
    "/profile", "/dashboard", "/mechanic-dashboard", "/garage-dashboard",
    "/my-car-health", "/add-car", "/edit-car/1",
    "/create-post", "/post/1/edit", "/comment/1/edit",
    "/blogs/write", "/blogs/1/edit", "/blogs/me", "/blogs/moderation",
    "/marketplace/create", "/marketplace/inbox", "/garages/register",
    "/videos/1/edit", "/api/profile", "/static/style.css",
])
def test_private_and_noncontent_routes_are_excluded_even_if_html_200(path):
    with website.app.test_request_context(path, headers=BROWSER):
        response = website.app.make_response("<html></html>")
        response.mimetype = "text/html"
        assert not traffic.eligible_response(response), path


@pytest.mark.parametrize("path", [
    "/", "/about", "/privacy", "/news", "/community", "/tools",
    "/marketplace", "/garages", "/blogs", "/videos",
])
def test_reviewed_public_content_routes_remain_eligible(path):
    with website.app.test_request_context(path, headers=BROWSER):
        response = website.app.make_response("<html></html>")
        response.mimetype = "text/html"
        assert traffic.eligible_response(response), path


@pytest.mark.parametrize("failure_point", ["eligibility", "classification", "database"])
def test_traffic_pipeline_failure_never_breaks_public_response(monkeypatch, failure_point):
    def fail(*_args, **_kwargs):
        raise RuntimeError("synthetic traffic-quality failure")

    with monkeypatch.context() as patch:
        if failure_point == "eligibility":
            patch.setattr(traffic, "eligible_response", fail)
        elif failure_point == "classification":
            patch.setattr(traffic, "classify_request", fail)
        else:
            with website.app.app_context():
                patch.setattr(db.engine, "begin", fail)
        response = website.app.test_client().get("/about", headers=BROWSER)
        assert response.status_code == 200
        assert b"about" in response.data.lower()
    assert counts() == {}


def test_authenticated_user_lookup_failure_never_breaks_public_response(monkeypatch):
    class BrokenUser:
        @property
        def is_authenticated(self):
            raise RuntimeError("synthetic authentication lookup failure")

    with monkeypatch.context() as patch:
        patch.setattr(traffic, "current_user", BrokenUser())
        response = website.app.test_client().get("/about", headers=BROWSER)
        assert response.status_code == 200
    assert counts() == {}


@pytest.mark.parametrize("method,path,headers", [
    ("GET", "/static/style.css", BROWSER),
    ("GET", "/api/unknown", BROWSER),
    ("GET", "/admin", BROWSER),
    ("GET", "/profile", BROWSER),
    ("GET", "/login", BROWSER),
    ("GET", "/not-a-real-page", BROWSER),
    ("GET", "/about", {**BROWSER, "Purpose": "prefetch"}),
    ("GET", "/about", {**BROWSER, "Sec-Purpose": "prefetch;prerender"}),
    ("GET", "/about", {**BROWSER, "Sec-Fetch-Dest": "image"}),
    ("POST", "/about", BROWSER),
    ("HEAD", "/about", BROWSER),
])
def test_ineligible_responses_excluded(method, path, headers):
    website.app.test_client().open(path, method=method, headers=headers)
    assert counts() == {}


def test_same_request_cannot_double_count():
    with website.app.test_request_context("/about", headers=BROWSER):
        response = website.app.make_response("<html></html>")
        response.mimetype = "text/html"
        count_response(response)
        count_response(response)
    assert counts() == {"human_like": 1}


def test_metric_schema_contains_only_aggregate_fields():
    columns = {column.name for column in inspect(TrafficMetric).columns}
    assert columns == {"hour_start_utc", "quality", "count"}
    assert "ampyan_analytics_consent" not in columns
