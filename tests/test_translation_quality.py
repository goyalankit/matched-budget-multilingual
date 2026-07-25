import json
from pathlib import Path
from types import SimpleNamespace

from src.mgsm import MgsmItem
from src.translation_quality import (
    BuiltinSurfaceOverlapScorer,
    CometScorer,
    TranslationTriple,
    analyze_translation_quality,
    extract_translation,
    translation_quality_markdown,
)


class CannedScorer:
    name = "canned-reference-scorer"
    scorer_type = "COMET"
    metric_names = ("COMET",)

    def __init__(self) -> None:
        self.triples: list[TranslationTriple] = []

    def score_batch(
        self, triples: list[TranslationTriple]
    ) -> dict[str, list[float]]:
        self.triples = triples
        return {"COMET": [0.8 for _ in triples]}


def _write_shard(root: Path, records: list[dict[str, object]]) -> None:
    path = root / "model" / "de" / "translate_act" / "shard.jsonl"
    path.parent.mkdir(parents=True)
    complete_records = []
    for record in records:
        item_id = str(record["item_id"])
        sample_index = int(record["sample_index"])
        complete_records.append(
            {
                "record_id": f"model-de-translate_act-{item_id}-{sample_index}",
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
                "text": record["text"],
                "eos": True,
                "started_at": "2026-01-01T00:00:00+00:00",
                "completed_at": "2026-01-01T00:00:01+00:00",
            }
        )
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in complete_records),
        encoding="utf-8",
    )


def test_extract_translation_removes_observed_scaffold() -> None:
    trace = (
        "Here is the translation of the problem into English:\n\n"
        '"Janet has 16 eggs. How many remain?"\n\n'
        "=== TRANSLATION END ===\n"
        "Now solve the problem.\n"
        "=== TRANSLATION END ==="
    )

    segment = extract_translation(trace)

    assert segment.text == "Janet has 16 eggs. How many remain?"
    assert not segment.missing_delimiter


def test_extract_translation_excludes_missing_exact_delimiter() -> None:
    segment = extract_translation(
        "A translated problem.\n### TRANSLATION END ###\nReasoning follows."
    )

    assert segment.text is None
    assert segment.missing_delimiter


def test_comet_adapter_is_offline_with_canned_model_scores() -> None:
    calls = []

    class FakeCometModel:
        def predict(self, data, batch_size: int, gpus: int):
            calls.append((data, batch_size, gpus))
            return SimpleNamespace(scores=[0.25])

    triple = TranslationTriple("4", "Quelle", "Translation", "Reference")
    scorer = CometScorer(
        FakeCometModel(), "mock/checkpoint", batch_size=3, gpus=0
    )

    assert scorer.score_batch([triple]) == {"COMET": [0.25]}
    assert calls == [
        (
            [{"src": "Quelle", "mt": "Translation", "ref": "Reference"}],
            3,
            0,
        )
    ]


def test_builtin_surface_proxy_scores_exact_reference_at_one_hundred() -> None:
    triple = TranslationTriple(
        "4",
        "Die Quelle.",
        "The exact reference.",
        "The exact reference.",
    )

    scores = BuiltinSurfaceOverlapScorer().score_batch([triple])

    assert scores == {"chrF": [100.0], "sentenceBLEU": [100.0]}


def test_analysis_scores_sample_zero_against_parallel_english_reference(
    tmp_path: Path,
) -> None:
    _write_shard(
        tmp_path,
        [
            {
                "item_id": "0",
                "sample_index": 0,
                "text": "Good translation.\n=== TRANSLATION END ===\nsolution",
            },
            {
                "item_id": "1",
                "sample_index": 0,
                "text": "missing delimiter",
            },
            {
                "item_id": "0",
                "sample_index": 1,
                "text": "Ignored sample.\n=== TRANSLATION END ===\nsolution",
            },
        ],
    )
    fixtures = {
        "en": [
            MgsmItem("0", "English reference zero.", 10),
            MgsmItem("1", "English reference one.", 20),
        ],
        "de": [
            MgsmItem("0", "Deutsche Quelle null.", 10),
            MgsmItem("1", "Deutsche Quelle eins.", 20),
        ],
    }
    scorer = CannedScorer()

    report = analyze_translation_quality(
        ("model",),
        tmp_path,
        scorer,
        languages=("de",),
        item_loader=fixtures.__getitem__,
        n_boot=99,
        seed=7,
    )

    assert scorer.triples == [
        TranslationTriple(
            item_id="0",
            source="Deutsche Quelle null.",
            mt="Good translation.",
            reference="English reference zero.",
        )
    ]
    cell = report["models"]["model"]["de"]
    assert cell["sample_index"] == 0
    assert cell["n_total"] == 2
    assert cell["n_scored"] == 1
    assert cell["missing_delimiter_n"] == 1
    assert cell["missing_delimiter_rate"] == 0.5
    assert cell["metrics"]["COMET"] == {
        "mean": 0.8,
        "median": 0.8,
        "p10": 0.8,
        "p90": 0.8,
        "bootstrap_ci_95": [0.8, 0.8],
    }

    markdown = translation_quality_markdown(report)
    assert "non-confirmatory (§11)" in markdown
    assert "never condition, gate, exclude, reweight" in markdown
    assert "| model | de | COMET | 1 | 50.00% | 0.8000 |" in markdown
