import gzip
import os
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import connect, OperationalError

from app.db import close_pool, get_conn, init_pool
from app.ingest import ingest_delivery
from app.query import query_rag
from app.recrawl import list_live_urls, run_recrawl
from app.webhook import register_webhook
from tests.fakes import fake_chat_answer, fake_embed_query, fake_embed_texts

pytestmark = pytest.mark.integration


def _db_ready() -> bool:
    url = os.environ["DATABASE_URL"]
    try:
        with connect(url, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except OperationalError:
        return False


@pytest.fixture(scope="session")
def postgres():
    deadline = time.time() + 90
    while time.time() < deadline:
        if _db_ready():
            break
        time.sleep(2)
    else:
        pytest.skip("Postgres on DATABASE_URL is not reachable (start docker compose test db)")

    init_pool()
    yield
    close_pool()


@pytest.fixture
def db(postgres):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE chunks, pages, deliveries CASCADE")
        conn.commit()
    yield


@pytest.fixture
def embed_mocks(monkeypatch):
    monkeypatch.setattr("app.ingest.embed_texts", fake_embed_texts)
    monkeypatch.setattr("app.query.embed_query", fake_embed_query)
    monkeypatch.setattr("app.query.chat_answer", fake_chat_answer)


def test_ingest_embeds_then_skips_unchanged(db, embed_mocks, monkeypatch):
    calls = {"n": 0}

    def counting_embed(texts):
        calls["n"] += 1
        return fake_embed_texts(texts)

    monkeypatch.setattr("app.ingest.embed_texts", counting_embed)
    url = "https://example.com/doc"
    md = "# Hello\n\nStable body.\n"
    assert ingest_delivery("rid-1", url, 200, 200, md) == "embedded"
    assert ingest_delivery("rid-2", url, 200, 200, md) == "unchanged"
    assert ingest_delivery("rid-3", url, 200, 200, "# Hello\n\nChanged.\n") == "embedded"
    assert calls["n"] == 2

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE url = %s", (url,))
            assert cur.fetchone()["n"] >= 1
            cur.execute("SELECT content_hash FROM pages WHERE url = %s", (url,))
            assert cur.fetchone()["content_hash"]


def test_ingest_tombstone_404_drops_chunks(db, embed_mocks):
    url = "https://example.com/gone"
    ingest_delivery("rid-a", url, 200, 200, "# Live\n")
    assert ingest_delivery("rid-b", url, 404, 200, "") == "deleted"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE url = %s", (url,))
            assert cur.fetchone()["n"] == 0
            cur.execute("SELECT deleted_at FROM pages WHERE url = %s", (url,))
            assert cur.fetchone()["deleted_at"] is not None


def test_ingest_skips_bad_cb_status(db, embed_mocks):
    assert ingest_delivery("rid-x", "https://example.com/captcha", 200, 503, "nope") == "skipped"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM pages")
            assert cur.fetchone()["n"] == 0


def test_query_returns_citations_and_skips_tombstones(db, embed_mocks):
    live = "https://example.com/live"
    dead = "https://example.com/dead"
    ingest_delivery("q1", live, 200, 200, "# Pricing\n\nThe price is 9.\n")
    ingest_delivery("q2", dead, 200, 200, "# Old\n\nShould vanish.\n")
    ingest_delivery("q3", dead, 410, 200, "")
    result = query_rag("What is the price?", k=8)
    assert result["answer"].startswith("answer:")
    urls = {c["url"] for c in result["citations"]}
    assert live in urls
    assert dead not in urls
    assert all(c["last_verified_at"] for c in result["citations"])


def test_webhook_gzip_idempotent_rid(db, embed_mocks, monkeypatch):
    monkeypatch.setattr("app.ingest.embed_texts", fake_embed_texts)
    ingest_calls: list = []

    def tracking_ingest(*args):
        ingest_calls.append(args)
        return ingest_delivery(*args)

    app = FastAPI()
    register_webhook(app, tracking_ingest)
    client = TestClient(app)
    body = gzip.compress(b"# Page\n\nHello webhook.\n")
    headers = {
        "Content-Encoding": "gzip",
        "rid": "same-rid",
        "url": "https://example.com/hook",
        "original_status": "200",
        "cb_status": "200",
    }
    first = client.post("/webhook?token=test-secret", content=body, headers=headers)
    second = client.post("/webhook?token=test-secret", content=body, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(ingest_calls) == 1


def test_recrawl_pushes_live_urls_only(db, embed_mocks, monkeypatch):
    live = "https://example.com/a"
    dead = "https://example.com/b"
    ingest_delivery("r1", live, 200, 200, "# A\n")
    ingest_delivery("r2", dead, 200, 200, "# B\n")
    ingest_delivery("r3", dead, 404, 200, "")
    pushed: list[str] = []

    def fake_push(url: str) -> str:
        pushed.append(url)
        return "rid-fake"

    monkeypatch.setattr("app.recrawl.push_url", fake_push)
    assert list_live_urls() == [live]
    assert run_recrawl() == {live: "rid-fake"}
    assert pushed == [live]
