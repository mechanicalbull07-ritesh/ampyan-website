"""Complete Website Blog CSRF matrix with disposable DB no-mutation proof."""
import json
import os

import psycopg2
from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:5510"
DB = "postgresql://riteshkumar@127.0.0.1:55432/ampyan_blog_phase1d"


def snapshot():
    tables = (
        "blogs", "blog_content_blocks", "blog_comments", "blog_likes",
        "blog_bookmarks", "blog_follows", "blog_reports",
        "blog_moderation_actions",
    )
    with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
        result = {}
        for table in tables:
            cursor.execute(f"SELECT count(*), COALESCE(MAX(id), 0) FROM {table}")
            result[table] = cursor.fetchone()
        cursor.execute(
            "SELECT id,status,version,like_count,bookmark_count,comment_count "
            "FROM blogs ORDER BY id"
        )
        result["blog_state"] = cursor.fetchall()
        return result


def run():
    report = {"missing_rejected": 0, "invalid_rejected": 0, "valid_accepted": 0,
              "no_mutation": 0}
    before = snapshot()
    cases = (
        ("create", "/blogs/write", {"title": "Denied"}),
        ("update", "/blogs/2/edit", {"title": "Denied", "version": "1"}),
        ("submit", "/blogs/2/submit", {}),
        ("media", "/blogs/media", {}),
        ("comment", "/blogs/1/comments", {"body": "Denied"}),
        ("reply", "/blogs/1/comments", {"body": "Denied", "parent_comment_id": "1"}),
        ("edit-comment", "/blogs/comments/1/edit", {"body": "Denied"}),
        ("delete-comment", "/blogs/comments/1/delete", {}),
        ("like", "/blogs/1/like", {}),
        ("bookmark", "/blogs/1/bookmark", {}),
        ("follow", "/blogs/authors/1/follow", {}),
        ("report", "/blogs/1/report", {"reason": "spam"}),
        ("moderate", "/blogs/1/moderate", {
            "action": "archive", "reason": "Denied", "version": "1",
        }),
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE + "/login")
        page.get_by_label("Username or Email").fill("blocked")
        page.get_by_label("Password").fill("Phase1dPass!9")
        page.get_by_role("button", name="Login").click()
        page.wait_for_load_state("domcontentloaded")
        page.goto(BASE + "/blogs/write")
        token = page.locator('meta[name="csrf-token"]').get_attribute("content")

        for name, path, fields in cases:
            for kind, supplied in (("missing", None), ("invalid", "invalid-token"), ("valid", token)):
                result = page.evaluate(
                    """async ({path, fields, supplied}) => {
                      const body = new URLSearchParams(fields);
                      const headers = {'Content-Type':'application/x-www-form-urlencoded'};
                      if (supplied !== null) {
                        body.set('csrf_token', supplied);
                        headers['X-CSRFToken'] = supplied;
                      }
                      const response = await fetch(path, {
                        method:'POST', credentials:'same-origin', headers, body
                      });
                      return {status:response.status, text:await response.text()};
                    }""",
                    {"path": path, "fields": fields, "supplied": supplied},
                )
                if kind in {"missing", "invalid"}:
                    assert result["status"] == 400, (name, kind, result["status"])
                    assert "csrf" in result["text"].lower()
                    report[f"{kind}_rejected"] += 2
                else:
                    assert "csrf token is missing" not in result["text"].lower()
                    assert "csrf token is invalid" not in result["text"].lower()
                    report["valid_accepted"] += 2
        context.close()
        browser.close()
    assert before == snapshot()
    report["no_mutation"] += len(before)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
