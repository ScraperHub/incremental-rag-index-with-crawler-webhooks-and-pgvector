# Step 05 — Deletes and redirects

What this step adds: if `original_status` is 404 or 410, set `pages.deleted_at` and `DELETE FROM chunks` for that URL. Non-200 `cb_status` still skips embedding (captcha / crawl failure).

The webhook `url` header is the post-redirect URL. Recrawl will re-push whatever is stored in `pages.url`.

## Run

Same uvicorn + webhook tunnel as step 04. Deliver a 404 for a previously indexed URL and confirm chunks are gone.

## Next

Step 06: scheduled recrawl of live `pages` URLs and crawler stats.
