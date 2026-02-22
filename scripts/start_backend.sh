#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${HOUND_CONDA_ENV:=hound}"
: "${HOUND_HOST:=127.0.0.1}"
: "${HOUND_PORT:=8000}"
: "${HOUND_LLM_PROVIDER:=ollama}"
: "${HOUND_LLM_MATCHING:=auto}"
: "${HOUND_OLLAMA_URL:=http://127.0.0.1:11434}"
: "${HOUND_OLLAMA_MODEL:=gemma3:27b}"
: "${HOUND_OLLAMA_TIMEOUT_SECONDS:=120}"
: "${HOUND_RELOAD:=1}"

UVICORN_ARGS=(hound_core.api:app --host "$HOUND_HOST" --port "$HOUND_PORT")
if [[ "$HOUND_RELOAD" == "1" ]]; then
  UVICORN_ARGS+=(--reload)
fi

echo "[hound] starting backend"
echo "[hound] conda env: $HOUND_CONDA_ENV"
echo "[hound] api: http://$HOUND_HOST:$HOUND_PORT"
echo "[hound] llm provider: $HOUND_LLM_PROVIDER"
echo "[hound] llm matching: $HOUND_LLM_MATCHING"
echo "[hound] ollama url: $HOUND_OLLAMA_URL"
echo "[hound] ollama model: $HOUND_OLLAMA_MODEL"

env \
  PYTHONPATH=backend/src \
  HOUND_LLM_PROVIDER="$HOUND_LLM_PROVIDER" \
  HOUND_LLM_MATCHING="$HOUND_LLM_MATCHING" \
  HOUND_OLLAMA_URL="$HOUND_OLLAMA_URL" \
  HOUND_OLLAMA_MODEL="$HOUND_OLLAMA_MODEL" \
  HOUND_OLLAMA_TIMEOUT_SECONDS="$HOUND_OLLAMA_TIMEOUT_SECONDS" \
  conda run -n "$HOUND_CONDA_ENV" uvicorn "${UVICORN_ARGS[@]}"
