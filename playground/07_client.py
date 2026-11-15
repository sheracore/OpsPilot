import logging

from opspilot.llm import LLMClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx2").setLevel(logging.WARNING)

llm = LLMClient()
messages = [
    {"role": "system", "content": "You are an SRE assistant. Be brief."},
    {
        "role": "user",
        "content": "What are the 3 most common causes of a Postgres 'too many connections' error?",
    },
]

print("--- complete() ---")
result = llm.complete(messages)
print(result.text)
print(result)

print("\n--- complete() with a tiny max_tokens ---")
llm.complete(messages, max_tokens=5)

print("\n--- stream() ---")
for piece in llm.stream(messages):
    print(piece, end="", flush=True)
print()
