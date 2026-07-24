"""Generation-engine interfaces and deterministic mock from preregistration §4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np


@dataclass(frozen=True)
class GenerationResult:
    """One generated trace and its exact stored output token IDs."""

    token_ids: Sequence[int]
    text: str
    eos: bool


class EngineProtocol(Protocol):
    """Thin interface shared by mock and real inference engines."""

    def generate(self, prompt: str, seed: int, max_tokens: int) -> GenerationResult:
        """Generate one deterministic-seed trace."""


class MockEngine:
    """Seed-driven character-token generator for offline harness tests."""

    def generate(self, prompt: str, seed: int, max_tokens: int) -> GenerationResult:
        rng = np.random.default_rng(seed)
        answer = int(rng.integers(-50, 151))
        sections = [f"Reasoning for seed {seed}.\n"]
        if seed % 3:
            sections.append("English translation.\n=== TRANSLATION END ===\n")
        sections.append("Compute carefully.\n")
        if seed % 4:
            sections.append(f"#### {answer}\n")
        text = "".join(sections)
        token_ids = [ord(character) for character in text[:max_tokens]]
        eos = len(text) <= max_tokens
        return GenerationResult(
            token_ids=token_ids,
            text=text[:max_tokens],
            eos=eos,
        )


class VLLMEngine:
    """Real-backend placeholder; construction requires the gated dependency."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        try:
            import vllm  # noqa: F401
        except ImportError as error:
            raise ImportError("VLLMEngine requires the vllm dependency") from error
        raise NotImplementedError(
            "Real vLLM wiring is GPU-gated and must be supplied after registration"
        )

