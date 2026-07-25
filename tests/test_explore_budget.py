from pathlib import Path

import numpy as np

from src.generate import append_ledger_records, record_id
from src.mgsm import MgsmItem


class CharDecoder:
    def __call__(self, ids: list[int]) -> str:
        return "".join(map(chr, ids))

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return [self(ids) for ids in sequences]


def _write_record(
    ledger_root: Path,
    *,
    language: str,
    arm: str,
    item_id: str,
    text: str,
) -> None:
    append_ledger_records(
        ledger_root / "model" / language / arm / "shard.jsonl",
        [
            {
                "record_id": record_id("model", language, arm, item_id, 0),
                "model_id": "model",
                "language": language,
                "arm": arm,
                "item_id": item_id,
                "sample_index": 0,
                "seed": 1,
                "input_token_ids": [],
                "input_token_count": 0,
                "output_token_ids": list(map(ord, text)),
                "output_token_count": len(text),
                "text": text,
                "eos": True,
                "started_at": "2026-07-25T00:00:00+00:00",
                "completed_at": "2026-07-25T00:00:01+00:00",
            }
        ],
    )


def _trace_with_emission(answer: int, emission: int, total: int) -> str:
    answer_line = f"\n#### {answer}"
    if emission < len(answer_line) or total < emission:
        raise ValueError("invalid crafted emission position")
    prefix = "x" * (emission - len(answer_line)) + answer_line
    if total == emission:
        return prefix
    return prefix + "\n" + "x" * (total - emission - 1)


def test_emission_index_detects_first_parseable_prefix(tmp_path) -> None:
    from src.explore_budget import emission_index_stats

    text = "xxxxx\n#### 42"
    _write_record(
        tmp_path,
        language="de",
        arm="native",
        item_id="0",
        text=text,
    )

    result = emission_index_stats("model", tmp_path, CharDecoder())
    cell = result["cells"]["de"]["native"]

    assert len(text) == 13
    assert cell["median_e_tokens"] == 13
    assert cell["p10_e_tokens"] == 13
    assert cell["p90_e_tokens"] == 13
    assert cell["fraction_never_emitted"] == 0
    assert result["grid_resolution_tokens"] == 16


def test_delta_vs_budget_has_expected_small_budget_sign_and_ci(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real, explore_budget

    for item_id in ("0", "1"):
        _write_record(
            tmp_path,
            language="de",
            arm="native",
            item_id=item_id,
            text=_trace_with_emission(42, emission=12, total=20),
        )
        _write_record(
            tmp_path,
            language="de",
            arm="translate_act",
            item_id=item_id,
            text=_trace_with_emission(42, emission=8, total=20),
        )

    monkeypatch.setattr(
        analyze_real,
        "load_mgsm",
        lambda language: [
            MgsmItem("0", "question 0", 42),
            MgsmItem("1", "question 1", 42),
        ],
    )
    monkeypatch.setattr(explore_budget, "_N_BOOTSTRAP", 199)

    result = explore_budget.delta_vs_budget(
        "model",
        tmp_path,
        CharDecoder(),
        {"de": 2.0},
        budgets=(8, 16),
    )
    small = result["delta_points"]["de"]["8"]
    large = result["delta_points"]["de"]["16"]

    assert np.isfinite(small["estimate"])
    assert len(small["ci_95"]) == 2
    assert all(np.isfinite(bound) for bound in small["ci_95"])
    assert small["estimate"] > 0
    assert small["ci_95"] == [100.0, 100.0]
    assert large["estimate"] == 0
    assert result["token_accuracy_points"]["de"]["native"] == {
        "8": 0.0,
        "16": 100.0,
    }
