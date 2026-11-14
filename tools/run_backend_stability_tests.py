"""Run affected tests against a new Unix-socket-only disposable PostgreSQL.

Never reads application environment files or connects to a configured database.
Requires local PostgreSQL binaries and the website's test dependencies.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TESTS = [
    "test_backend_stability.py", "test_admin_analytics_v2_postgres.py",
    "test_admin_analytics_v2.py", "test_analytics_foundation.py",
    "test_account_deletion_discovery.py", "test_account_deletion_public.py",
    "test_account_deletion_request.py", "test_manual_deletion_admin.py",
    "test_csrf_rendered_audit.py", "test_traffic_quality.py",
    "test_google_profile_picture.py",
]


def main():
    candidate = Path(__file__).resolve().parents[1]
    pg_bin = Path(shutil.which("pg_ctl") or "/opt/homebrew/opt/postgresql/bin/pg_ctl").parent
    for name in ("pg_ctl", "initdb", "createdb"):
        if not (pg_bin / name).is_file():
            raise SystemExit("Local PostgreSQL binaries required: " + name)
    root = Path(tempfile.mkdtemp(prefix="ampyan-v2-sql-pg-", dir="/private/tmp"))
    socket = root / "socket"
    socket.mkdir()
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("PG") and "DATABASE_URL" not in key
        and key not in ("AMPYAN_WEBSITE_TEST_PG_META", "TRAFFIC_TEST_DATABASE_URL")
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    def run(name, *args):
        subprocess.run([str(pg_bin / name), *map(str, args)], env=environment, check=True)

    run("initdb", "-D", root / "data", "-U", "ampyan_v2_fixture",
        "--auth=trust", "--no-locale", "-E", "UTF8")
    started = False
    try:
        run("pg_ctl", "-D", root / "data", "-l", root / "server.log", "-o",
            f"-k {socket} -p 55468 -c listen_addresses='' -c fsync=off", "-w", "start")
        started = True
        run("createdb", "-h", socket, "-p", "55468", "-U", "ampyan_v2_fixture",
            "ampyan_v2_sql_fixture")
        meta = root / "meta.json"
        meta.write_text(json.dumps({"socket": str(socket), "port": 55468,
            "user": "ampyan_v2_fixture", "database": "ampyan_v2_sql_fixture"}))
        environment["AMPYAN_V2_DISPOSABLE_PG_META"] = str(meta)
        result = subprocess.run([
            sys.executable, "-B", "-m", "pytest", "-q", "--disable-warnings",
            *["tests/" + name for name in TESTS],
        ], cwd=candidate, env=environment)
        return result.returncode
    finally:
        if started:
            run("pg_ctl", "-D", root / "data", "-m", "fast", "-w", "stop")


if __name__ == "__main__":
    raise SystemExit(main())
