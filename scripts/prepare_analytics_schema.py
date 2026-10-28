"""Additive analytics-only schema preflight for an isolated staging database.

Run once before enabling analytics traffic. Requires DATABASE_URL and SECRET_KEY.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if not os.environ.get("DATABASE_URL") or not os.environ.get("SECRET_KEY"):
    raise SystemExit("DATABASE_URL and SECRET_KEY are required")

from app import app  # noqa: E402
from services.analytics_service import ensure_analytics_schema  # noqa: E402

with app.app_context():
    if not ensure_analytics_schema():
        raise SystemExit("analytics schema preflight failed")
print("analytics schema preflight passed")
