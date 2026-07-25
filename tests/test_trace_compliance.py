import json
from pathlib import Path

from src.glotlid_classifier import GlotLIDClassifier, map_glotlid_label
from src.trace_compliance import trace_language_compliance


class CannedClassifier:
    def classify(self, text: str) -> str:
        if "German marker" in text:
            return "de"
        return "en"


class RecordingClassifier:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def classify(self, text: str) -> str:
        self.texts.append(text)
        return "en"


class FirstTokenClassifier:
    def classify(self, text: str) -> str:
        return text.split(maxsplit=1)[0]


def _write_shard(
    root: Path,
    model_key: str,
    language: str,
    arm: str,
    texts: list[str],
) -> None:
    path = root / model_key / language / arm / "shard.jsonl"
    path.parent.mkdir(parents=True)
    records = [
        {
            "record_id": f"{model_key}-{language}-{arm}-{index}",
            "model_id": model_key,
            "language": language,
            "arm": arm,
            "item_id": str(index),
            "sample_index": 0,
            "seed": index,
            "input_token_ids": [],
            "input_token_count": 0,
            "output_token_ids": [],
            "output_token_count": 0,
            "text": text,
            "eos": True,
            "started_at": "2026-01-01T00:00:00+00:00",
            "completed_at": "2026-01-01T00:00:01+00:00",
        }
        for index, text in enumerate(texts)
    ]
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_native_arm_is_compared_with_item_language(tmp_path: Path) -> None:
    text = "German marker with enough alphabetic characters for classification."
    _write_shard(tmp_path, "model", "de", "native", [text])

    report = trace_language_compliance("model", tmp_path, CannedClassifier())

    cell = report["cells"]["de"]["native"]
    assert cell["instructed_trace_language"] == "de"
    assert cell["n"] == 1
    assert cell["compliance_rate"] == 1.0


def test_translate_act_classifies_only_reasoning_after_delimiter(
    tmp_path: Path,
) -> None:
    translation = "German marker before delimiter with many alphabetic characters."
    reasoning = "English reasoning after delimiter with many alphabetic characters."
    _write_shard(
        tmp_path,
        "model",
        "de",
        "translate_act",
        [f"{translation}\n=== TRANSLATION END ===\n{reasoning}"],
    )
    classifier = RecordingClassifier()

    report = trace_language_compliance("model", tmp_path, classifier)

    cell = report["cells"]["de"]["translate_act"]
    assert classifier.texts == [f"\n{reasoning}"]
    assert cell["instructed_trace_language"] == "en"
    assert cell["missing_translation_delimiter_n"] == 0
    assert cell["compliance_rate"] == 1.0


def test_translate_act_missing_delimiter_classifies_whole_trace_and_notes_it(
    tmp_path: Path,
) -> None:
    text = "English reasoning without delimiter but with many alphabetic characters."
    _write_shard(tmp_path, "model", "th", "translate_act", [text])
    classifier = RecordingClassifier()

    report = trace_language_compliance("model", tmp_path, classifier)

    cell = report["cells"]["th"]["translate_act"]
    assert classifier.texts == [text]
    assert cell["missing_translation_delimiter_n"] == 1
    assert cell["missing_translation_delimiter_rate"] == 1.0
    assert "whole trace" in report["missing_translation_delimiter_note"]


def test_indeterminate_traces_are_excluded_from_compliance_denominator(
    tmp_path: Path,
) -> None:
    german = "German marker with enough alphabetic characters for classification."
    english = "English marker with enough alphabetic characters for classification."
    _write_shard(
        tmp_path,
        "model",
        "de",
        "native",
        [german, german, german, english, "#### 42\n$1+1$ kurz"],
    )

    report = trace_language_compliance("model", tmp_path, CannedClassifier())

    cell = report["cells"]["de"]["native"]
    assert cell["n"] == 5
    assert cell["determinate_n"] == 4
    assert cell["indeterminate_rate"] == 0.2
    assert cell["compliance_rate"] == 0.75
    assert cell["english_detection_rate"] == 0.25
    assert cell["non_compliant"] is True


def test_top_three_detected_languages_use_determinate_shares(
    tmp_path: Path,
) -> None:
    texts = [
        f"{language} trace contains enough alphabetic characters to classify."
        for language in ("de", "de", "de", "de", "en", "en", "en", "th", "th", "sw")
    ]
    _write_shard(tmp_path, "model", "de", "native", texts)

    report = trace_language_compliance("model", tmp_path, FirstTokenClassifier())

    assert report["cells"]["de"]["native"]["top_detected_languages"] == [
        {"language": "de", "share": 0.4},
        {"language": "en", "share": 0.3},
        {"language": "th", "share": 0.2},
    ]


def test_instructed_trace_language_mapping_for_every_arm(tmp_path: Path) -> None:
    for arm, detected in (
        ("native", "sw"),
        ("translate_act", "en"),
        ("pivot", "en"),
        ("code_switched", "en"),
    ):
        text = f"{detected} trace contains enough alphabetic characters to classify."
        if arm == "translate_act":
            text = f"translated problem\n=== TRANSLATION END ===\n{text}"
        _write_shard(tmp_path, "model", "sw", arm, [text])

    report = trace_language_compliance("model", tmp_path, FirstTokenClassifier())

    assert {
        arm: cell["instructed_trace_language"]
        for arm, cell in report["cells"]["sw"].items()
    } == {
        "native": "sw",
        "translate_act": "en",
        "pivot": "en",
        "code_switched": "en",
    }
    assert all(
        cell["compliance_rate"] == 1.0 for cell in report["cells"]["sw"].values()
    )


def test_glotlid_iso_script_labels_map_to_study_languages() -> None:
    assert map_glotlid_label("__label__deu_Latn") == "de"
    assert map_glotlid_label("__label__tha_Thai") == "th"
    assert map_glotlid_label("__label__swh_Latn") == "sw"
    assert (
        map_glotlid_label("__label__swc_Latn") == "sw"
    )  # Congo Swahili (macrolanguage swa)
    assert map_glotlid_label("__label__eng_Latn") == "en"
    assert map_glotlid_label("__label__fra_Latn") == "other"
    assert (
        map_glotlid_label("__label__kam_Latn") == "other"
    )  # Kamba: a different Bantu language


def test_glotlid_classifier_lazy_loads_model_from_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"offline test placeholder")
    monkeypatch.setenv("GLOTLID_MODEL_PATH", str(model_path))
    loaded_paths: list[str] = []
    predicted_texts: list[str] = []

    class FakeModel:
        def predict(self, text: str, k: int = 1):
            predicted_texts.append(text)
            assert k == 1
            return (["__label__tha_Thai"], [0.99])

    def load_model(path: str):
        loaded_paths.append(path)
        return FakeModel()

    classifier = GlotLIDClassifier(model_loader=load_model)
    assert loaded_paths == []

    assert classifier.classify("ข้อความ\nภาษาไทย") == "th"
    assert loaded_paths == [str(model_path)]
    assert predicted_texts == ["ข้อความ ภาษาไทย"]
