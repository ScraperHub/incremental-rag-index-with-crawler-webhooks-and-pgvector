"""Step 03: claim the delivery, then log. Hashing and embedding arrive in step 04."""

import logging

log = logging.getLogger(__name__)


def ingest_delivery(
    rid: str,
    url: str,
    original_status: int | None,
    cb_status: int | None,
    markdown: str,
) -> str:
    log.info(
        "queued work rid=%s url=%s original_status=%s cb_status=%s markdown_chars=%s",
        rid,
        url,
        original_status,
        cb_status,
        len(markdown),
    )
    return "accepted"
