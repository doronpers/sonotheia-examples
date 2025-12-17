#!/usr/bin/env bash
set -euo pipefail

: "${SONOTHEIA_API_KEY:?Set SONOTHEIA_API_KEY}"
SONOTHEIA_API_URL="${SONOTHEIA_API_URL:-https://api.sonotheia.com}"
SONOTHEIA_DEEPFAKE_PATH="${SONOTHEIA_DEEPFAKE_PATH:-/v1/voice/deepfake}"

AUDIO_PATH="${1:-}"

if [[ -z "$AUDIO_PATH" ]]; then
  echo "Usage: $0 <audio-file.wav>" >&2
  exit 1
fi

curl -X POST "${SONOTHEIA_API_URL%/}${SONOTHEIA_DEEPFAKE_PATH}" \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -H "Accept: application/json" \
  -F "audio=@${AUDIO_PATH}" \
  -F 'metadata={"session_id":"demo-session","channel":"web"};type=application/json'
