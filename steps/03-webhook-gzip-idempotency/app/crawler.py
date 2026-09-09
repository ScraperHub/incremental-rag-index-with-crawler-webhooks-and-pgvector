import json

from crawlbase import CrawlingAPI

from app.config import settings


def _client() -> CrawlingAPI:
    if not settings.crawlbase_token:
        raise RuntimeError("CRAWLBASE_TOKEN is not set")
    # Published crawlbase SDK exposes CrawlingAPI, not CrawlerAPI.
    # Crawler queue push is Crawling API GET with crawler= and callback=true.
    return CrawlingAPI({"token": settings.crawlbase_token})


def push_options() -> dict:
    options = {
        "crawler": settings.crawler_name,
        "callback": "true",
        "format": "md",
        "md_readability": "true",
    }
    if settings.page_wait is not None:
        options["page_wait"] = str(settings.page_wait)
    if settings.ajax_wait is not None:
        options["ajax_wait"] = str(settings.ajax_wait)
    return options


def _rid_from_response(res: dict) -> str | None:
    payload = res.get("json")
    if isinstance(payload, dict) and payload.get("rid"):
        return str(payload["rid"])
    body = res.get("body")
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    if isinstance(body, str) and body.strip():
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict) and data.get("rid"):
            return str(data["rid"])
    return None


def push_url(url: str) -> str:
    """Enqueue one URL. Returns the Crawlbase rid."""
    api = _client()
    res = api.get(url, push_options())
    rid = _rid_from_response(res if isinstance(res, dict) else {})
    if not rid:
        raise RuntimeError(f"Crawler push failed for {url!r}: {res!r}")
    return rid
