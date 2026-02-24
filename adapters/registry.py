from typing import Callable
from datetime import UTC, datetime
from urllib.parse import urlsplit

from .claude_status import map_claude_status_url, parse_claude_incident_content
from .openai_status import map_openai_status_url, parse_openai_incident_content

INCIDENT_URL_ADAPTERS: dict[str, Callable[[str], str]] = {
    "status.openai.com": map_openai_status_url,
    "status.claude.com": map_claude_status_url,
}

INCIDENT_CONTENT_PARSERS: dict[str, Callable[[str], dict[str, str]]] = {
    "status.openai.com": parse_openai_incident_content,
    "status.claude.com": parse_claude_incident_content,
}


def _extract_host(url: str) -> str:
    split_url = urlsplit(url)
    if not split_url.netloc:
        return ""

    host = split_url.netloc.rsplit("@", maxsplit=1)[-1]
    return host.split(":", maxsplit=1)[0].lower()


def normalize_incident_url(url: str) -> str:
    if not url:
        return ""

    host = _extract_host(url)
    for host_prefix, adapter in INCIDENT_URL_ADAPTERS.items():
        if host.startswith(host_prefix):
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
    for host_prefix, parser in INCIDENT_CONTENT_PARSERS.items():
        if host.startswith(host_prefix):
            try:
                data = parser(fetched_text)
                timestamp = _format_timestamp(data.get("timestamp", ""))
                product = data.get("product", "Unknown")
                status_text = data.get("status_text", "Unknown")
                return f"[{timestamp}] Product: {product}\nStatus: {status_text}"
            except Exception:
                now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                provider_name = "OpenAI" if host_prefix == "status.openai.com" else "Claude"
                return (
                    f"[{now}] Product: {provider_name} - Unknown incident\n"
                    "Status: Could not parse provider response"
                )

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    return f"[{now}] Product: Unknown\nStatus: Unable to parse provider payload"
