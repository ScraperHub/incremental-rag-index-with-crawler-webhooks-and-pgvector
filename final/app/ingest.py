"""Ingest a webhook delivery: tombstone, skip, or re-embed.

Cloud Storage is a *crawler creation* choice (webhook XOR storage), not a
per-push `store=true` on a webhook crawler. To re-chunk later without
recrawling, create a second Storage-mode crawler and pull bodies by RID
via the Storage API, then call replace_chunks() with the stored Markdown.
"""

from __future__ import annotations

import logging

from app.chunk import chunk_markdown
from app.db import get_conn
from app.embed import embed_texts, embedding_to_pgvector
from app.normalize import content_sha256, normalize_markdown

log = logging.getLogger(__name__)


def ingest_delivery(
    rid: str,
    url: str,
    original_status: int | None,
    cb_status: int | None,
    markdown: str,
) -> str:
    log.info(
        "ingest rid=%s url=%s original_status=%s cb_status=%s",
        rid,
        url,
        original_status,
        cb_status,
    )
    if not url:
        log.warning("skip rid=%s: missing url header", rid)
        return "skipped"

    with get_conn() as conn:
        if original_status in (404, 410):
            tombstone_page(conn, url, original_status)
            conn.commit()
            return "deleted"

        if cb_status is not None and cb_status != 200:
            log.warning("skip rid=%s: cb_status=%s (not embedding)", rid, cb_status)
            conn.commit()
            return "skipped"

        normalized = normalize_markdown(markdown)
        content_hash = content_sha256(normalized)
        page = fetch_page(conn, url)
        if page and page["content_hash"] == content_hash and page["deleted_at"] is None:
            touch_page(conn, url, original_status)
            conn.commit()
            return "unchanged"

        texts = chunk_markdown(normalized)
        vectors = embed_texts(texts)
        upsert_page(conn, url, content_hash, original_status)
        replace_chunks(conn, url, texts, vectors)
        conn.commit()
        return "embedded"


def fetch_page(conn, url: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT url, content_hash, last_verified_at, deleted_at, original_status
            FROM pages
            WHERE url = %s
            """,
            (url,),
        )
        return cur.fetchone()


def touch_page(conn, url: str, original_status: int | None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE pages
            SET last_verified_at = now(),
                original_status = %s,
                deleted_at = NULL,
                updated_at = now()
            WHERE url = %s
            """,
            (original_status, url),
        )


def upsert_page(
    conn, url: str, content_hash: str, original_status: int | None
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pages (url, content_hash, last_verified_at, deleted_at, original_status, updated_at)
            VALUES (%s, %s, now(), NULL, %s, now())
            ON CONFLICT (url) DO UPDATE SET
                content_hash = EXCLUDED.content_hash,
                last_verified_at = now(),
                deleted_at = NULL,
                original_status = EXCLUDED.original_status,
                updated_at = now()
            """,
            (url, content_hash, original_status),
        )


def tombstone_page(conn, url: str, original_status: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pages (url, content_hash, last_verified_at, deleted_at, original_status, updated_at)
            VALUES (%s, NULL, now(), now(), %s, now())
            ON CONFLICT (url) DO UPDATE SET
                content_hash = NULL,
                last_verified_at = now(),
                deleted_at = now(),
                original_status = EXCLUDED.original_status,
                updated_at = now()
            """,
            (url, original_status),
        )
        cur.execute("DELETE FROM chunks WHERE url = %s", (url,))


def replace_chunks(
    conn, url: str, texts: list[str], vectors: list[list[float]]
) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM chunks WHERE url = %s", (url,))
        for index, (text, vector) in enumerate(zip(texts, vectors)):
            cur.execute(
                """
                INSERT INTO chunks (url, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s::vector)
                """,
                (url, index, text, embedding_to_pgvector(vector)),
            )
