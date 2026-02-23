from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import PlainTextResponse

INCIDENT_LOG_FILE = Path("incident.log")


def append_incident_log(message: str) -> None:
    with INCIDENT_LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(message)
        log_file.write("\n")


def classify_webhook_payload(payload: dict[str, Any]) -> str:
    if payload.get("meta") is not None:
        return "atlassian"
    elif payload.get("event") and payload.get("event").get("channel_type") is not None:
        return "slack"
    else:
        return "unknown"


def format_slack_template(payload: dict[str, Any]) -> str:
    event = payload["event"]
    message = event["message"] if event.get("subtype") == "message_changed" else event
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    text = message.get("text", "")

    product = message.get("username", "Slack")
    status_value = ""
    text_value = ""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("Status:"):
            status_value = line.split("Status:", 1)[1].strip()
            for next_line in lines[index + 1 :]:
                if next_line.strip():
                    text_value = next_line.strip()
                    break
            break
    if not status_value:
        status_value = message.get("subtype", event.get("type", "message"))
    if not text_value:
        text_value = text.strip()

    return (
        f"[{timestamp}] Product: {product}\n"
        f"Status: {status_value}\n"
        f"Text: {text_value}"
    )


def format_atlassian_template(payload: dict[str, Any]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    if payload.get("component") and payload.get("component_update"):
        component = payload["component"]
        component_update = payload["component_update"]
        return (
            f"[{timestamp}] Product: {component.get('name', 'Unknown')}\n"
            f"Status: {component_update.get('new_status', 'unknown')}\n"
            f"Text: {component_update.get('old_status', 'unknown')} -> "
            f"{component_update.get('new_status', 'unknown')}"
        )

    if payload.get("incident"):
        incident = payload["incident"]
        text_value = ""
        incident_updates = incident.get("incident_updates", [])
        if incident_updates:
            text_value = incident_updates[0].get("body", "")
        return (
            f"[{timestamp}] Product: {incident.get('name', 'Unknown')}\n"
            f"Status: {incident.get('status', 'unknown')}\n"
            f"Text: {text_value}"
        )

    return f"[{timestamp}] Product: Atlassian\nStatus: unknown\nText: "


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=PlainTextResponse, tags=["incidents"])
    async def incident_log_view() -> str:
        if not INCIDENT_LOG_FILE.exists():
            return ""
        return INCIDENT_LOG_FILE.read_text(encoding="utf-8")

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.head("/health", status_code=status.HTTP_200_OK, tags=["health"])
    async def health_check_head() -> Response:
        return Response(status_code=status.HTTP_200_OK)

    @app.post("/webhook", tags=["slack"])
    async def slack_webhook(payload: dict[str, Any]) -> dict[str, Any]:
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

        payload_type = classify_webhook_payload(payload)

        if payload_type == "slack":
            append_incident_log(format_slack_template(payload))
        if payload_type == "atlassian":
            append_incident_log(format_atlassian_template(payload))

        # Acknowledge event callbacks quickly so Slack doesn't retry.
        return {"ok": True}

    return app


app = create_app()


if __name__ == "__main__":
    print("Run with an ASGI server, e.g. `uvicorn main:app --reload`.")
