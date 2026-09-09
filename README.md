# Incremental RAG index (companion code)

Runnable FastAPI + PostgreSQL 16 / pgvector app for the tutorial **Keep Your RAG Index Fresh: Incremental Re-Indexing with the Crawlbase Crawler, Webhooks, and pgvector**.

- `final/` — the complete app. Start here.
- `steps/01` … `steps/07` — cumulative snapshots, one per article section. `steps/07` is the same code as `final/`.

## What you need

- Python 3.11+ and Docker
- A Crawlbase token and an OpenAI API key
- A public HTTPS tunnel (ngrok, Cloudflare Tunnel). This is required, not optional: the Crawler delivers results by POSTing to your callback URL, so it must reach you from the internet.

Commands below are bash. On Windows, activate the venv with `.venv\Scripts\activate` and use PowerShell quoting for the `curl` call.

## Run

Everything runs from `final/`.

### 1. Start Postgres

```bash
cd final
docker compose up -d
```

`sql/schema.sql` loads on first boot. Wait for the healthcheck to pass.

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Fill in `CRAWLBASE_TOKEN`, `CRAWLER_NAME`, `WEBHOOK_TOKEN`, and `OPENAI_API_KEY`. The remaining variables are documented inline in `.env.example` and have working defaults. Never commit `.env`.

### 4. Create the crawler

In the Crawlbase dashboard, create a crawler whose name matches `CRAWLER_NAME` and choose **webhook delivery** (not Cloud Storage). The two modes are exclusive at create time. Leave the callback URL empty for now.

### 5. Start the app and expose it

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open a tunnel to port 8000, then set the crawler callback URL to:

```
https://<your-host>/webhook?token=<WEBHOOK_TOKEN>
```

`GET /health` should return `{"ok": true}`. Crawlbase monitoring probes also get a 200.

### 6. Push the seed URLs

```bash
python push.py
```

Edit `seeds/urls.txt` first if you want a different corpus. Each push prints an `rid`.

### 7. Query

Crawling is asynchronous. Wait until you see `POST /webhook` 200s in the uvicorn log before querying.

```bash
curl -s http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How do Crawler webhooks deliver results?"}'
```

Citations include `last_verified_at`.

### 8. Recrawl

```bash
python recrawl.py
# or
curl -X POST http://127.0.0.1:8000/recrawl
```

APScheduler also re-pushes every `RECRAWL_INTERVAL_HOURS` (`0` disables it; use cron with `recrawl.py` instead). Check the queue with `GET http://127.0.0.1:8000/crawler-stats`.

## Tests

From `final/`, with Docker running:

```bash
docker compose -f docker-compose.test.yml -p rag-test run --rm tests
```

Starts Postgres 16 + pgvector, installs dependencies, and runs pytest. OpenAI and Crawlbase are mocked; hash skip, 404 tombstones, gzip webhook idempotency, and `/query` citations are covered.

## `steps/` → article

| Folder | Article section |
|---|---|
| [`steps/01-postgres-pgvector`](steps/01-postgres-pgvector) | Setting up Postgres + pgvector |
| [`steps/02-crawler-push`](steps/02-crawler-push) | Creating the Crawler and pushing Markdown |
| [`steps/03-webhook-gzip-idempotency`](steps/03-webhook-gzip-idempotency) | A production-safe webhook: gzip, headers, `rid` |
| [`steps/04-hash-gated-embed`](steps/04-hash-gated-embed) | Hash-gated re-embedding |
| [`steps/05-deletes-and-redirects`](steps/05-deletes-and-redirects) | Deletions and redirects |
| [`steps/06-scheduled-recrawl`](steps/06-scheduled-recrawl) | Scheduling recrawls and crawler stats |
| [`steps/07-query-freshness`](steps/07-query-freshness) | Answering with freshness-aware citations |

Each folder has its own `README.md` and runs standalone. Work from `final/` unless you are following the article section by section.

---

Copyright 2026 [Crawlbase](https://crawlbase.com/)
