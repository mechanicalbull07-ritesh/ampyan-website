"""One-time idempotent seed for admin-managed community personas.

This script is intentionally separate from app startup and request handling.
It does not run database initialization, migrations, create_all, or destructive
operations. Existing real users are never overwritten.
"""

from __future__ import annotations

import secrets
import sys
from argparse import ArgumentParser

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app import app
from models.models import User, db


PERSONAS = [
    {
        "username": "PuneAutoGuy",
        "email": "puneautoguy@ampyan.community",
        "city": "Pune",
        "badge": "Weekend Driver",
        "style": "Calm, technical but simple",
    },
    {
        "username": "BangaloreEVFan",
        "email": "bangaloreevfan@ampyan.community",
        "city": "Bengaluru",
        "badge": "EV User",
        "style": "EV focused, modern tone",
    },
    {
        "username": "HighwayDriver90",
        "email": "highwaydriver90@ampyan.community",
        "city": "Jaipur",
        "badge": "Highway Expert",
        "style": "Long-drive experience",
    },
    {
        "username": "GurgaonMechanic",
        "email": "gurgaonmechanic@ampyan.community",
        "city": "Gurugram",
        "badge": "Mechanic",
        "style": "Expert, practical advice",
    },
    {
        "username": "FirstTimeCarBuyer",
        "email": "firsttimecarbuyer@ampyan.community",
        "city": "Noida",
        "badge": "New Owner",
        "style": "Beginner questions",
    },
    {
        "username": "DailyCommuteUser",
        "email": "dailycommuteuser@ampyan.community",
        "city": "Mumbai",
        "badge": "City Commuter",
        "style": "Traffic/mileage focused",
    },
    {
        "username": "UsedCarAdvisor",
        "email": "usedcaradvisor@ampyan.community",
        "city": "Lucknow",
        "badge": "Used Car Guide",
        "style": "Smart buyer advice",
    },
    {
        "username": "ServiceCenterExpert",
        "email": "servicecenterexpert@ampyan.community",
        "city": "Chandigarh",
        "badge": "Service Expert",
        "style": "Detailed service advice",
    },
    {
        "username": "PetrolHeadIndia",
        "email": "petrolheadindia@ampyan.community",
        "city": "Hyderabad",
        "badge": "Enthusiast",
        "style": "Passionate auto lover",
    },
]


REQUIRED_COLUMNS = {
    "is_managed_persona",
    "managed_by_admin_id",
    "managed_note",
}


def set_short_timeouts() -> None:
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        db.session.execute(text("SET LOCAL lock_timeout = '1000ms'"))


def managed_persona_columns_exist() -> bool:
    if db.engine.dialect.name == "sqlite":
        rows = db.session.execute(text('PRAGMA table_info("user")')).fetchall()
        existing = {row[1] for row in rows}
    else:
        rows = db.session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'user'
                  AND column_name IN (
                    'is_managed_persona',
                    'managed_by_admin_id',
                    'managed_note'
                  )
                """
            )
        ).fetchall()
        existing = {row[0] for row in rows}

    missing = REQUIRED_COLUMNS - existing
    if missing:
        print(
            "managed_persona_seed_aborted missing_columns="
            + ",".join(sorted(missing)),
            flush=True,
        )
        return False
    return True


def seed_personas(apply_changes: bool = False) -> int:
    created = 0
    updated = 0
    skipped = 0

    set_short_timeouts()
    if not managed_persona_columns_exist():
        db.session.rollback()
        return 2

    for persona_data in PERSONAS:
        email = persona_data["email"].lower()
        username = persona_data["username"]
        note = f"Style: {persona_data['style']}"

        existing_by_email = User.query.filter_by(email=email).first()
        if existing_by_email:
            if not getattr(existing_by_email, "is_managed_persona", False):
                print(
                    f"managed_persona_skipped email={email} reason=real_user_exists",
                    flush=True,
                )
                skipped += 1
                continue

            username_owner = User.query.filter_by(username=username).first()
            if username_owner and username_owner.id != existing_by_email.id:
                print(
                    f"managed_persona_skipped email={email} reason=username_exists",
                    flush=True,
                )
                skipped += 1
                continue

            if apply_changes:
                existing_by_email.username = username
                existing_by_email.mobile = existing_by_email.mobile or ""
                existing_by_email.role = "user"
                existing_by_email.email_verified = True
                existing_by_email.is_banned = False
                existing_by_email.city = persona_data["city"]
                existing_by_email.country = existing_by_email.country or "India"
                existing_by_email.badge = persona_data["badge"]
                existing_by_email.managed_note = note
            updated += 1
            action = "updated" if apply_changes else "would_update"
            print(f"managed_persona_{action} email={email}", flush=True)
            continue

        username_owner = User.query.filter_by(username=username).first()
        if username_owner:
            print(
                f"managed_persona_skipped username={username} reason=username_exists",
                flush=True,
            )
            skipped += 1
            continue

        if apply_changes:
            user = User(
                username=username,
                email=email,
                mobile="",
                password=generate_password_hash(secrets.token_urlsafe(32)),
                role="user",
                email_verified=True,
                is_banned=False,
                city=persona_data["city"],
                country="India",
                badge=persona_data["badge"],
                reputation=0,
                posts_count=0,
                helpful_answers=0,
                contributor_score=0,
                is_managed_persona=True,
                managed_by_admin_id=None,
                managed_note=note,
            )
            db.session.add(user)
        created += 1
        action = "created" if apply_changes else "would_create"
        print(f"managed_persona_{action} email={email}", flush=True)

    if apply_changes:
        db.session.commit()
    else:
        db.session.rollback()
    print(
        "managed_persona_seed_completed "
        f"mode={'apply' if apply_changes else 'dry_run'} "
        f"created={created} updated={updated} skipped={skipped}",
        flush=True,
    )
    return 0


def main() -> int:
    parser = ArgumentParser(description="Seed AMPYAN managed community personas.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create/update personas. Without this flag the script is a dry run.",
    )
    args = parser.parse_args()

    with app.app_context():
        try:
            return seed_personas(apply_changes=args.apply)
        except Exception as exc:
            db.session.rollback()
            print(
                f"managed_persona_seed_failed error={exc.__class__.__name__} detail={str(exc)[:300]}",
                flush=True,
            )
            return 1


if __name__ == "__main__":
    sys.exit(main())
