"""Run the secondary real-ledger analysis for Llama-3.1-8B-Instruct."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import sqlite3
import sys

# Matches Llama special-token markup like <|eot_id|>, <|end_of_text|>.
_SPECIAL_TOKEN_RE = re.compile(r"<\|[^|>]*\|>")
from pathlib import Path
from threading import Lock
from urllib import request

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_qwen import _summary  # noqa: E402
from src.analyze_real import (  # noqa: E402
    mcb_rows,
    real_study_configuration,
    run_real_confirmatory,
    score_ledger,
    write_mcb_table,
)


class CachedVllmDecoder:
    """Concurrent vLLM detokenization with a persistent prefix cache."""

    def __init__(
        self,
        base_url: str,
        cache_path: Path,
        *,
        max_workers: int = 16,
        timeout: float = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers
        self.timeout = timeout
        self._write_lock = Lock()
        self.model = self._discover_model()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(cache_path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS detokenized "
            "(cache_key TEXT PRIMARY KEY, text TEXT NOT NULL)"
        )

    def _request_json(self, endpoint: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers=({"Content-Type": "application/json"} if data is not None else {}),
            method="POST" if data is not None else "GET",
        )
        with request.urlopen(http_request, timeout=self.timeout) as response:
            payload = json.loads(response.read())
        if not isinstance(payload, dict):
            raise ValueError("vLLM response must be a JSON object")
        return payload

    def _discover_model(self) -> str:
        payload = self._request_json("/v1/models")
        model = payload["data"][0]["id"]
        if not isinstance(model, str) or not model:
            raise ValueError("vLLM returned an invalid model id")
        return model

    def _cache_key(self, tokens: tuple[int, ...]) -> str:
        serialized = json.dumps([self.model, *tokens], separators=(",", ":")).encode(
            "ascii"
        )
        return hashlib.sha256(serialized).hexdigest()

    def _remote_decode(self, tokens: tuple[int, ...]) -> str:
        payload = self._request_json(
            "/detokenize", {"model": self.model, "tokens": list(tokens)}
        )
        text = payload.get("prompt")
        if not isinstance(text, str):
            raise ValueError("vLLM /detokenize response has no prompt text")
        # vLLM /detokenize ignores skip_special_tokens and emits literal special
        # markup (e.g. the terminal <|eot_id|>), which corrupts the final
        # '#### <n>' answer line and makes every parse fail. Strip <|...|> markup;
        # real answer content never contains it. (Qwen used the local tokenizer
        # with skip_special_tokens=True and did not need this.)
        return _SPECIAL_TOKEN_RE.sub("", text)

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        token_tuples = [tuple(sequence) for sequence in sequences]
        keys = [self._cache_key(tokens) for tokens in token_tuples]
        cached = (
            {
                key: text
                for key, text in self.connection.execute(
                    f"SELECT cache_key, text FROM detokenized "
                    f"WHERE cache_key IN ({','.join('?' for _ in keys)})",
                    keys,
                )
            }
            if keys
            else {}
        )
        missing = {
            key: tokens for key, tokens in zip(keys, token_tuples) if key not in cached
        }
        if missing:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                texts = executor.map(self._remote_decode, missing.values())
                additions = list(zip(missing, texts))
            with self._write_lock:
                self.connection.executemany(
                    "INSERT OR REPLACE INTO detokenized(cache_key, text) VALUES (?, ?)",
                    additions,
                )
                self.connection.commit()
            cached.update(additions)
        return [cached[key] for key in keys]

    def __call__(self, token_ids: list[int]) -> str:
        return self.decode_many([token_ids])[0]

    def close(self) -> None:
        self.connection.close()


def main() -> None:
    output_root = _ROOT / "analysis-out"
    decoder = CachedVllmDecoder(
        "http://[::1]:9001",
        output_root / "llama_detokenize_cache.sqlite3",
    )
    try:
        prices = json.loads(
            (_ROOT / "configs" / "prices.json").read_text(encoding="utf-8")
        )
        snapshots = {
            "primary": prices["primary_snapshot"],
            "sensitivity": prices["sensitivity_snapshot"],
        }
        output_root.mkdir(parents=True, exist_ok=True)
        rows = []
        summaries = {}

        for snapshot_name, snapshot in snapshots.items():
            result = run_real_confirmatory(
                "llama_3_1_8b_instruct",
                _ROOT / "runs",
                decoder,
                snapshot,
            )
            (output_root / f"confirmatory_llama_{snapshot_name}.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            study, power = real_study_configuration("llama_3_1_8b_instruct", snapshot)
            frames = score_ledger(
                "llama_3_1_8b_instruct",
                _ROOT / "runs",
                power["languages"],
                power["arms"],
                study,
                decoder,
            )
            rows.extend(mcb_rows(snapshot_name, frames, study, power))
            summaries[snapshot_name] = _summary(result)

        write_mcb_table(
            rows,
            output_root / "deliverable_table_llama.md",
            output_root / "deliverable_table_llama.csv",
        )
        print(json.dumps(summaries, indent=2, sort_keys=True))
    finally:
        decoder.close()


if __name__ == "__main__":
    main()
