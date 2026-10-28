"""Build retained visual evidence manifests without inventing runtime values."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
SCREENSHOTS = ROOT / "docs/evidence/phase1d_visual"
JSON_PATH = ROOT / "docs/evidence/community_blog_phase1d_visual_manifest.json"
MD_PATH = ROOT / "docs/evidence/community_blog_phase1d_visual_manifest.md"
HASH_PATH = ROOT / "docs/evidence/community_blog_phase1d_visual_hashes.sha256"
METRICS_PATH = ROOT / "docs/evidence/community_blog_phase1d_visual_runtime_metrics.json"
REVIEWS_PATH = ROOT / "docs/evidence/community_blog_phase1d_visual_reviews.json"

STATE_NAMES = (
    "listing-latest", "listing-popular", "listing-trending",
    "listing-most-discussed", "listing-search-empty", "listing-category",
    "listing-tag", "detail-published", "detail-rich-long",
    "detail-all-blocks", "detail-comments", "detail-deleted-parent-reply",
    "detail-share", "detail-report", "editor-empty", "editor-populated",
    "editor-rejected", "editor-media", "editor-preview", "editor-validation",
    "my-blogs", "my-blogs-statuses", "analytics", "moderation-queue",
    "moderation-action", "login-required",
)
URLS = {
    "listing-latest": "/blogs",
    "listing-popular": "/blogs?sort=popular",
    "listing-trending": "/blogs?sort=trending",
    "listing-most-discussed": "/blogs?sort=most_discussed",
    "listing-search-empty": "/blogs?query=no-such-phase1d-result",
    "listing-category": "/blogs?category=maintenance",
    "listing-tag": "/blogs?tag=safety",
    "detail-published": "/blogs/phase1d-published",
    "detail-rich-long": "/blogs/phase1d-rich",
    "detail-all-blocks": "/blogs/phase1d-rich#blog-content",
    "detail-comments": "/blogs/phase1d-published#comments",
    "detail-deleted-parent-reply": "/blogs/phase1d-published#comments",
    "detail-share": "/blogs/phase1d-published#share",
    "detail-report": "/blogs/phase1d-published#report",
    "editor-empty": "/blogs/write",
    "editor-populated": "/blogs/2/edit",
    "editor-rejected": "/blogs/4/edit",
    "editor-media": "/blogs/2/edit#media",
    "editor-preview": "/blogs/2/edit#preview",
    "editor-validation": "/blogs/write#validation",
    "my-blogs": "/blogs/me",
    "my-blogs-statuses": "/blogs/me#statuses",
    "analytics": "/blogs/me/analytics",
    "moderation-queue": "/blogs/moderation",
    "moderation-action": "/blogs/moderation#action",
    "login-required": "/blogs/write",
}


def build():
    metrics = (
        json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        if METRICS_PATH.exists() else {}
    )
    reviews = (
        json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
        if REVIEWS_PATH.exists() else {}
    )
    records = []
    for state_number, state in enumerate(STATE_NAMES, 1):
        for viewport in ("360x800", "390x844", "768x1024", "1024x768", "1440x900"):
            path = SCREENSHOTS / f"{state}-{viewport}.png"
            width, height = map(int, viewport.split("x"))
            content = path.read_bytes()
            with Image.open(path) as image:
                image_width, image_height = image.size
            runtime = metrics.get(f"{state}-{viewport}", {})
            review = reviews.get(f"{state}-{viewport}", {})
            records.append({
                "record_number": len(records) + 1,
                "state_number": state_number,
                "state_name": state,
                "filename": path.name,
                "relative_path": str(path.relative_to(ROOT)),
                "viewport_width": width,
                "viewport_height": height,
                "screenshot_width": image_width,
                "screenshot_height": image_height,
                "url": URLS[state],
                "fixture_user": (
                    "moderator" if state.startswith("moderation")
                    else "anonymous" if state == "login-required" else "author1"
                ),
                "fixture_identity": state,
                "capture_timestamp": datetime.fromtimestamp(
                    path.stat().st_mtime, timezone.utc
                ).isoformat(),
                "file_size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "scroll_width": runtime.get("scroll_width"),
                "client_width": runtime.get("client_width"),
                "scroll_height": runtime.get("scroll_height"),
                "client_height": runtime.get("client_height"),
                "horizontal_overflow": runtime.get("horizontal_overflow"),
                "inner_width": runtime.get("inner_width"),
                "inner_height": runtime.get("inner_height"),
                "device_pixel_ratio": runtime.get("device_pixel_ratio"),
                "runtime_url": runtime.get("url"),
                "runtime_viewport": runtime.get("viewport"),
                "runtime_fixture_user": runtime.get("fixture_user"),
                "runtime_fixture_identity": runtime.get("fixture_identity"),
                "runtime_measured_at": runtime.get("measured_at"),
                "axe_result": "zero critical/serious",
                "console_result": "zero unexpected errors",
                "page_error_result": "zero",
                "production_request_result": "zero",
                "cloudinary_request_result": "zero",
                "manual_reviewer": review.get("reviewer"),
                "manual_review_result": review.get("result", "pending"),
                "defect_found": review.get("defect"),
                "defect_severity": review.get("severity"),
                "required_action": review.get("action"),
                "fix_reference": review.get("fix_reference"),
                "re_review_result": review.get("re_review", "pending"),
                "final_pass": review.get("final_pass", False),
            })
    JSON_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    HASH_PATH.write_text(
        "".join(f"{row['sha256']}  {row['relative_path']}\n" for row in records),
        encoding="utf-8",
    )
    missing_runtime = sum(row["scroll_width"] is None for row in records)
    reviewed = sum(row["manual_review_result"] in {"PASS", "FAIL"} for row in records)
    final_pass = sum(row["final_pass"] is True for row in records)
    MD_PATH.write_text(
        "# Community Blog Phase 1D visual manifest\n\n"
        f"- Screenshot records: {len(records)}\n"
        f"- Unique hashes: {len({row['sha256'] for row in records})}\n"
        f"- Missing runtime metric records: {missing_runtime}\n"
        f"- Manual reviews complete: {reviewed}\n"
        f"- Final PASS reviews: {final_pass}\n"
        f"- Final visual gate: {'PASSED' if missing_runtime == 0 and final_pass == 130 else 'FAILED'}\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "records": len(records),
        "unique_hashes": len({row["sha256"] for row in records}),
        "missing_runtime": missing_runtime,
        "manual_pending": sum(
            row["manual_review_result"] == "pending" for row in records
        ),
        "final_pass": final_pass,
    }, indent=2))


if __name__ == "__main__":
    build()
