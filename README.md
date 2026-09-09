# Incremental RAG index (companion code)

Runnable FastAPI + PostgreSQL 16 / pgvector app for the tutorial **Keep Your RAG Index Fresh: Incremental Re-Indexing with the Crawlbase Crawler, Webhooks, and pgvector**.

The article is **not** duplicated here. Read [`draft/incremental-rag-index-with-crawler-webhooks-and-pgvector.md`](../draft/incremental-rag-index-with-crawler-webhooks-and-pgvector.md) in the parent repo. This README is how to run `final/` and how `steps/` map to that article.

## Layout

- `final/` — complete app (union of the steps).
- `steps/01` … `steps/07` — cumulative snapshots, one folder per article beat.

Do not commit `.env`. Copy `.env.example` only.

## Run `final/`

Python 3.11+, Docker, a Crawlbase token, and an OpenAI key.

### 1. Postgres

```bash
cd final
docker compose up -d
```

Wait until the healthcheck passes. Schema loads from `sql/schema.sql` on first boot.

### 2. Environment

```bash
cp .env.example .env
```

Set `CRAWLBASE_TOKEN`, `CRAWLER_NAME`, `WEBHOOK_TOKEN`, `OPENAI_API_KEY`. Optional: `PAGE_WAIT` / `AJAX_WAIT` (JS-token crawler), `RECRAWL_INTERVAL_HOURS` (`0` disables the in-process scheduler).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Dashboard crawler

1. In the Crawlbase dashboard, create a crawler named to match `CRAWLER_NAME`.
2. Choose **webhook delivery** (not Cloud Storage). The two modes are exclusive at create time.
3. Leave the callback URL empty until the tunnel exists, or update it after step 5.

### 4. App + tunnel

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expose port 8000 with ngrok or Cloudflare Tunnel. Set the crawler callback to:

```
https://<your-host>/webhook?token=<WEBHOOK_TOKEN>
```

`GET /health` should return `{"ok": true}`. Crawlbase monitoring probes (`User-Agent: Crawlbase Monitoring Bot 1.0`) also receive 200.

### 5. Seed push

```bash
python push.py
```

Edit `seeds/urls.txt` first if you want a different corpus. Pushes use `callback=true`, `format=md`, `md_readability=true`.

### 6. Recrawl

After pages exist:

```bash
python recrawl.py
# or
curl -X POST http://127.0.0.1:8000/recrawl
```

APScheduler also re-pushes on `RECRAWL_INTERVAL_HOURS`. Cron calling `recrawl.py` is the same job.

Crawler queue: `GET http://127.0.0.1:8000/crawler-stats`.

### 7. Query

```bash
curl -s http://127.0.0.1:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"How do Crawler webhooks deliver results?\"}"
```

On Unix, drop the `^` line continuations. Citations include `last_verified_at`.

## Tests

From `final/`, with Docker running:

```bash
docker compose -f docker-compose.test.yml -p rag-test run --rm tests
```

This starts Postgres 16 + pgvector, installs deps, and runs pytest. OpenAI and Crawlbase are mocked; hash skip, 404 tombstones, gzip webhook idempotency, and `/query` citations are covered.

## `steps/` → article

| Folder | Article section |
|---|---|
| [`steps/01-postgres-pgvector`](steps/01-postgres-pgvector) | Setting up Postgres + pgvector |
| [`steps/02-crawler-push`](steps/02-crawler-push) | Creating the Crawler and pushing Markdown |
| [`steps/03-webhook-gzip-idempotency`](steps/03-webhook-gzip-idempotency) | Production-safe webhook |
| [`steps/04-hash-gated-embed`](steps/04-hash-gated-embed) | Hash-gated re-embedding |
| [`steps/05-deletes-and-redirects`](steps/05-deletes-and-redirects) | Deletions and redirects |
| [`steps/06-scheduled-recrawl`](steps/06-scheduled-recrawl) | Scheduling recrawls and crawler stats |
| [`steps/07-query-freshness`](steps/07-query-freshness) | Freshness-aware citations (same as `final/`) |

Each step folder has its own `README.md` (what it adds, how to run, what comes next). Work from `final/` unless you are following the article section by section.

---

Copyright 2026 [Crawlbase](https://crawlbase.com/)
