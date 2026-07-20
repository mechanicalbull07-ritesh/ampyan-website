import json
from html.parser import HTMLParser
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.news_content import blocks_plain_text, normalize_content_blocks


class _InitialBlocksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_payload = False
        self.payload = []
        self.hidden_value = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("id") == "initialNewsBlocks":
            self.in_payload = True
        if tag == "input" and attributes.get("name") == "content_blocks":
            self.hidden_value = attributes.get("value")

    def handle_endtag(self, tag):
        if tag == "script" and self.in_payload:
            self.in_payload = False

    def handle_data(self, data):
        if self.in_payload:
            self.payload.append(data)


class NewsContentValidationTest(unittest.TestCase):
    def test_media_blocks_accept_only_supported_public_urls(self):
        document = normalize_content_blocks({"blocks": [
            {"type": "youtube", "url": "https://youtu.be/dQw4w9WgXcQ"},
            {"type": "instagram", "url": "https://www.instagram.com/p/ABC_123/"},
            {"type": "youtube", "url": "javascript:alert(1)"},
            {"type": "youtube", "url": "data:text/html,<script>alert(1)</script>"},
            {"type": "youtube", "url": '<iframe src="https://youtube.com/embed/dQw4w9WgXcQ">'},
            {"type": "instagram", "url": "https://evil.example/reel/ABC_123/"},
            {"type": "instagram", "url": "<script>alert(1)</script>"},
        ]})
        self.assertEqual([item["type"] for item in document["blocks"]], ["youtube", "instagram"])
        self.assertEqual(document["blocks"][0]["video_id"], "dQw4w9WgXcQ")
        self.assertEqual(document["blocks"][1]["url"], "https://www.instagram.com/p/ABC_123/")

    def test_partial_failure_keeps_valid_blocks(self):
        document = normalize_content_blocks({"blocks": [
            {"type": "paragraph", "content": [{"text": "Safe", "bold": True}]},
            {"type": "youtube", "url": "https://youtube.com/shorts/dQw4w9WgXcQ"},
            {"type": "instagram", "url": "https://evil.example/reel/nope"},
            {"type": "future_chart", "script": "alert(1)"},
        ]})
        self.assertEqual([item["type"] for item in document["blocks"]], ["paragraph", "youtube"])
        self.assertEqual(document["blocks"][1]["video_id"], "dQw4w9WgXcQ")

    def test_unsafe_inline_link_is_removed_not_executed(self):
        document = normalize_content_blocks({"blocks": [{
            "type": "paragraph",
            "content": [{"text": "Do not run", "link": "javascript:alert(1)"}],
        }]})
        self.assertNotIn("link", document["blocks"][0]["content"][0])

    def test_inline_formatting_preserves_word_spacing(self):
        document = normalize_content_blocks({"blocks": [{
            "type": "paragraph",
            "content": [
                {"text": "Updated "},
                {"text": "paragraph", "bold": True},
                {"text": " after safe reload."},
            ],
        }]})
        self.assertEqual(
            "".join(run["text"] for run in document["blocks"][0]["content"]),
            "Updated paragraph after safe reload.",
        )

    def test_plain_text_fallback_is_readable(self):
        document = {"blocks": [
            {"type": "heading", "text": "Powertrain"},
            {"type": "numbered_list", "items": ["Petrol", "Electric"]},
        ]}
        self.assertEqual(blocks_plain_text(document), "Powertrain\n\nPetrol\n\nElectric")


class WebsiteNewsCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.app = app

    def test_template_renders_rich_blocks_and_safe_embeds(self):
        news = SimpleNamespace(
            id=1, title="Rich article", content="Legacy remains", category="auto-news",
            image=None, created_at=None, reply_count=0, reply_threads=[],
            content_blocks={"blocks": [
                {"type": "paragraph", "content": [{"text": "Important", "bold": True}]},
                {"type": "youtube", "url": "https://youtu.be/dQw4w9WgXcQ"},
                {"type": "instagram", "url": "https://www.instagram.com/reel/ABC_123/"},
            ]},
        )
        with self.app.test_request_context("/news/1"):
            from flask import render_template
            with patch("app.static_image_url_if_exists", return_value="/static/fallback.webp"):
                html = render_template(
                    "news_detail.html",
                    news=news,
                    rich_content=normalize_content_blocks(news.content_blocks),
                )
        self.assertIn("<strong>Important</strong>", html)
        self.assertIn("youtube-nocookie.com/embed/dQw4w9WgXcQ", html)
        self.assertIn("instagram.com/reel/ABC_123/embed/captioned/", html)
        self.assertNotIn("Legacy remains</p>", html)

    def test_edit_template_bootstraps_blocks_as_application_json(self):
        blocks = {"version": 1, "blocks": [{
            "type": "paragraph",
            "content": [{
                "text": 'Quotes: "double" and \'single\'; closing tag: </script>',
                "bold": True,
                "link": "https://example.com/news?x=1&y=2",
            }],
        }]}
        news = SimpleNamespace(
            id=4, title="Edit safely", content="Legacy remains", category="auto-news",
            content_blocks=blocks,
        )
        with self.app.test_request_context("/admin/news/edit/4"):
            from flask import render_template
            html = render_template("edit_news.html", news=news)
        parser = _InitialBlocksParser()
        parser.feed(html)
        self.assertEqual(parser.hidden_value, "")
        self.assertEqual(json.loads("".join(parser.payload)), blocks)
        self.assertNotIn('name="content_blocks" value="{', html)

    def test_create_and_edit_templates_expose_media_shortcuts(self):
        news = SimpleNamespace(
            id=4, title="Edit safely", content="Legacy remains", category="auto-news",
            content_blocks=None,
        )
        with self.app.test_request_context("/admin/news/create"):
            from flask import render_template
            create_html = render_template("create_news.html")
            edit_html = render_template("edit_news.html", news=news)
        for html in (create_html, edit_html):
            self.assertIn('data-add-media-block="youtube"', html)
            self.assertIn('data-add-media-block="instagram"', html)
            self.assertIn("Add YouTube video", html)
            self.assertIn("Add Instagram post/reel", html)

    def test_api_sync_keeps_legacy_body_and_adds_optional_blocks(self):
        from services.app_api_sync import sync_news_to_app
        news = SimpleNamespace(
            id=7, title="Safe", content="Legacy body", category="auto-news",
            image=None, created_at=None,
            content_blocks={"blocks": [{"type": "paragraph", "text": "Rich body"}]},
        )
        with self.app.test_request_context("/"):
            with patch("services.app_api_sync._request", return_value=True) as request_mock:
                self.assertTrue(sync_news_to_app(news))
        payload = request_mock.call_args.kwargs["json"]
        self.assertEqual(payload["body"], "Legacy body")
        self.assertIn("content_blocks", payload)


if __name__ == "__main__":
    unittest.main()
