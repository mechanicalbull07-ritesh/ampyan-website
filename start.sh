#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-10000}"

if [[ "${RENDER:-}" == "true" && -z "${SECRET_KEY:-}" ]]; then
  echo "ERROR: SECRET_KEY is required on Render before the server can start." >&2
  echo "Add SECRET_KEY in the Render service Environment settings and redeploy." >&2
  exit 1
fi

echo "Starting AMPYAN website on 0.0.0.0:${PORT}"
echo "Gunicorn workers=${WEB_CONCURRENCY:-2} threads=${GUNICORN_THREADS:-4} timeout=${GUNICORN_TIMEOUT:-120}"

exec gunicorn app:app \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile - \
  --error-logfile -
