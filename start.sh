#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-10000}"

echo "Starting AMPYAN website on 0.0.0.0:${PORT}"

exec python3 app.py
