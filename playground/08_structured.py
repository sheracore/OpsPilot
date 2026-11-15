import logging

from opspilot.explain import explain_log
from opspilot.llm import LLMClient, StructuredOutputError
from queueless_samples import SAMPLES

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

llm = LLMClient()
comp_ok = sev_ok = 0

for log, want_comp, want_sev in SAMPLES:
    print("\n" + (log[:110] + "…" if len(log) > 110 else log))
    try:
        r = explain_log(llm, log)
    except StructuredOutputError as exc:
        print(f"  FAILED after {exc.attempts} attempts: {exc.last_text[:120]!r}")
        continue
    d = r.data
    comp_ok += d.component.value == want_comp
    sev_ok += d.severity.value == want_sev
    print(f"  component: {d.component.value:<22} expected {want_comp}")
    print(f"  severity:  {d.severity.value:<22} expected {want_sev}")
    print(f"  summary:   {d.summary}")
    print(f"  attempts={r.attempts} prompt_tokens={r.prompt_tokens} completion_tokens={r.completion_tokens}")

print(f"\ncomponent {comp_ok}/{len(SAMPLES)}, severity {sev_ok}/{len(SAMPLES)}")