# Step 06 — Scheduled recrawl and stats

What this step adds: `app/recrawl.py` re-pushes every live URL; APScheduler runs it on `RECRAWL_INTERVAL_HOURS` (set `0` to disable). `GET /crawler-stats` calls `GET /crawler/{token}/stats`. CLI: `python recrawl.py`. Cron is equivalent.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
curl -X POST http://127.0.0.1:8000/recrawl
curl http://127.0.0.1:8000/crawler-stats
```

Confirm the stats path against current [Crawler docs](https://crawlbase.com/docs/crawler/) if the API moves.

## Next

Step 07: `POST /query` with cosine search and `last_verified_at` on citations.
