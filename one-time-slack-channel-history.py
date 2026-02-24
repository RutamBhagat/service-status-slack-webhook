import os
import time
import json
import hmac
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://localhost:8000/webhook")

ONLY_BOT_MESSAGES = True
LIMIT_MESSAGES = None # you can set the number like 20 or None to fetch all

def slack_api(method: str, payload: dict):
    r = requests.post(
        f"https://slack.com/api/{method}",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        data=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error ({method}): {data}")
    return data

def sign_slack_request(body: bytes):
    ts = str(int(time.time()))
    basestring = f"v0:{ts}:".encode() + body
    sig = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        basestring,
        hashlib.sha256,
    ).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": sig,
    }

def fetch_history(channel_id: str, limit_total: int | None = None):
    messages = []
    cursor = None

    while True:
        payload = {"channel": channel_id, "limit": 100}
        if cursor:
            payload["cursor"] = cursor

        resp = slack_api("conversations.history", payload)
        batch = resp.get("messages", [])
        messages.extend(batch)

        if limit_total and len(messages) >= limit_total:
            messages = messages[:limit_total]
            break

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    # conversations.history usually returns newest first; replay oldest->newest
    messages.sort(key=lambda m: float(m["ts"]))
    return messages

def to_event_callback(msg: dict, channel_id: str):
    ts = msg["ts"]
    event_time = int(float(ts))

    # Keep only fields your FastAPI parser likely uses (+ extras if you need)
    inner_event = {
        "type": "message",
        "channel": channel_id,
        "text": msg.get("text", ""),
        "ts": ts,
        "event_ts": ts,
    }

    # Carry over common Slack message fields if present
    for key in [
        "subtype", "user", "bot_id", "username",
        "thread_ts", "parent_user_id", "blocks", "attachments", "files"
    ]:
        if key in msg:
            inner_event[key] = msg[key]

    # Set channel_type for public channel
    inner_event["channel_type"] = "channel"

    return {
        "token": "replay-local",
        "team_id": "T_REPLAY",
        "api_app_id": "A_REPLAY",
        "type": "event_callback",
        "event_id": f"replay-{channel_id}-{ts}",
        "event_time": event_time,
        "authorizations": [],
        "is_ext_shared_channel": False,
        "event_context": f"EC_REPLAY_{ts.replace('.', '')}",
        "event": inner_event,
    }

def main():
    messages = fetch_history(CHANNEL_ID, LIMIT_MESSAGES)
    print(f"Fetched {len(messages)} messages")

    sent = 0
    skipped = 0

    for msg in messages:
        # Optional: mostly replay app/bot posts (RSS app posts are bot/app messages)
        if ONLY_BOT_MESSAGES and not (msg.get("bot_id") or msg.get("subtype") == "bot_message"):
            skipped += 1
            continue

        payload = to_event_callback(msg, CHANNEL_ID)
        body = json.dumps(payload).encode("utf-8")
        headers = sign_slack_request(body)

        r = requests.post(WEBHOOK_URL, data=body, headers=headers, timeout=30)
        print(f"{msg['ts']} -> {r.status_code} {r.text[:200]}")
        if r.ok:
            sent += 1

        # small delay so logs are readable
        time.sleep(0.2)

    print(f"Done. Sent={sent}, skipped={skipped}")

if __name__ == "__main__":
    main()
