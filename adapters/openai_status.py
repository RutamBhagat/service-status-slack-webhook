import json
from datetime import datetime

from pydantic import BaseModel, Field

OPENAI_STATUS_PREFIX = "https://status.openai.com/"
OPENAI_STATUS_PROXY_PREFIX = "https://status.openai.com/proxy/status.openai.com/"


def map_openai_status_url(url: str) -> str:
    if url.startswith(OPENAI_STATUS_PROXY_PREFIX):
        return url
    if url.startswith(OPENAI_STATUS_PREFIX):
        return url.replace(OPENAI_STATUS_PREFIX, OPENAI_STATUS_PROXY_PREFIX, 1)
    return url


class OpenAIUpdate(BaseModel):
    message_string: str | None = None
    published_at: str | None = None
    to_status: str | None = None


class OpenAIIncident(BaseModel):
    name: str
    status: str
    published_at: str | None = None
    updates: list[OpenAIUpdate] = Field(default_factory=list)


class OpenAIIncidentResponse(BaseModel):
    incident: OpenAIIncident


def parse_openai_incident_content(fetched_text: str) -> dict[str, str]:
    payload = OpenAIIncidentResponse.model_validate(json.loads(fetched_text))
    incident = payload.incident

    latest_update: OpenAIUpdate | None = incident.updates[-1] if incident.updates else None
    status_text = incident.status
    timestamp = incident.published_at or datetime.now().isoformat()

    if latest_update:
        status_text = latest_update.message_string or latest_update.to_status or incident.status
        timestamp = latest_update.published_at or timestamp

    return {
        "provider": "OpenAI",
        "product": f"OpenAI - {incident.name}",
        "status_text": status_text,
        "timestamp": timestamp,
    }
