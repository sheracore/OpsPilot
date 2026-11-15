import pytest

from opspilot.llm import LLMClient, LLMResult, StructuredOutputError
from opspilot.schemas import LogExplanation

GOOD = '{"summary": "DB down", "severity": "high", "component": "payment-worker"}'

class FakeLLM(LLMClient):
    """Replays canned (text, finish_reason) replies; no network, no Ollama."""

    def __init__(self, replies):
        self._replies = iter(replies)
        self.calls = []

    def complete(self, messages, temperature=0.0, max_tokens=512, response_format=None):
        self.calls.append(list(messages))
        text, finish = next(self._replies)
        return LLMResult(text, "fake", 10, 5, 1.0, finish, 0.0)

MSGS = [{"role": "user", "content": "x"}]


def test_valid_first_try():
    r = FakeLLM([(GOOD, "stop")]).complete_json(MSGS, LogExplanation)
    assert r.attempts == 1 and r.data.severity == "high"


def test_fenced_json_is_accepted():
    r = FakeLLM([(f"```json\n{GOOD}\n```", "stop")]).complete_json(MSGS, LogExplanation)
    assert r.attempts == 1


def test_retry_feeds_back_the_error():
    fake = FakeLLM([('{"summary": "x", "severity": "high"}', "stop"), (GOOD, "stop")])
    r = fake.complete_json(MSGS, LogExplanation)
    assert r.attempts == 2
    assert "component: Field required" in fake.calls[1][-1]["content"]
    assert r.prompt_tokens == 20  # summed over both attempts


def test_truncated_output_is_retried():
    r = FakeLLM([('{"summary": "cut', "length"), (GOOD, "stop")]).complete_json(MSGS, LogExplanation)
    assert r.attempts == 2


def test_gives_up_after_max_attempts():
    fake = FakeLLM([("not json", "stop")] * 3)
    with pytest.raises(StructuredOutputError) as e:
        fake.complete_json(MSGS, LogExplanation)
    assert e.value.attempts == 3 and len(fake.calls) == 3