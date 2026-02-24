OPENAI_STATUS_PREFIX = "https://status.openai.com/"
OPENAI_STATUS_PROXY_PREFIX = "https://status.openai.com/proxy/status.openai.com/"


def map_openai_status_url(url: str) -> str:
    if url.startswith(OPENAI_STATUS_PROXY_PREFIX):
        return url
    if url.startswith(OPENAI_STATUS_PREFIX):
        return url.replace(OPENAI_STATUS_PREFIX, OPENAI_STATUS_PROXY_PREFIX, 1)
    return url
