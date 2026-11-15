from openai import OpenAI

from opspilot.config import settings

client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

resp = client.chat.completions.create(
    model=settings.llm_model,
    messages=[
        {"role": "system", "content": "You are an SRE assistant. Answer in one sentence."},
        {"role": "user", "content": "What does HTTP 503 usually mean?"},
    ],
    temperature=0,
)

print("answer:       ", resp.choices[0].message.content)
print("finish_reason:", resp.choices[0].finish_reason)
print("usage:        ", resp.usage)
print("type:         ", type(resp))
