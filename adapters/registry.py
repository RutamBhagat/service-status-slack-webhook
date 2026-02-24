from typing import Callable
from urllib.parse import urlsplit

from .claude_status import map_claude_status_url
from .openai_status import map_openai_status_url

INCIDENT_URL_ADAPTERS: dict[str, Callable[[str], str]] = {
    "status.openai.com": map_openai_status_url,
    "status.claude.com": map_claude_status_url,
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
