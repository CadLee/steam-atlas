#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export HF_HOME=/opt/hf-cache
export SENTENCE_TRANSFORMERS_HOME=/opt/hf-cache
export OLLAMA_MODELS=/opt/ollama-models
export OLLAMA_HOST=127.0.0.1:11434

sudo apt-get update
sudo apt-get install -y \
  postgresql \
  postgresql-contrib \
  postgresql-16-pgvector \
  postgresql-16-age \
  python3-venv \
  python3-pip \
  zstd

sudo mkdir -p /opt/steam-atlas /opt/hf-cache /opt/ollama-models
sudo chown -R ubuntu:ubuntu /opt/steam-atlas /opt/hf-cache /opt/ollama-models

/usr/bin/python3 -m venv /opt/steam-atlas
/opt/steam-atlas/bin/pip install --upgrade 'pip==26.3'
/opt/steam-atlas/bin/pip install \
  'numpy==2.5.4' \
  'pandas==3.1.1' \
  'psycopg[binary]==3.3.8' \
  'python-docx==1.2.0' \
  'scikit-learn==1.9.1' \
  'sentence-transformers==6.3.0' \
  'langgraph==1.2.20' \
  'langchain==1.5.0' \
  'langchain-ollama==1.1.0'
/opt/steam-atlas/bin/pip install 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu
nvidia_pkgs="$(/opt/steam-atlas/bin/pip freeze | awk -F= '/^nvidia-/ {print $1}')"
if [ -n "$nvidia_pkgs" ]; then
  # shellcheck disable=SC2086
  /opt/steam-atlas/bin/pip uninstall -y $nvidia_pkgs
fi

sudo tee /etc/profile.d/steam-atlas.sh >/dev/null <<'EOF'
export PATH="/opt/steam-atlas/bin:${PATH}"
export HF_HOME="/opt/hf-cache"
export SENTENCE_TRANSFORMERS_HOME="/opt/hf-cache"
export OLLAMA_MODELS="/opt/ollama-models"
export OLLAMA_HOST="127.0.0.1:11434"
export STEAM_ATLAS_LLM="qwen2.5:3b"
export STEAM_ATLAS_EMBEDDING="sentence-transformers/all-MiniLM-L6-v2"
EOF
sudo chmod 644 /etc/profile.d/steam-atlas.sh

if ! command -v ollama >/dev/null 2>&1 || ! ollama --version 2>&1 | grep -q '0.40.16'; then
  curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.40.16 sh
fi

started_ollama=0
if ! curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null; then
  ollama serve >/tmp/ollama-install.log 2>&1 &
  echo $! >/tmp/ollama-install.pid
  started_ollama=1
  for _ in $(seq 1 30); do
    if curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null; then
      break
    fi
    sleep 1
  done
fi
curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null
ollama pull qwen2.5:3b
if [ "$started_ollama" -eq 1 ]; then
  kill "$(cat /tmp/ollama-install.pid)" || true
fi

/opt/steam-atlas/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
