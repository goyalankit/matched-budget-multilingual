from pathlib import Path

import numpy as np

from src.comet_gain_correlation import (
    PeakOutcome,
    analyze_comet_gain_associations,
    comet_gain_markdown,
    load_sample_zero_translation_triples,
    peak_outcomes_from_frames,
)
from src.generate import append_ledger_records, record_id
from src.mgsm import MgsmItem
from src.translation_quality import TranslationTriple


class OrderedMockScorer:
    name = "ordered mock COMET"
    scorer_type = "COMET"
    metric_names = ("COMET",)

    def score_batch(self, triples):
        return {
            "COMET": [
                float(triple.mt.removeprefix("score="))
                for triple in triples
            ]
        }


def test_associations_link_comet_to_synthetic_item_level_gains() -> None:
    triples = {
        ("model", "de"): [
            TranslationTriple(str(i), "source", f"score={score}", "reference")
            for i, score in enumerate((0.1, 0.2, 0.8, 0.9))
        ]
    }
    outcomes = {
        ("model", "de"): {
            "0": PeakOutcome(0, 1, 0.0),
            "1": PeakOutcome(0, 0, 0.0),
            "2": PeakOutcome(1, 1, 0.0),
            "3": PeakOutcome(1, 0, 1.0),
        }
    }

    report = analyze_comet_gain_associations(
        triples,
        outcomes,
        {("model", "de"): 192},
        OrderedMockScorer(),
        n_boot=199,
        seed=7,
    )

    cell = report["models"]["model"]["de"]
    assert cell["n_items"] == 4
    assert cell["correctness_gain_counts"] == {
        "-1": 1,
        "0": 2,
        "1": 1,
    }
    assert cell["spearman_comet_vs_correctness_gain"]["estimate"] > 0
    assert cell["point_biserial_comet_vs_translate_win"]["estimate"] > 0
    assert cell["mean_comet"]["translate_win"] == 0.9
    assert cell["mean_comet"]["not_translate_win"] < 0.9
    assert cell["token_frame_gap_contribution"]["mean"] == 0.25
    assert len(report["verdict"].split(". ")) == 4
    markdown = comet_gain_markdown(report)
    assert "appendix only" in markdown.lower()
    assert "never conditions" in markdown
    assert "| model | de | 192 | 4 | 1 |" in markdown
    assert report["verdict"] in markdown


def test_peak_outcomes_select_sample_zero_and_compute_frame_contribution() -> None:
    shape = (2, 1, 2, 2, 2)
    token = np.zeros(shape)
    flores = np.zeros(shape)
    # Peak budget index 1, sample index 0. Arm order is native, translate_act.
    token[:, 0, 0, 1, 0] = [0, 1]
    token[:, 0, 1, 1, 0] = [1, 0]
    flores[:, 0, 0, 1, 0] = [1, 0]
    flores[:, 0, 1, 1, 0] = [1, 0]

    outcomes = peak_outcomes_from_frames(
        {"token": token, "flores": flores},
        languages=("de",),
        arms=("native", "translate_act"),
        budgets=(10, 20),
        peak_budgets={"de": 20},
    )

    assert outcomes == {
        "de": {
            "0": PeakOutcome(1, 0, 1.0),
            "1": PeakOutcome(0, 1, -1.0),
        }
    }


def test_peak_outcomes_reject_missing_budget_frame() -> None:
    with np.testing.assert_raises_regex(
        ValueError, "token and FLORES frames are required"
    ):
        peak_outcomes_from_frames(
            {"token": np.zeros((1, 1, 2, 1, 1))},
            languages=("de",),
            arms=("native", "translate_act"),
            budgets=(10,),
            peak_budgets={"de": 10},
        )


def _write_translation_record(
    root: Path, item_id: str, sample_index: int, text: str
) -> None:
    append_ledger_records(
        root / "model" / "de" / "translate_act" / "shard.jsonl",
        [
            {
                "record_id": record_id(
                    "model", "de", "translate_act", item_id, sample_index
                ),
                "model_id": "model",
                "language": "de",
                "arm": "translate_act",
                "item_id": item_id,
                "sample_index": sample_index,
                "seed": sample_index,
                "input_token_ids": [],
                "input_token_count": 0,
                "output_token_ids": [],
                "output_token_count": 0,
                "text": text,
                "eos": True,
                "started_at": "2026-07-25T00:00:00+00:00",
                "completed_at": "2026-07-25T00:00:01+00:00",
            }
        ],
    )


def test_translation_loader_extracts_only_scored_sample_zero_items(
    tmp_path: Path,
) -> None:
    _write_translation_record(
        tmp_path,
        "0",
        0,
        "Translation: English zero.\n=== TRANSLATION END ===\n#### 1",
    )
    _write_translation_record(tmp_path, "1", 0, "missing delimiter")
    _write_translation_record(
        tmp_path,
        "0",
        1,
        "Ignored sample.\n=== TRANSLATION END ===\n#### 1",
    )
    fixtures = {
        "en": [
            MgsmItem("0", "Reference zero.", 1),
            MgsmItem("1", "Reference one.", 2),
        ],
        "de": [
            MgsmItem("0", "Quelle null.", 1),
            MgsmItem("1", "Quelle eins.", 2),
        ],
    }

    triples, missing = load_sample_zero_translation_triples(
        ("model",),
        tmp_path,
        languages=("de",),
        item_loader=fixtures.__getitem__,
    )

    assert triples == {
        ("model", "de"): [
            TranslationTriple(
                "0", "Quelle null.", "English zero.", "Reference zero."
            )
        ]
    }
    assert missing == {("model", "de"): 1}


def test_verdict_does_not_treat_opposite_direction_cells_as_consistent() -> None:
    triples = {
        ("model", language): [
            TranslationTriple(str(i), "source", f"score={score}", "reference")
            for i, score in enumerate((0.1, 0.2, 0.8, 0.9))
        ]
        for language in ("de", "sw")
    }
    outcomes = {
        ("model", "de"): {
            str(i): PeakOutcome(int(i >= 2), 0, 0.0)
            for i in range(4)
        },
        ("model", "sw"): {
            str(i): PeakOutcome(int(i < 2), 0, 0.0)
            for i in range(4)
        },
    }

    report = analyze_comet_gain_associations(
        triples,
        outcomes,
        {("model", "de"): 192, ("model", "sw"): 128},
        OrderedMockScorer(),
        n_boot=199,
        seed=8,
    )

    assert "do not show a consistent strong relationship" in report["verdict"]
