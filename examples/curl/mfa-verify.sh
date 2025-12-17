#!/usr/bin/env bash
set -euo pipefail

: "${SONOTHEIA_API_KEY:?Set SONOTHEIA_API_KEY}"
SONOTHEIA_API_URL="${SONOTHEIA_API_URL:-https://api.sonotheia.com}"
SONOTHEIA_MFA_PATH="${SONOTHEIA_MFA_PATH:-/v1/mfa/voice/verify}"
SONOTHEIA_ENROLLMENT_ID="${SONOTHEIA_ENROLLMENT_ID:-}"

AUDIO_PATH="${1:-}"

if [[ -z "$AUDIO_PATH" ]]; then
  echo "Usage: $0 <audio-file.wav>" >&2
  exit 1
fi

if [[ -z "$SONOTHEIA_ENROLLMENT_ID" ]]; then
  echo "Set SONOTHEIA_ENROLLMENT_ID to the enrollment/voiceprint identifier for the caller." >&2
  exit 1
fi

curl -X POST "${SONOTHEIA_API_URL%/}${SONOTHEIA_MFA_PATH}" \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -H "Accept: application/json" \
  -F "audio=@${AUDIO_PATH}" \
  -F "enrollment_id=${SONOTHEIA_ENROLLMENT_ID}" \
  -F 'context={"session_id":"demo-session","channel":"ivr"};type=application/json'
