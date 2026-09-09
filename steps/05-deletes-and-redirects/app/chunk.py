import tiktoken

ENCODING = "cl100k_base"
CHUNK_TOKENS = 512
OVERLAP_TOKENS = 64


def chunk_markdown(text: str) -> list[str]:
    enc = tiktoken.get_encoding(ENCODING)
    token_ids = enc.encode(text)
    if not token_ids:
        return []
    chunks: list[str] = []
    start = 0
    n = len(token_ids)
    while start < n:
        end = min(start + CHUNK_TOKENS, n)
        chunks.append(enc.decode(token_ids[start:end]).strip())
        if end >= n:
            break
        start = max(end - OVERLAP_TOKENS, start + 1)
    return [c for c in chunks if c]
