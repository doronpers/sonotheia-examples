#!/usr/bin/env bash
set -euo pipefail

: "${SONOTHEIA_API_KEY:?Set SONOTHEIA_API_KEY}"
SONOTHEIA_API_URL="${SONOTHEIA_API_URL:-https://api.sonotheia.com}"
SONOTHEIA_SAR_PATH="${SONOTHEIA_SAR_PATH:-/v1/reports/sar}"

SESSION_ID="${1:-}"
DECISION="${2:-review}"
REASON="${3:-Manual review requested}"

if [[ -z "$SESSION_ID" ]]; then
  echo "Usage: $0 <session-id> [decision] [reason]" >&2
  exit 1
fi

payload=$(cat <<EOF
{
  "session_id": "${SESSION_ID}",
  "decision": "${DECISION}",
  "reason": "${REASON}",
  "metadata": {
    "agent": "public-example",
    "channel": "ivr"
  }
}
EOF
)

curl -X POST "${SONOTHEIA_API_URL%/}${SONOTHEIA_SAR_PATH}" \
  -H "Authorization: Bearer ${SONOTHEIA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${payload}"
