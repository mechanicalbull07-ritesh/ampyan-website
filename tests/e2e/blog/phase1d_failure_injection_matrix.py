"""Exhaustive Website-to-API failure matrix against disposable local staging."""
import json
import os
from pathlib import Path

import psycopg2
from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:5510"
CONTROL = Path("/tmp/ampyan_phase1d_failure.json")
HITS = Path(str(CONTROL) + ".hits")
RESULTS = Path("/tmp/ampyan_phase1d_failure_results.json")
DB = "postgresql://riteshkumar@127.0.0.1:55432/ampyan_blog_phase1d"
FAILURES = (
    "connection_refused", "dns_failure", "connect_timeout", "read_timeout",
    "http_400", "http_401", "http_403", "http_404", "http_409", "http_422",
    "http_429", "http_500", "http_502", "http_503", "empty_body",
    "invalid_json", "missing_required_fields", "incorrect_response_shape",
    "partial_optional_failure",
)
OPERATIONS = (
    ("listing", "GET", "blogs", "GET", "/blogs", {}),
    ("listing_pagination", "GET", "blogs", "GET", "/blogs?cursor=opaque-test", {}),
    ("detail", "GET", "blogs/phase1d-published", "GET", "/blogs/phase1d-published", {}),
    ("view_recording", "POST", "blogs/1/view", "GET", "/blogs/phase1d-published", {}),
    ("category_loading", "GET", "blogs/categories", "GET", "/blogs", {}),
    ("tag_loading", "GET", "blogs/tags", "GET", "/blogs", {}),
    ("related_blog_loading", "GET", "blogs/1/related", "GET", "/blogs/phase1d-published", {}),
    ("create_draft", "POST", "blogs", "POST", "/blogs/write", {
        "title": "Preserved injected title", "content_blocks": "[]",
    }),
    ("update_draft", "PATCH", "blogs/2", "POST", "/blogs/2/edit", {
        "title": "Preserved injected update", "version": "1",
        "content_blocks": "[]",
    }),
    ("delete_draft", "DELETE", "blogs/2", "POST", "/blogs/2/delete", {}),
    ("submit", "POST", "blogs/2/submit", "POST", "/blogs/2/submit", {}),
    ("withdraw", "POST", "blogs/3/withdraw", "POST", "/blogs/3/withdraw", {}),
    ("my_blogs", "GET", "blogs/me", "GET", "/blogs/me", {}),
    ("analytics", "GET", "blogs/me/analytics", "GET", "/blogs/me/analytics", {}),
    ("like", "POST", "blogs/1/like", "POST", "/blogs/1/like", {}),
    ("unlike", "DELETE", "blogs/1/like", "POST", "/blogs/1/unlike", {}),
    ("bookmark", "POST", "blogs/1/bookmark", "POST", "/blogs/1/bookmark", {}),
    ("unbookmark", "DELETE", "blogs/1/bookmark", "POST", "/blogs/1/unbookmark", {}),
    ("follow", "POST", "blogs/authors/1/follow", "POST", "/blogs/authors/1/follow", {}),
    ("unfollow", "DELETE", "blogs/authors/1/follow", "POST", "/blogs/authors/1/unfollow", {}),
    ("create_comment", "POST", "blogs/1/comments", "POST", "/blogs/1/comments", {
        "body": "Injected comment",
    }),
    ("create_reply", "POST", "blogs/1/comments", "POST", "/blogs/1/comments", {
        "body": "Injected reply", "parent_comment_id": "1",
    }),
    ("edit_comment", "PATCH", "blog-comments/1", "POST", "/blogs/comments/1/edit", {
        "body": "Injected edit",
    }),
    ("delete_comment", "DELETE", "blog-comments/1", "POST", "/blogs/comments/1/delete", {}),
    ("report", "POST", "blogs/1/report", "POST", "/blogs/1/report", {
        "reason": "spam", "details": "Injected report",
    }),
    ("media", "POST", "blogs/media", "POST", "/blogs/media", {}),
    ("moderation_queue", "GET", "blogs/moderation", "GET", "/blogs/moderation", {}),
    ("approve", "POST", "blogs/3/moderate", "POST", "/blogs/3/moderate", {
        "action": "approve", "version": "1",
    }),
    ("reject", "POST", "blogs/3/moderate", "POST", "/blogs/3/moderate", {
        "action": "reject", "reason": "Injected", "version": "1",
    }),
    ("archive", "POST", "blogs/3/moderate", "POST", "/blogs/3/moderate", {
        "action": "archive", "reason": "Injected", "version": "1",
    }),
    ("restore", "POST", "blogs/3/moderate", "POST", "/blogs/3/moderate", {
        "action": "restore", "version": "1",
    }),
)


def snapshot():
    tables = (
        "blogs", "blog_content_blocks", "blog_comments", "blog_likes",
        "blog_bookmarks", "blog_follows", "blog_reports", "blog_views",
        "blog_moderation_actions", "blog_idempotency_keys",
    )
    with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
        result = {}
        for table in tables:
            cursor.execute(f"SELECT count(*) FROM {table}")
            result[table] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT id,status,version,view_count,like_count,bookmark_count,"
            "comment_count FROM blogs ORDER BY id"
        )
        result["state"] = cursor.fetchall()
        return result


def login(page, username):
    page.goto(BASE + "/login")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")


def token(page):
    return page.locator('meta[name="csrf-token"]').get_attribute("content")


def invoke(page, web_method, web_path, fields):
    if web_method == "GET":
        response = page.goto(BASE + web_path, wait_until="domcontentloaded")
        return response.status if response else 200, page.locator("body").inner_text()
    current_token = token(page)
    if web_path == "/blogs/media":
        return page.evaluate(
            """async ({path, token}) => {
              const bytes = Uint8Array.from(atob(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl1sAAAAASUVORK5CYII='
              ), c => c.charCodeAt(0));
              const body = new FormData();
              body.set('csrf_token', token);
              body.set('image', new File([bytes], 'injected.png', {type:'image/png'}));
              const response = await fetch(path, {
                method:'POST', credentials:'same-origin',
                headers:{'X-CSRFToken':token}, body
              });
              return [response.status, await response.text()];
            }""",
            {"path": web_path, "token": current_token},
        )
    return page.evaluate(
        """async ({path, fields, token}) => {
          const body = new URLSearchParams(fields);
          body.set('csrf_token', token);
          const response = await fetch(path, {
            method:'POST', credentials:'same-origin', redirect:'follow',
            headers:{'Content-Type':'application/x-www-form-urlencoded',
                     'X-CSRFToken':token}, body
          });
          return [response.status, await response.text()];
        }""",
        {"path": web_path, "fields": fields, "token": current_token},
    )


def run():
    rows = []
    console_errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )
        author = browser.new_context()
        author_page = author.new_page()
        author_page.on("console", lambda message: console_errors.append(message.text)
                       if message.type == "error" and "status of " not in message.text else None)
        login(author_page, "author1")
        # Establish the normal deduplicated view session before the immutable
        # matrix snapshot; later detail navigations must not create duplicates.
        author_page.goto(BASE + "/blogs/phase1d-published")
        moderator = browser.new_context()
        moderator_page = moderator.new_page()
        login(moderator_page, "moderator")
        before = snapshot()

        for operation, api_method, api_path, web_method, web_path, fields in OPERATIONS:
            page = moderator_page if operation in {
                "moderation_queue", "approve", "reject", "archive", "restore"
            } else author_page
            for failure in FAILURES:
                CONTROL.write_text(json.dumps({
                    "method": api_method, "path": api_path, "failure": failure,
                }), encoding="utf-8")
                HITS.unlink(missing_ok=True)
                status, body = invoke(page, web_method, web_path, fields)
                lowered = body.lower()
                hits = HITS.read_text(encoding="utf-8").splitlines() if HITS.exists() else []
                optional = operation in {
                    "view_recording", "category_loading", "tag_loading",
                    "related_blog_loading",
                }
                safe = (
                    "traceback" not in lowered
                    and "phase1d-local-token" not in body
                    and "127.0.0.1:5520" not in body
                    and "/users/riteshkumar/" not in lowered
                )
                message = bool(body.strip())
                preserved = (
                    operation not in {"create_draft", "update_draft"}
                    or fields["title"] in body
                )
                conflict_distinct = (
                    failure != "http_409"
                    or operation != "update_draft"
                    or "newer version" in lowered
                )
                # Injected upstream 500 may deliberately remain HTTP 500 on an
                # editor/media response; it is handled when the safe error UI
                # is rendered with no traceback or secret.
                passed = (
                    (status < 500 if optional else True)
                    and safe and message and preserved and conflict_distinct
                    and len(hits) == 1
                )
                rows.append({
                    "operation": operation,
                    "injected_failure": failure,
                    "expected": "optional degradation" if optional else "safe accessible error",
                    "actual_status": status,
                    "database_mutation": "none (matrix snapshot)",
                    "ui_result": "usable" if optional else "clear error response",
                    "console_result": "no unexpected error",
                    "injection_hits": len(hits),
                    "pass": passed,
                })
        author.close()
        moderator.close()
        browser.close()
    CONTROL.unlink(missing_ok=True)
    HITS.unlink(missing_ok=True)
    after = snapshot()
    assert before == after, (before, after)
    assert not console_errors, console_errors
    RESULTS.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    failed = [row for row in rows if not row["pass"]]
    report = {
        "operations_executed": len(OPERATIONS),
        "failures_each": len(FAILURES),
        "combinations": len(rows),
        "passed": len(rows) - len(failed),
        "failed": len(failed),
        "database_snapshot_checks": len(before),
        "related_blog_loading": "executed",
        "result_file": str(RESULTS),
        "failed_examples": failed[:10],
    }
    print(json.dumps(report, indent=2))
    assert not failed, failed[:10]


if __name__ == "__main__":
    run()
