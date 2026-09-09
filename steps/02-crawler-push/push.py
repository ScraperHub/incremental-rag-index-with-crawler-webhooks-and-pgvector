#!/usr/bin/env python3
"""Push seed URLs to the Crawlbase Crawler (Markdown + webhook callback)."""

from pathlib import Path

from app.crawler import push_url

SEEDS = Path(__file__).resolve().parent / "seeds" / "urls.txt"


def load_urls() -> list[str]:
    urls = []
    for line in SEEDS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


if __name__ == "__main__":
    for url in load_urls():
        rid = push_url(url)
        print(f"{rid}\t{url}")
