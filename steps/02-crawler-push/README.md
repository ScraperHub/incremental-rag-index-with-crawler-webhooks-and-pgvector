# Step 02 — Crawler push (Markdown)

What this step adds: `app/crawler.py` and `push.py` — enqueue URLs with `crawler`, `callback=true`, `format=md`, and `md_readability=true`.

## Run

1. Create a **webhook-mode** crawler in the Crawlbase dashboard (callback URL can be a placeholder until step 03).
2. Copy `.env.example` to `.env` and set `CRAWLBASE_TOKEN` and `CRAWLER_NAME`.
3. Install deps and push seeds:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python push.py
```

Each line prints `rid` and URL. Crawls run asynchronously; deliveries need the webhook in step 03.

## Next

Step 03: FastAPI webhook — gzip, metadata headers, `rid` uniqueness, fast 200.
