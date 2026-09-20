import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app as website
from services import analytics_service as analytics
from services.analytics_contract import CANONICAL_EVENTS, LEGACY_EVENTS, CANONICAL_FEATURE, CANONICAL_CONTENT
import routes.auth_routes as auth_routes
import routes.garage_routes as garage_routes
import routes.tools_routes as tools_routes
from tests.csrf_helpers import csrf_form_data, csrf_json_headers


@pytest.fixture(autouse=True)
def analytics_state(monkeypatch):
    monkeypatch.setenv("ANALYTICS_ENABLED", "true")


@pytest.mark.parametrize("event", sorted(CANONICAL_EVENTS))
def test_all_canonical_events_accepted(event):
    parameter = analytics.EVENT_PARAMETERS[event]
    payload = {"event_type": event}
    if "method" in parameter:
        payload["method"] = "email"
    if "feature" in parameter:
        payload["feature"] = CANONICAL_FEATURE[event]
    if "content_type" in parameter:
        payload["content_type"] = next(iter(CANONICAL_CONTENT[event]))
    assert analytics.validate_event(event, payload)


@pytest.mark.parametrize("event", sorted(LEGACY_EVENTS))
def test_legacy_names_remain_accepted(event):
    assert analytics.validate_event(event, {"event_type": event})


@pytest.mark.parametrize("payload", [
    {"event_type": "unknown"},
    {"event_type": "sign_up", "method": "email", "email": "x@example.com"},
    {"event_type": "diagnosis_started", "feature": "diagnosis", "symptoms": "private"},
    {"event_type": "vehicle_added", "feature": "vehicle", "registration_plate": "AB123"},
    {"event_type": "login", "method": "email", "metadata": {"name": "secret"}},
    {"event_type": "login", "method": "arbitrary"},
    {"event_type": "vehicle_added", "feature": "diagnosis"},
])
def test_rejects_unknown_and_pii(payload):
    with pytest.raises(analytics.InvalidAnalyticsEvent):
        analytics.validate_event(payload["event_type"], payload)


def test_path_referrer_and_attribution_are_reduced():
    assert analytics.safe_path("https://ampyan.com/tools/fuel-cost?email=x&car=abc") == "/tools/fuel-cost"
    assert analytics.safe_path("/post/123?token=abc") == "/post/:id"
    assert analytics.safe_path("/user/someone@example.com") == "/other"
    assert analytics.safe_referrer("https://example.com/page?token=abc") == "https://example.com/"
    with website.app.test_request_context("/tools?email=x", headers={"Referer": "https://example.com/?phone=123"}):
        context = analytics.request_context({"utm_source": "x@example.com"})
    assert context["path"] == "/tools"
    assert context["referrer"] == "https://example.com/"
    assert context["source"] == "example.com"
    assert context["ip_address"] == "" and context["user_id"] is None


def test_endpoint_distinguishes_rejected_denied_accepted_and_failed(monkeypatch):
    client = website.app.test_client()
    headers = csrf_json_headers(client)
    assert client.post("/api/track-event", json={"event_type": "unknown"}, headers=headers).status_code == 422
    assert client.post("/api/track-event", data="[", headers=headers).status_code == 400
    assert client.post("/api/track-event", json={"event_type": "login", "method": "email"}, headers=headers).status_code == 403
    client.set_cookie("ampyan_analytics_consent", "granted")
    monkeypatch.setattr(analytics, "_enqueue", lambda item: True)
    accepted = client.post("/api/track-event", json={"event_type": "login", "method": "email", "session_id": "a" * 32}, headers=headers)
    assert accepted.status_code == 202 and accepted.json["status"] == "accepted"
    monkeypatch.setattr(analytics, "_enqueue", lambda item: False)
    failed = client.post("/api/track-event", json={"event_type": "page_view"}, headers=headers)
    assert failed.status_code == 503 and failed.json["status"] == "failed"


def test_consent_gates_queue(monkeypatch):
    items = []
    monkeypatch.setattr(analytics, "_enqueue", lambda item: items.append(item) or True)
    payload = {"feature": "vehicle", "session_id": "a" * 32}
    with website.app.test_request_context("/garage", headers={"Cookie": "ampyan_analytics_consent=granted"}):
        assert analytics.safe_track_event("vehicle_added", payload)
        assert analytics.safe_track_event("vehicle_added", payload)
    assert len(items) == 2
    with website.app.test_request_context("/garage", headers={"Cookie": "ampyan_analytics_consent=denied"}):
        assert not analytics.safe_track_event("vehicle_added", payload)
    assert len(items) == 2


def test_successful_canonical_event_queues_safe_ga4_event(monkeypatch):
    monkeypatch.setattr(analytics, "_enqueue", lambda item: True)
    with website.app.test_request_context("/register", headers={"Cookie": "ampyan_analytics_consent=granted"}):
        assert analytics.safe_track_event("sign_up", {"method":"email"})
        from flask import session
        assert session["_analytics_pending"] == [{"name":"sign_up", "parameters":{"method":"email"}}]


def test_private_routes_absent_from_sitemap():
    sitemap = website.app.test_client().get("/sitemap.xml").get_data(as_text=True)
    assert "https://ampyan.com/login" not in sitemap
    assert "https://ampyan.com/my-car-health" not in sitemap
    assert "https://ampyan.com/tools/ai-diagnosis" in sitemap


def test_browser_session_and_consent_implementation_present():
    base = (Path(__file__).parents[1] / "templates" / "base.html").read_text()
    assert "1800000" in base
    assert "sessionStorage" in base
    assert "analytics-grant" in base and "analytics-deny" in base
    assert "target.innerText" not in base


def test_server_session_rotates_after_inactivity(monkeypatch):
    monkeypatch.setattr(website, "safe_track_page_visit", lambda: True)
    client = website.app.test_client()
    client.set_cookie("ampyan_analytics_consent", "granted")
    first = client.get("/about")
    initial = next(c.value for c in client._cookies.values() if c.key == "ampyan_analytics_session")
    assert len(initial.split(".")[0]) == 32
    client.get("/about")
    current = next(c.value for c in client._cookies.values() if c.key == "ampyan_analytics_session")
    assert current.split(".")[0] == initial.split(".")[0]
    client.set_cookie("ampyan_analytics_session", f"{initial.split('.')[0]}.{initial.split('.')[1]}.1")
    client.get("/about")
    expired = next(c.value for c in client._cookies.values() if c.key == "ampyan_analytics_session")
    assert expired.split(".")[0] != initial.split(".")[0]


def test_safe_attribution_persists_after_landing(monkeypatch):
    captured = []
    monkeypatch.setattr(website, "safe_track_page_visit", lambda: captured.append(analytics.request_context()) or True)
    client = website.app.test_client()
    client.set_cookie("ampyan_analytics_consent", "granted")
    client.get("/?utm_source=instagram&utm_medium=social&utm_campaign=speed16&email=secret@example.com")
    client.get("/about")
    assert captured[0]["source"] == "instagram"
    assert captured[1]["source"] == "instagram"
    assert captured[1]["utm_medium"] == "social"
    assert captured[1]["utm_campaign"] == "speed16"
    assert "secret" not in json.dumps(captured)


def test_signup_event_only_after_account_commit(monkeypatch):
    events = []
    with website.app.app_context():
        monkeypatch.setattr(auth_routes.User, "query", MagicMock())
    auth_routes.User.query.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(auth_routes, "_email_verification_required", lambda: False)
    monkeypatch.setattr(auth_routes, "_sync_profile", lambda *args: None)
    monkeypatch.setattr(auth_routes, "safe_track_event", lambda *args: events.append(args))
    monkeypatch.setattr(auth_routes, "_commit_new_user_with_id_fallback", lambda user: None)
    with website.app.test_request_context("/register", method="POST", data={"username":"testuser", "email":"test@example.com", "password":"secret123"}):
        assert auth_routes.register().status_code == 302
    assert events == [("sign_up", {"method":"email"})]
    events.clear()
    def fail_commit(user):
        raise RuntimeError("database failure")
    monkeypatch.setattr(auth_routes, "_commit_new_user_with_id_fallback", fail_commit)
    with website.app.test_request_context("/register", method="POST", data={"username":"testuser", "email":"test@example.com", "password":"secret123"}):
        auth_routes.register()
    assert events == []


def test_login_event_only_after_authentication(monkeypatch):
    events = []
    user = SimpleNamespace(password="hash", is_managed_persona=False, is_banned=False, email_verified=True, username="tester", email="test@example.com", mobile="")
    with website.app.app_context():
        monkeypatch.setattr(auth_routes.User, "query", MagicMock())
    auth_routes.User.query.filter.return_value.first.return_value = user
    monkeypatch.setattr(auth_routes, "check_password_hash", lambda *args: True)
    monkeypatch.setattr(auth_routes, "_apply_admin_policy", lambda user: False)
    monkeypatch.setattr(auth_routes, "_email_verification_required", lambda: False)
    monkeypatch.setattr(auth_routes, "login_user", lambda user: events.append(("session", None)))
    monkeypatch.setattr(auth_routes, "safe_track_event", lambda *args: events.append(args))
    with website.app.test_request_context("/login", method="POST", data={"username":"tester", "password":"secret123"}):
        assert auth_routes.login().status_code == 302
    assert events == [("session", None), ("login", {"method":"email"})]


def test_vehicle_and_health_events_follow_success(monkeypatch):
    events = []
    monkeypatch.setattr(garage_routes, "current_user", SimpleNamespace(id=123))
    with website.app.app_context():
        monkeypatch.setattr(garage_routes.Car, "query", MagicMock())
    garage_routes.Car.query.filter_by.return_value.first.return_value = None
    garage_routes.Car.query.filter_by.return_value.all.return_value = []
    with website.app.app_context():
        monkeypatch.setattr(garage_routes.DiagnosticLearning, "query", MagicMock())
    garage_routes.DiagnosticLearning.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
    monkeypatch.setattr(garage_routes, "safe_track_event", lambda *args: events.append(args))
    monkeypatch.setattr(garage_routes.db.session, "add", lambda car: None)
    monkeypatch.setattr(garage_routes.db.session, "commit", lambda: None)
    with website.app.test_request_context("/add-car", method="POST", data={"brand":"Test", "model":"Test"}):
        assert garage_routes.add_car.__wrapped__().status_code == 302
    assert ("vehicle_added", {"feature":"vehicle"}) in events
    with website.app.test_request_context("/garage-dashboard"):
        garage_routes.garage_dashboard.__wrapped__()
    assert ("car_health_viewed", {"feature":"car_health"}) in events


@pytest.mark.parametrize("response_type,expected_completed", [("ranking", True), ("clarification", False), ("error", False)])
def test_diagnosis_completion_boundary(monkeypatch, response_type, expected_completed):
    events = []
    monkeypatch.setattr(tools_routes, "safe_track_event", lambda *args: events.append(args))
    monkeypatch.setattr(tools_routes, "canonical_diagnose", lambda problem: {
        "response_type": response_type, "success": response_type != "error",
        "summary": "Usable summary" if response_type == "ranking" else None,
        "top_matches": [{"problem":"Battery"}] if response_type == "ranking" else [],
    })
    client = website.app.test_client()
    response = client.post("/tools/ai-diagnosis", data=csrf_form_data(client, problem="test problem"))
    assert response.status_code == 200
    assert any(name == "diagnosis_started" for name, _ in events)
    assert any(name == "diagnosis_completed" for name, _ in events) is expected_completed
