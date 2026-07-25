"""Generation-engine interfaces and deterministic mock from preregistration §4."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Sequence
from urllib import request

import numpy as np

_UINT64 = 1 << 64
_INT64_MAX = (1 << 63) - 1


def _to_signed_int64(seed: int) -> int:
    """Map an unsigned 64-bit seed into vLLM's signed-int64 API range.

    The prereg §4 seed derivation yields an unsigned 64-bit int, but vLLM's
    OpenAI endpoint rejects values above signed-int64 max with HTTP 400. The
    mapping is a bijective two's-complement reinterpretation, so a given seed
    always transports to the same value (preserving cross-arm pairing), and it
    is idempotent on already-signed values.
    """
    seed %= _UINT64
    return seed - _UINT64 if seed > _INT64_MAX else seed


class _HTTPResponse(Protocol):
    def __enter__(self) -> "_HTTPResponse": ...

    def __exit__(self, *args: object) -> None: ...

    def read(self) -> bytes: ...


class _URLOpener(Protocol):
    def open(self, request: request.Request, timeout: float) -> _HTTPResponse: ...


@dataclass(frozen=True)
class GenerationResult:
    """One generated trace and its exact stored output token IDs."""

    token_ids: Sequence[int]
    text: str
    eos: bool
    input_token_ids: Optional[Sequence[int]] = None
    input_token_count: Optional[int] = None


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
    """HTTP client for a remote vLLM OpenAI-compatible server."""

    def __init__(
        self,
        base_url: str,
        model_id: str | None = None,
        temperature: float = 0.6,
        enable_thinking: bool = False,
        timeout: float = 180,
        opener: _URLOpener | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.enable_thinking = enable_thinking
        self.timeout = timeout
        self.opener = opener if opener is not None else request.build_opener()
        self.model_id = model_id if model_id is not None else self._discover_model_id()

    def _request_json(
        self, endpoint: str, body: dict[str, object] | None = None
    ) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method="POST" if data is not None else "GET",
        )
        with self.opener.open(http_request, timeout=self.timeout) as response:
            payload = json.loads(response.read())
        if not isinstance(payload, dict):
            raise ValueError("vLLM response must be a JSON object")
        return payload

    def _discover_model_id(self) -> str:
        response = self._request_json("/v1/models")
        model_id = response["data"][0]["id"]
        if not isinstance(model_id, str):
            raise ValueError("vLLM model id must be a string")
        return model_id

    def generate(self, prompt: str, seed: int, max_tokens: int) -> GenerationResult:
        body: dict[str, object] = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "seed": _to_signed_int64(seed),
            "return_token_ids": True,
        }
        if not self.enable_thinking:
            body["chat_template_kwargs"] = {"enable_thinking": False}

        response = self._request_json("/v1/chat/completions", body)
        choice = response["choices"][0]
        message = choice["message"]
        input_token_ids = choice.get(
            "prompt_token_ids", response.get("prompt_token_ids")
        )
        return GenerationResult(
            token_ids=choice["token_ids"],
            text=message.get("content") or "",
            eos=choice["finish_reason"] == "stop",
            input_token_ids=input_token_ids,
            input_token_count=response["usage"]["prompt_tokens"],
        )
