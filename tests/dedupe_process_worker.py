"""One isolated Gunicorn-like process for the local database dedupe check."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask
from models.models import db
from services.analytics_service import _insert_payload


def main():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = sys.argv[1]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        _insert_payload({
            "_kind": "event", "event_type": "share_clicked",
            "_dedupe_key": sys.argv[2], "session_id": "a" * 32,
            "metadata_json": '{"content_type":"blog","schema_version":1}',
        })


if __name__ == "__main__":
    main()
