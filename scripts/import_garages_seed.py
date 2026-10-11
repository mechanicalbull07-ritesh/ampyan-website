#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app
from models.models import MechanicProfile, db

DEFAULT_SEED_PATHS = (
    ROOT / "garage_seed.json",
    ROOT / "scripts" / "garage_seed.json",
)

STABLE_INSERT_COLUMNS = (
    "business_name",
    "owner_name",
    "phone",
    "city",
    "state",
    "country",
    "address",
    "specialties",
    "service_types",
    "experience_years",
    "trust_score",
    "trust_level",
    "is_featured",
    "accepts_emergency",
    "pickup_drop_available",
    "is_verified",
    "created_at",
)
OPTIONAL_INSERT_COLUMNS = (
    "area",
    "latitude",
    "longitude",
    "image_url",
    "listing_status",
    "source",
    "email",
    "pincode",
    "about",
)


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalized_text(value):
    return re.sub(r"\s+", " ", _text(value).lower())


def _phone_digits(value):
    phone = _text(value)
    if not phone:
        return None, None
    compact = re.sub(r"[\s()+-]+", "", phone)
    if not compact or not compact.isdigit():
        return None, "phone must contain digits only if present"
    return compact, None


def _existing_phone_digits(value):
    digits = re.sub(r"\D+", "", _text(value))
    return digits or None


def _services(value):
    if isinstance(value, list):
        return [item for item in (_text(item) for item in value) if item]
    if not _text(value):
        return []
    return [item.strip() for item in _text(value).split(",") if item.strip()]


def _service_text(value):
    services = _services(value)
    if not services:
        return None
    return ", ".join(services)


def _record_summary(data):
    return {
        "name": data["business_name"],
        "phone": data["phone"],
        "city": data["city"],
        "state": data["state"],
        "address": data["address"],
        "area": data["area"],
        "services": _services(data["service_types"]),
        "listing_status": data["listing_status"],
        "source": data["source"],
        "is_verified": False,
        "is_featured": False,
    }


def _seed_path(raw_path):
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    for path in DEFAULT_SEED_PATHS:
        if path.exists():
            return path
    return DEFAULT_SEED_PATHS[-1]


def _load_seed(path):
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    raise ValueError("Seed must be a JSON list.")


def _normalize(raw):
    services = raw.get("services") or raw.get("service_types")
    name = _text(raw.get("business_name") or raw.get("name"))
    city = _text(raw.get("city"))
    address = _text(raw.get("address"))
    phone, phone_error = _phone_digits(raw.get("phone"))
    return {
        "business_name": name,
        "owner_name": _text(raw.get("owner_name")) or "Listing Owner Not Provided",
        "email": None,
        "phone": phone,
        "phone_error": phone_error,
        "city": city,
        "area": _text(raw.get("area")) or None,
        "state": _text(raw.get("state")) or None,
        "country": _text(raw.get("country")) or "India",
        "pincode": None,
        "address": address or None,
        "specialties": _service_text(services),
        "service_types": _service_text(services),
        "experience_years": None,
        "about": None,
        "accepts_emergency": False,
        "pickup_drop_available": False,
        "latitude": None,
        "longitude": None,
        "image_url": None,
        "listing_status": "public_unverified",
        "source": "public_manual_seed",
        "trust_score": 30,
        "trust_level": "Listed for discovery",
    }


def _mechanic_profile_columns():
    if db.engine.dialect.name == "postgresql":
        rows = db.session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'mechanic_profile'
        """))
        return {row.column_name for row in rows}
    if db.engine.dialect.name == "sqlite":
        rows = db.session.execute(text("PRAGMA table_info(mechanic_profile)"))
        return {row.name for row in rows}
    raise RuntimeError(f"Unsupported database dialect: {db.engine.dialect.name}")


def _insert_mechanic_profile(data, available_columns):
    missing_columns = [name for name in STABLE_INSERT_COLUMNS if name not in available_columns]
    if missing_columns:
        raise RuntimeError(f"mechanic_profile is missing required columns: {', '.join(missing_columns)}")

    payload = {
        "business_name": data["business_name"],
        "owner_name": data["owner_name"],
        "phone": data["phone"],
        "city": data["city"],
        "state": data["state"],
        "country": data["country"],
        "address": data["address"],
        "specialties": data["specialties"],
        "service_types": data["service_types"],
        "experience_years": data["experience_years"],
        "trust_score": data["trust_score"],
        "trust_level": data["trust_level"],
        "is_featured": False,
        "accepts_emergency": data["accepts_emergency"],
        "pickup_drop_available": data["pickup_drop_available"],
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "area": data["area"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "image_url": data["image_url"],
        "listing_status": data["listing_status"],
        "source": data["source"],
        "email": data["email"],
        "pincode": data["pincode"],
        "about": data["about"],
    }
    insert_columns = [
        name
        for name in (*STABLE_INSERT_COLUMNS, *OPTIONAL_INSERT_COLUMNS)
        if name in available_columns
    ]
    column_sql = ", ".join(insert_columns)
    value_sql = ", ".join(f":{name}" for name in insert_columns)
    db.session.execute(
        text(f"INSERT INTO mechanic_profile ({column_sql}) VALUES ({value_sql})"),
        {name: payload[name] for name in insert_columns},
    )


def _duplicate_query(data):
    phone = data.get("phone")
    if phone:
        existing_with_phone = (
            MechanicProfile.query
            .with_entities(MechanicProfile.id, MechanicProfile.phone)
            .filter(MechanicProfile.phone.isnot(None))
            .all()
        )
        for existing in existing_with_phone:
            if _existing_phone_digits(existing.phone) == phone:
                return existing
    name = _normalized_text(data["business_name"])
    city = _normalized_text(data["city"])
    address = _normalized_text(data["address"])
    candidates = (
        MechanicProfile.query
        .with_entities(MechanicProfile.id, MechanicProfile.business_name, MechanicProfile.address)
        .filter(db.func.lower(MechanicProfile.city) == city)
        .all()
    )
    for candidate in candidates:
        if (
            _normalized_text(candidate.business_name) == name
            and _normalized_text(candidate.address) == address
        ):
            return candidate
    return None


def import_seed(path, limit=None, commit=False):
    rows = _load_seed(path)
    if limit is not None:
        rows = rows[:limit]

    result = {
        "seed": str(path),
        "processed": 0,
        "created": 0,
        "duplicates": 0,
        "skipped": 0,
        "invalid": 0,
        "errors": [],
        "will_insert": [],
        "duplicate_records": [],
        "invalid_records": [],
    }

    try:
        available_columns = _mechanic_profile_columns()
        missing_columns = [name for name in STABLE_INSERT_COLUMNS if name not in available_columns]
        if missing_columns:
            raise RuntimeError(f"mechanic_profile is missing required columns: {', '.join(missing_columns)}")
        seen_phones = set()
        seen_identities = set()
        for index, raw in enumerate(rows, start=1):
            result["processed"] += 1
            data = _normalize(raw)
            missing = [field for field in ("business_name", "city", "address") if not data.get(field)]
            if missing or data.get("phone_error"):
                result["invalid"] += 1
                result["skipped"] += 1
                error = {"index": index}
                if missing:
                    error["missing"] = missing
                if data.get("phone_error"):
                    error["phone"] = data["phone_error"]
                result["errors"].append(error)
                result["invalid_records"].append({
                    "index": index,
                    "record": raw,
                    "errors": error,
                })
                continue
            identity = (
                _normalized_text(data["business_name"]),
                _normalized_text(data["city"]),
                _normalized_text(data["address"]),
            )
            if data.get("phone") and data["phone"] in seen_phones:
                result["duplicates"] += 1
                result["duplicate_records"].append({
                    "index": index,
                    "record": _record_summary(data),
                    "matched_existing_id": None,
                    "reason": "duplicate phone in seed file",
                })
                continue
            if identity in seen_identities:
                result["duplicates"] += 1
                result["duplicate_records"].append({
                    "index": index,
                    "record": _record_summary(data),
                    "matched_existing_id": None,
                    "reason": "duplicate name/city/address in seed file",
                })
                continue
            duplicate = _duplicate_query(data)
            if duplicate:
                result["duplicates"] += 1
                result["duplicate_records"].append({
                    "index": index,
                    "record": _record_summary(data),
                    "matched_existing_id": duplicate.id,
                })
                continue

            if commit:
                _insert_mechanic_profile(data, available_columns)
            result["created"] += 1
            result["will_insert"].append(_record_summary(data))
            if data.get("phone"):
                seen_phones.add(data["phone"])
            seen_identities.add(identity)

        if commit:
            db.session.commit()
            result["mode"] = "commit"
        else:
            db.session.rollback()
            result["mode"] = "dry-run"
    except Exception as exc:
        db.session.rollback()
        result["mode"] = "commit" if commit else "dry-run"
        result["errors"].append({"fatal": exc.__class__.__name__, "message": str(exc)})
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description="Import garage_seed.json into the AMPYAN API database.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate and count rows without writing. This is the default.")
    mode.add_argument("--commit", action="store_true", help="Write new non-duplicate rows.")
    parser.add_argument("--limit", type=int, default=None, help="Import at most this many rows.")
    parser.add_argument("--seed", default=None, help="Path to garage_seed.json.")
    args = parser.parse_args()

    path = _seed_path(args.seed)
    if not path.exists():
        raise SystemExit(f"Seed file not found: {path}")

    try:
        with app.app_context():
            result = import_seed(path, limit=args.limit, commit=args.commit)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        details = str(exc)
        cause = exc
        is_lock_timeout = False
        while cause is not None:
            cause_text = str(cause).lower()
            cause_code = getattr(cause, "pgcode", None)
            if cause_code == "55P03" or "locknotavailable" in cause_text or "lock timeout" in cause_text:
                is_lock_timeout = True
                break
            cause = cause.__cause__ or cause.__context__
        print(json.dumps({
            "mode": "commit" if args.commit else "dry-run",
            "failed": True,
            "error": "LockTimeout" if is_lock_timeout else exc.__class__.__name__,
            "message": (
                "Database lock timeout while reading garage records; no inserts were attempted. Retry after the lock is released."
                if is_lock_timeout and not args.commit
                else details
            ),
        }, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
