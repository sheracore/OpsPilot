import logging

from runbook_snippets import CASES, RUNBOOKS

from opspilot.embeddings import Embedder, cosine_matrix
from opspilot.logprep import normalize_log

logging.basicConfig(level=logging.WARNING)

emb = Embedder()
ids = [r["id"] for r in RUNBOOKS]
doc_vecs = emb.embed_documents([f"{r['title']}. {r['text']}" for r in RUNBOOKS])


def evaluate(name: str, queries: list[str]) -> None:
    sims = cosine_matrix(emb.embed_queries(queries), doc_vecs)
    hits, margins = 0, []
    print(f"\n=== {name}")
    for (_, want), row in zip(CASES, sims, strict=True):
        order = row.argsort()[::-1]
        best, second = order[0], order[1]
        ok = ids[best] == want
        hits += ok
        margins.append(float(row[best] - row[second]))
        print(
            f"{'OK  ' if ok else 'MISS'} want={want:<22} got={ids[best]:<22} "
            f"{row[best]:.2f} (2nd: {ids[second]} {row[second]:.2f})"
        )
    print(f"hit@1 {hits}/{len(CASES)}   mean margin {sum(margins) / len(margins):.3f}")


raw = [log for log, _ in CASES]
evaluate("raw log lines", raw)
evaluate("normalized log lines", [normalize_log(line) for line in raw])
