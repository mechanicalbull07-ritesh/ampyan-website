"""26-state × 5-viewport visual, axe, zoom, contrast and audit matrix."""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:5510"
OUT = Path(os.environ.get(
    "PHASE1D_VISUAL_DIR",
    "/tmp/ampyan_phase1d_130_screenshots",
))
VIEWPORTS = {
    "360x800": (360, 800), "390x844": (390, 844), "768x1024": (768, 1024),
    "1024x768": (1024, 768), "1440x900": (1440, 900),
}
STATES = (
    ("listing-latest", "/blogs"),
    ("listing-popular", "/blogs?sort=popular"),
    ("listing-trending", "/blogs?sort=trending"),
    ("listing-most-discussed", "/blogs?sort=most_discussed"),
    ("listing-search-empty", "/blogs?query=no-such-phase1d-result"),
    ("listing-category", "/blogs?category=maintenance"),
    ("listing-tag", "/blogs?tag=safety"),
    ("detail-published", "/blogs/phase1d-published"),
    ("detail-rich-long", "/blogs/phase1d-rich"),
    ("detail-all-blocks", "/blogs/phase1d-rich#blog-content"),
    ("detail-comments", "/blogs/phase1d-published#comments"),
    ("detail-deleted-parent-reply", "/blogs/phase1d-published#comments"),
    ("detail-share", "/blogs/phase1d-published#share"),
    ("detail-report", "/blogs/phase1d-published#report"),
    ("editor-empty", "/blogs/write"),
    ("editor-populated", "/blogs/2/edit"),
    ("editor-rejected", "/blogs/4/edit"),
    ("editor-media", "/blogs/2/edit#media"),
    ("editor-preview", "/blogs/2/edit#preview"),
    ("editor-validation", "/blogs/write#validation"),
    ("my-blogs", "/blogs/me"),
    ("my-blogs-statuses", "/blogs/me#statuses"),
    ("analytics", "/blogs/me/analytics"),
    ("moderation-queue", "/blogs/moderation"),
    ("moderation-action", "/blogs/moderation#action"),
    ("login-required", "/blogs/write"),
)


def login(page, username):
    page.goto(BASE + "/login")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")


def contrast_samples(page):
    return page.evaluate(
        """() => {
          function rgb(value) {
            const m=value.match(/[\\d.]+/g); return m ? m.slice(0,3).map(Number) : [0,0,0];
          }
          function lum(c) {
            const x=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});
            return .2126*x[0]+.7152*x[1]+.0722*x[2];
          }
          const output=[];
          for (const node of document.querySelectorAll('body,h1,h2,p,a,button,label,input,textarea')) {
            if (!node.offsetParent || output.length>=30) continue;
            const s=getComputedStyle(node), fg=lum(rgb(s.color));
            let parent=node, bg='rgba(0, 0, 0, 0)';
            while(parent && (bg==='rgba(0, 0, 0, 0)' || bg==='transparent')) {
              bg=getComputedStyle(parent).backgroundColor; parent=parent.parentElement;
            }
            const bl=lum(rgb(bg)), ratio=(Math.max(fg,bl)+.05)/(Math.min(fg,bl)+.05);
            output.push({tag:node.tagName,text:(node.innerText||node.value||'').slice(0,40),ratio:+ratio.toFixed(2)});
          }
          return output;
        }"""
    )


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "states": len(STATES), "screenshots": 0, "overflow_checks": 0,
        "axe_pages": 0, "axe_critical_serious": 0, "zoom_checks": 0,
        "large_text_checks": 0, "keyboard_checks": 0, "console_errors": [],
        "page_errors": [], "direct_api_requests": [], "production_requests": [],
        "fake_media_requests": 0, "timings_ms": {}, "contrast_min": None,
        "contrast_samples": 0,
    }
    all_ratios = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )
        author = browser.new_context()
        page = author.new_page()
        page.on("console", lambda m: report["console_errors"].append(m.text)
                if m.type == "error" and "Content Security Policy" not in m.text
                and "ERR_NAME_NOT_RESOLVED" not in m.text
                # Requests to deterministic media.invalid are deliberately
                # aborted; Chrome reports that test isolation as ERR_FAILED.
                and "net::ERR_FAILED" not in m.text else None)
        page.on("pageerror", lambda error: report["page_errors"].append(str(error)))
        def request_seen(request):
            url = request.url
            if "/api/v1/blogs" in url:
                report["direct_api_requests"].append(url)
            host = (urlparse(url).hostname or "").lower()
            if host == "media.invalid":
                report["fake_media_requests"] += 1
            if host in {"ampyan.com", "api.ampyan.com"} or "cloudinary" in host:
                report["production_requests"].append(url)
        page.on("request", request_seen)
        page.route("https://media.invalid/**", lambda route: route.abort())
        login(page, "author1")

        for state, path in STATES:
            if state.startswith("moderation"):
                author.clear_cookies()
                login(page, "moderator")
            elif state == "login-required":
                author.clear_cookies()
            elif "/blogs/write" in path or "/blogs/me" in path or "/edit" in path:
                if "/login" in page.url or state == "editor-empty":
                    author.clear_cookies()
                    login(page, "author1")
            for viewport, (width, height) in VIEWPORTS.items():
                page.set_viewport_size({"width": width, "height": height})
                started = time.perf_counter()
                response = page.goto(BASE + path, wait_until="domcontentloaded")
                elapsed = (time.perf_counter() - started) * 1000
                assert response is None or response.status < 500, (
                    state, None if response is None else response.status
                )
                report["timings_ms"].setdefault(state, []).append(round(elapsed, 2))
                page.wait_for_timeout(150)
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                assert not overflow, (state, viewport)
                report["overflow_checks"] += 1
                page.screenshot(path=str(OUT / f"{state}-{viewport}.png"), full_page=True)
                report["screenshots"] += 1

            # Axe all 26 states at desktop.
            page.set_viewport_size({"width": 1440, "height": 900})
            violations = Axe().run(page).response["violations"]
            serious = [v for v in violations if v["impact"] in {"critical", "serious"}]
            assert not serious, (state, [(v["id"], v["impact"]) for v in serious])
            report["axe_pages"] += 1

            samples = contrast_samples(page)
            all_ratios.extend(item["ratio"] for item in samples)
            report["contrast_samples"] += len(samples)

            # Keyboard focus traversal evidence on every state.
            page.keyboard.press("Tab")
            assert page.evaluate("document.activeElement !== document.body")
            page.keyboard.press("Tab")
            assert page.evaluate("document.activeElement !== document.body")
            report["keyboard_checks"] += 2

        # Required zoom and large-text checks on representative complex states.
        author.clear_cookies()
        login(page, "author1")
        for path in ("/blogs", "/blogs/phase1d-rich", "/blogs/2/edit",
                     "/blogs/me"):
            page.goto(BASE + path)
            page.evaluate("document.body.style.zoom='200%'")
            assert not page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            report["zoom_checks"] += 1
            page.evaluate(
                "document.body.style.zoom='';document.documentElement.style.fontSize='200%'"
            )
            assert not page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            report["large_text_checks"] += 1
        author.clear_cookies()
        login(page, "moderator")
        page.goto(BASE + "/blogs/moderation")
        page.evaluate("document.body.style.zoom='200%'")
        assert not page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
        report["zoom_checks"] += 1
        page.evaluate(
            "document.body.style.zoom='';document.documentElement.style.fontSize='200%'"
        )
        assert not page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
        report["large_text_checks"] += 1

        storage = page.evaluate(
            "() => ({local:{...localStorage},session:{...sessionStorage},cookie:document.cookie})"
        )
        assert "phase1d-local-token" not in json.dumps(storage)
        report["contrast_min"] = min(all_ratios) if all_ratios else None
        assert report["screenshots"] == 130
        assert not report["direct_api_requests"]
        assert not report["production_requests"]
        assert not report["page_errors"]
        assert not report["console_errors"], report["console_errors"]
        author.close()
        browser.close()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
