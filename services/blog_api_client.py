import logging
import json as json_module
import os

import requests


logger = logging.getLogger(__name__)


class BlogApiError(RuntimeError):
    def __init__(self, code, message, status=503, meta=None):
        super().__init__(message)
        self.code = code or "BLOG_API_UNAVAILABLE"
        self.message = message or "The Community Blog is temporarily unavailable."
        self.status = status
        self.meta = meta or {}


class BlogApiClient:
    def __init__(self, base_url=None, service_token=None, session=None):
        self.base_url = (
            base_url
            or os.environ.get("AMPYAN_API_BASE_URL")
            or "https://api.ampyan.com"
        ).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else os.environ.get("BLOG_WEBSITE_SERVICE_TOKEN", "")
        )
        self.session = session or requests.Session()

    def _injected_failure(self, method, path):
        control = os.environ.get("BLOG_API_FAILURE_INJECTION_FILE", "").strip()
        if (
            not control
            or os.environ.get("ENV", "").strip().lower() == "production"
            or os.environ.get("RENDER", "").strip().lower() == "true"
        ):
            return None
        try:
            if not os.path.abspath(control).startswith("/tmp/"):
                return None
            with open(control, encoding="utf-8") as handle:
                value = json_module.load(handle)
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(value, dict):
            return None
        expected_method = str(value.get("method") or "").upper()
        expected_path = str(value.get("path") or "")
        if expected_method not in {"*", method.upper()}:
            return None
        if expected_path not in {"*", path}:
            return None
        failure = str(value.get("failure") or "").strip().lower() or None
        if failure:
            try:
                with open(control + ".hits", "a", encoding="utf-8") as handle:
                    handle.write(f"{method.upper()} {path} {failure}\n")
            except OSError:
                pass
        return failure

    @staticmethod
    def _raise_injected(failure):
        if failure in {"connection_refused", "dns_failure"}:
            raise BlogApiError(
                "BLOG_API_UNAVAILABLE",
                "The Community Blog is temporarily unavailable.",
                503,
            )
        if failure in {"connect_timeout", "read_timeout"}:
            raise BlogApiError(
                "BLOG_API_TIMEOUT",
                "The Community Blog took too long to respond. Please try again.",
                503,
            )
        if failure in {
            "empty_body", "invalid_json", "missing_required_fields",
            "incorrect_response_shape",
        }:
            raise BlogApiError(
                "BLOG_API_INVALID_RESPONSE",
                "The Community Blog returned an invalid response.",
                503,
            )
        if failure == "partial_optional_failure":
            raise BlogApiError(
                "BLOG_API_PARTIAL_RESPONSE",
                "Some optional Blog information is temporarily unavailable.",
                503,
            )
        if failure and failure.startswith("http_"):
            try:
                status = int(failure.split("_", 1)[1])
            except (TypeError, ValueError):
                status = 503
            code = "BLOG_EDIT_CONFLICT" if status == 409 else (
                "BLOG_RATE_LIMITED" if status == 429 else "BLOG_API_INJECTED_ERROR"
            )
            message = (
                "A newer version of this Blog is available."
                if status == 409 else
                "Too many Blog requests. Please try again later."
                if status == 429 else
                "The Community Blog operation could not be completed."
            )
            raise BlogApiError(code, message, status)

    def _headers(self, user_id=None, extra=None):
        headers = {"Accept": "application/json"}
        if user_id is not None:
            if not self.service_token:
                raise BlogApiError(
                    "BLOG_SERVICE_AUTH_UNAVAILABLE",
                    "Authenticated Blog actions are temporarily unavailable.",
                    503,
                )
            headers.update({
                "X-AMPYAN-BLOG-SERVICE-TOKEN": self.service_token,
                "X-AMPYAN-BLOG-USER-ID": str(int(user_id)),
            })
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method,
        path,
        *,
        user_id=None,
        params=None,
        json=None,
        files=None,
        headers=None,
        media=False,
    ):
        failure = self._injected_failure(method, path.lstrip("/"))
        if failure:
            self._raise_injected(failure)
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        timeout = (5, 30 if media else 15)
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json,
                files=files,
                headers=self._headers(user_id, headers),
                timeout=timeout,
            )
        except requests.Timeout as exc:
            raise BlogApiError(
                "BLOG_API_TIMEOUT",
                "The Community Blog took too long to respond. Please try again.",
                503,
            ) from exc
        except requests.RequestException as exc:
            logger.warning("Community Blog API request failed: %s", exc.__class__.__name__)
            raise BlogApiError(
                "BLOG_API_UNAVAILABLE",
                "The Community Blog is temporarily unavailable.",
                503,
            ) from exc

        try:
            envelope = response.json()
        except ValueError as exc:
            raise BlogApiError(
                "BLOG_API_INVALID_RESPONSE",
                "The Community Blog returned an invalid response.",
                503,
            ) from exc
        if not isinstance(envelope, dict):
            raise BlogApiError(
                "BLOG_API_INVALID_RESPONSE",
                "The Community Blog returned an invalid response.",
                503,
            )
        if not response.ok or envelope.get("success") is not True:
            error = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
            raise BlogApiError(
                error.get("code"),
                error.get("message"),
                response.status_code,
                envelope.get("meta"),
            )
        return envelope.get("data"), envelope.get("meta") or {}

    def list_blogs(self, params=None, user_id=None):
        return self.request("GET", "blogs", params=params, user_id=user_id)

    def get_blog(self, slug, user_id=None):
        return self.request("GET", f"blogs/{slug}", user_id=user_id)[0]

    def list_related_blogs(self, blog_id, user_id=None):
        return self.request(
            "GET", f"blogs/{int(blog_id)}/related", user_id=user_id
        )[0]

    def create_draft(self, payload, user_id, key):
        return self.request(
            "POST", "blogs", user_id=user_id, json=payload,
            headers={"Idempotency-Key": key},
        )[0]

    def update_draft(self, blog_id, payload, user_id, version):
        return self.request(
            "PATCH", f"blogs/{int(blog_id)}", user_id=user_id, json=payload,
            headers={"If-Match": str(int(version))},
        )[0]

    def delete_draft(self, blog_id, user_id):
        return self.request("DELETE", f"blogs/{int(blog_id)}", user_id=user_id)[0]

    def submit_blog(self, blog_id, user_id):
        return self.request("POST", f"blogs/{int(blog_id)}/submit", user_id=user_id)[0]

    def withdraw_blog(self, blog_id, user_id):
        return self.request("POST", f"blogs/{int(blog_id)}/withdraw", user_id=user_id)[0]

    def list_my_blogs(self, user_id):
        return self.request("GET", "blogs/me", user_id=user_id)[0]

    def get_my_analytics(self, user_id):
        return self.request("GET", "blogs/me/analytics", user_id=user_id)[0]

    def list_categories(self):
        return self.request("GET", "blogs/categories")[0]

    def list_tags(self):
        return self.request("GET", "blogs/tags")[0]

    def set_engagement(self, blog_id, kind, enabled, user_id):
        method = "POST" if enabled else "DELETE"
        return self.request(method, f"blogs/{int(blog_id)}/{kind}", user_id=user_id)[0]

    def set_follow(self, author_id, enabled, user_id):
        method = "POST" if enabled else "DELETE"
        return self.request(
            method, f"blogs/authors/{int(author_id)}/follow", user_id=user_id
        )[0]

    def list_comments(self, blog_id, params=None):
        return self.request("GET", f"blogs/{int(blog_id)}/comments", params=params)

    def create_comment(self, blog_id, payload, user_id):
        return self.request(
            "POST", f"blogs/{int(blog_id)}/comments", user_id=user_id, json=payload
        )[0]

    def edit_comment(self, comment_id, body, user_id):
        return self.request(
            "PATCH", f"blog-comments/{int(comment_id)}",
            user_id=user_id, json={"body": body},
        )[0]

    def delete_comment(self, comment_id, user_id):
        return self.request(
            "DELETE", f"blog-comments/{int(comment_id)}", user_id=user_id
        )[0]

    def report_blog(self, blog_id, payload, user_id):
        return self.request(
            "POST", f"blogs/{int(blog_id)}/report", user_id=user_id, json=payload
        )[0]

    def record_view(self, blog_id, session_id):
        return self.request(
            "POST", f"blogs/{int(blog_id)}/view", json={"session_id": session_id}
        )[0]

    def upload_media(self, file_storage, user_id):
        return self.request(
            "POST",
            "blogs/media",
            user_id=user_id,
            files={
                "image": (
                    file_storage.filename,
                    file_storage.stream,
                    file_storage.mimetype,
                )
            },
            media=True,
        )[0]

    def list_moderation_queue(self, user_id, status=None):
        return self.request(
            "GET", "blogs/moderation", user_id=user_id,
            params={"status": status} if status else None,
        )[0]

    def moderate_blog(self, blog_id, payload, user_id, version):
        return self.request(
            "POST", f"blogs/{int(blog_id)}/moderate", user_id=user_id, json=payload,
            headers={"If-Match": str(int(version))},
        )[0]
