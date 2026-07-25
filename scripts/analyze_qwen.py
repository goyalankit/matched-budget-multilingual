"""Run the real-ledger confirmatory analysis for Qwen3-8B."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.analyze_real import (  # noqa: E402
    mcb_rows,
    real_study_configuration,
    run_real_confirmatory,
    score_ledger,
    write_mcb_table,
)


def _summary(result: dict) -> dict:
    checkpoint = "1024"
    return {
        "primary_estimand_delta_points": result[
            "primary_estimand_delta_points"
        ],
        "tiered_h1_outcome": result["tiered_h1_outcome"],
        "h1": {
            name: {
                "reject": values["reject"],
                "raw_p_value": values["raw_p_value"],
                "holm_local_alpha": values["holm_local_alpha"],
            }
            for name, values in result["h1"].items()
        },
        "h2": {
            "reject": result["h2"]["reject"],
            "raw_p_value": result["h2"]["raw_p_value"],
            "holm_local_alpha": result["h2"]["holm_local_alpha"],
        },
        "h3": {
            language: {
                "reject": values["reject"],
                "raw_p_value": values["p_reversal"],
                "holm_local_alpha": values["holm_local_alpha"],
            }
            for language, values in result["h3"].items()
        },
        "observed_accuracy_points_at_1024": {
            frame: {
                language: {
                    arm: budgets[checkpoint]
                    for arm, budgets in language_curves.items()
                }
                for language, language_curves in frame_curves.items()
            }
            for frame, frame_curves in result[
                "accuracy_curves_points"
            ].items()
        },
    }


def main() -> None:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
    decode = lambda ids: tokenizer.decode(  # noqa: E731
        ids, skip_special_tokens=True
    )
    decode.decode_many = lambda sequences: tokenizer.batch_decode(  # type: ignore[attr-defined]
        sequences, skip_special_tokens=True
    )

    prices = json.loads(
        (_ROOT / "configs" / "prices.json").read_text(encoding="utf-8")
    )
    snapshots = {
        "primary": prices["primary_snapshot"],
        "sensitivity": prices["sensitivity_snapshot"],
    }
    output_root = _ROOT / "analysis-out"
    output_root.mkdir(parents=True, exist_ok=True)
    rows = []
    summaries = {}

    for snapshot_name, snapshot in snapshots.items():
        result = run_real_confirmatory(
            "qwen3_8b", _ROOT / "runs", decode, snapshot
        )
        (output_root / f"confirmatory_qwen_{snapshot_name}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        study, power = real_study_configuration("qwen3_8b", snapshot)
        frames = score_ledger(
            "qwen3_8b",
            _ROOT / "runs",
            power["languages"],
            power["arms"],
            study,
            decode,
        )
        rows.extend(mcb_rows(snapshot_name, frames, study, power))
        summaries[snapshot_name] = _summary(result)

    write_mcb_table(
        rows,
        output_root / "deliverable_table_qwen.md",
        output_root / "deliverable_table_qwen.csv",
    )
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
