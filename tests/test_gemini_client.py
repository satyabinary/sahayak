import pytest
from types import SimpleNamespace
from unittest.mock import Mock

from utils.ai.gemini_client import GeminiClient, GeminiRateLimitError


class FakeRateLimitError(Exception):
    code = 429


def test_rate_limit_is_reported_without_retrying(monkeypatch):
    client = GeminiClient(api_key="test-only")
    call_count = 0

    def fail_with_rate_limit():
        nonlocal call_count
        call_count += 1
        raise FakeRateLimitError()

    monkeypatch.setattr("utils.ai.gemini_client.time.sleep", lambda _: None)

    with pytest.raises(GeminiRateLimitError, match="quota or rate limit"):
        client._call_with_retry("test", fail_with_rate_limit)

    assert call_count == 1


def test_text_generation_uses_configured_output_budget(monkeypatch):
    client = GeminiClient(api_key="test-only")
    generate_content = Mock(return_value=SimpleNamespace(text="A complete answer."))

    monkeypatch.setattr(
        "utils.ai.gemini_client.settings.chat_max_output_tokens",
        1400,
    )
    monkeypatch.setattr(client.client.models, "generate_content", generate_content)

    answer = client.generate_text("Write a complete answer.")

    assert answer == "A complete answer."
    assert generate_content.call_args.kwargs["config"].max_output_tokens == 1400
