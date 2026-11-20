from functools import lru_cache

from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from opspilot.config import settings


def make_pool(url: str | None = None, wait_timeout: float = 10.0) -> ConnectionPool:
    pool = ConnectionPool(
        url or settings.database_url,
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        configure=register_vector,  # teach every new connection the `vector` type
        open=False,
    )
    try:
        pool.open(wait=True, timeout=wait_timeout)
    except Exception:
        pool.close()
        raise
    return pool


@lru_cache
def get_pool() -> ConnectionPool:
    return make_pool()
