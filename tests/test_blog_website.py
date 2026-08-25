import io
import unittest
from datetime import datetime
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


def rich_media_blog():
    blog = sample_blog()
    blog["cover_image_url"] = "https://cdn.example.test/cover.webp"
    blog["content_blocks"] = [
        {"type": "image", "data": {
            "url": "https://cdn.example.test/inline.webp",
            "caption": "Caption <script>alert(1)</script>",
        }},
        {"type": "youtube", "data": {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }},
        {"type": "instagram", "data": {
            "url": "https://www.instagram.com/reel/ABC_123-/",
        }},
    ]
    return blog


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

    def test_public_nav_has_one_blog_link_for_anonymous_and_authenticated_users(self):
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ):
            anonymous = self.client.get("/")
            self.assertEqual(anonymous.status_code, 200)
            self.assertEqual(anonymous.data.count(b'href="/blogs"'), 1)

            actor = SimpleNamespace(
                is_authenticated=True,
                is_active=True,
                is_anonymous=False,
                id=4,
                username="author",
                role="user",
                email="author@example.com",
                profile_photo=None,
                ai_last_reset=datetime.utcnow(),
                ai_uses_today=0,
                city=None,
                mobile=None,
            )
            with self.client.session_transaction() as session:
                session["_user_id"] = "4"
                session["_fresh"] = True
            with patch.object(
                self.app.login_manager, "_user_callback", return_value=actor
            ):
                authenticated = self.client.get("/")
            self.assertEqual(authenticated.status_code, 200)
            self.assertEqual(authenticated.data.count(b'href="/blogs"'), 1)

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

    def test_detail_renders_cover_image_caption_and_provider_players(self):
        api = Mock()
        api.get_blog.return_value = rich_media_blog()
        api.list_comments.return_value = ({"items": []}, {})
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ), patch("routes.blog_routes.client", return_value=api):
            response = self.client.get("/blogs/safe-story")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'class="blog-cover"', response.data)
        self.assertIn(b"https://cdn.example.test/inline.webp", response.data)
        self.assertIn(b"Caption &lt;script&gt;alert(1)&lt;/script&gt;", response.data)
        self.assertIn(b"https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", response.data)
        self.assertIn(b"https://www.instagram.com/reel/ABC_123-/embed/", response.data)
        self.assertIn(b"View on Instagram", response.data)

    def test_provider_url_validation_supports_expected_formats_only(self):
        from routes.blog_routes import instagram_embed, youtube_embed_url

        for url in (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ?t=2",
            "https://youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
        ):
            with self.subTest(url=url):
                self.assertEqual(
                    youtube_embed_url(url),
                    "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
                )
        for url in (
            "javascript:alert(1)",
            "https://evil.example/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=%3Ciframe%3E",
            "https://www.youtube.com.evil.example/watch?v=dQw4w9WgXcQ",
        ):
            self.assertEqual(youtube_embed_url(url), "")
        self.assertEqual(
            instagram_embed("https://instagram.com/p/POST123/?utm_source=x")["embed_url"],
            "https://www.instagram.com/p/POST123/embed/",
        )
        self.assertEqual(
            instagram_embed("https://www.instagram.com/reel/REEL_123-/")["embed_url"],
            "https://www.instagram.com/reel/REEL_123-/embed/",
        )
        for url in (
            "https://evil.example/p/POST123/",
            "https://instagram.com/stories/POST123/",
            "https://instagram.com/p/<iframe>/",
            "javascript:alert(1)",
        ):
            self.assertIsNone(instagram_embed(url))

    def test_invalid_provider_blocks_do_not_render_iframes_or_raw_html(self):
        blog = sample_blog()
        blog["content_blocks"] = [
            {"type": "youtube", "data": {"url": "<iframe src=https://evil.test>"}},
            {"type": "instagram", "data": {"url": "https://evil.test/p/bad"}},
        ]
        api = Mock()
        api.get_blog.return_value = blog
        api.list_comments.return_value = ({"items": []}, {})
        with patch.dict(
            self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
        ), patch("routes.blog_routes.client", return_value=api):
            response = self.client.get("/blogs/safe-story")
        self.assertNotIn(b"<iframe", response.data)
        self.assertNotIn(b"evil.test", response.data)

    def test_media_upload_rejects_oversized_image_before_api(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        api = Mock()
        with patch.dict(self.app.config, {
            "COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True,
        }), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.post("/blogs/media", data={
                "image": (io.BytesIO(b"x" * (8 * 1024 * 1024 + 1)), "large.webp"),
            }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 413)
        api.upload_media.assert_not_called()

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

    def test_rejection_reason_is_escaped_and_state_forms_carry_version(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        rejected = sample_blog()
        rejected.update({
            "status": "rejected", "version": 7,
            "rejection": {"reason": "Needs <script>alert(1)</script> evidence"},
        })
        api = Mock()
        api.list_my_blogs.return_value = {"items": [rejected]}
        with patch.dict(self.app.config, {
            "COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True,
        }), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs/me")
        self.assertIn(b"Needs &lt;script&gt;alert(1)&lt;/script&gt; evidence", response.data)
        self.assertIn(b'name="version" value="7"', response.data)
        self.assertNotIn(b'action="/blogs/7/delete"', response.data)

    def test_submit_forwards_browser_rendered_version_not_identity(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        api = Mock()
        with patch.dict(self.app.config, {
            "COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True,
        }), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.post("/blogs/7/submit", data={
                "version": "12", "user_id": "999", "author_id": "999",
            })
        self.assertEqual(response.status_code, 302)
        api.submit_blog.assert_called_once_with(7, 4, "12")

    def test_report_moderation_page_does_not_render_reporter_identity(self):
        actor = SimpleNamespace(is_authenticated=True, id=4)
        api = Mock()
        api.list_reports.return_value = {"items": [{
            "id": 2, "status": "open", "reason": "spam", "details": "Review",
            "created_at": "2026-08-25T00:00:00Z", "reporter_id": 99,
            "blog": {"id": 7, "title": "Reported Blog"},
        }]}
        with patch.dict(self.app.config, {
            "COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True,
        }), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs/moderation/reports")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reported Blog", response.data)
        self.assertNotIn(b"99", response.data)
        self.assertNotIn(b"reporter", response.data.lower())


if __name__ == "__main__":
    unittest.main()
