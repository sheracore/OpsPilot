import logging

from runbook_snippets import RUNBOOKS

from opspilot.db import get_pool
from opspilot.embeddings import Embedder
from opspilot.runbooks import index_runbooks

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx2").setLevel(logging.WARNING)

pool = get_pool()
print(f"indexed {index_runbooks(pool, Embedder(), RUNBOOKS)} runbooks")
pool.close()
