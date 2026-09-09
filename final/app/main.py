import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.db import close_pool, init_pool
from app.ingest import ingest_delivery
from app.query import query_rag
from app.recrawl import run_recrawl
from app.stats import fetch_crawler_stats
from app.webhook import register_webhook
from app.config import settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    if settings.recrawl_interval_hours > 0:
        scheduler.add_job(
            run_recrawl,
            "interval",
            hours=settings.recrawl_interval_hours,
            id="recrawl",
            replace_existing=True,
        )
        scheduler.start()
        log.info("recrawl every %s hour(s)", settings.recrawl_interval_hours)
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)
    close_pool()


app = FastAPI(title="Incremental RAG index", lifespan=lifespan)
register_webhook(app, ingest_delivery)


class QueryBody(BaseModel):
    question: str
    k: int = Field(default=8, ge=1, le=32)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/query")
def query(body: QueryBody) -> dict:
    return query_rag(body.question, k=body.k)


@app.post("/recrawl")
def recrawl() -> dict:
    return {"rids": run_recrawl()}


@app.get("/crawler-stats")
def crawler_stats() -> dict:
    return fetch_crawler_stats()
