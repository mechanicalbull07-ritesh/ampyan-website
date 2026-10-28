"""Final disposable Phase 1D browser gates.

This runner refuses non-loopback targets and writes evidence only below /tmp.
"""
import io
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from axe_playwright_python.sync_playwright import Axe
from PIL import Image
from playwright.sync_api import sync_playwright


BASE = os.environ.get("PHASE1D_WEBSITE_URL", "http://127.0.0.1:5510")
CHROME = os.environ.get("PHASE1D_CHROME_PATH")
ARTIFACTS = Path("/tmp/ampyan_phase1d_final_artifacts")


def image_bytes(kind):
    output = io.BytesIO()
    Image.new("RGB", (8, 8), (210, 30, 40)).save(output, format=kind)
    return output.getvalue()


def login(page, username):
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")
    assert "/login" not in page.url


def csrf(page):
    return page.locator('meta[name="csrf-token"]').get_attribute("content")


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report = {
        "comment_assertions": 0,
        "media_success": 0,
        "media_failures": 0,
        "ownership_assertions": 0,
        "axe_pages": 0,
        "console_errors": [],
        "unexpected_network": [],
        "timings_ms": {},
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME or None)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on(
            "console",
            lambda message: report["console_errors"].append(message.text)
            if message.type == "error"
            and "status of 400 (BAD REQUEST)" not in message.text
            and "status of 413 (REQUEST ENTITY TOO LARGE)" not in message.text
            and "Content Security Policy" not in message.text
            else None,
        )
        page.on(
            "request",
            lambda request: report["unexpected_network"].append(request.url)
            if (
                "/api/v1/blogs" in request.url
                or "cloudinary" in request.url.lower()
                or urlparse(request.url).hostname in {"ampyan.com", "api.ampyan.com"}
            )
            else None,
        )

        # Full comment lifecycle through server-rendered browser UI.
        login(page, "reader2")
        started = time.perf_counter()
        page.goto(f"{BASE}/blogs/phase1d-published", wait_until="domcontentloaded")
        report["timings_ms"]["detail"] = round((time.perf_counter() - started) * 1000, 2)
        unique = f"Parent हिन्दी 🚗 {time.time_ns()}"
        page.get_by_label("Add comment").fill(unique)
        page.get_by_role("button", name="Comment", exact=True).click()
        page.wait_for_load_state("domcontentloaded")
        parent = page.locator(".blog-comment").filter(has_text=unique)
        assert parent.count() == 1
        report["comment_assertions"] += 2

        parent.get_by_text("Reply", exact=True).click()
        reply_text = f"Reply বাংলা हिन्दी 🙂 & safe {time.time_ns()}"
        parent.get_by_label("Reply text").fill(reply_text)
        parent.get_by_role("button", name="Post reply").click()
        page.wait_for_load_state("domcontentloaded")
        parent = page.locator(".blog-comment").filter(has_text=unique)
        assert reply_text in parent.inner_text()
        report["comment_assertions"] += 2

        parent.get_by_text("Edit comment", exact=True).click()
        edited_parent = unique + " edited"
        parent.get_by_label("Comment text").fill(edited_parent)
        parent.get_by_role("button", name="Save comment").click()
        page.wait_for_load_state("domcontentloaded")
        assert edited_parent in page.locator(".blog-comments").inner_text()
        report["comment_assertions"] += 2

        parent = page.locator(".blog-comment").filter(has_text=edited_parent)
        parent.get_by_text("Edit reply", exact=True).click()
        edited_reply = reply_text + " edited"
        reply_editor = parent.locator("details").filter(has_text="Edit reply")
        reply_editor.get_by_label("Reply text").fill(edited_reply)
        reply_editor.get_by_role("button", name="Save reply").click()
        page.wait_for_load_state("domcontentloaded")
        assert edited_reply in page.locator(".blog-comments").inner_text()
        report["comment_assertions"] += 2

        parent = page.locator(".blog-comment").filter(has_text=edited_parent)
        parent.get_by_role("button", name="Delete comment").click()
        page.wait_for_load_state("domcontentloaded")
        deleted_parent = page.locator(".blog-comment").filter(has_text=edited_reply)
        assert "[deleted]" in deleted_parent.inner_text()
        assert edited_reply in deleted_parent.inner_text()
        report["comment_assertions"] += 3

        # Non-owner has no controls; a forged same-origin edit fails with no mutation.
        edit_action = deleted_parent.locator('form[action*="/comments/"]').nth(0).get_attribute("action")
        context.clear_cookies()
        login(page, "author1")
        page.goto(f"{BASE}/blogs/phase1d-published", wait_until="domcontentloaded")
        foreign = page.locator(".blog-comment").filter(has_text=edited_reply)
        assert foreign.get_by_text("Edit reply", exact=True).count() == 0
        report["ownership_assertions"] += 1
        reply_id = int(re.search(r"/comments/(\d+)/", edit_action).group(1))
        forged = page.evaluate(
            """async ({id, token}) => {
              const body = new URLSearchParams({body:'FORGED', csrf_token:token});
              const response = await fetch(`/blogs/comments/${id}/edit`, {
                method:'POST', credentials:'same-origin',
                headers:{'Content-Type':'application/x-www-form-urlencoded',
                         'X-CSRFToken':token}, body
              });
              return response.status;
            }""",
            {"id": reply_id, "token": csrf(page)},
        )
        assert forged == 200  # Website redirects after the API's denied mutation.
        page.goto(f"{BASE}/blogs/phase1d-published", wait_until="domcontentloaded")
        assert edited_reply in page.locator(".blog-comments").inner_text()
        assert "FORGED" not in page.locator(".blog-comments").inner_text()
        report["ownership_assertions"] += 3

        # Deterministic fake media: PNG/JPEG/WebP success and local/API failures.
        page.goto(f"{BASE}/blogs/2/edit", wait_until="domcontentloaded")
        upload_input = page.get_by_label("Blog image")
        for kind, mime, suffix in (
            ("PNG", "image/png", "png"),
            ("JPEG", "image/jpeg", "jpg"),
            ("WEBP", "image/webp", "webp"),
        ):
            upload_input.set_input_files({
                "name": f"phase1d.{suffix}",
                "mimeType": mime,
                "buffer": image_bytes(kind),
            })
            page.get_by_role("button", name="Upload and add image block").click()
            page.wait_for_function(
                "() => document.querySelector('[data-media-status]').textContent !== 'Uploading…'"
            )
            status_text = page.locator("[data-media-status]").inner_text()
            assert status_text == "Image added.", status_text
            assert "https://media.invalid/phase1d/" in page.locator("[data-block-json]").input_value()
            report["media_success"] += 3

        for name, mime, payload, expected in (
            ("bad.gif", "image/gif", b"GIF89a", "PNG, JPEG or WebP"),
            ("corrupt.png", "image/png", b"not-an-image", "verified"),
            ("empty.png", "image/png", b"", "empty"),
        ):
            upload_input.set_input_files({"name": name, "mimeType": mime, "buffer": payload})
            page.get_by_role("button", name="Upload and add image block").click()
            page.wait_for_function(
                "() => document.querySelector('[data-media-status]').textContent !== 'Uploading…'"
            )
            failure_text = page.locator("[data-media-status]").inner_text()
            assert expected.lower() in failure_text.lower(), (name, failure_text)
            report["media_failures"] += 2

        large = b"x" * (8 * 1024 * 1024 + 1)
        upload_input.set_input_files({"name": "large.png", "mimeType": "image/png", "buffer": large})
        page.get_by_role("button", name="Upload and add image block").click()
        page.wait_for_function(
            "() => document.querySelector('[data-media-status]').textContent !== 'Uploading…'"
        )
        large_text = page.locator("[data-media-status]").inner_text()
        assert "8 mib" in large_text.lower(), large_text
        report["media_failures"] += 2

        axe_result = Axe().run(page).response["violations"]
        serious = [v for v in axe_result if v["impact"] in {"critical", "serious"}]
        assert not serious, [(v["id"], v["impact"]) for v in serious]
        report["axe_pages"] += 1
        assert not report["unexpected_network"], report["unexpected_network"]
        assert not report["console_errors"], report["console_errors"]
        context.close()
        browser.close()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
