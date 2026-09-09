#!/usr/bin/env python3
"""Re-push every live URL in pages (same as the scheduled job)."""

from app.recrawl import run_recrawl

if __name__ == "__main__":
    for url, rid in run_recrawl().items():
        print(f"{rid}\t{url}")
