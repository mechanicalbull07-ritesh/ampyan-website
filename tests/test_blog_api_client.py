import io
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from services.blog_api_client import BlogApiClient, BlogApiError


class JsonResponse:
    def __init__(self, payload, status=200, invalid=False):
        self.payload = payload
        self.status_code = status
        self.ok = 200 <= status < 400
        self.invalid = invalid

    def json(self):
        if self.invalid:
            raise ValueError("not json")
        return self.payload


class BlogApiClientTest(unittest.TestCase):
    def setUp(self):
        self.http = Mock()
        self.client = BlogApiClient(
            "https://api.example.test/",
            "server-secret",
            session=self.http,
        )

    def success(self, data=None, meta=None):
        self.http.request.return_value = JsonResponse(
            {"success": True, "data": data or {}, "meta": meta or {}}
        )

    def test_anonymous_get_has_no_service_identity_headers(self):
        self.success({"items": []}, {"next_cursor": "opaque+/=="})
        data, meta = self.client.list_blogs({"cursor": "opaque+/=="})
        self.assertEqual(data, {"items": []})
        self.assertEqual(meta["next_cursor"], "opaque+/==")
        call = self.http.request.call_args.kwargs
        self.assertEqual(call["headers"], {"Accept": "application/json"})
        self.assertEqual(call["params"]["cursor"], "opaque+/==")
        self.assertEqual(call["timeout"], (5, 15))

    def test_authenticated_request_uses_only_server_identity(self):
        self.success({"id": 4})
        self.client.create_draft({"title": "Safe"}, 27, "same-key")
        call = self.http.request.call_args
        self.assertEqual(call.args[:2], ("POST", "https://api.example.test/api/v1/blogs"))
        self.assertEqual(call.kwargs["headers"]["X-AMPYAN-BLOG-USER-ID"], "27")
        self.assertEqual(
            call.kwargs["headers"]["X-AMPYAN-BLOG-SERVICE-TOKEN"], "server-secret"
        )
        self.assertEqual(call.kwargs["headers"]["Idempotency-Key"], "same-key")
        self.assertEqual(self.http.request.call_count, 1)

    def test_missing_service_token_fails_before_network(self):
        with self.assertRaises(BlogApiError) as raised:
            BlogApiClient(
                "https://api.example.test", "", session=self.http
            ).list_my_blogs(1)
        self.assertEqual(raised.exception.code, "BLOG_SERVICE_AUTH_UNAVAILABLE")
        self.http.request.assert_not_called()

    def test_api_error_status_and_code_are_preserved(self):
        for status in (401, 403, 404, 409, 429, 503):
            with self.subTest(status=status):
                self.http.reset_mock()
                self.http.request.return_value = JsonResponse(
                    {
                        "success": False,
                        "error": {"code": f"E{status}", "message": "Safe failure"},
                        "meta": {"retry_after": 2},
                    },
                    status,
                )
                with self.assertRaises(BlogApiError) as raised:
                    self.client.get_blog("hidden")
                self.assertEqual(raised.exception.status, status)
                self.assertEqual(raised.exception.code, f"E{status}")
                self.assertEqual(raised.exception.message, "Safe failure")

    def test_timeout_connection_and_invalid_json_are_stable(self):
        failures = (
            (requests.Timeout(), "BLOG_API_TIMEOUT"),
            (requests.ConnectionError(), "BLOG_API_UNAVAILABLE"),
        )
        for failure, code in failures:
            with self.subTest(code=code):
                self.http.request.side_effect = failure
                with self.assertRaises(BlogApiError) as raised:
                    self.client.list_blogs()
                self.assertEqual(raised.exception.code, code)
        self.http.request.side_effect = None
        self.http.request.return_value = JsonResponse(None, invalid=True)
        with self.assertRaises(BlogApiError) as raised:
            self.client.list_blogs()
        self.assertEqual(raised.exception.code, "BLOG_API_INVALID_RESPONSE")

    def test_media_is_forwarded_with_media_timeout(self):
        self.success({"url": "https://cdn.example.test/image.webp"})
        upload = SimpleNamespace(
            filename="image.webp",
            stream=io.BytesIO(b"image"),
            mimetype="image/webp",
        )
        self.client.upload_media(upload, 8)
        call = self.http.request.call_args.kwargs
        self.assertEqual(call["timeout"], (5, 30))
        self.assertEqual(call["files"]["image"][0], "image.webp")
        self.assertEqual(call["files"]["image"][2], "image/webp")

    def test_state_mutations_forward_required_versions(self):
        self.success({"id": 4})
        operations = (
            (self.client.delete_draft, (4, 8, 11), "DELETE", "blogs/4"),
            (self.client.submit_blog, (4, 8, 12), "POST", "blogs/4/submit"),
            (self.client.withdraw_blog, (4, 8, 13), "POST", "blogs/4/withdraw"),
        )
        for method, args, expected_method, path in operations:
            with self.subTest(path=path):
                self.http.reset_mock()
                self.success({"id": 4})
                method(*args)
                call = self.http.request.call_args
                self.assertEqual(call.args[:2], (expected_method, f"https://api.example.test/api/v1/{path}"))
                self.assertEqual(call.kwargs["headers"]["If-Match"], str(args[2]))

    def test_report_management_remains_server_authenticated(self):
        self.success({"items": []})
        self.client.list_reports(9, "open")
        call = self.http.request.call_args.kwargs
        self.assertEqual(call["params"], {"status": "open"})
        self.assertEqual(call["headers"]["X-AMPYAN-BLOG-USER-ID"], "9")
        self.success({"id": 3, "status": "resolved"})
        self.client.resolve_report(3, {"action": "resolve", "reason": "safe"}, 9)
        call = self.http.request.call_args.kwargs
        self.assertEqual(call["json"]["action"], "resolve")
        self.assertNotIn("reporter_id", call["json"])

    def test_failure_injection_is_local_only_and_production_fails_closed(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", dir="/tmp", delete=False
        ) as control:
            json.dump({
                "method": "GET",
                "path": "blogs",
                "failure": "http_503",
            }, control)
            path = control.name
        try:
            with patch.dict(os.environ, {
                "BLOG_API_FAILURE_INJECTION_FILE": path,
                "ENV": "development",
                "RENDER": "",
            }, clear=False):
                with self.assertRaises(BlogApiError) as raised:
                    self.client.list_blogs()
                self.assertEqual(raised.exception.status, 503)
                self.http.request.assert_not_called()

            self.success({"items": []})
            for guard in ({"ENV": "production", "RENDER": ""},
                          {"ENV": "development", "RENDER": "true"}):
                with self.subTest(guard=guard), patch.dict(os.environ, {
                    "BLOG_API_FAILURE_INJECTION_FILE": path,
                    **guard,
                }, clear=False):
                    data, _ = self.client.list_blogs()
                    self.assertEqual(data, {"items": []})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
