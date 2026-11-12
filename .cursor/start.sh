#!/usr/bin/env bash
set -euo pipefail

export OLLAMA_MODELS=/opt/ollama-models
export OLLAMA_HOST=127.0.0.1:11434

if ! curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null; then
  ollama serve >/tmp/ollama-serve.log 2>&1 &
fi

ollama_ready=0
for _ in $(seq 1 30); do
  if curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null; then
    ollama_ready=1
    break
  fi
  sleep 1
done
if [ "$ollama_ready" -ne 1 ]; then
  echo "Ollama did not become ready" >&2
  exit 1
fi

if ! pg_isready -q; then
  sudo pg_ctlcluster 16 main start
fi

pg_ready=0
for _ in $(seq 1 30); do
  if pg_isready -q; then
    pg_ready=1
    break
  fi
  sleep 1
done
if [ "$pg_ready" -ne 1 ]; then
  echo "PostgreSQL did not become ready" >&2
  exit 1
fi

sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ubuntu') THEN
    CREATE ROLE ubuntu LOGIN SUPERUSER;
  END IF;
END
$$;
SQL

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname = 'steam_atlas'" | grep -q 1; then
  sudo -u postgres createdb -O ubuntu steam_atlas
fi

psql -d steam_atlas -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
SQL
