import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import PlainTextResponse

from adapters import normalize_incident_url

load_dotenv()

WEBHOOK_EVENTS_LOG_PATH = Path("webhook_events.log")


def append_webhook_event_log(payload: dict[str, Any]) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    entry = {"timestamp": timestamp, "payload": payload}
    with WEBHOOK_EVENTS_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(f"{json.dumps(entry, ensure_ascii=True)}\n")


def extract_incident_block_url(payload: dict[str, Any]) -> str:
    data = payload.get("payload", payload)
    event = data.get("event", {})

    # For "message_changed", links are inside event.message.
    if event.get("subtype") == "message_changed":
        event = event.get("message", {})

    try:
        return event["blocks"][0]["elements"][0]["elements"][0]["url"]
    except (KeyError, IndexError, TypeError):
        return ""

def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=PlainTextResponse, tags=["incidents"])
    async def incident_log_view() -> str:
        return "Logging is enabled to stdout. Please check deployment logs."

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.head("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health_check_head() -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @app.post("/webhook", tags=["slack"])
    async def slack_webhook(payload: dict[str, Any]) -> dict[str, Any]:
        append_webhook_event_log(payload)
        block_url = extract_incident_block_url(payload)
        if block_url:
            normalized_url = normalize_incident_url(block_url)
            response = requests.get(normalized_url)
            print(response.text)
        event_type = payload.get("type")

        # Slack URL verification handshake: echo back the challenge value.
        if event_type == "url_verification":
            challenge = payload.get("challenge")
            if not isinstance(challenge, str) or not challenge:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing or invalid challenge",
                )
            return {"challenge": challenge}

        # Acknowledge event callbacks quickly so Slack doesn't retry.
        return {"ok": True}

    return app


app = create_app()


if __name__ == "__main__":
    print("Run with an ASGI server, e.g. `uvicorn main:app --reload`.")
