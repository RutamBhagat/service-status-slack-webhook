from typing import Callable
from datetime import UTC, datetime
from urllib.parse import urlsplit

from .claude_status import map_claude_status_url, parse_claude_incident_content
from .openai_status import map_openai_status_url, parse_openai_incident_content

ProviderAdapter = dict[
    str, str | Callable[[str], str] | Callable[[str], dict[str, str]]
]

INCIDENT_ADAPTERS: dict[str, ProviderAdapter] = {
    "status.openai.com": {
        "provider_name": "OpenAI",
        "url_adapter": map_openai_status_url,
        "content_parser": parse_openai_incident_content,
    },
    "status.claude.com": {
        "provider_name": "Claude",
        "url_adapter": map_claude_status_url,
        "content_parser": parse_claude_incident_content,
    },
}


def _extract_host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def normalize_incident_url(url: str) -> str:
    if not url:
        return ""

    host = _extract_host(url)
    for host_prefix, adapter_config in INCIDENT_ADAPTERS.items():
        if host.startswith(host_prefix):
            adapter = adapter_config["url_adapter"]
            return adapter(url)

    return url


def _format_timestamp(timestamp: str) -> str:
    if not timestamp:
        return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp


def parse_incident_content(url: str, fetched_text: str) -> str:
    host = _extract_host(url)
    for host_prefix, adapter_config in INCIDENT_ADAPTERS.items():
        if host.startswith(host_prefix):
            parser = adapter_config["content_parser"]
            data = parser(fetched_text)
            timestamp = _format_timestamp(data.get("timestamp", ""))
            product = data.get("product", "Unknown")
            status_text = data.get("status_text", "Unknown")
            return f"[{timestamp}] Product: {product}\nStatus: {status_text}"

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return f"[{now}] Product: Unknown\nStatus: Unable to parse provider payload"
