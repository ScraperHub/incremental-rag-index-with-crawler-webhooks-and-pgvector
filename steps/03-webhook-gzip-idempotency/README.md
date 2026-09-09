# Step 03 — Webhook: gzip, headers, idempotency

What this step adds: FastAPI `POST /webhook` that gunzips the body, reads `rid` / `url` / `original_status` / `cb_status`, ACKs Crawlbase monitoring probes, inserts `deliveries` with `ON CONFLICT (rid) DO NOTHING`, and enqueues work via `BackgroundTasks`.

Ingest here only logs the payload. Embedding starts in step 04.

## Run

```bash
docker compose up -d
cp .env.example .env   # set WEBHOOK_TOKEN, CRAWLBASE_TOKEN, DATABASE_URL
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expose the app with ngrok or Cloudflare Tunnel. Point the crawler callback at:

`https://<tunnel>/webhook?token=YOUR_WEBHOOK_TOKEN`

Push URLs (`python push.py`). You should see 200s and log lines; duplicate `rid`s skip work.

## Next

Step 04: normalize Markdown, SHA-256, embed only when the hash changes.
