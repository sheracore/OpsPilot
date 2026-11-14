import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass

from openai import OpenAI

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
    ) -> LLMResult:
        start = time.perf_counter()
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
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
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

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
            r.model, r.prompt_tokens, r.completion_tokens,
            r.latency_ms, r.finish_reason, r.cost_usd,
        )
        if r.finish_reason == "length":
            logger.warning("llm_truncated model=%s: output hit max_tokens and is cut off", r.model)