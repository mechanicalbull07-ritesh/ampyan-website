"""Run with `python tests/local_analytics_e2e.py`; uses an isolated temporary DB."""

import json
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.csrf_helpers import csrf_form_data, csrf_json_headers


def main():
    with tempfile.TemporaryDirectory(prefix="ampyan-analytics-e2e-") as directory:
        os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(directory) / "analytics.db")
        os.environ["SECRET_KEY"] = secrets.token_hex(32)
        os.environ["ANALYTICS_ENABLED"] = "true"
        os.environ["BOT_FILTER_ENABLED"] = "true"

        import app as website
        from models.models import AnalyticsDedupeClaim, AnalyticsEvent, db
        from services import analytics_service as analytics

        with website.app.app_context():
            db.create_all()
        preflight = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "prepare_analytics_schema.py")],
            env=os.environ.copy(), capture_output=True, text=True, timeout=20,
        )
        assert preflight.returncode == 0, preflight.stderr[-500:]
        client = website.app.test_client()
        client.set_cookie("ampyan_analytics_consent", "granted")
        client.get("/about")
        csrf_headers = csrf_json_headers(client, "/about")
        session_cookie = next(c.value for c in client._cookies.values() if c.key == "ampyan_analytics_session")
        session_id = session_cookie.split(".")[0]
        events = {
            "sign_up": {"method": "email"},
            "login": {"method": "email"},
            "vehicle_added": {"feature": "vehicle"},
            "diagnosis_started": {"feature": "diagnosis"},
            "diagnosis_completed": {"feature": "diagnosis"},
            "car_health_viewed": {"feature": "car_health"},
        }
        results = []
        for name, parameters in events.items():
            body = {
                "event_type": name, "session_id": session_id,
                "path": "/tools/ai-diagnosis?email=private@example.com",
                "referrer": "https://search.example/?phone=private",
                "utm_source": "instagram", "utm_medium": "social",
                "utm_campaign": "speed16", **parameters,
            }
            if name != "car_health_viewed":
                body["event_id"] = secrets.token_hex(16)
            first = client.post("/api/track-event", json=body, headers=csrf_headers)
            if name != "car_health_viewed":
                duplicate = client.post("/api/track-event", json=body, headers=csrf_headers)
                assert duplicate.status_code == 202, (name, duplicate.status_code)
            analytics._queue.join()
            with website.app.app_context():
                db.session.remove()
                rows = AnalyticsEvent.query.filter_by(event_type=name).all()
                assert first.status_code == 202, (name, first.status_code, first.json)
                assert len(rows) == 1, (name, len(rows))
                row = rows[0]
                assert row.session_id == session_id
                assert row.path == "/tools/ai-diagnosis"
                assert row.referrer == "https://search.example/"
                assert row.source == "instagram"
                assert row.utm_medium == "social" and row.utm_campaign == "speed16"
                assert row.ip_address == "" and row.user_id is None and row.city == ""
                assert json.loads(row.metadata_json) == {**parameters, "schema_version": 1}
                assert "private" not in str(row.__dict__)
            results.append((name, first.status_code, len(rows), session_id[:8]))

        negatives = [
            ("unknown", {"event_type": "unknown"}, 422),
            ("unsafe", {"event_type": "login", "method": "email", "target_url": "/private"}, 422),
            ("pii", {"event_type": "sign_up", "method": "email", "email": "private@example.com"}, 422),
            ("malformed", ["invalid"], 400),
            ("oversized", {"event_type": "login", "method": "email", "padding": "x" * 33_000}, 413),
        ]
        with website.app.app_context():
            before = AnalyticsEvent.query.count()
        for label, body, expected in negatives:
            response = client.post("/api/track-event", json=body, headers=csrf_headers)
            assert response.status_code == expected, (label, response.status_code)
        huge = client.post("/api/track-event", data="x" * (11 * 1024 * 1024), headers=csrf_headers)
        assert huge.status_code == 413
        client.set_cookie("ampyan_analytics_consent", "denied")
        denied = client.post("/api/track-event", json={"event_type": "login", "method": "email"}, headers=csrf_headers)
        assert denied.status_code == 403
        client.set_cookie("ampyan_analytics_consent", "granted")
        original_enqueue = analytics._enqueue
        analytics._enqueue = lambda item: False
        try:
            failed = client.post("/api/track-event", json={"event_type": "login", "method": "email"}, headers=csrf_headers)
        finally:
            analytics._enqueue = original_enqueue
        assert failed.status_code == 503
        analytics._queue.join()
        with website.app.app_context():
            db.session.remove()
            assert AnalyticsEvent.query.count() == before
        for name, status, count, prefix in results:
            print(f"{name}: HTTP {status}, stored {count}, session {prefix}..., safe fields PASS, duplicate PASS")
        print("negative cases: unknown/unsafe/PII/malformed/denied/failure PASS")

        # Two independent interpreters simulate separate Gunicorn workers.
        key = secrets.token_hex(32)
        command = [sys.executable, str(Path(__file__).with_name("dedupe_process_worker.py")), os.environ["DATABASE_URL"], key]
        workers = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        for worker in workers:
            _, errors = worker.communicate(timeout=20)
            assert worker.returncode == 0, errors.decode()[-500:]
        with website.app.app_context():
            db.session.remove()
            assert AnalyticsEvent.query.filter_by(event_type="share_clicked").count() == 1
        print("two independent workers, one deduplicated row: PASS")
        # A different action ID remains countable, even inside five seconds.
        distinct = command[:-1] + [secrets.token_hex(32)]
        subprocess.run(distinct, check=True, capture_output=True, timeout=20)
        with website.app.app_context():
            db.session.remove()
            assert AnalyticsEvent.query.filter_by(event_type="share_clicked").count() == 2
            from datetime import datetime, timedelta
            claim = db.session.get(AnalyticsDedupeClaim, key)
            claim.expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.session.commit()
        subprocess.run(command, check=True, capture_output=True, timeout=20)
        with website.app.app_context():
            db.session.remove()
            assert AnalyticsEvent.query.filter_by(event_type="share_clicked").count() == 3
        print("distinct action and expired claim accepted: PASS")

        # Consent and session lifecycle use only first-party test clients.
        def session_value(test_client):
            return next((c.value for c in test_client._cookies.values() if c.key == "ampyan_analytics_session"), None)

        unknown_client = website.app.test_client()
        with website.app.app_context():
            before_visits = db.session.execute(text("SELECT count(*) FROM website_visit")).scalar_one()
        unknown_client.get("/about")
        analytics._queue.join()
        assert session_value(unknown_client) is None
        with website.app.app_context():
            assert db.session.execute(text("SELECT count(*) FROM website_visit")).scalar_one() == before_visits
        unknown_client.set_cookie("ampyan_analytics_consent", "granted")
        unknown_client.get("/about")
        first = session_value(unknown_client)
        assert first
        unknown_client.get("/about")  # refresh
        unknown_client.get("/tools")  # navigation
        assert session_value(unknown_client).split(".")[0] == first.split(".")[0]
        # A new tab shares the browser cookie jar.
        new_tab = website.app.test_client()
        new_tab.set_cookie("ampyan_analytics_consent", "granted")
        new_tab.set_cookie("ampyan_analytics_session", session_value(unknown_client))
        new_tab.get("/about")
        assert session_value(new_tab).split(".")[0] == first.split(".")[0]
        from datetime import datetime, timedelta
        recent = first.split(".")
        unknown_client.set_cookie("ampyan_analytics_session", f"{recent[0]}.{recent[1]}.{int(recent[2]) - 29 * 60}")
        unknown_client.get("/about")
        assert session_value(unknown_client).split(".")[0] == recent[0]
        unknown_client.set_cookie("ampyan_analytics_session", f"{recent[0]}.{recent[1]}.{int(recent[2]) - 31 * 60}")
        unknown_client.get("/about")
        assert session_value(unknown_client).split(".")[0] != recent[0]
        # New browser process drops the session cookie but retains consent.
        restarted = website.app.test_client()
        restarted.set_cookie("ampyan_analytics_consent", "granted")
        restarted.get("/about")
        assert session_value(restarted).split(".")[0] != session_value(unknown_client).split(".")[0]
        unknown_client.set_cookie("ampyan_analytics_consent", "denied")
        unknown_client.get("/about")
        assert session_value(unknown_client) is None
        unknown_client.set_cookie("ampyan_analytics_consent", "granted")
        unknown_client.get("/about")
        assert session_value(unknown_client)
        analytics._queue.join()
        with website.app.app_context():
            db.session.remove()
            after_visits = db.session.execute(text("SELECT count(*) FROM website_visit")).scalar_one()
            assert after_visits > before_visits
        print("session: first/navigation/refresh/<30/>30/new tab/restart PASS; visitor ID separate PASS")
        print("consent: unknown/grant/deny/granted-to-denied/denied-to-granted/return PASS")

        # Exercise real website actions against the same isolated database.
        import routes.auth_routes as auth_routes
        import routes.tools_routes as tools_routes
        auth_routes._sync_profile = lambda *args: None
        tools_routes.canonical_diagnose = lambda problem: {
            "response_type": "ranking", "success": True,
            "summary": "Battery check", "top_matches": [{"problem": "Battery", "confidence": 70}],
            "recommended_actions": ["Inspect battery"],
        }
        browser = website.app.test_client()
        browser.set_cookie("ampyan_analytics_consent", "granted")
        browser.get("/register")
        signup = browser.post("/register", data=csrf_form_data(browser, "/register", **{
            "username": "localtester", "email": "local@example.test", "password": "localpass123",
            "analytics_request_token": secrets.token_hex(16),
        }))
        assert signup.status_code == 302
        login = browser.post("/login", data=csrf_form_data(browser, "/login", **{
            "username": "localtester", "password": "localpass123",
            "analytics_request_token": secrets.token_hex(16),
        }))
        assert login.status_code == 302
        vehicle = browser.post("/add-car", data=csrf_form_data(browser, "/add-car", **{
            "brand": "Tata", "model": "Altroz", "year": "2022", "fuel": "petrol",
            "analytics_request_token": secrets.token_hex(16),
        }))
        assert vehicle.status_code == 302
        diagnosis = browser.post("/tools/ai-diagnosis", data=csrf_form_data(browser, "/tools/ai-diagnosis", **{
            "problem": "battery issue", "analytics_request_token": secrets.token_hex(16),
        }))
        assert diagnosis.status_code == 200
        health = browser.get("/garage-dashboard")
        assert health.status_code == 200
        analytics._queue.join()
        with website.app.app_context():
            db.session.remove()
            browser_session_id = session_value(browser).split(".")[0]
            for name in events:
                rows = AnalyticsEvent.query.filter_by(event_type=name).all()
                assert len(rows) == 2, name
                route_row = next(row for row in rows if row.session_id == browser_session_id)
                assert json.loads(route_row.metadata_json) == {**events[name], "schema_version": 1}
                assert route_row.ip_address == "" and route_row.user_id is None
                assert "local@example.test" not in str(route_row.__dict__)
        denied_browser = website.app.test_client()
        denied_browser.set_cookie("ampyan_analytics_consent", "denied")
        for name, parameters in events.items():
            rejected = denied_browser.post("/api/track-event", json={"event_type": name, **parameters}, headers=csrf_json_headers(denied_browser, "/about"))
            assert rejected.status_code == 403, name
        denied_browser.post("/tools/ai-diagnosis", data=csrf_form_data(denied_browser, "/tools/ai-diagnosis", problem="battery issue"))
        analytics._queue.join()
        with website.app.app_context():
            db.session.remove()
            for name in events:
                assert AnalyticsEvent.query.filter_by(event_type=name).count() == 2, name
        print("real website signup/login/vehicle/diagnosis/health actions -> database: PASS")
        print("all six events denied by consent; denied diagnosis creates no rows: PASS")


if __name__ == "__main__":
    main()
