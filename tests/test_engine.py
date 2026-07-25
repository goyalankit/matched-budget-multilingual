import json
import os
from urllib import error, request

import pytest

from src.engine import MockEngine, VLLMEngine


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, *payloads: dict[str, object]) -> None:
        self.responses = [FakeResponse(payload) for payload in payloads]
        self.requests: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.requests.append((request, timeout))
        return self.responses.pop(0)


def _real_server_is_reachable() -> bool:
    base_url = os.environ.get("LR_VLLM_URL")
    if base_url is None:
        return False
    try:
        with request.urlopen(
            f"{base_url.rstrip('/')}/v1/models", timeout=2
        ) as response:
            response.read(1)
    except (error.URLError, OSError, ValueError):
        return False
    return True


def test_mock_engine_is_seed_deterministic() -> None:
    engine = MockEngine()
    assert engine.generate("prompt", 42, 4096) == engine.generate(
        "prompt", 42, 4096
    )


def test_mock_engine_reports_hard_truncation() -> None:
    result = MockEngine().generate("prompt", 42, 5)
    assert len(result.token_ids) == 5
    assert not result.eos


def test_vllm_engine_discovers_model_and_returns_server_tokenization() -> None:
    opener = FakeOpener(
        {"data": [{"id": "Qwen/Qwen3-8B"}]},
        {
            "choices": [
                {
                    "token_ids": [101, 102, 151645],
                    "message": {"content": "#### 42"},
                    "finish_reason": "stop",
                    "prompt_token_ids": [1, 2, 3, 4],
                }
            ],
            "usage": {"prompt_tokens": 4},
        },
    )

    result = VLLMEngine("http://[::1]:9002", opener=opener).generate(
        "Solve this.", seed=123, max_tokens=8
    )

    model_request, model_timeout = opener.requests[0]
    generation_request, generation_timeout = opener.requests[1]
    assert model_request.full_url == "http://[::1]:9002/v1/models"
    assert model_timeout == 180
    assert generation_request.full_url == "http://[::1]:9002/v1/chat/completions"
    assert generation_request.get_method() == "POST"
    assert generation_timeout == 180
    assert json.loads(generation_request.data) == {
        "model": "Qwen/Qwen3-8B",
        "messages": [{"role": "user", "content": "Solve this."}],
        "max_tokens": 8,
        "temperature": 0.6,
        "seed": 123,
        "return_token_ids": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    assert list(result.token_ids) == [101, 102, 151645]
    assert result.text == "#### 42"
    assert result.eos
    assert list(result.input_token_ids or []) == [1, 2, 3, 4]
    assert result.input_token_count == 4


def test_vllm_engine_can_leave_model_thinking_configuration_unchanged() -> None:
    opener = FakeOpener(
        {
            "choices": [
                {
                    "token_ids": [201, 202],
                    "message": {"content": None},
                    "finish_reason": "length",
                }
            ],
            "prompt_token_ids": [10, 11, 12],
            "usage": {"prompt_tokens": 3},
        }
    )

    result = VLLMEngine(
        "http://[::1]:9001",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        enable_thinking=True,
        opener=opener,
    ).generate("Solve this.", seed=321, max_tokens=8)

    generation_request, _ = opener.requests[0]
    body = json.loads(generation_request.data)
    assert "chat_template_kwargs" not in body
    assert result.text == ""
    assert not result.eos
    assert list(result.input_token_ids or []) == [10, 11, 12]
    assert result.input_token_count == 3


@pytest.mark.skipif(
    not _real_server_is_reachable(),
    reason="LR_VLLM_URL is unset or the vLLM server is unreachable",
)
def test_real_vllm_backend() -> None:
    result = VLLMEngine(os.environ["LR_VLLM_URL"]).generate(
        "Reply with the number 1 only.", seed=1, max_tokens=8
    )

    assert result.token_ids
    assert "<think>" not in result.text
