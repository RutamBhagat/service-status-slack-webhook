import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response, status

SLACK_WEBHOOK_LOG_FILE = Path("webhook_events.log")


def append_slack_webhook_log(payload: dict[str, Any]) -> None:
    log_entry = {
        "received_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    with SLACK_WEBHOOK_LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(log_entry, ensure_ascii=False))
        log_file.write("\n")


def classify_webhook_payload(payload: dict[str, Any]) -> str:
    if payload.get("meta") is not None:
        return "atlassian"
    elif payload.get("event") and payload.get("event").get("channel_type") is not None:
        return "slack"
    else:
        return "unknown"


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.head("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health_check_head() -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @app.post("/webhook", tags=["slack"])
    async def slack_webhook(payload: dict[str, Any]) -> dict[str, Any]:
        append_slack_webhook_log(payload)
        payload_type = classify_webhook_payload(payload)

        event_type = payload.get("type") if payload_type == "slack" else None

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
