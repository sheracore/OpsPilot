import logging

import numpy as np

from opspilot.embeddings import Embedder, cosine_matrix

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx2").setLevel(logging.WARNING)

TEXTS = [
    "The payment service cannot connect to its database.",
    "Postgres refused the connection from the payment worker.",
    "The SMS provider returned a 503 error.",
    "Banana bread recipe with walnuts and brown sugar.",
    "سرویس پرداخت نمی‌تواند به پایگاه داده وصل شود.",
]

vecs = Embedder().embed_documents(TEXTS)
print(
    f"shape: {vecs.shape}  |  norm of vector 0: {np.linalg.norm(vecs[0]):.3f} because they have been normalized"
)
print(
    f"shape: {vecs.shape}  |  norm of vector 1: {np.linalg.norm(vecs[1]):.3f} because they have been normalized"
)
print(
    f"shape: {vecs.shape}  |  norm of vector 2: {np.linalg.norm(vecs[2]):.3f} because they have been normalized"
)
print(
    f"shape: {vecs.shape}  |  norm of vector 3: {np.linalg.norm(vecs[3]):.3f} because they have been normalized"
)
print(
    f"shape: {vecs.shape}  |  norm of vector 4: {np.linalg.norm(vecs[4]):.3f} because they have been normalized"
)
print(f"first 6 numbers of vector 0: {np.round(vecs[0][:6], 4)}")
print(f"storage: {vecs.shape[1] * 4} bytes per vector (float32)\n")

for i, row in enumerate(cosine_matrix(vecs, vecs)):
    print(f"{i}: " + " ".join(f"{x:5.2f}" for x in row) + f"   {TEXTS[i][:45]}")
