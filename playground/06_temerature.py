from openai import OpenAI

from opspilot.config import settings

client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

prompt = [
    {"role": "user", "content": "Invent a name for an AI incident-response bot. Reply with the name only."}
]

for temperature in (0.0, 0.8, 1.5):
    names = []
    for _ in range(4):
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=prompt,
            temperature=temperature,
            max_tokens=10,
        )
        names.append(resp.choices[0].message.content.strip())
    print(f"temperature={temperature}: {names}")