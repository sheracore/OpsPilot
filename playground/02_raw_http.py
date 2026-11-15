import json

import httpx

from opspilot.config import settings

payload = {
    "model": settings.llm_model,
    "messages": [
        {"role": "system", "content": "You are an SRE assistant. Answer in one sentence."},
        {"role": "user", "content": "What does HTTP 503 usually mean?"},
    ],
    "temperature": 0,
}

resp = httpx.post(
    f"{settings.llm_base_url}/chat/completions",
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    json=payload,
    timeout=120,
)
resp.raise_for_status()
data = resp.json()

print(json.dumps(data, indent=2))
print("\nanswer:", data["choices"][0]["message"]["content"])
print("usage:", data["usage"])
