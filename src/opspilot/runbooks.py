from dataclasses import dataclass

from psycopg_pool import ConnectionPool

from opspilot.embeddings import Embedder


@dataclass(frozen=True)
class Hit:
    id: str
    title: str
    services: list[str]
    body: str
    score: float  # cosine similarity: 1 - cosine distance


def runbook_text(r: dict) -> str:
    return f"{r['title']}. {r['text']}"


def index_runbooks(pool: ConnectionPool, embedder: Embedder, runbooks: list[dict]) -> int:
    vectors = embedder.embed_documents([runbook_text(r) for r in runbooks])
    # strict=True ensures both collections have the same number of elements.
    # If their lengths differ, Python raises a ValueError rather than silently dropping unmatched elements.
    rows = [
        (r["id"], r["title"], r["text"], r["services"], v, embedder.model)
        for r, v in zip(runbooks, vectors, strict=True)
    ]
    with pool.connection() as conn, conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO runbooks (id, title, body, services, embedding, embed_model)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO
            UPDATE SET
                title = EXCLUDED.title, body = EXCLUDED.body, services = EXCLUDED.services,
                embedding = EXCLUDED.embedding, embed_model = EXCLUDED.embed_model
            """,
            rows,
        )
    return len(rows)


def search_runbooks(
    pool: ConnectionPool,
    embedder: Embedder,
    query: str,
    services: list[str] | None = None,
    k: int = 5,
) -> list[Hit]:
    q = embedder.embed_queries([query])[0]
    where = ["embed_model = %(model)s"]
    params: dict = {"q": q, "model": embedder.model, "k": k}
    #  ::text[] is PostgreSQL type casting.
    #       It explicitly tells PostgreSQL that this parameter should be interpreted as an array of text values.
    #  && means **array overlap**. In other words, it checks whether two arrays have at least one common element.
    if services:
        where.append("services && %(services)s::text[]")
        params["services"] = services
    # `where` holds only fixed SQL fragments; every value goes through bound parameters.
    sql = f"""
        SELECT id, title, services, body, 1 - (embedding <=> %(q)s) AS score
        FROM runbooks
        WHERE {" AND ".join(where)}
        ORDER BY embedding <=> %(q)s
        LIMIT %(k)s
    """
    with pool.connection() as conn, conn.transaction():
        # keep scanning the index until enough rows pass the filter (pgvector >= 0.8)
        # relaxed_order lets the index return results slightly out of order.
        #   We re-sort in Python, which is cheap for k ≤ 20.
        # SET LOCAL lasts only for this transaction, so it never leaks into other pooled connections.
        conn.execute("SET LOCAL hnsw.iterative_scan = 'relaxed_order'")
        rows = conn.execute(sql, params).fetchall()
    hits = [Hit(**r) for r in rows]
    hits.sort(key=lambda h: h.score, reverse=True)  # relaxed_order can be slightly unsorted
    return hits
