# Step 01 — Postgres + pgvector

What this step adds: Docker Compose for PostgreSQL 16 with `pgvector`, and the `pages`, `chunks`, and `deliveries` schema.

## Run

```bash
docker compose up -d
```

Init SQL runs only on an empty volume. To re-apply after edits: `docker compose down -v && docker compose up -d`.

Connect with `DATABASE_URL=postgresql://rag:rag@localhost:5432/rag`.

## Next

Step 02 creates a Crawlbase Crawler and pushes seed URLs as Markdown with `callback=true`.
