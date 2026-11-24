#!/usr/bin/env bash
# Start the local milestone 1 prototype.
# Databases: `docker compose up -d` from the repo root when Docker is available.
# This host falls back to a local Postgres database named steam_atlas and Qdrant on 127.0.0.1:6333.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null; then
  echo "python3 is required" >&2
  exit 1
fi
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
  docker compose up -d
  export DATABASE_URL="${DATABASE_URL:-postgresql://steam:steam@127.0.0.1:5432/steam_atlas}"
fi

export QDRANT_URL="${QDRANT_URL:-http://127.0.0.1:6333}"
exec .venv/bin/python -m app
