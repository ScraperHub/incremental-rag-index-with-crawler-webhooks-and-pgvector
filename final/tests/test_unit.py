import gzip

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.normalize import content_sha256, normalize_markdown
from app.webhook import decode_body, is_monitor_probe, register_webhook


def test_normalize_collapses_blank_lines_and_trailing_space():
    raw = "Hello   \n\n\n\nWorld  \r\n"
    got = normalize_markdown(raw)
    assert got == "Hello\n\n\nWorld\n"
    assert content_sha256(got) == content_sha256(normalize_markdown("Hello\n\n\nWorld"))


def test_decode_gzip_and_plain():
    plain = "# Title\n\nBody"
    assert decode_body(plain.encode(), None) == plain
    zipped = gzip.compress(plain.encode())
    assert decode_body(zipped, "gzip") == plain
    assert decode_body(zipped, None) == plain


def test_monitor_probe_user_agent_and_json():
    assert is_monitor_probe("Crawlbase Monitoring Bot 1.0", "{}")
    assert is_monitor_probe("curl/8.0", '{"monitor": true}')
    assert not is_monitor_probe("curl/8.0", "# markdown")


def test_webhook_rejects_bad_token():
    ingest_calls: list = []
    app = FastAPI()
    register_webhook(app, lambda *a: ingest_calls.append(a))
    client = TestClient(app)
    res = client.post("/webhook?token=wrong", content=b"hi")
    assert res.status_code == 401
    assert ingest_calls == []


def test_webhook_monitor_does_not_ingest():
    ingest_calls: list = []
    app = FastAPI()
    register_webhook(app, lambda *a: ingest_calls.append(a))
    client = TestClient(app)
    res = client.post(
        "/webhook?token=test-secret",
        content=b'{"monitor": true}',
        headers={"User-Agent": "Crawlbase Monitoring Bot 1.0"},
    )
    assert res.status_code == 200
    assert ingest_calls == []


def test_chunk_markdown_splits_long_text():
    from app.chunk import chunk_markdown

    text = "word " * 2000
    chunks = chunk_markdown(text)
    assert len(chunks) > 1
    assert all(chunks)


def test_embedding_to_pgvector_format():
    from app.embed import embedding_to_pgvector

    assert embedding_to_pgvector([1.0, -0.5]) == "[1.0,-0.5]"


def test_rid_from_crawler_response():
    from app.crawler import _rid_from_response

    assert _rid_from_response({"json": {"rid": "abc"}}) == "abc"
    assert _rid_from_response({"body": b'{"rid": "xyz"}'}) == "xyz"
    assert _rid_from_response({"body": "not-json"}) is None


def test_fake_embed_length():
    from tests.fakes import fake_embed_texts

    vecs = fake_embed_texts(["a", "b"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 1536
    assert vecs[0] != vecs[1]
