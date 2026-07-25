from pathlib import Path

import numpy as np

from src.generate import append_ledger_records, record_id
from src.mgsm import MgsmItem


def _write_record(
    ledger_root: Path,
    *,
    model_key: str,
    language: str,
    arm: str,
    item_id: str,
    output_token_ids: list[int],
    text: str,
    input_token_count: int = 1,
    sample_index: int = 0,
    eos: bool = True,
) -> None:
    append_ledger_records(
        ledger_root / model_key / language / arm / "shard.jsonl",
        [
            {
                "record_id": record_id(
                    model_key, language, arm, item_id, sample_index
                ),
                "model_id": model_key,
                "language": language,
                "arm": arm,
                "item_id": item_id,
                "sample_index": sample_index,
                "seed": 1,
                "input_token_ids": [],
                "input_token_count": input_token_count,
                "output_token_ids": output_token_ids,
                "output_token_count": len(output_token_ids),
                "text": text,
                "eos": eos,
                "started_at": "2026-07-25T00:00:00+00:00",
                "completed_at": "2026-07-25T00:00:01+00:00",
            }
        ],
    )


def test_score_ledger_joins_mgsm_gold_and_decodes_token_prefix(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real

    _write_record(
        tmp_path,
        model_key="model",
        language="de",
        arm="native",
        item_id="0",
        output_token_ids=[10, 11],
        text="##",
    )
    monkeypatch.setattr(
        analyze_real,
        "load_mgsm",
        lambda language: [MgsmItem("0", "question", 42)],
    )
    token_text = {10: "#### ", 11: "42"}

    class BatchDecoder:
        called = False

        def __call__(self, ids):
            raise AssertionError("batch decoding should be preferred")

        def decode_many(self, sequences):
            self.called = True
            return [
                "".join(token_text[token] for token in ids)
                for ids in sequences
            ]

    decoder = BatchDecoder()
    frames = analyze_real.score_ledger(
        "model",
        tmp_path,
        ["de"],
        ["native"],
        {
            "n_items": 1,
            "k": 1,
            "token_checkpoints": [2],
            "premiums": {"de": 1.0},
            "prices": {"input": 0.0, "output": 1.0},
            "dollar_grid": [2.0],
        },
        decoder,
    )

    assert decoder.called
    assert frames["token"][0, 0, 0, 0, 0] == 1


def test_score_ledger_scores_all_cells_with_each_languages_gold(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real

    languages = ["de", "th", "sw"]
    arms = ["native", "translate_act", "pivot", "code_switched"]
    language_golds = {"de": 42, "th": 43, "sw": 44}
    for language in languages:
        for arm in arms:
            for item_id, answer in (("0", language_golds[language]), ("1", 999)):
                text = f"work\n#### {answer}"
                _write_record(
                    tmp_path,
                    model_key="model",
                    language=language,
                    arm=arm,
                    item_id=item_id,
                    output_token_ids=list(map(ord, text)),
                    text=text,
                    input_token_count=2,
                )
    monkeypatch.setattr(
        analyze_real,
        "load_mgsm",
        lambda language: [
            MgsmItem("0", "question 0", language_golds[language]),
            MgsmItem("1", "question 1", 100),
        ],
    )

    frames = analyze_real.score_ledger(
        "model",
        tmp_path,
        languages,
        arms,
        {
            "n_items": 2,
            "k": 1,
            "token_checkpoints": [32],
            "premiums": dict.fromkeys(languages, 1.0),
            "prices": {"input": 1.0, "output": 1.0},
            "dollar_grid": [1.0],
        },
        lambda ids: "".join(map(chr, ids)),
    )

    assert np.all(frames["token"][0] == 1)
    assert np.all(frames["token"][1] == 0)
    assert np.isnan(frames["dollar"]).all()


def test_run_real_confirmatory_assembles_frozen_study_config(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real

    captured = {}
    sentinel_frames = {
        name: np.zeros((250, 3, 4, 4, 8))
        for name in ("token", "flores", "dollar")
    }

    def fake_score(model_key, ledger_root, languages, arms, study, decode):
        captured.update(
            {
                "model_key": model_key,
                "ledger_root": ledger_root,
                "languages": list(languages),
                "arms": list(arms),
                "study": study,
            }
        )
        return sentinel_frames

    def fake_analyze(frames, study, power):
        assert frames is sentinel_frames
        captured["power"] = power
        return {"confirmatory": "result"}

    monkeypatch.setattr(analyze_real, "score_ledger", fake_score)
    monkeypatch.setattr(analyze_real, "analyze_confirmatory", fake_analyze)
    snapshot = {
        "models": {
            "qwen3_8b": {
                "P_in_usd_per_tok": 0.25,
                "P_out_usd_per_tok": 2.0,
            }
        }
    }

    result = analyze_real.run_real_confirmatory(
        "qwen3_8b", tmp_path, lambda ids: "", snapshot
    )

    assert result == {"confirmatory": "result"}
    assert captured["languages"] == ["de", "th", "sw"]
    assert captured["arms"] == [
        "native",
        "translate_act",
        "pivot",
        "code_switched",
    ]
    assert captured["study"]["n_items"] == 250
    assert captured["study"]["k"] == 8
    assert captured["study"]["b_star"] == 1024
    assert captured["study"]["token_checkpoints"] == [512, 1024, 2048, 4096]
    assert captured["study"]["prices"] == {"input": 0.25, "output": 2.0}
    assert captured["study"]["dollar_grid"] == [1024.0, 2048.0, 4096.0, 8192.0]
    assert captured["study"]["premiums"]["th"] == 2.550777
    assert captured["study"]["six_tests"] == [
        "h1_existence",
        "h1_sesoi",
        "h2",
        "h3_de",
        "h3_th",
        "h3_sw",
    ]


def test_real_frames_feed_validated_confirmatory_analysis(
    tmp_path, monkeypatch
) -> None:
    from src import analyze_real
    from src.rehearsal import analyze_confirmatory

    languages = ["de", "th", "sw"]
    arms = ["native", "translate_act", "pivot", "code_switched"]
    golds = {str(item_index): 40 + item_index for item_index in range(4)}
    emissions = [8, 14, 24, 40]
    for language_index, language in enumerate(languages):
        for arm_index, arm in enumerate(arms):
            for item_index in range(4):
                for sample_index in range(2):
                    gold = golds[str(item_index)]
                    correct = (
                        item_index + sample_index + arm_index + language_index
                    ) % 3
                    answer = gold if correct else gold + 1
                    emission = emissions[
                        (item_index + sample_index + arm_index) % len(emissions)
                    ]
                    answer_line = f"\n#### {answer}"
                    text = "x" * (emission - len(answer_line)) + answer_line
                    _write_record(
                        tmp_path,
                        model_key="model",
                        language=language,
                        arm=arm,
                        item_id=str(item_index),
                        output_token_ids=list(map(ord, text)),
                        text=text,
                        input_token_count=2,
                        sample_index=sample_index,
                    )
    monkeypatch.setattr(
        analyze_real,
        "load_mgsm",
        lambda language: [
            MgsmItem(item_id, f"question {item_id}", gold)
            for item_id, gold in golds.items()
        ],
    )
    study = {
        "n_items": 4,
        "k": 2,
        "n_boot": 31,
        "base_seed": 20260724,
        "b_star": 16,
        "token_checkpoints": [8, 16, 32, 64],
        "premiums": {"de": 1.5, "th": 2.0, "sw": 1.75},
        "prices": {"input": 1.0, "output": 1.0},
        "dollar_grid": [1.0, 16.0, 32.0, 64.0],
        "six_tests": [
            "h1_existence",
            "h1_sesoi",
            "h2",
            "h3_de",
            "h3_th",
            "h3_sw",
        ],
    }
    power = {"languages": languages, "arms": arms}

    frames = analyze_real.score_ledger(
        "model",
        tmp_path,
        languages,
        arms,
        study,
        lambda ids: "".join(map(chr, ids)),
    )
    result = analyze_confirmatory(frames, study, power)

    assert set(result) >= {
        "primary_estimand_delta_points",
        "tiered_h1_outcome",
        "h1",
        "h2",
        "h3",
        "holm_family",
        "accuracy_curves_points",
    }
    assert set(result["primary_estimand_delta_points"]) == set(languages)
    assert len(result["holm_family"]) == 6
