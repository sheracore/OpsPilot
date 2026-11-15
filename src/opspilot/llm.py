import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass

from openai import BaseModel, OpenAI
from pydantic import ValidationError

from opspilot.config import settings

logger = logging.getLogger(__name__)

Message = dict[str, str]


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    finish_reason: str | None
    cost_usd: float


@dataclass(frozen=True)
class StructuredResult[T]:
    data: T
    attempts: int
    prompt_tokens: int  # summed over all attempts
    completion_tokens: int
    cost_usd: float


class StructuredOutputError(Exception):
    def __init__(self, attempts: int, last_text: str, problem: str) -> None:
        super().__init__(f"no valid JSON after {attempts} attempts: {problem}")
        self.attempts = attempts
        self.last_text = last_text
        self.problem = problem


def _strip_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json ... ``` even when told not to."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t.rsplit("```", 1)[0]
    return t.strip()


def _describe(exc: ValidationError) -> str:
    parts = [f"{'.'.join(map(str, e['loc'])) or 'root'}: {e['msg']}" for e in exc.errors()]
    return "; ".join(parts)[:500]


class LLMClient:
    def __init__(
        self,
        model: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        self.model = model or settings.llm_model
        self._client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int = 512,
        response_format: dict | None = None,
    ) -> LLMResult:
        extra = {"response_format": response_format} if response_format else {}
        start = time.perf_counter()
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        choice = resp.choices[0]
        prompt_tokens = resp.usage.prompt_tokens if resp.usage else 0
        completion_tokens = resp.usage.completion_tokens if resp.usage else 0

        result = LLMResult(
            text=choice.message.content or "",
            model=resp.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            finish_reason=choice.finish_reason,
            cost_usd=self._cost(prompt_tokens, completion_tokens),
        )
        self._log(result)
        return result

    def stream(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> Iterator[str]:
        start = time.perf_counter()
        first_at: float | None = None
        usage = None
        finish_reason: str | None = None
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )
            for chunk in stream:
                if chunk.usage:
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                if choice.delta.content:
                    if first_at is None:
                        first_at = time.perf_counter()
                    yield choice.delta.content
        finally:
            end = time.perf_counter()
            pt = usage.prompt_tokens if usage else 0
            ct = usage.completion_tokens if usage else 0
            logger.info(
                "llm_stream model=%s ttft_ms=%.0f total_ms=%.0f prompt_tokens=%d "
                "completion_tokens=%d finish_reason=%s cost_usd=%.6f",
                self.model,
                ((first_at or end) - start) * 1000,
                (end - start) * 1000,
                pt,
                ct,
                finish_reason,
                self._cost(pt, ct),
            )

    def complete_json[T: BaseModel](
        self,
        messages: list[Message],
        schema: type[T],
        max_attempts: int = 3,
        max_tokens: int = 400,
    ) -> StructuredResult[T]:
        history = list(messages)
        prompt_tokens = completion_tokens = 0
        cost = 0.0
        last_text, problem = "", ""

        for attempt in range(1, max_attempts + 1):
            result = self.complete(
                history,
                temperature=0.0,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            prompt_tokens += result.prompt_tokens
            completion_tokens += result.completion_tokens
            cost += result.cost_usd
            last_text = result.text

            if result.finish_reason == "length":
                problem = "Your answer was cut off before the JSON ended. Keep it shorter."
            else:
                try:
                    data = schema.model_validate_json(_strip_fences(result.text))
                except ValidationError as exc:
                    problem = _describe(exc)
                else:
                    return StructuredResult(data, attempt, prompt_tokens, completion_tokens, cost)

            logger.warning(
                "llm_json_retry attempt=%d/%d problem=%s", attempt, max_attempts, problem
            )
            history = history + [
                {"role": "assistant", "content": result.text},
                {
                    "role": "user",
                    "content": f"That was not valid: {problem}\nReply again with ONLY the corrected JSON object.",
                },
            ]

        raise StructuredOutputError(max_attempts, last_text, problem)

    @staticmethod
    def _cost(prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens * settings.llm_input_price_per_mtok
            + completion_tokens * settings.llm_output_price_per_mtok
        ) / 1_000_000

    @staticmethod
    def _log(r: LLMResult) -> None:
        logger.info(
            "llm_call model=%s prompt_tokens=%d completion_tokens=%d "
            "latency_ms=%.0f finish_reason=%s cost_usd=%.6f",
            r.model,
            r.prompt_tokens,
            r.completion_tokens,
            r.latency_ms,
            r.finish_reason,
            r.cost_usd,
        )
        if r.finish_reason == "length":
            logger.warning("llm_truncated model=%s: output hit max_tokens and is cut off", r.model)
