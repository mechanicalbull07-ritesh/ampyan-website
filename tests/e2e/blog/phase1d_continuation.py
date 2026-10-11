"""Remaining high-risk Phase 1D gates against disposable local staging."""
import json
import os
from urllib.parse import urlparse

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright


BASE = os.environ.get("PHASE1D_WEBSITE_URL", "http://127.0.0.1:5510")
VIEWPORTS = [(360, 800), (390, 844), (768, 1024), (1024, 768), (1440, 900)]


def login(page, username):
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")


def no_overflow(page):
    assert not page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )


def axe_gate(page):
    page.wait_for_timeout(300)
    violations = Axe().run(page).response["violations"]
    serious = [v for v in violations if v["impact"] in {"critical", "serious"}]
    assert not serious, [(v["id"], v["impact"]) for v in serious]


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    report = {
        "engagement": 0,
        "comments": 0,
        "reports": 0,
        "csrf": 0,
        "conflict": 0,
        "responsive_pages": 0,
        "axe_pages": 0,
        "console_errors": [],
        "direct_blog_api": [],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None,
        )

        # Reader engagement, comment, report, and CSRF gates.
        context = browser.new_context()
        page = context.new_page()
        def console_seen(message):
            if message.type != "error":
                return
            if "violates the following Content Security Policy directive" in message.text:
                return
            if "status of 400 (BAD REQUEST)" in message.text:
                report.setdefault("expected_csrf_400_console", 0)
                report["expected_csrf_400_console"] += 1
                return
            report["console_errors"].append(message.text)
        page.on("console", console_seen)
        page.on(
            "request",
            lambda request: report["direct_blog_api"].append(request.url)
            if "/api/v1/blogs" in request.url else None,
        )
        login(page, "reader2")
        page.goto(f"{BASE}/blogs/phase1d-published")

        page.get_by_role("button", name="Like · 0").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.get_by_role("button", name="Unlike · 1").is_visible()
        page.reload()
        assert page.get_by_role("button", name="Unlike · 1").is_visible()
        page.get_by_role("button", name="Unlike · 1").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.get_by_role("button", name="Like · 0").is_visible()
        report["engagement"] += 4

        page.get_by_role("button", name="Bookmark").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.get_by_role("button", name="Remove bookmark").is_visible()
        page.reload()
        assert page.get_by_role("button", name="Remove bookmark").is_visible()
        page.get_by_role("button", name="Remove bookmark").click()
        report["engagement"] += 3

        page.wait_for_load_state("domcontentloaded")
        page.get_by_role("button", name="Follow author").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.get_by_role("button", name="Unfollow").is_visible()
        page.reload()
        assert page.get_by_role("button", name="Unfollow").is_visible()
        page.get_by_role("button", name="Unfollow").click()
        report["engagement"] += 3

        comment = "<script>alert(1)</script> plain comment"
        page.wait_for_load_state("domcontentloaded")
        page.get_by_label("Add comment").fill(comment)
        page.get_by_role("button", name="Comment").click()
        page.wait_for_load_state("domcontentloaded")
        assert page.locator(".blog-comments script").count() == 0
        assert comment not in page.locator(".blog-comments").inner_text()
        page.get_by_label("Add comment").fill("Persistent plain comment हिन्दी")
        page.get_by_role("button", name="Comment").click()
        page.wait_for_load_state("domcontentloaded")
        assert "Persistent plain comment हिन्दी" in page.locator(".blog-comments").inner_text()
        report["comments"] += 4

        page.get_by_text("Report this Blog").click()
        page.get_by_label("Reason").select_option("spam")
        page.get_by_label("Details").fill("Disposable report details")
        page.get_by_role("button", name="Send report").click()
        page.wait_for_load_state("domcontentloaded")
        assert "does not automatically remove" in page.locator("body").inner_text()
        report["reports"] += 2

        # Missing and invalid same-origin CSRF cause no like mutation.
        missing = page.evaluate(
            """async () => (await fetch('/blogs/1/like', {
              method:'POST', credentials:'same-origin'
            })).status"""
        )
        invalid = page.evaluate(
            """async () => (await fetch('/blogs/1/like', {
              method:'POST', credentials:'same-origin',
              headers:{'X-CSRFToken':'invalid'}
            })).status"""
        )
        assert missing == 400 and invalid == 400
        page.reload()
        assert page.get_by_role("button", name="Like · 0").is_visible()
        report["csrf"] += 3

        # Required viewport matrix for comments/report/detail state.
        for width, height in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            no_overflow(page)
            axe_gate(page)
            report["responsive_pages"] += 1
            report["axe_pages"] += 1

        # Actual two-context stale edit conflict.
        first = browser.new_context()
        second = browser.new_context()
        page_a, page_b = first.new_page(), second.new_page()
        login(page_a, "author1")
        login(page_b, "author1")
        draft_url = f"{BASE}/blogs/2/edit"
        page_a.goto(draft_url)
        page_b.goto(draft_url)
        assert page_a.locator('[name="version"]').input_value() == "1"
        assert page_b.locator('[name="version"]').input_value() == "1"
        page_a.get_by_label("Title", exact=True).fill("Browser A wins")
        with page_a.expect_response(
            lambda response: response.url == draft_url
            and response.request.method == "POST"
        ) as saved:
            page_a.get_by_role("button", name="Save draft").click()
        assert saved.value.status in {200, 302}
        page_b.get_by_label("Title", exact=True).fill("Browser B unsaved")
        with page_b.expect_response(
            lambda response: response.url == draft_url
            and response.request.method == "POST"
        ) as conflicted:
            page_b.get_by_role("button", name="Save draft").click()
        assert conflicted.value.status == 409
        page_b.wait_for_timeout(500)
        assert page_b.locator('[role="alert"]').is_visible()
        assert "newer version" in page_b.locator('[role="alert"]').inner_text().lower()
        assert page_b.get_by_label("Title", exact=True).input_value() == "Browser B unsaved"
        assert page_b.locator('[name="version"]').input_value() == "1"
        assert page_b.locator('[role="alert"]').evaluate(
            "(node) => document.activeElement === node"
        )
        report["conflict"] += 5
        axe_gate(page_b)
        report["axe_pages"] += 1

        # Blocked API identity: Website login succeeds, API write fails closed.
        blocked = browser.new_context()
        blocked_page = blocked.new_page()
        login(blocked_page, "blocked")
        blocked_page.goto(f"{BASE}/blogs/write")
        blocked_page.get_by_label("Title", exact=True).fill("Must not persist")
        blocked_page.get_by_role("button", name="Save draft").click()
        blocked_page.wait_for_load_state("domcontentloaded")
        assert "unavailable" in blocked_page.locator("body").inner_text().lower()

        storage = page.evaluate(
            "() => ({local:{...localStorage},session:{...sessionStorage},cookie:document.cookie})"
        )
        assert "phase1d-continuation" not in json.dumps(storage)
        assert not report["direct_blog_api"]
        assert not report["console_errors"], report["console_errors"]
        for ctx in (context, first, second, blocked):
            ctx.close()
        browser.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
