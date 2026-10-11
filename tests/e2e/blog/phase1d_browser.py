"""Disposable Phase 1D Chromium gate.

Run only against the explicitly local staging stack. Generated screenshots go
to /tmp and are not production assets.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright


BASE = os.environ.get("PHASE1D_WEBSITE_URL", "http://127.0.0.1:5510")
ARTIFACTS = Path(os.environ.get("PHASE1D_ARTIFACTS", "/tmp/ampyan_phase1d_artifacts"))
VIEWPORTS = {
    "mobile-360": (360, 800),
    "mobile-390": (390, 844),
    "tablet-768": (768, 1024),
    "desktop-1024": (1024, 768),
    "desktop-1440": (1440, 900),
}
LOCAL_HOSTS = {"127.0.0.1:5510"}


def check_page(page, label, axe):
    # Let the existing intersection-based fade-in complete before measuring
    # rendered contrast; otherwise axe can sample an intentional transition.
    page.wait_for_timeout(500)
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, f"{label}: horizontal page overflow"
    assert "phase1d-7f83" not in page.content(), f"{label}: service token in HTML"
    results = axe.run(page)
    serious = [
        issue for issue in results.response["violations"]
        if issue["impact"] in {"critical", "serious"}
    ]
    assert not serious, f"{label}: axe violations {[(x['id'], x['impact']) for x in serious]}"


def login(page, username):
    page.goto(f"{BASE}/login")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")
    assert "/login" not in page.url


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report = {"viewports": {}, "requests": [], "console_errors": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None,
        )
        version = browser.version
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        axe = Axe()

        def request_seen(request):
            report["requests"].append(request.url)
            host = urlparse(request.url).netloc
            if host and host not in LOCAL_HOSTS:
                report.setdefault("external_static_hosts", [])
                if host not in report["external_static_hosts"]:
                    report["external_static_hosts"].append(host)
                if host.endswith("ampyan.com") or "cloudinary" in host:
                    report.setdefault("unexpected_hosts", []).append(host)

        def console_seen(message):
            if message.type != "error":
                return
            text = message.text
            # axe inspects cross-origin stylesheets via fetch; the application's
            # CSP correctly blocks those analyzer-only connect attempts.
            if (
                "violates the following Content Security Policy directive" in text
                and ("fonts.googleapis.com" in text or "cdnjs.cloudflare.com" in text)
            ):
                report.setdefault("axe_csp_diagnostics", 0)
                report["axe_csp_diagnostics"] += 1
                return
            report["console_errors"].append(text)

        page.on("request", request_seen)
        page.on("console", console_seen)
        page.on(
            "pageerror",
            lambda error: report["console_errors"].append(str(error)),
        )

        # Public and mandatory responsive matrix.
        for name, (width, height) in VIEWPORTS.items():
            page.set_viewport_size({"width": width, "height": height})
            page.goto(f"{BASE}/blogs")
            page.wait_for_load_state("domcontentloaded")
            check_page(page, f"listing-{name}", axe)
            page.screenshot(path=str(ARTIFACTS / f"listing-{name}.png"), full_page=True)
            report["viewports"][name] = "passed"

        # Keyboard-only author draft workflow.
        page.set_viewport_size({"width": 390, "height": 844})
        login(page, "author1")
        page.goto(f"{BASE}/blogs/write")
        check_page(page, "editor-empty", axe)
        page.get_by_label("Title", exact=True).fill("Phase 1D सुरक्षित Editor 🚗")
        page.get_by_label("Subtitle").fill("Disposable browser validation")
        page.get_by_label("Block type").select_option("paragraph")
        page.get_by_role("button", name="Add block").press("Enter")
        page.get_by_label("Text").fill("Hindi हिन्दी, emoji 🚘 and script alert as plain text")
        page.get_by_label("Block type").select_option("heading")
        page.get_by_role("button", name="Add block").press("Enter")
        page.get_by_label("Text").nth(1).fill("A very long heading " + ("word " * 25))
        page.get_by_role("button", name="Move up").nth(1).press("Enter")
        page.get_by_role("button", name="Preview").press("Enter")
        assert page.locator("[data-blog-preview]").inner_text()
        page.get_by_role("button", name="Save draft").press("Enter")
        page.wait_for_url("**/blogs/*/edit")
        edit_url = page.url
        check_page(page, "editor-saved", axe)
        page.screenshot(path=str(ARTIFACTS / "editor-mobile-390.png"), full_page=True)
        stable_ids = page.locator("[data-block-json]").input_value()
        assert '"id":' in stable_ids and "हिन्दी" in stable_ids

        # Submit and verify author pages.
        page.goto(f"{BASE}/blogs/me")
        check_page(page, "my-blogs", axe)
        page.get_by_role("button", name="Submit").click()
        page.wait_for_load_state("domcontentloaded")
        page.goto(f"{BASE}/blogs/me/analytics")
        check_page(page, "analytics", axe)
        assert "noindex" in page.locator('meta[name="robots"]').get_attribute("content")

        # Moderator queue and publish.
        page.locator(".user-button").click()
        page.locator('form[action="/logout"] button').click()
        login(page, "moderator")
        page.goto(f"{BASE}/blogs/moderation")
        check_page(page, "moderation", axe)
        page.screenshot(path=str(ARTIFACTS / "moderation-390.png"), full_page=True)
        page.get_by_label("Action").select_option("approve")
        page.get_by_role("button", name="Apply").click()
        page.wait_for_load_state("domcontentloaded")

        # Published content remains escaped and responsive.
        page.goto(f"{BASE}/blogs")
        page.get_by_role("link", name="Phase 1D सुरक्षित Editor 🚗").click()
        page.wait_for_load_state("domcontentloaded")
        assert "हिन्दी" in page.locator(".blog-content").inner_text()
        for name, (width, height) in VIEWPORTS.items():
            page.set_viewport_size({"width": width, "height": height})
            check_page(page, f"detail-{name}", axe)
            page.screenshot(path=str(ARTIFACTS / f"detail-{name}.png"), full_page=True)

        # Browser-side security storage/network inspection.
        storage = page.evaluate(
            """() => ({
              local: Object.assign({}, localStorage),
              session: Object.assign({}, sessionStorage),
              cookies: document.cookie
            })"""
        )
        assert "phase1d-7f83" not in json.dumps(storage)
        assert not report.get("unexpected_hosts"), report.get("unexpected_hosts")
        assert not [
            url for url in report["requests"]
            if "/api/v1/blogs" in url or "api.ampyan.com" in url
        ]
        assert not report["console_errors"], report["console_errors"]
        context.close()
        browser.close()
    report["chromium"] = version
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
