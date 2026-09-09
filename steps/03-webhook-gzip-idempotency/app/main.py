import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import close_pool, init_pool
from app.ingest import ingest_delivery
from app.webhook import register_webhook

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    yield
    close_pool()


app = FastAPI(title="Incremental RAG index (webhook)", lifespan=lifespan)
register_webhook(app, ingest_delivery)


@app.get("/health")
def health() -> dict:
    return {"ok": True}
