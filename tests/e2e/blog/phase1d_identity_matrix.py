"""Blocked/banned disposable identity matrix with browser and DB evidence."""
import io
import json
import os

import psycopg2
import requests
from PIL import Image
from playwright.sync_api import sync_playwright


WEB = "http://127.0.0.1:5510"
API = "http://127.0.0.1:5520"
TOKEN = "phase1d-local-token"
DB = "postgresql://riteshkumar@127.0.0.1:55432/ampyan_blog_phase1d"
CHROME = os.environ.get("PHASE1D_CHROME_PATH")


def snapshot():
    tables = (
        "blogs", "blog_comments", "blog_likes", "blog_bookmarks",
        "blog_follows", "blog_reports", "blog_moderation_actions",
    )
    with psycopg2.connect(DB) as connection:
        with connection.cursor() as cursor:
            result = {}
            for table in tables:
                cursor.execute(f"SELECT count(*) FROM {table}")
                result[table] = cursor.fetchone()[0]
            return result


def image():
    output = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(output, "PNG")
    return output.getvalue()


def headers(user_id, extra=None):
    value = {
        "X-AMPYAN-BLOG-SERVICE-TOKEN": TOKEN,
        "X-AMPYAN-BLOG-USER-ID": str(user_id),
    }
    value.update(extra or {})
    return value


def run():
    report = {"api_denials": 0, "no_mutation": 0, "browser_denials": 0}
    before = snapshot()
    operations = (
        ("create", "POST", "/api/v1/blogs", {"json": {
            "title": "Denied", "content_blocks": [], "tags": [],
        }, "headers": {"Idempotency-Key": "denied-key"}}),
        ("update", "PATCH", "/api/v1/blogs/2", {"json": {
            "title": "Denied", "content_blocks": [], "expected_version": 1,
        }, "headers": {"If-Match": "1"}}),
        ("delete", "DELETE", "/api/v1/blogs/2", {}),
        ("submit", "POST", "/api/v1/blogs/2/submit", {}),
        ("withdraw", "POST", "/api/v1/blogs/2/withdraw", {}),
        ("media", "POST", "/api/v1/blogs/media", {
            "files": {"image": ("denied.png", image(), "image/png")},
        }),
        ("comment", "POST", "/api/v1/blogs/1/comments", {
            "json": {"body": "Denied comment"},
        }),
        ("edit-comment", "PATCH", "/api/v1/blog-comments/1", {
            "json": {"body": "Denied edit"},
        }),
        ("delete-comment", "DELETE", "/api/v1/blog-comments/1", {}),
        ("like", "POST", "/api/v1/blogs/1/like", {}),
        ("bookmark", "POST", "/api/v1/blogs/1/bookmark", {}),
        ("follow", "POST", "/api/v1/blogs/authors/1/follow", {}),
        ("report", "POST", "/api/v1/blogs/1/report", {
            "json": {"reason": "spam", "details": "Denied"},
        }),
        ("moderation-list", "GET", "/api/v1/blogs/moderation", {}),
        ("moderate", "POST", "/api/v1/blogs/1/moderate", {
            "json": {"action": "archive", "reason": "Denied"},
            "headers": {"If-Match": "1"},
        }),
    )
    for user_id, identity in ((5, "blocked"), (6, "banned")):
        for name, method, path, options in operations:
            options = dict(options)
            supplied = options.pop("headers", {})
            response = requests.request(
                method, API + path, timeout=5,
                headers=headers(user_id, supplied), **options,
            )
            assert response.status_code == 403, (
                identity, name, response.status_code, response.text
            )
            error = response.json()["error"]
            assert error["code"] == "BLOG_USER_UNAVAILABLE"
            report["api_denials"] += 2

    after = snapshot()
    assert before == after, (before, after)
    report["no_mutation"] += len(before)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME or None)
        for username in ("blocked", "banned"):
            context = browser.new_context()
            page = context.new_page()
            page.goto(WEB + "/login")
            page.get_by_label("Username or Email").fill(username)
            page.get_by_label("Password").fill("Phase1dPass!9")
            page.get_by_role("button", name="Login").click()
            page.wait_for_load_state("domcontentloaded")
            page.goto(WEB + "/blogs/write")
            page.get_by_label("Title", exact=True).fill("Must not persist")
            page.get_by_role("button", name="Save draft").click()
            page.wait_for_load_state("domcontentloaded")
            assert "unavailable" in page.locator("body").inner_text().lower()
            report["browser_denials"] += 2
            context.close()
        browser.close()
    assert before == snapshot()
    report["no_mutation"] += 1
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
