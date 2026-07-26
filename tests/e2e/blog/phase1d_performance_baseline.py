"""Local-only five-run browser performance and resource baseline."""
import json
import io
import math
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import psutil
import psycopg2
from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:5510"
DB = "postgresql://riteshkumar@127.0.0.1:55432/ampyan_blog_phase1d_final"
RAW = ROOT / "docs/evidence/community_blog_phase1d_performance_raw.json"
SUMMARY = ROOT / "docs/evidence/community_blog_phase1d_performance_summary.md"
CYCLES = ROOT / "docs/evidence/community_blog_phase1d_resource_cycles.json"
CHROME = os.environ.get("PHASE1D_CHROME_PATH")


def login(page, username):
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill("Phase1dPass!9")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("domcontentloaded")
    assert "/login" not in page.url


def process_rss(pid):
    try:
        return psutil.Process(int(pid)).memory_info().rss
    except (psutil.Error, TypeError, ValueError):
        return None


def postgres_connections():
    with psycopg2.connect(DB) as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database()"
        )
        return cursor.fetchone()[0]


def browser_rss():
    process = psutil.Process()
    descendants = process.children(recursive=True)
    return sum(
        child.memory_info().rss
        for child in descendants
        if "chrome" in child.name().lower()
    )


def page_metrics(page):
    navigation = page.evaluate(
        """() => {
          const n=performance.getEntriesByType('navigation')[0];
          return n ? {
            dom_content_loaded_ms:n.domContentLoadedEventEnd,
            load_event_ms:n.loadEventEnd,
            main_document_duration_ms:n.duration,
            transferred_bytes:n.transferSize,
          } : {};
        }"""
    )
    resources = page.evaluate(
        """() => {
          const rows=performance.getEntriesByType('resource');
          return {
            resource_count:rows.length,
            resource_transferred_bytes:rows.reduce((n,r)=>n+(r.transferSize||0),0),
            dom_nodes:document.getElementsByTagName('*').length,
            object_urls:performance.getEntriesByType('resource')
              .filter(r=>r.name.startsWith('blob:')).length,
          };
        }"""
    )
    cdp = page.context.new_cdp_session(page)
    cdp.send("Performance.enable")
    values = {
        row["name"]: row["value"]
        for row in cdp.send("Performance.getMetrics")["metrics"]
    }
    cdp.detach()
    return {
        **navigation,
        **resources,
        "js_heap_used": values.get("JSHeapUsedSize"),
        "event_listeners": values.get("JSEventListeners"),
        "layout_count": values.get("LayoutCount"),
        "layout_duration_ms": (
            values.get("LayoutDuration", 0) * 1000
            if values.get("LayoutDuration") is not None else None
        ),
        "long_task_observations": page.evaluate(
            "() => performance.getEntriesByType('longtask').length"
        ),
        "layout_shift_observations": page.evaluate(
            "() => performance.getEntriesByType('layout-shift').length"
        ),
    }


def measurement(page, scenario, run_number, action):
    requests, failed, responses = [], [], []
    console_errors, page_errors = [], []
    def on_request(request):
        requests.append((request.method, request.url, request.resource_type))
    def on_failed(request):
        failed.append(request.url)
    def on_response(response):
        responses.append((response.request.method, response.url, response.status))
    def on_console(message):
        if (
            message.type == "error"
            and "ERR_NAME_NOT_RESOLVED" not in message.text
            and "ERR_FAILED" not in message.text
        ):
            console_errors.append(message.text)
    def on_page_error(error):
        page_errors.append(str(error))
    page.on("request", on_request)
    page.on("requestfailed", on_failed)
    page.on("response", on_response)
    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    rss_before = browser_rss()
    heap_before = page_metrics(page).get("js_heap_used") if page.url != "about:blank" else None
    started = time.perf_counter()
    mutation_ms = action()
    elapsed = (time.perf_counter() - started) * 1000
    page.wait_for_timeout(100)
    metrics = page_metrics(page)
    duplicates = len(requests) - len(set((method, url) for method, url, _ in requests))
    api_durations = [
        float(value)
        for response in responses
        if "127.0.0.1:5520" in response[1]
        for value in [response[2] if False else 0]
    ]
    result = {
        "scenario": scenario,
        "run_number": run_number,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        **metrics,
        "main_api_duration_ms": max(api_durations) if api_durations else None,
        "mutation_duration_ms": mutation_ms,
        "wall_duration_ms": round(elapsed, 3),
        "total_request_count": len(requests),
        "failed_request_count": len(failed),
        "failed_request_urls": failed,
        "duplicate_request_count": duplicates,
        "transferred_bytes": (
            metrics.get("transferred_bytes", 0)
            + metrics.get("resource_transferred_bytes", 0)
        ),
        "console_errors": console_errors,
        "page_errors": page_errors,
        "js_heap_before": heap_before,
        "js_heap_after": metrics.get("js_heap_used"),
        "browser_rss_before": rss_before,
        "browser_rss_after": browser_rss(),
        "website_rss": process_rss(os.environ.get("PHASE1D_WEBSITE_PID")),
        "api_rss": process_rss(os.environ.get("PHASE1D_API_PID")),
        "postgresql_connection_count": postgres_connections(),
    }
    page.remove_listener("request", on_request)
    page.remove_listener("requestfailed", on_failed)
    page.remove_listener("response", on_response)
    page.remove_listener("console", on_console)
    page.remove_listener("pageerror", on_page_error)
    return result


def goto(page, path):
    def action():
        target = path
        fragment = ""
        if "#" in target:
            target, fragment = target.split("#", 1)
            fragment = "#" + fragment
        separator = "&" if "?" in target else "?"
        page.goto(
            BASE + target + separator + "_phase1d_run=" + str(time.time_ns()) + fragment,
            wait_until="domcontentloaded",
        )
        return None
    return action


def editor_save(page):
    def action():
        page.goto(BASE + "/blogs/2/edit", wait_until="domcontentloaded")
        page.locator('[name="subtitle"]').fill(f"Measured {time.time_ns()}")
        started = time.perf_counter()
        with page.expect_navigation(wait_until="domcontentloaded"):
            page.get_by_role("button", name="Save draft").click()
        return round((time.perf_counter() - started) * 1000, 3)
    return action


def fake_media(page):
    def action():
        page.goto(BASE + "/blogs/2/edit", wait_until="domcontentloaded")
        image_output = io.BytesIO()
        Image.new("RGB", (8, 8), (210, 30, 40)).save(
            image_output, format="PNG"
        )
        page.get_by_label("Blog image").set_input_files({
            "name": "phase1d-performance.png",
            "mimeType": "image/png",
            "buffer": image_output.getvalue(),
        })
        started = time.perf_counter()
        page.get_by_role("button", name="Upload and add image block").click()
        page.wait_for_function(
            "() => document.querySelector('[data-media-status]').textContent !== 'Uploading…'"
        )
        assert page.locator("[data-media-status]").inner_text() == "Image added."
        return round((time.perf_counter() - started) * 1000, 3)
    return action


def create_and_submit(page):
    page.goto(BASE + "/blogs/write", wait_until="domcontentloaded")
    page.locator('[name="title"]').fill(f"Performance Submit {time.time_ns()}")
    page.locator("[data-new-block-type]").select_option("paragraph")
    page.get_by_role("button", name="Add block").click()
    page.get_by_label("Text").fill("Measured content")
    with page.expect_navigation(wait_until="domcontentloaded"):
        page.get_by_role("button", name="Save draft").click()
    edit_url = page.url
    blog_id = int(edit_url.split("/blogs/")[1].split("/")[0])
    page.goto(BASE + "/blogs/me", wait_until="domcontentloaded")
    row = page.locator(".blog-dashboard-row").filter(
        has_text="Performance Submit"
    ).first
    started = time.perf_counter()
    with page.expect_navigation(wait_until="domcontentloaded"):
        row.get_by_role("button", name="Submit").click()
    return blog_id, round((time.perf_counter() - started) * 1000, 3)


def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    rows, cycles = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME or None)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.route("https://media.invalid/**", lambda route: route.abort())
        login(page, "author1")

        static = (
            ("Blog listing", "/blogs"),
            ("Paginated listing", "/blogs?sort=latest"),
            ("Published detail", "/blogs/phase1d-published"),
            ("Long rich article", "/blogs/phase1d-rich"),
            ("Article with comments", "/blogs/phase1d-published#comments"),
            ("Empty editor", "/blogs/write"),
            ("Populated editor", "/blogs/2/edit"),
            ("My Blogs", "/blogs/me"),
            ("Analytics", "/blogs/me/analytics"),
        )
        for scenario, path in static:
            goto(page, path)()  # warm-up
            for number in range(1, 6):
                rows.append(measurement(page, scenario, number, goto(page, path)))

        for scenario in ("Save draft", "Update draft"):
            editor_save(page)()
            for number in range(1, 6):
                rows.append(measurement(page, scenario, number, editor_save(page)))

        submitted = []
        submitted.append(create_and_submit(page)[0])  # warm-up
        for number in range(1, 6):
            holder = {}
            def submit_action():
                blog_id, duration = create_and_submit(page)
                holder["blog_id"] = blog_id
                return duration
            rows.append(measurement(page, "Submit for review", number, submit_action))
            submitted.append(holder["blog_id"])

        context.clear_cookies()
        login(page, "moderator")
        goto(page, "/blogs/moderation")()
        for number in range(1, 6):
            rows.append(measurement(
                page, "Moderation queue", number, goto(page, "/blogs/moderation")
            ))

        for index, blog_id in enumerate(submitted):
            page.goto(BASE + "/blogs/moderation", wait_until="domcontentloaded")
            row = page.locator(".blog-dashboard-row").filter(
                has=page.locator(f'form[action="/blogs/{blog_id}/moderate"]')
            )
            def moderate_action(row=row):
                started = time.perf_counter()
                with page.expect_navigation(wait_until="domcontentloaded"):
                    row.get_by_role("button", name="Apply").click()
                return round((time.perf_counter() - started) * 1000, 3)
            if index == 0:
                moderate_action()
            else:
                rows.append(measurement(
                    page, "Moderation action", index, moderate_action
                ))

        context.clear_cookies()
        login(page, "author1")
        fake_media(page)()
        for number in range(1, 6):
            rows.append(measurement(page, "Fake-media upload", number, fake_media(page)))

        assert len(rows) == 75, len(rows)

        flows = (
            ("reader", "reader2", "/blogs/phase1d-published", 6),
            ("author", "author1", "/blogs/2/edit", 5),
            ("moderator", "moderator", "/blogs/moderation", 5),
            ("fake-media", "author1", "/blogs/2/edit", 4),
        )
        for flow, username, path, cycle_count in flows:
            context.clear_cookies()
            login(page, username)
            for number in range(1, cycle_count + 1):
                before = page_metrics(page)
                rss_before = browser_rss()
                if flow == "fake-media":
                    fake_media(page)()
                else:
                    page.goto(BASE + path, wait_until="domcontentloaded")
                page.wait_for_timeout(50)
                cdp = page.context.new_cdp_session(page)
                cdp.send("HeapProfiler.collectGarbage")
                cdp.detach()
                after = page_metrics(page)
                cycles.append({
                    "flow": flow,
                    "cycle": number,
                    "js_heap_before": before.get("js_heap_used"),
                    "js_heap_after": after.get("js_heap_used"),
                    "browser_rss_before": rss_before,
                    "browser_rss_after": browser_rss(),
                    "website_rss": process_rss(os.environ.get("PHASE1D_WEBSITE_PID")),
                    "api_rss": process_rss(os.environ.get("PHASE1D_API_PID")),
                    "dom_nodes": after.get("dom_nodes"),
                    "event_listeners": after.get("event_listeners"),
                    "object_urls": after.get("object_urls"),
                    "request_count": after.get("resource_count"),
                    "postgresql_connection_count": postgres_connections(),
                })

        context.close()
        browser.close()

    RAW.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    CYCLES.write_text(json.dumps(cycles, indent=2), encoding="utf-8")
    lines = [
        "# Community Blog Phase 1D local performance baseline",
        "",
        "This is a local browser regression and resource baseline, not a production load test.",
        "",
        "| Scenario | Runs | Min ms | Max ms | Mean ms | Median ms | Std dev | p95 | Variation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in dict.fromkeys(row["scenario"] for row in rows):
        values = [row["wall_duration_ms"] for row in rows if row["scenario"] == scenario]
        ordered = sorted(values)
        mean = statistics.mean(values)
        p95 = ordered[min(len(ordered) - 1, math.ceil(.95 * len(ordered)) - 1)]
        variation = ((max(values) - min(values)) / mean * 100) if mean else 0
        lines.append(
            f"| {scenario} | {len(values)} | {min(values):.2f} | {max(values):.2f} | "
            f"{mean:.2f} | {statistics.median(values):.2f} | "
            f"{statistics.pstdev(values):.2f} | {p95:.2f} | {variation:.2f}% |"
        )
    lines += [
        "", f"- Measured runs: **{len(rows)}**",
        f"- Resource cycles: **{len(cycles)}**",
        f"- Failed requests: **{sum(row['failed_request_count'] for row in rows)}**",
        f"- Console errors: **{sum(len(row['console_errors']) for row in rows)}**",
        f"- Page errors: **{sum(len(row['page_errors']) for row in rows)}**",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "scenarios": len(set(row["scenario"] for row in rows)),
        "measured_runs": len(rows),
        "resource_cycles": len(cycles),
        "failed_requests": sum(row["failed_request_count"] for row in rows),
        "console_errors": sum(len(row["console_errors"]) for row in rows),
        "page_errors": sum(len(row["page_errors"]) for row in rows),
    }, indent=2))


if __name__ == "__main__":
    run()
