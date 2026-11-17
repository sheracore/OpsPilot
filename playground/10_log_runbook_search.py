import logging

from runbook_snippets import CASES, RUNBOOKS

from opspilot.embeddings import Embedder, cosine_matrix
from opspilot.explain import explain_log
from opspilot.llm import LLMClient
from opspilot.logprep import normalize_log

logging.basicConfig(level=logging.WARNING)

emb = Embedder()
ids = [r["id"] for r in RUNBOOKS]
doc_vecs = emb.embed_documents([f"{r['title']}. {r['text']}" for r in RUNBOOKS])


def evaluate(name: str, queries: list[str]) -> None:
    sims = cosine_matrix(emb.embed_queries(queries), doc_vecs)
    top1 = top3 = 0
    margins = []
    print(f"\n=== {name}")
    for (_, want), row in zip(CASES, sims, strict=True):
        order = list(row.argsort()[::-1])
        rank = order.index(ids.index(want)) + 1
        top1 += rank == 1
        top3 += rank <= 3
        margins.append(float(row[order[0]] - row[order[1]]))
        print(
            f"rank={rank} want={want:<22} got={ids[order[0]]:<22} "
            f"top {row[order[0]]:.2f} | correct {row[ids.index(want)]:.2f}"
        )
    n = len(CASES)
    print(f"hit@1 {top1}/{n}   hit@3 {top3}/{n}   mean margin {sum(margins) / n:.3f}")


raw = [log for log, _ in CASES]
evaluate("raw log lines", raw)
evaluate("normalized log lines", [normalize_log(line) for line in raw])

llm = LLMClient()
summaries = [explain_log(llm, log).data.summary for log in raw]
print("\n" + "\n".join(summaries))
evaluate("LLM summary of the log (Part 3)", summaries)
