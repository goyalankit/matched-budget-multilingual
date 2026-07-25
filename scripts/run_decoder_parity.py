"""Run the mandatory exploratory Qwen decoder-parity preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from scripts.analyze_llama import CachedVllmDecoder  # noqa: E402
from src.decoder_parity import (  # noqa: E402
    DEFAULT_SAMPLE_SEED,
    DEFAULT_SAMPLE_SIZE,
    audit_decoder_parity,
    decoder_parity_markdown,
)
from src.mgsm import load_mgsm  # noqa: E402


class RawCachedVllmDecoder(CachedVllmDecoder):
    """Use the production vLLM client/cache while retaining raw endpoint text."""

    def _remote_decode(self, tokens: tuple[int, ...]) -> str:
        payload = self._request_json(
            "/detokenize", {"model": self.model, "tokens": list(tokens)}
        )
        text = payload.get("prompt")
        if not isinstance(text, str):
            raise ValueError("vLLM /detokenize response has no prompt text")
        return text


class QwenLocalDecoder:
    """Production Qwen AutoTokenizer decode policy."""

    def __init__(self, tokenizer: Any) -> None:
        self.tokenizer = tokenizer

    def __call__(self, token_ids: list[int]) -> str:
        return self.tokenizer.decode(token_ids, skip_special_tokens=True)

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return list(
            self.tokenizer.batch_decode(sequences, skip_special_tokens=True)
        )


def _tokenizer_snapshot(tokenizer: Any) -> str | None:
    for field in ("vocab_file", "merges_file"):
        configured_path = tokenizer.init_kwargs.get(field)
        if not configured_path:
            continue
        parts = Path(configured_path).parts
        if "snapshots" in parts:
            snapshot_index = parts.index("snapshots") + 1
            if snapshot_index < len(parts):
                return parts[snapshot_index]
    return tokenizer.init_kwargs.get("_commit_hash")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qwen-url", default="http://[::1]:9002")
    parser.add_argument("--tokenizer", default="Qwen/Qwen3-8B")
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--sample-seed", type=int, default=DEFAULT_SAMPLE_SEED)
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, default=_ROOT / "analysis-out")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    from transformers import AutoTokenizer
    import transformers

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    local_decoder = QwenLocalDecoder(tokenizer)
    gold_answers = {
        (language, item.item_id): item.gold
        for language in ("de", "th", "sw")
        for item in load_mgsm(language)
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="decoder-parity-") as cache_dir:
        vllm_decoder = RawCachedVllmDecoder(
            args.qwen_url,
            Path(cache_dir) / "qwen_raw_detokenize.sqlite3",
            max_workers=args.max_workers,
        )
        try:
            report = audit_decoder_parity(
                "qwen3_8b",
                _ROOT / "runs",
                local_decoder,
                vllm_decoder,
                gold_answers,
                traces_per_cell=args.sample_size,
                sample_seed=args.sample_seed,
                decoder_metadata={
                    "local_tokenizer_name": args.tokenizer,
                    "local_tokenizer_class": type(tokenizer).__name__,
                    "local_tokenizer_commit": _tokenizer_snapshot(tokenizer),
                    "transformers_version": transformers.__version__,
                    "vllm_base_url": args.qwen_url,
                    "vllm_model_id": vllm_decoder.model,
                },
            )
        finally:
            vllm_decoder.close()

    json_path = args.output_dir / "decoder_parity.json"
    markdown_path = args.output_dir / "decoder_parity.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        decoder_parity_markdown(report),
        encoding="utf-8",
    )

    parsed = report["agreement"]["parsed_answer"]
    correctness = report["agreement"]["correctness_verdict"]
    print(
        "Parsed-answer agreement: "
        f"{100 * parsed['rate']:.4f}% ({parsed['matches']}/{parsed['total']})"
    )
    print(
        "Correctness agreement: "
        f"{100 * correctness['rate']:.4f}% "
        f"({correctness['matches']}/{correctness['total']})"
    )
    cause_counts = report["divergence_counts_by_cause"]
    print(
        "Divergence causes (exact/parsed/correctness): "
        + ", ".join(
            f"{cause}={counts['exact_decoded_string']}/"
            f"{counts['parsed_answer']}/{counts['correctness_verdict']}"
            for cause, counts in cause_counts.items()
        )
    )
    print(
        f"Verdict: {report['verdict']['status']} — "
        f"{report['verdict']['cross_model_comparability']}"
    )
    if report["verdict"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
