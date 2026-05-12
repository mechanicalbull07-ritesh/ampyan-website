#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-10000}"

echo "Starting AMPYAN website on 0.0.0.0:${PORT}"

exec gunicorn app:app \
  --workers "${WEB_CONCURRENCY:-1}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile - \
  --error-logfile -
