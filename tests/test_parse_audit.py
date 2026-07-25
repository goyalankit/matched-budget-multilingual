from pathlib import Path

import numpy as np
import pytest

from src.generate import append_ledger_records, record_id
from src.mgsm import MgsmItem
from src.parse_audit import (
    PARSE_CATEGORIES,
    audit_model,
    categorize_prefix,
    parse_answer_terminated,
)


class CharDecoder:
    def __call__(self, ids: list[int]) -> str:
        return "".join(map(chr, ids))

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return [self(ids) for ids in sequences]


def _write_record(
    ledger_root: Path,
    *,
    arm: str,
    item_id: str,
    text: str,
    eos: bool = True,
) -> None:
    append_ledger_records(
        ledger_root / "model" / "de" / arm / "shard.jsonl",
        [
            {
                "record_id": record_id("model", "de", arm, item_id, 0),
                "model_id": "model",
                "language": "de",
                "arm": arm,
                "item_id": item_id,
                "sample_index": 0,
                "seed": 1,
                "input_token_ids": [],
                "input_token_count": 0,
                "output_token_ids": list(map(ord, text)),
                "output_token_count": len(text),
                "text": text,
                "eos": eos,
                "started_at": "2026-07-25T00:00:00+00:00",
                "completed_at": "2026-07-25T00:00:01+00:00",
            }
        ],
    )


@pytest.mark.parametrize(
    ("text", "sequence_ended", "expected"),
    [
        ("work\n#### 42\n", False, 42),
        ("work\n#### 42", True, 42),
        ("work\n#### 42", False, None),
        ("#### 42\nmore", False, 42),
        ("#### 42x\n", False, None),
    ],
)
def test_terminated_parser_requires_newline_or_eos(
    text: str, sequence_ended: bool, expected: int | None
) -> None:
    assert (
        parse_answer_terminated(
            text, "de", "native", sequence_ended=sequence_ended
        )
        == expected
    )


@pytest.mark.parametrize(
    ("prefix", "full", "gold", "censored", "expected"),
    [
        ("#### 42\n", "#### 42\n", 42, False, "strict_valid_correct"),
        ("#### 41\n", "#### 41\n", 42, False, "strict_valid_incorrect"),
        ("work", "work\n#### 42\n", 42, False, "answer_only_after_cap"),
        ("work", "work", 42, False, "no_marker"),
        (
            "#### forty\n",
            "#### forty\n",
            42,
            False,
            "marker_noninteger_or_malformed",
        ),
        (
            "#### 42",
            "#### 420\n",
            42,
            False,
            "multiple_or_revised",
        ),
        ("work", "work", 42, True, "censored_4096"),
    ],
)
def test_categories_are_mutually_exclusive(
    prefix: str,
    full: str,
    gold: int,
    censored: bool,
    expected: str,
) -> None:
    category = categorize_prefix(
        prefix,
        full,
        input_language="de",
        arm="native",
        gold_answer=gold,
        full_trace_censored=censored,
    )
    assert category == expected
    assert category in PARSE_CATEGORIES


def test_audit_counts_rescued_unstable_windows_and_delta(
    tmp_path, monkeypatch
) -> None:
    from src import parse_audit

    traces = {
        "0": "x" * 8 + "\n#### 42\n",
        "1": "x" * 8 + "\n#### 42",
        "2": "x" * 8 + "\n#### 42" + "0\n",
        "3": "x" * 7 + "\n#### 42\n#### bad\n",
    }
    for arm in ("native", "translate_act"):
        for item_id, text in traces.items():
            _write_record(
                tmp_path,
                arm=arm,
                item_id=item_id,
                text=text,
            )
    monkeypatch.setattr(
        parse_audit,
        "load_mgsm",
        lambda language: [
            MgsmItem(item_id, f"question {item_id}", 42)
            for item_id in traces
        ],
    )
    monkeypatch.setattr(parse_audit.explore_budget, "_N_BOOTSTRAP", 99)

    categories, sensitivity = audit_model(
        "model",
        tmp_path,
        CharDecoder(),
        {"de": 2.0},
        category_budgets=(8, 16),
        delta_budgets=(8,),
    )

    cells = {
        (cell["arm"], cell["budget"]): cell
        for cell in sensitivity["prefix_cells"]
    }
    native_16 = cells[("native", 16)]
    assert native_16["strict_correct"] == 4
    assert native_16["terminated_correct"] == 2
    assert native_16["rescued_correct"] == 2
    assert native_16["value_unstable"] == 1

    category_cell = next(
        cell
        for cell in categories["cells"]
        if cell["arm"] == "native" and cell["budget"] == 16
    )
    assert sum(category_cell["counts"].values()) == 4
    assert category_cell["counts"]["multiple_or_revised"] == 1

    window = next(
        row
        for row in sensitivity["native_flores_windows"]
        if row["budget"] == 8
    )
    assert window["n_gained_correct"] == 4
    assert window["rescued_correct"] == 1
    assert window["value_unstable"] == 1
    assert window["genuinely_terminated"] == 2

    strict_delta = sensitivity["delta"]["strict"][0]
    terminated_delta = sensitivity["delta"]["terminated"][0]
    assert np.isclose(strict_delta["estimate"], 100)
    assert np.isclose(terminated_delta["estimate"], 50)
