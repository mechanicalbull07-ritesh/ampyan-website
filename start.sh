#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-10000}"

echo "Starting AMPYAN website on 0.0.0.0:${PORT}"

exec gunicorn app:app \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
