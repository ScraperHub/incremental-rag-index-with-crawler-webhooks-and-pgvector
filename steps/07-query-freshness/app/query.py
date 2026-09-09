from app.db import get_conn
from app.embed import chat_answer, embed_query, embedding_to_pgvector


def query_rag(question: str, k: int = 8) -> dict:
    qvec = embedding_to_pgvector(embed_query(question))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.content, c.url, p.last_verified_at
                FROM chunks c
                JOIN pages p ON p.url = c.url
                WHERE p.deleted_at IS NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (qvec, k),
            )
            rows = cur.fetchall()

    citations = []
    blocks = []
    for row in rows:
        verified = row["last_verified_at"]
        verified_s = verified.isoformat() if verified else None
        excerpt = row["content"][:500]
        citations.append(
            {
                "url": row["url"],
                "last_verified_at": verified_s,
                "excerpt": excerpt,
            }
        )
        blocks.append(
            f"URL: {row['url']}\nlast_verified_at: {verified_s}\n{row['content']}"
        )

    answer = (
        chat_answer(question, blocks)
        if blocks
        else "No indexed chunks yet. Push URLs and wait for webhook deliveries."
    )
    return {"answer": answer, "citations": citations}
