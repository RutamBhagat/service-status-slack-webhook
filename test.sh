#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${1:-./webhook_events_direct.log}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8000/webhook}"
CONCURRENCY="${CONCURRENCY:-10}"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Log file not found: $LOG_FILE" >&2
  exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue

  (
    curl -sS \
      -w '\n' \
      -X POST "$WEBHOOK_URL" \
      -H "Content-Type: application/json" \
      --data "$line"
  ) &

  while (( $(jobs -rp | wc -l) >= CONCURRENCY )); do
    wait -n
  done
done < "$LOG_FILE"

wait
