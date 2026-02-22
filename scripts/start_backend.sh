#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${HOUND_CONDA_ENV:=hound}"
: "${HOUND_HOST:=127.0.0.1}"
: "${HOUND_PORT:=8000}"
: "${HOUND_LLM_PROVIDER:=ollama}"
: "${HOUND_LLM_MATCHING:=auto}"
: "${HOUND_LLM_BASE_URL:=}"
: "${HOUND_LLM_MODEL:=}"
: "${HOUND_LLM_API_KEY:=}"
: "${HOUND_LLM_TIMEOUT_SECONDS:=120}"

# Legacy compatibility vars (still supported)
: "${HOUND_OLLAMA_URL:=http://127.0.0.1:11434}"
: "${HOUND_OLLAMA_MODEL:=gemma3:27b}"
: "${HOUND_OLLAMA_TIMEOUT_SECONDS:=120}"
: "${HOUND_OPENAI_BASE_URL:=https://api.openai.com/v1}"
: "${HOUND_OPENAI_MODEL:=gpt-4o-mini}"
: "${HOUND_OPENAI_API_KEY:=}"
: "${HOUND_RELOAD:=1}"

if [[ -z "$HOUND_LLM_BASE_URL" ]]; then
  if [[ "${HOUND_LLM_PROVIDER,,}" == "openai" ]]; then
    HOUND_LLM_BASE_URL="$HOUND_OPENAI_BASE_URL"
  else
    HOUND_LLM_BASE_URL="$HOUND_OLLAMA_URL"
  fi
fi

if [[ -z "$HOUND_LLM_MODEL" ]]; then
  if [[ "${HOUND_LLM_PROVIDER,,}" == "openai" ]]; then
    HOUND_LLM_MODEL="$HOUND_OPENAI_MODEL"
  else
    HOUND_LLM_MODEL="$HOUND_OLLAMA_MODEL"
  fi
fi

if [[ -z "$HOUND_LLM_API_KEY" ]]; then
  HOUND_LLM_API_KEY="$HOUND_OPENAI_API_KEY"
fi

if [[ -z "${HOUND_LLM_TIMEOUT_SECONDS:-}" ]]; then
  HOUND_LLM_TIMEOUT_SECONDS="$HOUND_OLLAMA_TIMEOUT_SECONDS"
fi

UVICORN_ARGS=(hound_core.api:app --host "$HOUND_HOST" --port "$HOUND_PORT")
if [[ "$HOUND_RELOAD" == "1" ]]; then
  UVICORN_ARGS+=(--reload)
fi

echo "[hound] starting backend"
echo "[hound] conda env: $HOUND_CONDA_ENV"
echo "[hound] api: http://$HOUND_HOST:$HOUND_PORT"
echo "[hound] llm provider: $HOUND_LLM_PROVIDER"
echo "[hound] llm matching: $HOUND_LLM_MATCHING"
echo "[hound] llm base url: $HOUND_LLM_BASE_URL"
echo "[hound] llm model: $HOUND_LLM_MODEL"

env \
  PYTHONPATH=backend/src \
  HOUND_LLM_PROVIDER="$HOUND_LLM_PROVIDER" \
  HOUND_LLM_MATCHING="$HOUND_LLM_MATCHING" \
  HOUND_LLM_BASE_URL="$HOUND_LLM_BASE_URL" \
  HOUND_LLM_MODEL="$HOUND_LLM_MODEL" \
  HOUND_LLM_API_KEY="$HOUND_LLM_API_KEY" \
  HOUND_LLM_TIMEOUT_SECONDS="$HOUND_LLM_TIMEOUT_SECONDS" \
  HOUND_OLLAMA_URL="$HOUND_OLLAMA_URL" \
  HOUND_OLLAMA_MODEL="$HOUND_OLLAMA_MODEL" \
  HOUND_OLLAMA_TIMEOUT_SECONDS="$HOUND_OLLAMA_TIMEOUT_SECONDS" \
  HOUND_OPENAI_BASE_URL="$HOUND_OPENAI_BASE_URL" \
  HOUND_OPENAI_MODEL="$HOUND_OPENAI_MODEL" \
  HOUND_OPENAI_API_KEY="$HOUND_OPENAI_API_KEY" \
  conda run -n "$HOUND_CONDA_ENV" uvicorn "${UVICORN_ARGS[@]}"
