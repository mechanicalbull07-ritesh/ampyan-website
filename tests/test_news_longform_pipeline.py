import json
import os
import tempfile
import unittest
from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from services.app_api_sync import sync_news_to_app
from services.news_content import (
    blocks_plain_text,
    content_blocks_limit_error,
    normalize_content_blocks,
)


WORD_COUNTS = (500, 1_000, 2_000, 4_000, 8_000, 12_000)


def longform_fixture(word_count):
    vocabulary = (
        "engine safety mileage भारत गाड़ी परीक्षण 🚗 emoji "
        "unicode café O'Reilly ampersand& angle<bracket> quote“value”"
    ).split()
    words = [f"{vocabulary[index % len(vocabulary)]}-{index}" for index in range(word_count)]
    paragraphs = [
        " ".join(words[index:index + 100])
        for index in range(0, len(words), 100)
    ]
    blocks = [
        {"type": "heading", "level": 2, "text": f"{word_count}-word stress article"},
        *[
            {"type": "paragraph", "content": [{"text": paragraph}]}
            for paragraph in paragraphs
        ],
        {
            "type": "bullet_list",
            "items": [[{"text": "सूची 🚘 one"}], [{"text": "list two & <safe>"}]],
        },
        {
            "type": "numbered_list",
            "items": [[{"text": "पहला"}], [{"text": "second 😀"}]],
        },
        {
            "type": "table",
            "headers": ["Metric", "Value"],
            "rows": [["Range", "500 km"], ["Safety", "★★★★★"]],
        },
        {
            "type": "quote",
            "content": [{"text": "लंबी यात्रा सुरक्षित रखें 🚗"}],
            "cite": "AMPYAN",
        },
        {
            "type": "image",
            "url": "https://ampyan.com/static/news_images/stress.webp",
            "caption": "Unicode caption हिन्दी 😀",
            "alt_text": "Stress image",
        },
        {"type": "youtube", "url": "https://youtu.be/dQw4w9WgXcQ"},
        {"type": "instagram", "url": "https://www.instagram.com/reel/ABC_123/"},
    ]
    return " ".join(words), {"version": 1, "blocks": blocks}


class LongformNewsPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app

        cls.app = app

    def test_requested_sizes_survive_editor_validation_sync_serialization(self):
        for word_count in WORD_COUNTS:
            with self.subTest(word_count=word_count):
                legacy_body, raw_document = longform_fixture(word_count)
                editor_json = json.dumps(raw_document, ensure_ascii=False)
                self.assertEqual(json.loads(editor_json), raw_document)
                self.assertIsNone(content_blocks_limit_error(raw_document))

                stored_document = normalize_content_blocks(json.loads(editor_json))
                self.assertEqual(
                    normalize_content_blocks(stored_document),
                    stored_document,
                )
                self.assertEqual(
                    [
                        block["content"][0]["text"]
                        for block in stored_document["blocks"]
                        if block["type"] == "paragraph"
                    ],
                    [
                        block["content"][0]["text"]
                        for block in raw_document["blocks"]
                        if block["type"] == "paragraph"
                    ],
                )
                self.assertEqual(
                    " ".join(
                        block["content"][0]["text"]
                        for block in stored_document["blocks"]
                        if block["type"] == "paragraph"
                    ),
                    legacy_body,
                )
                self.assertIn("Unicode caption हिन्दी 😀", blocks_plain_text(stored_document))

                news = SimpleNamespace(
                    id=word_count,
                    title=f"Stress {word_count}",
                    content=legacy_body,
                    content_blocks=stored_document,
                    category="auto-news",
                    image=None,
                    created_at=datetime(2026, 7, 26),
                )
                with self.app.test_request_context("/", base_url="https://ampyan.com"):
                    with patch(
                        "services.app_api_sync._request", return_value=True
                    ) as request_mock:
                        self.assertTrue(sync_news_to_app(news))
                api_payload = request_mock.call_args.kwargs["json"]
                self.assertEqual(api_payload["body"], legacy_body)
                self.assertEqual(api_payload["content_blocks"], stored_document)
                self.assertLess(
                    len(json.dumps(api_payload, ensure_ascii=False).encode("utf-8")),
                    2 * 1024 * 1024,
                )

    def test_maximum_structural_document_is_preserved_exactly(self):
        raw = {
            "version": 1,
            "blocks": [{"type": "divider"} for _ in range(160)],
        }
        self.assertIsNone(content_blocks_limit_error(raw))
        self.assertEqual(normalize_content_blocks(raw), raw)

    def test_news_multipart_text_uses_the_explicit_request_ceiling(self):
        self.assertEqual(
            self.app.config["MAX_FORM_MEMORY_SIZE"],
            self.app.config["MAX_CONTENT_LENGTH"],
        )
        self.assertEqual(self.app.config["MAX_FORM_MEMORY_SIZE"], 10 * 1024 * 1024)

        from flask import Flask, request

        parser_app = Flask(__name__)
        parser_app.config.update(
            MAX_CONTENT_LENGTH=self.app.config["MAX_CONTENT_LENGTH"],
            MAX_FORM_MEMORY_SIZE=self.app.config["MAX_FORM_MEMORY_SIZE"],
        )

        @parser_app.post("/parse")
        def parse_multipart():
            return {"content_length": len(request.form["content"])}

        image_buffer = BytesIO(b"")
        try:
            response = parser_app.test_client().post(
                "/parse",
                data={
                    "content": "x" * 600_000,
                    "image": (image_buffer, "empty.webp"),
                },
            )
        finally:
            image_buffer.close()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["content_length"], 600_000)

    def test_website_database_round_trip_preserves_12k_words_and_blocks(self):
        from flask import Flask
        from models.models import News, db

        legacy_body, raw_document = longform_fixture(12_000)
        stored_document = normalize_content_blocks(raw_document)
        handle, database_path = tempfile.mkstemp(
            prefix="ampyan-website-news-stress-",
            suffix=".sqlite",
        )
        os.close(handle)
        try:
            isolated_app = Flask(__name__)
            isolated_app.config.update(
                SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
                SQLALCHEMY_TRACK_MODIFICATIONS=False,
            )
            db.init_app(isolated_app)
            with isolated_app.app_context():
                News.__table__.create(db.engine)
                article = News(
                    title="12,000-word database round trip",
                    content=legacy_body,
                    content_blocks=stored_document,
                    category="auto-news",
                )
                db.session.add(article)
                db.session.commit()
                article_id = article.id
                db.session.expire_all()
                fetched = db.session.get(News, article_id)
                self.assertEqual(fetched.content, legacy_body)
                self.assertEqual(fetched.content_blocks, stored_document)
        finally:
            os.unlink(database_path)


if __name__ == "__main__":
    unittest.main()
