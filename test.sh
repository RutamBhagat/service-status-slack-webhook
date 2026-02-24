#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1:-./webhook_events_direct.log}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8000/webhook}"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Log file not found: $LOG_FILE" >&2
  exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue

  curl -sS \
    -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    --data "$line"
  echo
done < "$LOG_FILE"
