import json
import re
import unittest
from html import unescape
from unittest.mock import Mock, patch

from services.blog_api_client import BlogApiError
from tests.test_blog_website import sample_blog


class BlogSeoP1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.app = app
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def setUp(self):
        self.client = self.app.test_client()

    def api_for(self, blog):
        api = Mock()
        api.get_blog.return_value = blog
        api.list_comments.return_value = ({"items": []}, {})
        api.list_related_blogs.return_value = {"items": []}
        return api

    def render_detail(self, blog):
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=self.api_for(blog)
        ):
            return self.client.get("/blogs/safe-story")

    def schema(self, html, name):
        match = re.search(
            rf'<script type="application/ld\+json" data-seo-schema="{name}">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        return json.loads(match.group(1))

    def test_blog_posting_contains_only_safe_public_fields(self):
        blog = sample_blog()
        blog["author"].update({
            "email": "private@example.test", "role": "admin", "moderation_note": "secret"
        })
        blog["cover_image_url"] = "https://cdn.example.test/cover.webp"
        response = self.render_detail(blog)
        posting = self.schema(response.get_data(as_text=True), "blog-posting")
        self.assertEqual(posting["@type"], "BlogPosting")
        self.assertEqual(posting["headline"], "Safe <Story>")
        self.assertEqual(posting["author"], {"@type": "Person", "name": "Author <name>"})
        self.assertEqual(posting["publisher"]["name"], "AMPYAN")
        self.assertEqual(posting["datePublished"], "2026-07-26T00:00:00Z")
        self.assertEqual(posting["dateModified"], "2026-07-26T01:00:00Z")
        self.assertEqual(posting["image"], "https://cdn.example.test/cover.webp")
        self.assertEqual(
            posting["mainEntityOfPage"]["@id"],
            "https://ampyan.com/blogs/safe-story",
        )
        serialized = json.dumps(posting)
        for private_value in ("private@example.test", "admin", "secret", '"id": 9'):
            self.assertNotIn(private_value, serialized)

    def test_structured_data_is_absent_from_private_and_management_pages(self):
        api = Mock()
        api.get_blog.side_effect = BlogApiError("BLOG_NOT_FOUND", "hidden", 404)
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            private = self.client.get("/blogs/private-story")
        self.assertNotIn(b'data-seo-schema="blog-posting"', private.data)
        self.assertNotIn(b'data-seo-schema="breadcrumbs"', private.data)

    def test_breadcrumb_jsonld_and_visible_navigation_are_canonical(self):
        response = self.render_detail(sample_blog())
        html = response.get_data(as_text=True)
        breadcrumb = self.schema(html, "breadcrumbs")
        self.assertEqual(breadcrumb["@type"], "BreadcrumbList")
        items = breadcrumb["itemListElement"]
        self.assertEqual([item["position"] for item in items], [1, 2, 3])
        self.assertEqual(items[0]["item"], "https://ampyan.com/")
        self.assertEqual(items[1]["item"], "https://ampyan.com/blogs")
        self.assertEqual(items[2]["item"], "https://ampyan.com/blogs/safe-story")
        self.assertIn('<nav class="blog-breadcrumbs" aria-label="Breadcrumb">', html)
        self.assertIn('<a href="/">Home</a>', html)
        self.assertIn('<a href="/blogs">Blogs</a>', html)
        self.assertIn('aria-current="page">Safe &lt;Story&gt;</li>', html)

    def test_jsonld_serialization_blocks_script_breakout(self):
        blog = sample_blog()
        attack = '</script><script id="owned">alert(1)</script> " \u2028'
        blog["title"] = attack
        blog["author"]["display_name"] = attack
        response = self.render_detail(blog)
        html = response.get_data(as_text=True)
        self.assertNotIn('<script id="owned">', html)
        posting = self.schema(html, "blog-posting")
        self.assertEqual(posting["headline"], attack)
        self.assertEqual(posting["author"]["name"], attack)

    def test_heading_levels_render_semantically_with_one_h1(self):
        blog = sample_blog()
        blog["content_blocks"] = [
            {"type": "heading", "data": {"text": "Level <two>", "level": 2}},
            {"type": "heading", "data": {"text": "Level three", "level": 3}},
            {"type": "heading", "data": {"text": "Level four", "level": 4}},
            {"type": "heading", "data": {"text": "Not H1", "level": 1}},
        ]
        html = self.render_detail(blog).get_data(as_text=True)
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", html)), 1)
        self.assertIn("<h2>Level &lt;two&gt;</h2>", html)
        self.assertIn("<h3>Level three</h3>", html)
        self.assertIn("<h4>Level four</h4>", html)
        self.assertIn("<h2>Not H1</h2>", html)

    def test_seo_title_is_branded_readable_and_bounded(self):
        from routes.blog_routes import seo_article_title

        self.assertEqual(seo_article_title("Safe Story"), "Safe Story | AMPYAN")
        long_title = seo_article_title("A practical family ownership story " * 5)
        self.assertLessEqual(len(long_title), 60)
        self.assertTrue(long_title.endswith("… | AMPYAN"))
        blog = sample_blog()
        blog["title"] = "A practical family ownership story " * 5
        html = self.render_detail(blog).get_data(as_text=True)
        title = unescape(html.split("<title>", 1)[1].split("</title>", 1)[0])
        self.assertEqual(title, long_title)

    def test_open_graph_and_large_twitter_card_use_safe_cover(self):
        blog = sample_blog()
        blog["cover_image_url"] = "https://cdn.example.test/cover.webp"
        html = self.render_detail(blog).get_data(as_text=True)
        self.assertIn('<meta property="og:type" content="article">', html)
        self.assertIn('<meta property="og:url" content="https://ampyan.com/blogs/safe-story">', html)
        self.assertIn('<meta property="og:image" content="https://cdn.example.test/cover.webp">', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertNotIn("og:image:width", html)
        self.assertNotIn("og:image:height", html)

    def test_twitter_fallback_without_cover_uses_summary(self):
        blog = sample_blog()
        blog["cover_image_url"] = None
        html = self.render_detail(blog).get_data(as_text=True)
        self.assertIn('<meta name="twitter:card" content="summary">', html)
        self.assertIn('/static/images/logo.png', html)
        posting = self.schema(html, "blog-posting")
        self.assertNotIn("image", posting)

    def test_pagination_and_taxonomy_links_are_crawlable_and_noindex(self):
        api = Mock()
        api.list_blogs.return_value = (
            {"items": [sample_blog()]}, {"next_cursor": "next+/=="}
        )
        api.list_categories.return_value = {"items": []}
        api.list_tags.return_value = {"items": []}
        with patch.dict(self.app.config, {"COMMUNITY_BLOG_ENABLED": "true"}), patch(
            "routes.blog_routes.client", return_value=api
        ):
            response = self.client.get("/blogs?sort=popular&tag=long-tag")
        html = response.get_data(as_text=True)
        self.assertIn('<a class="auth-button" href="/blogs?tag=long-tag&amp;sort=popular&amp;cursor=next%2B/%3D%3D" rel="next">', html)
        self.assertIn('href="/blogs?category=ownership"', html)
        self.assertIn('href="/blogs?tag=long-tag"', html)
        self.assertIn('<meta name="robots" content="noindex, follow">', html)
        self.assertIn('<link rel="canonical" href="https://ampyan.com/blogs">', html)


if __name__ == "__main__":
    unittest.main()
