import pytest

from src.comet_score import MockScorer, extract_translation_segment, score_translation
from src.langid_check import (
    GlotLIDClassifier,
    KeywordClassifier,
    balanced_validation_sample,
    classify_trace,
    evaluate_validation,
    strip_for_langid,
)
from src.comet_score import CometScorer


def test_langid_stripping_and_indeterminate_rule() -> None:
    cleaned = strip_for_langid("#### 42\n$1+x$ Deutsch reasoning 123")
    assert "42" not in cleaned
    assert "1+x" not in cleaned
    classifier = KeywordClassifier({"de": ["deutsch"]})
    assert classify_trace("Deutsch short", classifier) == "indeterminate"


def test_balanced_sampler_and_validation_thresholds() -> None:
    records = []
    labels = {}
    for arm in ("native", "pivot"):
        for language, word in (("de", "deutsch"), ("th", "thai")):
            for index in range(4):
                record_id = f"{arm}-{language}-{index}"
                record = {
                    "record_id": record_id,
                    "arm": arm,
                    "language": language,
                    "text": (word + " ") * 20,
                }
                records.append(record)
                labels[record_id] = language
    sample = balanced_validation_sample(records, per_cell=2, seed=4)
    result = evaluate_validation(
        sample,
        labels,
        KeywordClassifier({"de": ["deutsch"], "th": ["thai"]}),
    )
    assert len(sample) == 8
    assert result.passed
    assert result.overall_agreement == 1.0


def test_validation_fails_when_one_cell_is_below_ninety_percent() -> None:
    records = [
        {
            "record_id": f"x-{index}",
            "arm": "native",
            "language": "de",
            "text": "deutsch " * 20,
        }
        for index in range(20)
    ]
    labels = {record["record_id"]: "de" for record in records}
    labels["x-0"] = "th"
    labels["x-1"] = "th"
    labels["x-2"] = "th"
    result = evaluate_validation(
        records, labels, KeywordClassifier({"de": ["deutsch"]})
    )
    assert not result.passed
    assert result.overall_agreement == 0.85


def test_comet_segment_uses_first_delimiter_and_flags_missing() -> None:
    trace = "translation one\n=== TRANSLATION END ===\nreason\n=== TRANSLATION END ==="
    segment = extract_translation_segment(trace)
    assert segment.text == "translation one\n"
    assert not segment.missing_delimiter
    score, missing = score_translation("translation", trace, MockScorer())
    assert score is not None
    assert not missing

    missing_segment = extract_translation_segment("reasoning only")
    assert missing_segment.text == ""
    assert missing_segment.missing_delimiter


@pytest.mark.skip(reason="requires GlotLID")
def test_real_glotlid_backend() -> None:
    GlotLIDClassifier()


@pytest.mark.skip(reason="requires comet")
def test_real_comet_backend() -> None:
    CometScorer()
