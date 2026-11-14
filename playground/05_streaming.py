import time

from openai import OpenAI

from opspilot.config import settings

client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

start = time.perf_counter()
first_token_at = None
pieces: list[str] = []

stream = client.chat.completions.create(
    model=settings.llm_model,
    messages=[
        {"role": "system", "content": "You are an SRE assistant."},
        {"role": "user", "content": "In 5 short bullet points: how do I debug a pod stuck in CrashLoopBackOff?"},
    ],
    temperature=0,
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta.content if chunk.choices else None
    if not delta:
        continue
    if first_token_at is None:
        first_token_at = time.perf_counter()
    pieces.append(delta)
    print(delta, end="", flush=True)

end = time.perf_counter()
print("\n")
print(f"time to first token: {(first_token_at - start) * 1000:.0f} ms")
print(f"total time:          {(end - start) * 1000:.0f} ms")
print(f"chunks received:     {len(pieces)}")
