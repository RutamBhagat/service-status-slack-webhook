import json
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, Field

CLAUDE_STATUS_PREFIX = "https://status.claude.com/"


def map_claude_status_url(url: str) -> str:
    if not url.startswith(CLAUDE_STATUS_PREFIX):
        return url

    split_url = urlsplit(url)
    if split_url.path.endswith(".json"):
        return url

    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            f"{split_url.path}.json",
            split_url.query,
            split_url.fragment,
        )
    )


class ClaudeIncidentUpdate(BaseModel):
    body: str | None = None
    created_at: str | None = None
    status: str | None = None


class ClaudeIncident(BaseModel):
    name: str
    status: str
    updated_at: str | None = None
    incident_updates: list[ClaudeIncidentUpdate] = Field(default_factory=list)


def parse_claude_incident_content(fetched_text: str) -> dict[str, str]:
    incident = ClaudeIncident.model_validate(json.loads(fetched_text))
    latest_update: ClaudeIncidentUpdate | None = (
        incident.incident_updates[0] if incident.incident_updates else None
    )

    status_text = incident.status
    timestamp = incident.updated_at or datetime.now().isoformat()

    if latest_update:
        status_text = latest_update.body or latest_update.status or incident.status
        timestamp = latest_update.created_at or timestamp

    return {
        "provider": "Claude",
        "product": f"Claude - {incident.name}",
        "status_text": status_text,
        "timestamp": timestamp,
    }
