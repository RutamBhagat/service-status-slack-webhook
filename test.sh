#!/usr/bin/env bash

set -u

log_file="./webhook_events_direct.log"
webhook_url="http://localhost:8000/webhook"
# webhook_url="https://service-status-slack-webhook.vercel.app/webhook"
# webhook_url="https://service-status-slack-webhook.onrender.com/webhook"
max_workers=10

if [[ ! -f "$log_file" ]]; then
  echo "Log file not found: $log_file" >&2
  exit 1
fi

post_json_line() {
  local line="$1"
  local output
  if output="$(curl -sS -X POST "$webhook_url" -H "Content-Type: application/json" --data "$line")"; then
    printf '%s\n' "$output"
  else
    local exit_code=$?
    echo "curl failed (exit $exit_code)" >&2
  fi
}

pids=()

while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
  line="$(printf '%s' "$raw_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$line" ]] && continue

  post_json_line "$line" &
  pids+=("$!")

  if (( ${#pids[@]} >= max_workers )); then
    wait "${pids[0]}"
    pids=("${pids[@]:1}")
  fi
done < "$log_file"

for pid in "${pids[@]}"; do
  wait "$pid"
done
