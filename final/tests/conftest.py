import os

os.environ.setdefault("WEBHOOK_TOKEN", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://rag:rag@127.0.0.1:55432/rag")
os.environ.setdefault("RECRAWL_INTERVAL_HOURS", "0")
os.environ.setdefault("CRAWLBASE_TOKEN", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("CRAWLER_NAME", "incremental-rag-test")
