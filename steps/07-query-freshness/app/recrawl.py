import logging

from app.crawler import push_url
from app.db import get_conn

log = logging.getLogger(__name__)


def list_live_urls() -> list[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT url
                FROM pages
                WHERE deleted_at IS NULL
                ORDER BY url
                """
            )
            return [row["url"] for row in cur.fetchall()]


def run_recrawl() -> dict[str, str]:
    results: dict[str, str] = {}
    for url in list_live_urls():
        try:
            results[url] = push_url(url)
            log.info("recrawl queued url=%s rid=%s", url, results[url])
        except Exception:
            log.exception("recrawl push failed url=%s", url)
            results[url] = "error"
    return results
