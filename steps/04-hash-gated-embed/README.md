# Step 04 — Hash-gated embed

What this step adds: normalize Markdown, SHA-256, compare to `pages.content_hash`. Unchanged pages only get `last_verified_at`. Changed pages re-chunk, embed (`text-embedding-3-small`), and replace `chunks`.

Requires `OPENAI_API_KEY` in `.env`.

## Run

Same as step 03 (`docker compose up`, `uvicorn app.main:app`). After a delivery, check `pages.content_hash` and `chunks`. Push the same URL again: if the page did not change, no new embeddings.

## Next

Step 05: tombstone 404/410 pages and drop their chunks; note redirect `url` headers.
