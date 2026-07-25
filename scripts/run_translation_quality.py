"""Run appendix-only TRANSLATE-ACT reference-based quality analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.translation_quality import (  # noqa: E402
    BuiltinSurfaceOverlapScorer,
    CometScorer,
    SurfaceOverlapScorer,
    analyze_translation_quality,
    translation_quality_markdown,
)


_MODELS = ("qwen3_8b", "llama_3_1_8b_instruct")
_CHECKPOINTS = (
    "Unbabel/wmt22-comet-da",
    "wmt20-comet-da",
    "Unbabel/eamt22-cometinho-da",
)
_CHECKPOINT_ERRORS = (
    OSError,
    RuntimeError,
    ValueError,
    TypeError,
    KeyError,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend", choices=("auto", "comet", "proxy"), default="auto"
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument(
        "--gpus",
        type=int,
        default=None,
        help="COMET GPU count; defaults to 1 when CUDA is available, else 0",
    )
    parser.add_argument("--n-bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20_260_724)
    parser.add_argument("--output-dir", type=Path, default=_ROOT / "analysis-out")
    return parser.parse_args()


def _hf_token_available() -> bool:
    try:
        from huggingface_hub import get_token
    except ImportError:
        return False
    try:
        return bool(get_token())
    except OSError:
        return False


def _default_gpus() -> int:
    try:
        import torch
    except ImportError:
        return 0
    return int(torch.cuda.is_available())


def _failure(checkpoint: str, error: BaseException) -> dict[str, Any]:
    message = " ".join(str(error).split())
    return {
        "checkpoint": checkpoint,
        "status": "failed",
        "error_type": type(error).__name__,
        "error": message,
        "gated": "gated" in message.lower()
        or "restricted" in message.lower(),
    }


def _load_comet(
    *, batch_size: int, gpus: int
) -> tuple[CometScorer | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    try:
        from comet import download_model, load_from_checkpoint
    except (ImportError, RuntimeError) as error:
        attempts.append(_failure("unbabel-comet package import", error))
        return None, attempts

    for checkpoint in _CHECKPOINTS:
        try:
            checkpoint_path = download_model(checkpoint)
            model = load_from_checkpoint(checkpoint_path)
        except _CHECKPOINT_ERRORS as error:
            attempts.append(_failure(checkpoint, error))
            continue
        attempts.append(
            {
                "checkpoint": checkpoint,
                "status": "loaded",
                "checkpoint_path": str(checkpoint_path),
            }
        )
        return (
            CometScorer(
                model,
                checkpoint,
                batch_size=batch_size,
                gpus=gpus,
            ),
            attempts,
        )
    return None, attempts


def _format_failures(attempts: list[dict[str, Any]]) -> str:
    return "; ".join(
        f"{attempt['checkpoint']}: "
        f"{attempt.get('error_type', attempt['status'])}: "
        f"{attempt.get('error', '')}".rstrip()
        for attempt in attempts
    )


def _print_report(report: dict[str, Any]) -> None:
    scorer = report["scorer"]
    print(
        "TRANSLATE-ACT translation quality — non-confirmatory (§11); "
        f"scorer={scorer['name']} ({scorer['type']})"
    )
    for model_key, languages in report["models"].items():
        for language, cell in languages.items():
            for metric, summary in cell["metrics"].items():
                low, high = summary["bootstrap_ci_95"]
                print(
                    f"{model_key} {language} {metric}: n={cell['n_scored']}, "
                    "missing-delimiter="
                    f"{100 * cell['missing_delimiter_rate']:.2f}%, "
                    f"mean={summary['mean']:.4f}, "
                    f"median={summary['median']:.4f}, "
                    f"CI95=[{low:.4f}, {high:.4f}]"
                )


def main() -> None:
    args = _arguments()
    hf_token_available = _hf_token_available()
    attempts: list[dict[str, Any]] = []
    scorer = None
    proxy_import_error = None
    gpus = _default_gpus() if args.gpus is None else args.gpus

    if args.backend != "proxy":
        scorer, attempts = _load_comet(
            batch_size=args.batch_size, gpus=gpus
        )
    if scorer is None:
        if args.backend == "comet":
            raise SystemExit(
                "No reference-based COMET checkpoint could be loaded: "
                + _format_failures(attempts)
            )
        try:
            scorer = SurfaceOverlapScorer()
        except ImportError as error:
            proxy_import_error = f"{type(error).__name__}: {error}"
            scorer = BuiltinSurfaceOverlapScorer()

    report = analyze_translation_quality(
        _MODELS,
        _ROOT / "runs",
        scorer,
        n_boot=args.n_bootstrap,
        seed=args.seed,
    )
    report["scorer"]["hf_token_available"] = hf_token_available
    report["scorer"]["checkpoint_attempts"] = attempts
    if proxy_import_error is not None:
        report["scorer"]["sacrebleu_package_unavailable"] = proxy_import_error
    if scorer.scorer_type != "COMET":
        report["scorer"]["comet_unavailable_reason"] = (
            _format_failures(attempts)
            if attempts
            else "COMET acquisition was skipped with --backend proxy."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "translation_quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "translation_quality.md").write_text(
        translation_quality_markdown(report),
        encoding="utf-8",
    )
    _print_report(report)


if __name__ == "__main__":
    main()
