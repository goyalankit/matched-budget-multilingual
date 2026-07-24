import pytest

from src.engine import MockEngine, VLLMEngine


def test_mock_engine_is_seed_deterministic() -> None:
    engine = MockEngine()
    assert engine.generate("prompt", 42, 4096) == engine.generate(
        "prompt", 42, 4096
    )


def test_mock_engine_reports_hard_truncation() -> None:
    result = MockEngine().generate("prompt", 42, 5)
    assert len(result.token_ids) == 5
    assert not result.eos


@pytest.mark.skip(reason="requires vllm")
def test_real_vllm_backend() -> None:
    VLLMEngine()

