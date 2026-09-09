from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embedding_to_pgvector(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = client().embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    by_index = {item.index: item.embedding for item in response.data}
    return [by_index[i] for i in range(len(texts))]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def chat_answer(question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(context_blocks)
    response = client().chat.completions.create(
        model=settings.chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer using only the provided sources. "
                    "If the sources are insufficient, say so. "
                    "Mention URLs when you rely on a source."
                ),
            },
            {
                "role": "user",
                "content": f"Sources:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()
