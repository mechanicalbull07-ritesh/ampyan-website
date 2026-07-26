import unittest
from datetime import datetime
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests.csrf_helpers import csrf_form_data, csrf_json_headers, csrf_token


class WebsiteCsrfSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app

        cls.app = app
        cls.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=True,
        )

    def setUp(self):
        self.client = self.app.test_client()

    def test_global_csrf_is_active_and_get_does_not_require_token(self):
        self.assertTrue(self.app.config["WTF_CSRF_ENABLED"])
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="csrf-token"', response.data)

    def test_missing_and_invalid_html_tokens_are_rejected_safely(self):
        for data in ({}, {"csrf_token": "invalid"}):
            with self.subTest(data=data):
                response = self.client.post("/login", data=data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(b"session form token is missing or expired", response.data)
                self.assertNotIn(b"CSRF token is missing", response.data)

    def test_json_missing_and_invalid_tokens_use_stable_error(self):
        for headers in (
            {"Content-Type": "application/json"},
            {"Content-Type": "application/json", "X-CSRFToken": "invalid"},
        ):
            with self.subTest(headers=headers):
                response = self.client.post(
                    "/api/track-event",
                    headers=headers,
                    json={"event_type": "click"},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.get_json(),
                    {
                        "success": False,
                        "error": {
                            "code": "CSRF_VALIDATION_FAILED",
                            "message": (
                                "Your session form token is missing or expired. "
                                "Refresh the page and try again."
                            ),
                        },
                    },
                )

    def test_valid_form_token_reaches_login_and_registration_validation(self):
        login = self.client.post(
            "/login",
            data=csrf_form_data(
                self.client,
                "/login",
                username="",
                password="",
            ),
        )
        self.assertEqual(login.status_code, 302)

        registration = self.client.post(
            "/register",
            data=csrf_form_data(
                self.client,
                "/register",
                username="",
                email="",
                password="",
            ),
        )
        self.assertEqual(registration.status_code, 302)

    def test_valid_header_allows_same_origin_json_mutation(self):
        response = self.client.post(
            "/api/track-event",
            headers=csrf_json_headers(self.client),
            json={"event_type": "click", "label": "csrf validation"},
        )
        self.assertNotEqual(response.status_code, 400)

    def test_token_cannot_be_reused_by_another_session(self):
        token = csrf_token(self.client)
        other_client = self.app.test_client()
        response = other_client.post(
            "/api/track-event",
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": token,
            },
            json={"event_type": "click"},
        )
        self.assertEqual(response.status_code, 400)

    def test_password_profile_news_community_and_upload_require_csrf(self):
        protected_requests = (
            ("/forgot-password", {}),
            ("/update-profile", {}),
            ("/admin/news/create", {}),
            ("/admin/news/edit/1", {}),
            ("/admin/news/delete/1", {}),
            ("/create-post", {}),
            ("/admin/ban-user/1", {}),
            ("/admin/news/image-upload", {}),
        )
        for path, data in protected_requests:
            with self.subTest(path=path):
                response = self.client.post(path, data=data)
                self.assertEqual(response.status_code, 400)

    def test_valid_upload_token_reaches_normal_route_validation(self):
        form_data = csrf_form_data(self.client)
        actor = SimpleNamespace(
            is_authenticated=True,
            role="admin",
            id=1,
            email="mechanicalbull07@gmail.com",
            ai_last_reset=datetime.utcnow(),
            ai_uses_today=0,
        )
        with (
            patch.dict(self.app.config, {"LOGIN_DISABLED": True}),
            patch("app.current_user", actor),
        ):
            response = self.client.post(
                "/admin/news/image-upload",
                data=form_data,
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"storage is not configured", response.data)

    def test_logout_is_post_only_and_csrf_protected(self):
        self.assertEqual(self.client.get("/logout").status_code, 405)
        self.assertEqual(self.client.post("/logout").status_code, 400)
        response = self.client.post(
            "/logout",
            data=csrf_form_data(self.client),
        )
        self.assertEqual(response.status_code, 302)

    def test_templates_include_tokens_and_feature_disabled_state_is_unchanged(self):
        for path in (
            "/login",
            "/register",
            "/forgot-password",
            "/tools/fuel-cost",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'name="csrf_token"', response.data)
        self.assertNotIn(b"/blogs", self.client.get("/").data)

    def test_all_templates_compile(self):
        names = self.app.jinja_env.list_templates()
        for name in names:
            with self.subTest(template=name):
                self.app.jinja_env.get_template(name)
        self.assertIn("mechanic_dashboard.html", names)

    def test_static_post_forms_have_tokens_and_no_csrf_bypass_exists(self):
        root = Path(__file__).resolve().parents[1]
        bypass_patterns = (
            r"@csrf\.exempt",
            r"csrf\.exempt",
            r"WTF_CSRF_ENABLED\s*=\s*False",
            r"WTF_CSRF_CHECK_DEFAULT\s*=\s*False",
        )
        python_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [root / "app.py", *sorted((root / "routes").glob("*.py"))]
        )
        for pattern in bypass_patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, python_source))

        for path in sorted((root / "templates").glob("*.html")):
            source = path.read_text(encoding="utf-8")
            for match in re.finditer(
                r"<form\b[^>]*method=[\"']POST[\"'][^>]*>",
                source,
                re.IGNORECASE,
            ):
                closing = source.find("</form", match.end())
                form_source = source[match.end():closing]
                with self.subTest(template=path.name, offset=match.start()):
                    self.assertGreaterEqual(closing, 0)
                    self.assertIn('name="csrf_token"', form_source)

    def test_mechanic_dashboard_route_renders_sorted_recent_reviews(self):
        reviews = [
            SimpleNamespace(
                id=index,
                author=SimpleNamespace(username=f"Reviewer {index}"),
                rating=5,
                created_at=datetime(2026, 7, index),
                review_text=f"Review {index}",
            )
            for index in range(1, 7)
        ]
        mechanic = SimpleNamespace(
            id=1,
            business_name="CSRF Garage",
            owner_name="Owner",
            city="Delhi",
            phone="0000000000",
            specialties="General automotive",
            address="Safe address",
            pincode="110001",
            service_types="General",
            about="Safe",
            accepts_emergency=False,
            pickup_drop_available=False,
            experience_years=5,
            is_verified=True,
            is_featured=False,
            reviews=reviews,
            trust_score=0,
            trust_level="",
        )
        query = MagicMock()
        query.filter_by.return_value.order_by.return_value.first.return_value = mechanic
        actor = SimpleNamespace(
            is_authenticated=True,
            role="mechanic",
            id=1,
        )
        with self.app.app_context():
            with (
                patch.dict(self.app.config, {"LOGIN_DISABLED": True}),
                patch("routes.main_routes.current_user", actor),
                patch("routes.main_routes.MechanicProfile.query", query),
                patch("routes.main_routes.db.session.rollback"),
            ):
                response = self.client.get("/mechanic-dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CSRF Garage", response.data)
        self.assertIn(b"Reviewer 6", response.data)
        self.assertNotIn(b"Reviewer 1", response.data)
        self.assertIn(b'name="csrf-token"', response.data)
        self.assertNotIn(b'<div class="nav-priority-links" aria-label="Primary pages">\n<a href="/">Home</a>', response.data)
        self.assertNotIn(b"/blogs", response.data)


if __name__ == "__main__":
    unittest.main()
