import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.config import settings
from app.db import close_pool, init_pool
from app.ingest import ingest_delivery
from app.recrawl import run_recrawl
from app.stats import fetch_crawler_stats
from app.webhook import register_webhook

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


app = FastAPI(title="Incremental RAG index (recrawl)", lifespan=lifespan)
register_webhook(app, ingest_delivery)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/recrawl")
def recrawl() -> dict:
    return {"rids": run_recrawl()}


@app.get("/crawler-stats")
def crawler_stats() -> dict:
    return fetch_crawler_stats()
