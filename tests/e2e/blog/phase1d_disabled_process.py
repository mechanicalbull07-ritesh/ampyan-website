"""Separate-process feature-disabled browser/API gate."""
import json
import os

import requests
from playwright.sync_api import sync_playwright


def run():
    report = {"website_404": 0, "api_disabled": 0, "navigation": 0}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, executable_path=os.environ.get("PHASE1D_CHROME_PATH") or None
        )
        page = browser.new_page()
        for path in ("/blogs", "/blogs/write", "/blogs/1/edit", "/blogs/moderation"):
            response = page.goto("http://127.0.0.1:5511" + path)
            assert response.status == 404
            report["website_404"] += 1
        page.goto("http://127.0.0.1:5511/")
        assert page.locator('a[href="/blogs"]').count() == 0
        assert page.locator("body").is_visible()
        report["navigation"] += 2
        browser.close()

    for method, path in (
        ("GET", "/api/v1/blogs"),
        ("POST", "/api/v1/blogs"),
        ("GET", "/api/v1/blogs/moderation"),
        ("POST", "/api/v1/blogs/1/comments"),
        ("POST", "/api/v1/blogs/media"),
    ):
        response = requests.request(
            method, "http://127.0.0.1:5521" + path, timeout=5,
            headers={
                "X-AMPYAN-BLOG-SERVICE-TOKEN": "phase1d-disabled-token",
                "X-AMPYAN-BLOG-USER-ID": "1",
            },
            json={} if method == "POST" else None,
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "BLOG_FEATURE_DISABLED"
        report["api_disabled"] += 2
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
