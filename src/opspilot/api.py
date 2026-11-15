import json
import logging
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAIError
from pydantic import BaseModel, Field

from opspilot.explain import explain_log
from opspilot.llm import LLMClient, Message, StructuredOutputError
from opspilot.schemas import LogExplanation

# Entry point of the app: configure logging once, here (same format as queueless).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx2").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CHAT_SYSTEM = (
    "You are OpsPilot, an SRE assistant for QueueLess (FastAPI, Kafka, Postgres; "
    "services: queue-service, payment-worker, notification-worker and their outbox relays). "
    "Be concise and practical."
)

app = FastAPI(title="OpsPilot")


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()


class ExplainRequest(BaseModel):
    log: str = Field(min_length=1, max_length=8000)


class ExplainResponse(BaseModel):
    explanation: LogExplanation
    attempts: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/explain")
def explain(req: ExplainRequest, llm: Annotated[LLMClient, Depends(get_llm)]) -> ExplainResponse:
    try:
        r = explain_log(llm, req.log)
    except StructuredOutputError as exc:
        logger.error("explain_failed: %s", exc)
        raise HTTPException(status_code=502, detail="model did not return valid JSON") from exc
    except OpenAIError as exc:
        logger.error("llm_backend_error: %s", exc)
        raise HTTPException(status_code=503, detail="LLM backend unavailable") from exc
    return ExplainResponse(
        explanation=r.data,
        attempts=r.attempts,
        prompt_tokens=r.prompt_tokens,
        completion_tokens=r.completion_tokens,
        cost_usd=r.cost_usd,
    )


def sse(data: dict, event: str | None = None) -> str:
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(data, ensure_ascii=False)}\n\n"


def chat_events(llm: LLMClient, messages: list[Message]) -> Iterator[str]:
    try:
        for piece in llm.stream(messages, temperature=0.3, max_tokens=800):
            yield sse({"token": piece})
    except OpenAIError as exc:
        # The 200 status line is already sent, so an HTTP error is impossible now.
        logger.error("chat_stream_failed: %s", exc)
        yield sse({"message": "LLM backend failed"}, event="error")
        return
    yield sse({}, event="done")


@app.post("/chat")
def chat(req: ChatRequest, llm: Annotated[LLMClient, Depends(get_llm)]) -> StreamingResponse:
    messages: list[Message] = [{"role": "system", "content": CHAT_SYSTEM}]
    messages += [m.model_dump() for m in req.messages]
    return StreamingResponse(
        chat_events(llm, messages),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
