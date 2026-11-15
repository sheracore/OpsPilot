# OpsPilot

AI on-call copilot for [QueueLess](https://github.com/sheracore/queueless): explains log lines
as structured JSON and answers SRE questions with streaming. Built on a local LLM via any
OpenAI-compatible API (Ollama by default).

## Run locally

```bash
ollama pull llama3.2:3b
uv sync
uv run uvicorn opspilot.api:app --reload --port 8100
```

## Run with Docker

Ollama must listen on an address the container can reach (`OLLAMA_HOST=0.0.0.0` on Linux).

```bash
docker compose up --build -d
curl localhost:8100/health
```

## API

- `GET /health`
- `POST /explain` `{"log": "..."}` → `{explanation: {summary, severity, component}, attempts, tokens, cost}`
- `POST /chat` `{"messages": [...]}` → Server-Sent Events (`data: {"token": ...}`, then `event: done`)

## Development

```bash
uv run pre-commit install
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
```

Configuration is read from `OPSPILOT_*` environment variables (see `.env.example`).
