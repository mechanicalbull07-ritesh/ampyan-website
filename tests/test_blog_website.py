import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from services.blog_api_client import BlogApiError


def sample_blog():
    return {
        "id": 7,
        "slug": "safe-story",
        "title": "Safe <Story>",
        "subtitle": "Subtitle",
        "excerpt": "Excerpt",
        "category": {"name": "Ownership", "slug": "ownership"},
        "tags": [{"name": "Long tag", "slug": "long-tag"}],
        "author": {"id": 9, "display_name": "Author <name>", "is_following": False},
        "published_at": "2026-07-26T00:00:00Z",
        "updated_at": "2026-07-26T01:00:00Z",
        "reading_time_minutes": 8,
        "view_count": 10,
        "like_count": 2,
        "comment_count": 1,
        "is_liked": False,
        "is_bookmarked": False,
        "cover_image_url": "javascript:alert(1)",
        "content_blocks": [
            {"id": "p1", "type": "paragraph", "order": 0,
             "data": {"text": "<script>alert(1)</script>"}},
            {"id": "i1", "type": "image", "order": 1,
             "data": {"url": "data:text/html,bad", "caption": "bad"}},
            {"id": "t1", "type": "table", "order": 2,
             "data": {"headers": ["A"], "rows": [["B"]]}},
        ],
    }


class BlogWebsiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.app = app
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def setUp(self):
        self.client = self.app.test_client()

    def test_flag_disabled_and_unknown_values_make_no_api_call(self):
        for value in ("", "false", "unexpected"):
            with self.subTest(value=value), patch.dict(
                self.app.config, {"COMMUNITY_BLOG_ENABLED": value}
            ), patch("routes.blog_routes.BlogApiClient") as api:
                response = self.client.get("/blogs")
                self.assertEqual(response.status_code, 404)
                api.assert_not_called()
                self.assertNotIn(b'href="/blogs"', self.client.get("/").data)

    def test_explicit_true_values_enable_route_and_nav(self):
        for value in ("true", "1", "yes", "on"):
            api = Mock()
            api.list_blogs.return_value = ({"items": []}, {})
            api.list_categories.return_value = {"items": []}
            api.list_tags.return_value = {"items": []}
            with self.subTest(value=value), patch.dict(
                self.app.config, {"COMMUNITY_BLOG_ENABLED": value}
            ), patch("routes.blog_routes.client", return_value=api):
                response = self.client.get("/blogs")
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Community Blog", response.data)
                self.assertIn(b'href="/blogs"', self.client.get("/").data)

    def test_listing_preserves_opaque_cursor_and_blocks_unsafe_cover(self):
        api = Mock()
        api.list_blogs.return_value = (
            {"items": [sample_blog()]},
            {"next_cursor": "opaque+/=="},
        )
        api.list_categories.return_value = {"items": []}
        api.list_tags.return_value = {"items": []}
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ), patch("routes.blog_routes.client", return_value=api):
            response = self.client.get("/blogs?query=engine&sort=popular")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="opaque+/=="', response.data)
        self.assertIn(b'value="engine"', response.data)
        self.assertNotIn(b"javascript:alert", response.data)

    def test_detail_escapes_text_blocks_urls_and_records_view_once(self):
        api = Mock()
        api.get_blog.return_value = sample_blog()
        api.list_comments.return_value = ({"items": []}, {})
        api.record_view.return_value = {}
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ), patch("routes.blog_routes.client", return_value=api):
            response = self.client.get("/blogs/safe-story")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", response.data)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)
        self.assertNotIn(b"data:text/html", response.data)
        api.record_view.assert_called_once()

    def test_hidden_blog_is_safe_404(self):
        api = Mock()
        api.get_blog.side_effect = BlogApiError("BLOG_NOT_FOUND", "Not found", 404)
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ), patch("routes.blog_routes.client", return_value=api):
            response = self.client.get("/blogs/private-draft")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page not found", response.data)
        self.assertNotIn(b"BLOG_NOT_FOUND", response.data)
        self.assertNotIn(b"pending_review", response.data)

    def test_post_redirect_does_not_accept_cross_origin_referrer(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        api = Mock()
        with patch.dict(
            self.app.config,
            {"COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True},
        ), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.post(
                "/blogs/7/like",
                headers={"Referer": "https://evil.example/steal"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/blogs")

    def test_comment_tree_keeps_replies_after_parent_soft_delete(self):
        from routes.blog_routes import _comment_tree

        tree = _comment_tree([
            {"id": 1, "parent_comment_id": None, "status": "deleted"},
            {"id": 2, "parent_comment_id": 1, "status": "visible", "body": "reply"},
        ])
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["status"], "deleted")
        self.assertEqual([reply["id"] for reply in tree[0]["replies"]], [2])

    def test_report_details_are_not_silently_truncated_below_api_limit(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        api = Mock()
        details = "र" * 1500
        with patch.dict(
            self.app.config,
            {"COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True},
        ), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.post(
                "/blogs/7/report",
                data={"reason": "spam", "details": details},
            )
        self.assertEqual(response.status_code, 302)
        api.report_blog.assert_called_once_with(
            7, {"reason": "spam", "details": details}, 4
        )


if __name__ == "__main__":
    unittest.main()
