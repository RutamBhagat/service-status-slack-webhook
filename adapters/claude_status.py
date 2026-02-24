from urllib.parse import urlsplit, urlunsplit

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
