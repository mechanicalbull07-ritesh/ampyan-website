import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from services.blog_api_client import BlogApiError
from tests.test_blog_website import sample_blog


class BlogSeoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.app = app
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def setUp(self):
        self.client = self.app.test_client()

    def blog_api(self, blog=None):
        api = Mock()
        api.list_blogs.return_value = ({"items": []}, {})
        api.list_categories.return_value = {"items": []}
        api.list_tags.return_value = {"items": []}
        if blog is not None:
            api.get_blog.return_value = blog
            api.list_comments.return_value = ({"items": []}, {})
            api.list_related_blogs.return_value = {"items": []}
        return api

    def test_homepage_metadata_canonical_and_indexing(self):
        api = self.blog_api()
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'<meta name="description" content="Read automotive ownership stories, practical car advice and community experiences from AMPYAN drivers and enthusiasts.">',
            response.data,
        )
        self.assertIn(b'<link rel="canonical" href="https://ampyan.com/blogs">', response.data)
        self.assertIn(b'<meta name="robots" content="index, follow">', response.data)

    def test_listing_variants_are_noindex_follow_with_clean_canonical(self):
        for query in (
            "?query=brakes", "?category=ownership", "?tag=cng",
            "?author=9", "?sort=latest", "?cursor=opaque",
        ):
            api = self.blog_api()
            with self.subTest(query=query), patch.dict(
                self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
            ), patch("routes.blog_routes.client", return_value=api):
                response = self.client.get("/blogs" + query)
            self.assertIn(b'<meta name="robots" content="noindex, follow">', response.data)
            self.assertIn(b'<link rel="canonical" href="https://ampyan.com/blogs">', response.data)

    def test_article_description_hierarchy_canonical_and_escaping(self):
        cases = (
            ({"excerpt": "<b>Excerpt &amp; safe</b>", "subtitle": "Subtitle"}, "Excerpt &amp; safe"),
            ({"excerpt": "", "subtitle": "<i>Subtitle only</i>"}, "Subtitle only"),
            ({"excerpt": None, "subtitle": None}, "First meaningful &lt;content&gt;"),
        )
        for values, expected in cases:
            blog = sample_blog()
            blog.update(values)
            blog["content_blocks"] = [{
                "id": "p1", "type": "paragraph", "order": 0,
                "data": {"text": "<p>First meaningful &lt;content&gt;</p>"},
            }]
            api = self.blog_api(blog)
            with self.subTest(values=values), patch.dict(
                self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}
            ), patch("routes.blog_routes.client", return_value=api):
                response = self.client.get("/blogs/safe-story")
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                f'<meta name="description" content="{expected}">'.encode(),
                response.data,
            )
            self.assertIn(
                b'<link rel="canonical" href="https://ampyan.com/blogs/safe-story">',
                response.data,
            )
            self.assertIn(b'<meta name="robots" content="index, follow">', response.data)
            self.assertNotIn(b"author/9", response.data)

    def test_article_description_is_word_safe_and_limited(self):
        blog = sample_blog()
        blog["excerpt"] = "word " * 80
        api = self.blog_api(blog)
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs/safe-story")
        html = response.get_data(as_text=True)
        marker = '<meta name="description" content="'
        description = html.split(marker, 1)[1].split('">', 1)[0]
        self.assertLessEqual(len(description), 160)
        self.assertTrue(description.endswith("…"))

    def test_global_metadata_fallback_remains_available(self):
        response = self.client.get("/")
        self.assertIn(
            b'<meta name="description" content="AMPYAN is an AI powered automotive ecosystem',
            response.data,
        )

    def test_trailing_slash_redirect_is_permanent_and_flag_safe(self):
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}):
            response = self.client.get("/blogs/")
        self.assertEqual(response.status_code, 308)
        self.assertEqual(response.headers["Location"], "/blogs")
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "false"}):
            self.assertEqual(self.client.get("/blogs/").status_code, 404)

    def test_sitemap_contains_only_public_blog_entries(self):
        api = self.blog_api()
        api.list_blogs.return_value = ({"items": [
            {"slug": "published-story", "status": "published", "updated_at": "2026-08-25T12:00:00Z", "author": {"id": 999}},
            {"slug": "draft-story", "status": "draft"},
            {"slug": "pending-story", "status": "pending_review"},
            {"slug": "rejected-story", "status": "rejected"},
            {"slug": "archived-story", "status": "archived"},
        ]}, {})
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        root = ElementTree.fromstring(response.data)
        locations = [node.text for node in root.findall("{*}url/{*}loc")]
        self.assertIn("https://ampyan.com/blogs", locations)
        self.assertIn("https://ampyan.com/blogs/published-story", locations)
        for forbidden in (
            "draft-story", "pending-story", "rejected-story", "archived-story",
            "/blogs/write", "/blogs/me", "/blogs/moderation", "999",
        ):
            self.assertNotIn(forbidden, response.get_data(as_text=True))

    def test_sitemap_follows_cursor_and_fails_closed_for_api_errors(self):
        api = self.blog_api()
        api.list_blogs.side_effect = [
            ({"items": [{"slug": "first"}]}, {"next_cursor": "next"}),
            ({"items": [{"slug": "second"}]}, {}),
        ]
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/sitemap.xml")
        self.assertIn(b"https://ampyan.com/blogs/first", response.data)
        self.assertIn(b"https://ampyan.com/blogs/second", response.data)

        broken = self.blog_api()
        broken.list_blogs.side_effect = BlogApiError("BLOG_API_UNAVAILABLE", "offline", 503)
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=broken
        ):
            response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"https://ampyan.com/blogs", response.data)
        self.assertNotIn(b"offline", response.data)

    def test_disabled_feature_excludes_all_blog_sitemap_urls(self):
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "false"}), patch(
            "routes.blog_routes.client"
        ) as client_factory:
            response = self.client.get("/sitemap.xml")
        self.assertNotIn(b"https://ampyan.com/blogs", response.data)
        client_factory.assert_not_called()

    def test_private_slug_is_404_and_management_page_is_noindex_nofollow(self):
        api = self.blog_api()
        api.get_blog.side_effect = BlogApiError(
            "BLOG_NOT_FOUND", "SECRET PRIVATE CONTENT", 404
        )
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs/private-story")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"SECRET PRIVATE CONTENT", response.data)
        self.assertNotIn(b"BLOG_NOT_FOUND", response.data)
        self.assertIn(b'<meta name="robots" content="noindex, nofollow">', response.data)

        actor = SimpleNamespace(is_authenticated=True, id=4)
        api.list_my_blogs.return_value = {"items": []}
        with patch.dict(self.app.config, {
            "COMMUNITY_BLOG_ENABLED": "true", "LOGIN_DISABLED": True,
        }), patch("routes.blog_routes.current_user", actor), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs/me")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<meta name="robots" content="noindex, nofollow">', response.data)


if __name__ == "__main__":
    unittest.main()
