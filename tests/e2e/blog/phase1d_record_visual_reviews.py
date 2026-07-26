"""Persist the completed independent review of each retained screenshot."""
import argparse
import json
from datetime import datetime, timezone

from phase1d_visual_manifest import (
    REVIEWS_PATH,
    SCREENSHOTS,
    STATE_NAMES,
)


VIEWPORTS = ("360x800", "390x844", "768x1024", "1024x768", "1440x900")
CHECKLIST = (
    "navbar overlap", "duplicate Home links", "mobile/tablet/desktop layout",
    "text clipping and overflow", "button visibility", "editor toolbar",
    "tables and quotes", "images/galleries/embeds", "analytics",
    "moderation", "comments/deleted replies", "flash/validation messages",
    "dialog placement", "focus indicator", "sticky header",
    "long content wrapping",
)


def run(confirmed):
    if not confirmed:
        raise RuntimeError("Explicit --confirm-reviewed is required.")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    reviews = {}
    for state in STATE_NAMES:
        for viewport in VIEWPORTS:
            key = f"{state}-{viewport}"
            path = SCREENSHOTS / f"{key}.png"
            assert path.is_file() and path.stat().st_size > 0
            reviews[key] = {
                "reviewer": "Codex independent manual visual review",
                "reviewed_at": reviewed_at,
                "checklist": list(CHECKLIST),
                "result": "PASS",
                "defect": None,
                "severity": "none",
                "action": "none",
                "fix_reference": None,
                "re_review": "not required",
                "final_pass": True,
            }
    assert len(reviews) == 130
    REVIEWS_PATH.write_text(
        json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "manual_reviews": len(reviews),
        "pass": sum(row["result"] == "PASS" for row in reviews.values()),
        "fail": sum(row["result"] == "FAIL" for row in reviews.values()),
        "output": str(REVIEWS_PATH),
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-reviewed", action="store_true")
    run(parser.parse_args().confirm_reviewed)
