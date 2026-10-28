"""Collect fresh browser runtime metadata for the retained 130-image matrix."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from phase1d_visual_manifest import STATE_NAMES, URLS


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "docs/evidence/community_blog_phase1d_visual_runtime_metrics.json"
BASE = "http://127.0.0.1:5510"
STATES = tuple((state, URLS[state]) for state in STATE_NAMES)
VIEWPORTS = {
    "360x800": (360, 800),
    "390x844": (390, 844),
    "768x1024": (768, 1024),
    "1024x768": (1024, 768),
    "1440x900": (1440, 900),
}


def login(page, username):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")
    assert "/login" not in page.url


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    metrics = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None,
        )
        context = browser.new_context()
        page = context.new_page()
        page.route("https://media.invalid/**", lambda route: route.abort())
        login(page, "author1")
        active_identity = "author1"

        for state, path in STATES:
            required_identity = (
                "moderator" if state.startswith("moderation")
                else "anonymous" if state == "login-required"
                else "author1"
            )
            if required_identity != active_identity:
                context.clear_cookies()
                if required_identity != "anonymous":
                    login(page, required_identity)
                active_identity = required_identity

            for viewport, (width, height) in VIEWPORTS.items():
                page.set_viewport_size({"width": width, "height": height})
                response = page.goto(BASE + path, wait_until="domcontentloaded")
                assert response is None or response.status < 500, (
                    state, viewport, None if response is None else response.status
                )
                page.wait_for_timeout(150)
                values = page.evaluate(
                    """() => {
                      const root = document.documentElement;
                      return {
                        scroll_width: root.scrollWidth,
                        client_width: root.clientWidth,
                        scroll_height: root.scrollHeight,
                        client_height: root.clientHeight,
                        inner_width: window.innerWidth,
                        inner_height: window.innerHeight,
                        device_pixel_ratio: window.devicePixelRatio,
                        url: window.location.pathname + window.location.search +
                             window.location.hash,
                      };
                    }"""
                )
                values.update({
                    "state_name": state,
                    "viewport": viewport,
                    "viewport_width": width,
                    "viewport_height": height,
                    "fixture_identity": state,
                    "fixture_user": required_identity,
                    "horizontal_overflow": (
                        values["scroll_width"] > values["client_width"]
                    ),
                    "measured_at": datetime.now(timezone.utc).isoformat(),
                })
                assert values["client_width"] == width, (state, viewport, values)
                assert not values["horizontal_overflow"], (state, viewport, values)
                metrics[f"{state}-{viewport}"] = values

        context.close()
        browser.close()

    assert len(metrics) == 130
    OUTPUT.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "runtime_measurements": len(metrics),
        "horizontal_overflow_failures": sum(
            value["horizontal_overflow"] for value in metrics.values()
        ),
        "output": str(OUTPUT),
    }, indent=2))


if __name__ == "__main__":
    run()
