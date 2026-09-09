import httpx

from app.config import settings


def fetch_crawler_stats() -> dict:
    """GET /crawler/{token}/stats — confirm the path against current Crawler docs."""
    if not settings.crawlbase_token:
        raise RuntimeError("CRAWLBASE_TOKEN is not set")
    url = f"https://api.crawlbase.com/crawler/{settings.crawlbase_token}/stats"
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()
