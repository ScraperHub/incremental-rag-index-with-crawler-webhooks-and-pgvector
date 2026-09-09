# Step 07 — Query with freshness

What this step adds: `POST /query` embeds the question, cosine-searches `chunks`, skips tombstoned pages, answers with a chat model, and returns citations including `last_verified_at`.

This snapshot matches `code/final/`.

## Run

```bash
docker compose up -d
uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://127.0.0.1:8000/query -H "Content-Type: application/json" -d "{\"question\":\"What is the Crawlbase Crawler?\"}"
```

See the repo [`code/README.md`](../../README.md) for the full dashboard / tunnel / seed / recrawl flow.
