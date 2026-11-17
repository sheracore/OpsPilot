from types import SimpleNamespace

import numpy as np

from opspilot.embeddings import Embedder, cosine_matrix
from opspilot.logprep import normalize_log

LINE = (
    "payment-worker  | 2026-11-14 10:02:11,532 WARNING payment.worker: Retrying offset 4812 in 5s: "
    'connection to server at "payment-postgres" (172.19.0.6), port 5432 failed'
)


def test_normalize_removes_noise_and_keeps_meaning():
    out = normalize_log(LINE)
    assert "2026" not in out and "172.19.0.6" not in out and "4812" not in out
    assert "offset <n>" in out and "<ip>" in out
    assert "payment-worker" in out and "Retrying" in out


def test_normalize_replaces_uuid_but_keeps_short_status_codes():
    out = normalize_log("id 9b1e6c2a-31f4-4d0e-8a77-5c1f0d2e9a10 SMS provider returned 503")
    assert "<uuid>" in out and "503" in out


def test_embedder_orders_and_normalizes():
    fake_resp = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[0.0, 2.0]),
            SimpleNamespace(index=0, embedding=[3.0, 0.0]),
        ],
        usage=None,
    )
    e = Embedder.__new__(Embedder)  # skip __init__: no network client needed
    e.model, e.batch_size = "fake", 32
    e._client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kw: fake_resp))
    out = e.embed_documents(["a", "b"])
    assert np.allclose(out, [[1.0, 0.0], [0.0, 1.0]])


def test_cosine_of_normalized_vectors():
    a = np.array([[1.0, 0.0]], dtype=np.float32)
    b = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    assert np.allclose(cosine_matrix(a, b), [[0.0, 1.0]])
