import logging
import time

import numpy as np
from openai import OpenAI

from opspilot.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(
        self,
        model: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        batch_size: int = 32,
    ) -> None:
        self.model = model or settings.embed_model
        self.batch_size = batch_size
        self._client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed([settings.embed_doc_prefix + t for t in texts])

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self._embed([settings.embed_query_prefix + t for t in texts])

    def _embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        start = time.perf_counter()
        vectors: list[list[float]] = []
        tokens = 0
        for i in range(0, len(texts), self.batch_size):
            resp = self._client.embeddings.create(
                model=self.model,
                input=texts[i : i + self.batch_size],
                encoding_format="float",
            )
            vectors.extend(d.embedding for d in sorted(resp.data, key=lambda d: d.index))
            tokens += resp.usage.prompt_tokens if resp.usage else 0

        arr = np.asarray(vectors, dtype=np.float32)
        # 1. Calculate each vector's magnitude
        norms = np.linalg.norm(arr, axis=1, keepdims=True)  # ||A|| magnitude of each text
        # 2. Unit length(L2 normalization); avoid divide-by-zero (If a vector's norm is zero, use 1.0)
        # Normalize vectors, protecting against division by zero
        arr = arr / np.where(norms == 0, 1.0, norms)

        logger.info(
            "embed_call model=%s texts=%d dim=%d prompt_tokens=%d latency_ms=%.0f",
            self.model,
            len(texts),
            arr.shape[1],
            tokens,
            (time.perf_counter() - start) * 1000,
        )
        return arr


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity of every row of `a` with every row of `b`.

    Both inputs must already be L2-normalized (Embedder guarantees this),
    so the cosine is just a dot product.
    b.T: Transposes matrix b (swaps rows and columns).
    @: Performs matrix multiplication.
    Each row includes one Text(matric, 1*768) so Transposing them don't ruin multiplication.
    """
    return a @ b.T
