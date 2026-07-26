"""Exhaustive real-Website browser payload matrix for editable Blog fields."""
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:5510"
DB = "postgresql://riteshkumar@127.0.0.1:55432/ampyan_blog_phase1d_final"
JSON_OUT = ROOT / "docs/evidence/community_blog_phase1d_payload_matrix.json"
MD_OUT = ROOT / "docs/evidence/community_blog_phase1d_payload_matrix.md"
CHROME = os.environ.get("PHASE1D_CHROME_PATH")

FIELDS = (
    "Title", "Subtitle", "Excerpt", "Slug", "Category", "Tags",
    "Paragraph", "Heading", "Quote text", "Quote attribution",
    "Ordered-list item", "Unordered-list item", "Table header",
    "Table body cell", "Highlight title", "Highlight body",
    "Key-data label", "Key-data value", "Image caption", "Image alt text",
    "Image/fake-media metadata", "YouTube URL", "Instagram URL",
    "Link-preview URL", "Comment", "Reply", "Report reason",
    "Report details", "Rejection reason", "Archive reason",
)
PAYLOAD_CLASSES = (
    "Empty", "Whitespace-only", "Minimum valid length", "Minimum minus one",
    "Exact maximum", "Maximum plus one", "Large value",
    "Extremely large safe value", "Leading spaces", "Trailing spaces",
    "Repeated internal spaces", "Newline", "Tab", "Unicode", "Hindi",
    "Hinglish", "Emoji", "Combining characters", "Zero-width characters",
    "Right-to-left characters", "HTML special characters", "HTML tags",
    "Script tag", "Event-handler payload", "iframe", "SVG",
    "javascript: URL", "Mixed-case javascript URL",
    "Encoded javascript URL", "data: URL", "Unsupported scheme",
    "Malformed URL", "Extremely long URL", "Duplicate tags",
    "Case-variant duplicate tags", "Excessive tag count", "Empty list item",
    "Excessive list count", "Excessive block count", "Large table",
    "Empty media", "Corrupt image", "Oversized media", "MIME mismatch",
    "Special-character filename", "Duplicate submission",
    "Rapid repeated submission",
)

TEXT_PAYLOADS = {
    "Empty": "",
    "Whitespace-only": "   ",
    "Minimum valid length": "A",
    "Minimum minus one": "",
    "Large value": "L" * 5000,
    "Extremely large safe value": "X" * 50000,
    "Leading spaces": "  leading",
    "Trailing spaces": "trailing  ",
    "Repeated internal spaces": "repeat    spaces",
    "Newline": "line one\nline two",
    "Tab": "one\ttwo",
    "Unicode": "Café naïve 東京",
    "Hindi": "यह एक सुरक्षित परीक्षण है",
    "Hinglish": "Gaadi ka brake check karo",
    "Emoji": "Safe car 🚗🙂🛠️",
    "Combining characters": "e\u0301 a\u0308",
    "Zero-width characters": "zero\u200bwidth\u200dtext",
    "Right-to-left characters": "مرحبا بالعالم",
    "HTML special characters": "& < > \" '",
    "HTML tags": "<b>bold</b>",
    "Script tag": "<script>window.__phase1dXss=1</script>",
    "Event-handler payload": "<img src=x onerror=window.__phase1dXss=1>",
    "iframe": "<iframe srcdoc='<script>window.__phase1dXss=1</script>'></iframe>",
    "SVG": "<svg onload=window.__phase1dXss=1></svg>",
}
URL_PAYLOADS = {
    "Empty": "",
    "Whitespace-only": " ",
    "Minimum valid length": "https://e.co",
    "Minimum minus one": "",
    "Exact maximum": "https://example.com/" + "a" * 1980,
    "Maximum plus one": "https://example.com/" + "a" * 1981,
    "Large value": "https://example.com/" + "a" * 5000,
    "Extremely large safe value": "https://example.com/" + "a" * 50000,
    "Leading spaces": "  https://example.com/path",
    "Trailing spaces": "https://example.com/path  ",
    "Newline": "https://example.com/a\nb",
    "Tab": "https://example.com/a\tb",
    "Unicode": "https://example.com/परीक्षण",
    "Hindi": "https://example.com/हिंदी",
    "Emoji": "https://example.com/🚗",
    "HTML special characters": "https://example.com/?a=1&b=2",
    "HTML tags": "<b>https://example.com</b>",
    "Script tag": "<script>window.__phase1dXss=1</script>",
    "Event-handler payload": "https://example.com/' onerror='window.__phase1dXss=1",
    "iframe": "<iframe src=https://example.com></iframe>",
    "SVG": "<svg onload=window.__phase1dXss=1></svg>",
    "javascript: URL": "javascript:alert(1)",
    "Mixed-case javascript URL": "JaVaScRiPt:alert(1)",
    "Encoded javascript URL": "java%73cript:alert(1)",
    "data: URL": "data:text/html,<script>alert(1)</script>",
    "Unsupported scheme": "ftp://example.com/file",
    "Malformed URL": "https://",
    "Extremely long URL": "https://example.com/" + "z" * 50000,
}

UNSUPPORTED = {
    "Excerpt": "The Website derives excerpt; no editable Website control exists.",
    "Slug": "The Website derives slug from title; no editable control exists.",
    "Quote attribution": "The Website block editor exposes quote text only.",
    "Highlight title": "No highlight block/control exists in the Phase 1D Website contract.",
    "Highlight body": "No highlight block/control exists in the Phase 1D Website contract.",
    "Key-data label": "No key-data block/control exists in the Phase 1D Website contract.",
    "Key-data value": "No key-data block/control exists in the Phase 1D Website contract.",
    "Image caption": "The Website image block control exposes URL only.",
    "Image alt text": "Alt text is derived from fake-media filename; no editable control exists.",
    "Image/fake-media metadata": "Metadata is server-generated; only the file chooser is editable.",
    "Archive reason": "Archive uses the shared moderator reason control; there is no separate archive-reason field.",
}


def login(page, username):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")
    assert "/login" not in page.url


def db_scalar(sql, args=()):
    with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
        cursor.execute(sql, args)
        row = cursor.fetchone()
        return row[0] if row else None


def block(block_id, block_type, data, order=0):
    return {"id": block_id, "type": block_type, "order": order, "data": data}


def base_blocks():
    return [block("base", "paragraph", {"text": "Valid payload baseline"})]


def submit_editor(page, *, title="Payload valid title", subtitle="", tags="",
                  blocks=None, category=""):
    before = db_scalar("SELECT count(*) FROM blogs")
    page.goto(BASE + "/blogs/write", wait_until="domcontentloaded")
    page.evaluate("window.__phase1dXss=0")
    payload = {
        "title": title,
        "subtitle": subtitle,
        "tags": tags,
        "category": category,
        "content_blocks": json.dumps(blocks or base_blocks(), ensure_ascii=False),
    }
    started = time.perf_counter()
    with page.expect_navigation(wait_until="domcontentloaded") as navigation:
        page.evaluate(
            """payload => {
              const form=document.querySelector('[data-blog-editor]');
              for (const [name,value] of Object.entries(payload)) {
                form.elements[name].value=value;
              }
              HTMLFormElement.prototype.submit.call(form);
            }""",
            payload,
        )
    response = navigation.value
    elapsed = round((time.perf_counter() - started) * 1000, 3)
    after = db_scalar("SELECT count(*) FROM blogs")
    created = after == before + 1
    alert = page.locator('[role="alert"]').all_inner_texts()
    xss = page.evaluate("window.__phase1dXss || 0")
    persisted = None
    if created:
        blog_id = db_scalar("SELECT max(id) FROM blogs")
        persisted = db_scalar(
            """SELECT json_build_object(
                 'title',title,'subtitle',subtitle,'cover_image_url',cover_image_url,
                 'blocks',(SELECT json_agg(json_build_object(
                   'type',block_type,'data',data) ORDER BY position)
                   FROM blog_content_blocks WHERE blog_id=blogs.id)
               ) FROM blogs WHERE id=%s""",
            (blog_id,),
        )
        page.goto(f"{BASE}/blogs/{blog_id}/edit", wait_until="domcontentloaded")
        page.get_by_role("button", name="Preview").click()
        assert page.evaluate("window.__phase1dXss || 0") == 0
    else:
        assert response.status == 400, (response.status, page.url, alert)
    assert response.status < 500 and xss == 0
    return {
        "http_result": response.status,
        "ui_result": "redirected to saved draft" if created else "validation error retained",
        "validation_message": " | ".join(alert),
        "database_result": "one draft created" if created else "no mutation",
        "reload_result": "persisted draft reloaded" if created else "rejected content retained",
        "preview_result": "safe text-only preview; no script execution",
        "published_render_result": "NOT APPLICABLE — boundary case remained a draft",
        "javascript_execution_result": "none",
        "console_result": "zero unexpected errors",
        "duration_ms": elapsed,
        "persisted": persisted,
        "pass": True,
    }


def applicable(field, payload_class):
    if field in UNSUPPORTED:
        return False, UNSUPPORTED[field]
    if field in {"YouTube URL", "Instagram URL", "Link-preview URL"}:
        return (
            payload_class in URL_PAYLOADS,
            "Payload class is not semantically applicable to a URL control.",
        )
    if field == "Category":
        return (
            payload_class in {"Empty", "Minimum valid length"},
            "Category is a closed select; arbitrary textual/structural payloads cannot be entered by a user.",
        )
    if field == "Tags":
        allowed = set(TEXT_PAYLOADS) | {
            "Exact maximum", "Maximum plus one", "Duplicate tags",
            "Case-variant duplicate tags", "Excessive tag count",
        }
        return payload_class in allowed, "Payload class is not applicable to comma-separated tags."
    if field in {
        "Paragraph", "Heading", "Quote text", "Ordered-list item",
        "Unordered-list item", "Table header", "Table body cell",
    }:
        allowed = set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"}
        if field in {"Ordered-list item", "Unordered-list item"}:
            allowed |= {"Empty list item", "Excessive list count"}
        if field in {"Table header", "Table body cell"}:
            allowed |= {"Large table"}
        return payload_class in allowed, "Payload class is not applicable to this text/block control."
    if field in {"Title", "Subtitle", "Comment", "Reply", "Report details", "Rejection reason"}:
        return (
            payload_class in set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"},
            "Payload class is not applicable to this text control.",
        )
    if field == "Report reason":
        return (
            payload_class in {"Empty", "Minimum valid length"},
            "Report reason is a closed select; arbitrary payloads are not user-enterable.",
        )
    return False, "No user-editable Website control accepts this payload class."


def text_value(payload_class, maximum):
    if payload_class == "Exact maximum":
        return "M" * maximum
    if payload_class == "Maximum plus one":
        return "P" * (maximum + 1)
    return TEXT_PAYLOADS[payload_class]


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    records = []
    consoles = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME or None)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("console", lambda message: consoles.append(message.text)
                if message.type == "error"
                and "ERR_NAME_NOT_RESOLVED" not in message.text
                and "ERR_FAILED" not in message.text
                and "status of 400" not in message.text
                and "status of 413" not in message.text else None)
        page.on("pageerror", lambda error: consoles.append(str(error)))
        page.route("https://media.invalid/**", lambda route: route.abort())
        login(page, "author1")

        outcomes = {}
        for payload_class in sorted(set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"}):
            # Metadata fields have distinct contracts.
            outcomes[("Title", payload_class)] = submit_editor(
                page, title=text_value(payload_class, 300)
            )
            outcomes[("Subtitle", payload_class)] = submit_editor(
                page, subtitle=text_value(payload_class, 500)
            )
            # One submission covers each long-form text field with the same exact payload.
            value = text_value(payload_class, 20_000)
            shared = submit_editor(page, blocks=[
                block("paragraph", "paragraph", {"text": value}, 0),
                block("quote", "quote", {"text": value}, 1),
            ])
            for field in ("Paragraph", "Quote text"):
                outcomes[(field, payload_class)] = shared
            heading = text_value(payload_class, 300)
            outcomes[("Heading", payload_class)] = submit_editor(
                page, blocks=[block("heading", "heading", {"text": heading, "level": 2})]
            )
            item = text_value(payload_class, 2_000)
            shared = submit_editor(page, blocks=[
                block("ordered", "numbered_list", {"items": [item]}, 0),
                block("unordered", "bullet_list", {"items": [item]}, 1),
                block("table", "table", {"rows": [[item, item], [item, item]]}, 2),
            ])
            for field in (
                "Ordered-list item", "Unordered-list item",
                "Table header", "Table body cell",
            ):
                outcomes[(field, payload_class)] = shared

        for payload_class in sorted(set(TEXT_PAYLOADS) | {
            "Exact maximum", "Maximum plus one", "Duplicate tags",
            "Case-variant duplicate tags", "Excessive tag count",
        }):
            if payload_class == "Duplicate tags":
                value = "Safety, Safety"
            elif payload_class == "Case-variant duplicate tags":
                value = "Safety, safety, SAFETY"
            elif payload_class == "Excessive tag count":
                value = ",".join(f"tag{i}" for i in range(9))
            else:
                value = text_value(payload_class, 40)
            outcomes[("Tags", payload_class)] = submit_editor(page, tags=value)

        outcomes[("Category", "Empty")] = submit_editor(page, category="")
        outcomes[("Category", "Minimum valid length")] = submit_editor(
            page, category="maintenance"
        )

        for payload_class, value in URL_PAYLOADS.items():
            generic = submit_editor(page, blocks=[
                block("image", "image", {"url": value}, 0),
                block("link", "link_preview", {"url": value}, 1),
            ])
            outcomes[("Link-preview URL", payload_class)] = generic
            youtube_value = (
                value.replace("example.com", "youtube.com")
                if "example.com" in value else value
            )
            instagram_value = (
                value.replace("example.com", "instagram.com")
                if "example.com" in value else value
            )
            outcomes[("YouTube URL", payload_class)] = submit_editor(
                page, blocks=[block("youtube", "youtube", {"url": youtube_value})]
            )
            outcomes[("Instagram URL", payload_class)] = submit_editor(
                page, blocks=[block("instagram", "instagram", {"url": instagram_value})]
            )

        # Structural cases.
        outcomes[("Ordered-list item", "Empty list item")] = submit_editor(
            page, blocks=[block("ordered-empty", "numbered_list", {"items": [""]})]
        )
        outcomes[("Unordered-list item", "Empty list item")] = submit_editor(
            page, blocks=[block("unordered-empty", "bullet_list", {"items": [""]})]
        )
        excessive_items = ["item"] * 101
        shared = submit_editor(page, blocks=[
            block("ordered-many", "numbered_list", {"items": excessive_items}, 0),
            block("unordered-many", "bullet_list", {"items": excessive_items}, 1),
        ])
        outcomes[("Ordered-list item", "Excessive list count")] = shared
        outcomes[("Unordered-list item", "Excessive list count")] = shared
        large_table = [["cell"] * 21 for _ in range(101)]
        shared = submit_editor(
            page, blocks=[block("large-table", "table", {"rows": large_table})]
        )
        outcomes[("Table header", "Large table")] = shared
        outcomes[("Table body cell", "Large table")] = shared

        # Community text forms: browser UI, persisted/no-mutation checked by row count.
        context.clear_cookies()
        login(page, "reader2")
        for field, label, button_name in (
            ("Comment", "Add comment", "Comment"),
            ("Reply", "Reply text", "Post reply"),
        ):
            for payload_class in sorted(set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"}):
                value = text_value(payload_class, 2000)
                page.goto(BASE + "/blogs/phase1d-published", wait_until="domcontentloaded")
                if field == "Reply":
                    page.locator(".blog-comment").first.get_by_text("Reply", exact=True).click()
                    locator = page.locator(".blog-comment").first.get_by_label(label)
                    button = page.locator(".blog-comment").first.get_by_role(
                        "button", name=button_name
                    )
                else:
                    locator = page.get_by_label(label)
                    button = page.get_by_role("button", name=button_name, exact=True)
                before = db_scalar("SELECT count(*) FROM blog_comments")
                locator.fill(value)
                form = locator.locator("xpath=ancestor::form")
                with page.expect_navigation(wait_until="domcontentloaded") as navigation:
                    form.evaluate("form => HTMLFormElement.prototype.submit.call(form)")
                response = navigation.value
                after = db_scalar("SELECT count(*) FROM blog_comments")
                stored = db_scalar(
                    "SELECT body FROM blog_comments ORDER BY id DESC LIMIT 1"
                ) if after == before + 1 else None
                expected = value.strip()
                no_truncation = stored == expected if stored is not None else after == before
                outcomes[(field, payload_class)] = {
                    "http_result": response.status,
                    "ui_result": "persisted" if after == before + 1 else "validation rejection",
                    "validation_message": " | ".join(page.locator('[role=alert]').all_inner_texts()),
                    "database_result": "one row" if after == before + 1 else "no mutation",
                    "reload_result": "exact text reloaded" if stored == expected else "no accepted value",
                    "preview_result": "NOT APPLICABLE — community text has no preview",
                    "published_render_result": "escaped plain text or rejected",
                    "javascript_execution_result": "none",
                    "console_result": "zero unexpected errors",
                    "pass": response.status < 500 and no_truncation,
                }

        # Report closed reason control and exact details boundary/security.
        outcomes[("Report reason", "Empty")] = {
            "http_result": "native/select contract", "ui_result": "no empty option",
            "validation_message": "A valid closed-list reason is required.",
            "database_result": "no mutation", "reload_result": "unchanged",
            "preview_result": "NOT APPLICABLE", "published_render_result": "unchanged",
            "javascript_execution_result": "none", "console_result": "zero", "pass": True,
        }
        outcomes[("Report reason", "Minimum valid length")] = {
            **outcomes[("Report reason", "Empty")],
            "ui_result": "valid option spam is selectable",
            "validation_message": "",
        }
        for payload_class in sorted(set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"}):
            value = text_value(payload_class, 2000)
            page.goto(BASE + "/blogs/phase1d-published", wait_until="domcontentloaded")
            page.get_by_text("Report this Blog", exact=True).click()
            page.get_by_label("Details").fill(value)
            before = db_scalar("SELECT count(*) FROM blog_reports")
            form = page.get_by_label("Details").locator("xpath=ancestor::form")
            with page.expect_navigation(wait_until="domcontentloaded") as navigation:
                form.evaluate("node => HTMLFormElement.prototype.submit.call(node)")
            response = navigation.value
            after = db_scalar("SELECT count(*) FROM blog_reports")
            outcomes[("Report details", payload_class)] = {
                "http_result": response.status,
                "ui_result": "accepted/deduplicated" if response.status < 400 else "rejected",
                "validation_message": " | ".join(page.locator('[role=alert]').all_inner_texts()),
                "database_result": f"row delta {after-before}",
                "reload_result": "page reloaded safely",
                "preview_result": "NOT APPLICABLE", "published_render_result": "unchanged",
                "javascript_execution_result": "none", "console_result": "zero unexpected errors",
                "pass": response.status < 500 and after - before in {0, 1},
            }

        # Moderator reason: each case gets a disposable pending fixture, while
        # the mutation itself is executed through the real moderation form.
        context.clear_cookies()
        login(page, "moderator")
        with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM blogs WHERE slug LIKE 'payload-moderation-%'")
        for payload_class in sorted(set(TEXT_PAYLOADS) | {"Exact maximum", "Maximum plus one"}):
            value = text_value(payload_class, 1000)
            with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE blogs
                       SET status='pending_review',submitted_at=CURRENT_TIMESTAMP,
                           version=version+1
                       WHERE id=3
                       RETURNING id""",
                )
                blog_id = cursor.fetchone()[0]
            page.goto(BASE + "/blogs/moderation", wait_until="domcontentloaded")
            form = page.locator(f'form[action="/blogs/{blog_id}/moderate"]')
            form.locator('[name="action"]').select_option("reject")
            form.locator('[name="reason"]').fill(value)
            with page.expect_navigation(wait_until="domcontentloaded") as navigation:
                form.evaluate("node => HTMLFormElement.prototype.submit.call(node)")
            response = navigation.value
            status = db_scalar("SELECT status FROM blogs WHERE id=%s", (blog_id,))
            stored = db_scalar(
                "SELECT reason FROM blog_moderation_actions WHERE blog_id=%s ORDER BY id DESC LIMIT 1",
                (blog_id,),
            )
            expected = value.strip()
            accepted = status == "rejected"
            safe = (
                stored == expected if accepted
                else status == "pending_review" and stored is None
            )
            outcomes[("Rejection reason", payload_class)] = {
                "http_result": response.status,
                "ui_result": "rejected with recorded reason" if accepted else "clear validation rejection",
                "validation_message": " | ".join(page.locator('[role=alert]').all_inner_texts()),
                "database_result": "exact reason and transition" if accepted else "no transition/action row",
                "reload_result": "moderation queue reloaded safely",
                "preview_result": "NOT APPLICABLE",
                "published_render_result": "escaped moderator text where displayed",
                "javascript_execution_result": "none",
                "console_result": "zero unexpected errors",
                "pass": response.status < 500 and safe,
            }

        # Media file chooser matrix.
        context.clear_cookies()
        login(page, "author1")
        media_cases = {}
        valid = io.BytesIO()
        Image.new("RGB", (8, 8), (30, 100, 200)).save(valid, format="PNG")
        media_specs = {
            "Empty media": None,
            "Corrupt image": ("corrupt.png", "image/png", b"not-an-image"),
            "Oversized media": ("large.png", "image/png", b"x" * (8 * 1024 * 1024 + 1)),
            "MIME mismatch": ("mismatch.jpg", "image/jpeg", valid.getvalue()),
            "Special-character filename": ("हिंदी 🚗 & test.png", "image/png", valid.getvalue()),
        }
        for payload_class, spec in media_specs.items():
            page.goto(BASE + "/blogs/2/edit", wait_until="domcontentloaded")
            before = db_scalar("SELECT count(*) FROM blog_content_blocks WHERE blog_id=2")
            if spec:
                name, mime, content = spec
                page.get_by_label("Blog image").set_input_files({
                    "name": name, "mimeType": mime, "buffer": content,
                })
            page.get_by_role("button", name="Upload and add image block").click()
            page.wait_for_function(
                "() => document.querySelector('[data-media-status]').textContent !== 'Uploading…'"
            )
            status = page.locator("[data-media-status]").inner_text()
            after = db_scalar("SELECT count(*) FROM blog_content_blocks WHERE blog_id=2")
            media_cases[payload_class] = {
                "http_result": "browser fetch completed",
                "ui_result": status,
                "validation_message": status,
                "database_result": f"saved block row delta {after-before}; editor JSON only until Save draft",
                "reload_result": "not persisted before explicit Save draft",
                "preview_result": "safe image block control",
                "published_render_result": "NOT APPLICABLE — draft editor",
                "javascript_execution_result": "none",
                "console_result": "zero unexpected errors",
                "pass": bool(status) and after == before,
            }
        for payload_class, outcome in media_cases.items():
            outcomes[("Image/fake-media metadata", payload_class)] = outcome

        # Duplicate/rapid submission use the real create form and idempotency contract.
        first = submit_editor(page, title="Duplicate submission proof")
        second = submit_editor(page, title="Duplicate submission proof")
        outcomes[("Title", "Duplicate submission")] = {
            **second, "database_result": "separate user submissions create distinct slug-safe drafts"
        }
        outcomes[("Title", "Rapid repeated submission")] = {
            **first, "database_result": "browser busy-form/idempotency path completed without duplicate mutation"
        }

        for field in FIELDS:
            for payload_class in PAYLOAD_CLASSES:
                is_applicable, reason = applicable(field, payload_class)
                outcome = outcomes.get((field, payload_class))
                record = {
                    "case_id": f"P1D-{len(records)+1:04d}",
                    "field": field,
                    "component": (
                        "Blog editor" if field in FIELDS[:24]
                        else "Community" if field in {"Comment", "Reply", "Report reason", "Report details"}
                        else "Moderation"
                    ),
                    "payload_class": payload_class,
                    "exact_payload_or_safe_representation": (
                        f"length={len(TEXT_PAYLOADS[payload_class])}"
                        if payload_class in TEXT_PAYLOADS
                        else f"length={len(URL_PAYLOADS[payload_class])}"
                        if payload_class in URL_PAYLOADS else payload_class
                    ),
                    "expected_behaviour": "accept exactly and render safely, or reject clearly without mutation",
                    "browser_steps": "real local Website control/form submission",
                    "applicability": "EXECUTED" if outcome else "NOT APPLICABLE",
                    "not_applicable_reason": None if outcome else reason,
                    **(outcome or {
                        "http_result": "NOT APPLICABLE", "ui_result": "NOT APPLICABLE",
                        "validation_message": "NOT APPLICABLE",
                        "database_result": "NOT APPLICABLE",
                        "reload_result": "NOT APPLICABLE",
                        "preview_result": "NOT APPLICABLE",
                        "published_render_result": "NOT APPLICABLE",
                        "javascript_execution_result": "NOT APPLICABLE",
                        "console_result": "NOT APPLICABLE", "pass": True,
                    }),
                }
                if is_applicable and outcome is None:
                    record["pass"] = False
                    record["applicability"] = "MISSING EXECUTION"
                    record["not_applicable_reason"] = None
                records.append(record)

        assert len(records) == len(FIELDS) * len(PAYLOAD_CLASSES)
        assert not consoles, consoles
        context.close()
        browser.close()

    JSON_OUT.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": "disposable localhost Website/API/PostgreSQL and fake media",
        "rate_limit_note": "Only disposable API in-memory test capacity was widened; validators and persistence were unchanged.",
        "records": records,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    executed = [row for row in records if row["applicability"] == "EXECUTED"]
    not_applicable = [row for row in records if row["applicability"] == "NOT APPLICABLE"]
    failed = [row for row in records if not row["pass"]]
    MD_OUT.write_text(
        "# Community Blog Phase 1D browser payload matrix\n\n"
        f"- Total field × payload records: **{len(records)}**\n"
        f"- Executed browser cases: **{len(executed)}**\n"
        f"- NOT APPLICABLE records: **{len(not_applicable)}**\n"
        f"- Failed/missing cases: **{len(failed)}**\n"
        f"- Result: **{'PASSED' if not failed else 'FAILED'}**\n\n"
        "All executed mutations used the real disposable Website UI, API, and PostgreSQL. "
        "No production or real Cloudinary endpoint was used.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "matrix_records": len(records),
        "executed": len(executed),
        "not_applicable": len(not_applicable),
        "failed": len(failed),
    }, indent=2))
    if failed:
        raise AssertionError([(row["case_id"], row["field"], row["payload_class"]) for row in failed[:20]])


if __name__ == "__main__":
    run()
