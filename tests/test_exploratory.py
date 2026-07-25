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
    model: str = "model",
    language: str = "de",
    arm: str,
    item_id: int,
    sample_index: int = 0,
    text: str,
    input_tokens: int = 5,
    eos: bool = True,
) -> None:
    append_ledger_records(
        ledger_root / model / language / arm / "shard.jsonl",
        [
            {
                "record_id": record_id(
                    model, language, arm, str(item_id), sample_index
                ),
                "model_id": model,
                "language": language,
                "arm": arm,
                "item_id": str(item_id),
                "sample_index": sample_index,
                "seed": item_id * 10 + sample_index,
                "input_token_ids": list(range(input_tokens)),
                "input_token_count": input_tokens,
                "output_token_ids": list(map(ord, text)),
                "output_token_count": len(text),
                "text": text,
                "eos": eos,
                "started_at": "2026-07-25T00:00:00+00:00",
                "completed_at": "2026-07-25T00:00:01+00:00",
            }
        ],
    )


def _premium(ratio: float = 2.0) -> dict[str, dict[str, float]]:
    return {
        "de": {
            "ratio": ratio,
            "ci_low": ratio - 0.1,
            "ci_high": ratio + 0.1,
        }
    }


def test_verbosity_decomposition_uses_ledger_counts_and_flores_reference(
    tmp_path, monkeypatch
) -> None:
    from src import exploratory

    output_lengths = [10, 20, 30, 40]
    input_lengths = [8, 8, 12, 12]
    for index, (output_length, input_length) in enumerate(
        zip(output_lengths, input_lengths)
    ):
        _write_record(
            tmp_path,
            arm="native",
            item_id=index // 2,
            sample_index=index % 2,
            text="x" * output_length,
            input_tokens=input_length,
            eos=index != 3,
        )
    monkeypatch.setattr(exploratory, "_N_BOOTSTRAP", 199)

    result = exploratory.verbosity_decomposition(
        "model", tmp_path, _premium()
    )
    cell = result["cells"]["de"]["native"]

    assert cell["actual_input_tokens_median"]["estimate"] == 10
    assert (
        cell["flores_implied_english_equivalent_input_tokens_median"][
            "estimate"
        ]
        == 5
    )
    assert cell["output_tokens_median"]["estimate"] == 25
    assert np.isclose(cell["output_tokens_p90"]["estimate"], 37)
    assert cell["fraction_hitting_4096_cap"]["estimate"] == 0.25
    assert result["analysis_label"] == exploratory.ANALYSIS_LABEL


def test_best_english_arm_is_reselected_inside_bootstrap(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real, exploratory

    outcomes = {
        "native": [False, False, False, False],
        "translate_act": [True, True, False, False],
        "pivot": [False, True, True, True],
        "code_switched": [True, False, False, False],
    }
    for arm, arm_outcomes in outcomes.items():
        for item_id, correct in enumerate(arm_outcomes):
            _write_record(
                tmp_path,
                arm=arm,
                item_id=item_id,
                text=f"\n#### {42 if correct else 43}",
            )

    monkeypatch.setattr(
        analyze_real,
        "load_mgsm",
        lambda language: [
            MgsmItem(str(index), f"question {index}", 42)
            for index in range(4)
        ],
    )
    monkeypatch.setattr(exploratory, "_N_BOOTSTRAP", 499)

    result = exploratory.best_english_arm_comparison(
        "model",
        tmp_path,
        CharDecoder(),
        {"de": 2.0},
        budgets=(128,),
    )
    cell = result["cells"]["de"]["128"]

    assert cell["selected_best_english_arm"] == "pivot"
    assert cell["best_english_minus_native_points"]["estimate"] == 75
    assert cell["translate_act_minus_native_points"]["estimate"] == 50
    assert (
        cell["best_english_uplift_over_translate_act_points"]["estimate"]
        == 25
    )
    assert cell["bootstrap_selection_fraction"]["pivot"] > 0
    assert cell["bootstrap_selection_fraction"]["translate_act"] > 0


def test_trace_ratio_uses_decoded_post_delimiter_token_boundary(
    tmp_path, monkeypatch
) -> None:
    from src import exploratory

    delimiter = exploratory.TRANSLATION_DELIMITER
    for item_id, native_length in enumerate((20, 40)):
        _write_record(
            tmp_path,
            arm="native",
            item_id=item_id,
            text="n" * native_length,
        )
        _write_record(
            tmp_path,
            arm="translate_act",
            item_id=item_id,
            text="translation\n" + delimiter + "r" * 10,
        )
    monkeypatch.setattr(exploratory, "_N_BOOTSTRAP", 199)

    result = exploratory.trace_premium_ratio(
        "model", tmp_path, CharDecoder(), _premium()
    )
    cell = result["cells"]["de"]

    assert cell["native_output_tokens_median"]["estimate"] == 30
    assert (
        cell["translate_act_post_delimiter_tokens_median"]["estimate"]
        == 10
    )
    assert cell["trace_premium_ratio"]["estimate"] == 3
    assert cell["trace_minus_flores_ratio"]["estimate"] == 1
    assert cell["fraction_translate_act_missing_delimiter"]["estimate"] == 0


def test_markdown_outputs_carry_non_confirmatory_label(
    tmp_path, monkeypatch
) -> None:
    from src import exploratory

    for item_id in range(2):
        _write_record(
            tmp_path,
            arm="native",
            item_id=item_id,
            text="n" * 20,
        )
        _write_record(
            tmp_path,
            arm="translate_act",
            item_id=item_id,
            text=exploratory.TRANSLATION_DELIMITER + "r" * 10,
        )
    monkeypatch.setattr(exploratory, "_N_BOOTSTRAP", 19)
    verbosity = exploratory.verbosity_decomposition(
        "model", tmp_path, _premium()
    )
    trace = exploratory.trace_premium_ratio(
        "model", tmp_path, CharDecoder(), _premium()
    )

    verbosity_text = exploratory.verbosity_markdown(
        {"models": {"model": verbosity}}
    )
    trace_text = exploratory.trace_premium_markdown(
        {"models": {"model": trace}}
    )

    assert exploratory.ANALYSIS_LABEL in verbosity_text
    assert exploratory.ANALYSIS_LABEL in trace_text
    assert "no confirmatory test" in verbosity_text
    assert "no confirmatory test" in trace_text
