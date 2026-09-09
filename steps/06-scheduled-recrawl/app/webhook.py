from __future__ import annotations

import gzip
import json
from typing import Callable

from fastapi import BackgroundTasks, HTTPException, Query, Request, Response

from app.config import settings
from app.db import get_conn


def _header(request: Request, *names: str) -> str | None:
    for name in names:
        value = request.headers.get(name)
        if value:
            return value
    return None


def decode_body(raw: bytes, content_encoding: str | None) -> str:
    encoding = (content_encoding or "").lower()
    gzipped = "gzip" in encoding or (
        len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B
    )
    if gzipped:
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


def is_monitor_probe(user_agent: str, body_text: str) -> bool:
    if "crawlbase monitoring bot" in (user_agent or "").lower():
        return True
    stripped = body_text.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return False
        return bool(isinstance(payload, dict) and payload.get("monitor") is True)
    return False


def claim_delivery(
    rid: str, url: str | None, original_status: int | None, cb_status: int | None
) -> bool:
    """Insert rid. Returns False if this delivery was already processed."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deliveries (rid, url, original_status, cb_status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (rid) DO NOTHING
                """,
                (rid, url, original_status, cb_status),
            )
            inserted = cur.rowcount == 1
        conn.commit()
        return inserted


def register_webhook(app, ingest_delivery: Callable[..., None]) -> None:
    @app.post("/webhook")
    async def webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        token: str | None = Query(default=None),
    ) -> Response:
        raw = await request.body()
        markdown = decode_body(raw, request.headers.get("content-encoding"))
        if is_monitor_probe(request.headers.get("user-agent", ""), markdown):
            return Response(status_code=200)

        if settings.webhook_token and token != settings.webhook_token:
            raise HTTPException(status_code=401, detail="invalid webhook token")

        rid = _header(request, "rid", "RID")
        url = _header(request, "url", "URL")
        original_raw = _header(
            request, "original_status", "Original-Status", "original-status"
        )
        cb_raw = _header(request, "cb_status", "CB-Status", "cb-status")
        if not rid:
            raise HTTPException(status_code=400, detail="missing rid header")

        original_status = int(original_raw) if original_raw else None
        cb_status = int(cb_raw) if cb_raw else None

        if not claim_delivery(rid, url, original_status, cb_status):
            return Response(status_code=200)

        background_tasks.add_task(
            ingest_delivery, rid, url or "", original_status, cb_status, markdown
        )
        return Response(status_code=200)
