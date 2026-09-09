import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _optional_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    return int(raw)


@dataclass(frozen=True)
class Settings:
    crawlbase_token: str
    crawler_name: str
    webhook_token: str
    database_url: str
    openai_api_key: str
    embedding_model: str
    chat_model: str
    page_wait: int | None
    ajax_wait: int | None
    recrawl_interval_hours: int


def load_settings() -> Settings:
    return Settings(
        crawlbase_token=os.getenv("CRAWLBASE_TOKEN", ""),
        crawler_name=os.getenv("CRAWLER_NAME", "incremental-rag"),
        webhook_token=os.getenv("WEBHOOK_TOKEN", ""),
        database_url=os.getenv(
            "DATABASE_URL", "postgresql://rag:rag@localhost:5432/rag"
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        page_wait=_optional_int("PAGE_WAIT"),
        ajax_wait=_optional_int("AJAX_WAIT"),
        recrawl_interval_hours=int(os.getenv("RECRAWL_INTERVAL_HOURS", "24")),
    )


settings = load_settings()
