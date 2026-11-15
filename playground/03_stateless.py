import httpx

from opspilot.config import settings


def chat(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{settings.llm_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"},
        json={"model": settings.llm_model, "messages": messages, "temperature": 0},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


system = {"role": "system", "content": "You are an SRE assistant. Be brief."}

# Call 1: give the model some facts
first = [
    system,
    {
        "role": "user",
        "content": "Incident: order-svc fails with ERR_CONN_REFUSED to postgres:5432.",
    },
]
reply1 = chat(first)
print("1) reply:", reply1)

# Call 2: a brand-new request WITHOUT the history
print(
    "\n2) without history:",
    chat([system, {"role": "user", "content": "Which service is failing?"}]),
)

# Call 3: the same question WITH the history
history = first + [
    {"role": "assistant", "content": reply1},
    {"role": "user", "content": "Which service is failing?"},
]
print("\n3) with history:", chat(history))
