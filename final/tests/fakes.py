import hashlib


def fake_embed_texts(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < 1536:
            for byte in digest:
                values.append((byte / 127.5) - 1.0)
            digest = hashlib.sha256(digest).digest()
        out.append(values[:1536])
    return out


def fake_embed_query(text: str) -> list[float]:
    return fake_embed_texts([text])[0]


def fake_chat_answer(question: str, context_blocks: list[str]) -> str:
    return f"answer:{question}:{len(context_blocks)}"
