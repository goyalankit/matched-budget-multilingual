import dataclasses
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

from src.benchmark_spec import load_spec
from src.benchmark_data import Item, load_items, verify_parallelism


class _FakeDataset(list):
    pass


def _fake_loader(rows):
    def load(dataset, config, split):
        return _FakeDataset(rows)
    return load


def test_load_items_maps_spec_fields(monkeypatch):
    spec = load_spec("mgsm")
    rows = [{"question": f"q{index}", "answer_number": index} for index in range(250)]
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))
    items = load_items(spec, "de")
    assert len(items) == 250
    assert items[0] == Item(item_id="0", question="q0", gold=0)


def test_wrong_item_count_is_rejected(monkeypatch):
    spec = load_spec("mgsm")
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader([{"question": "q", "answer_number": 1}]))
    with pytest.raises(ValueError, match="expected 250"):
        load_items(spec, "de")


def test_verify_parallelism_detects_a_gold_mismatch(monkeypatch):
    # BenchmarkSpec is a frozen dataclass, so build a variant with
    # dataclasses.replace -- monkeypatch.setattr on the instance raises
    # FrozenInstanceError.
    spec = dataclasses.replace(load_spec("mgsm"), expected_items=1)
    by_language = {
        "de": [{"question": "a", "answer_number": 1}],
        "th": [{"question": "b", "answer_number": 1}],
        "sw": [{"question": "c", "answer_number": 2}],
    }

    def load(dataset, config, split):
        return _FakeDataset(by_language[config])

    monkeypatch.setattr("src.benchmark_data._load_split", load)
    report = verify_parallelism(spec)
    assert report["parallel"] is False
    assert report["n_mismatches"] == 1


@pytest.mark.skip(reason="requires the MGSM dataset download")
def test_matches_the_frozen_mgsm_loader():
    from src.mgsm import load_mgsm

    spec = load_spec("mgsm")
    for language in ("de", "th", "sw"):
        generic = load_items(spec, language)
        frozen = load_mgsm(language)
        assert [(i.item_id, i.question, i.gold) for i in generic] == [
            (i.item_id, i.question, i.gold) for i in frozen
        ]


def test_gold_is_normalised_to_the_answer_kind(monkeypatch):
    """MGSM ships answer_number as a STRING, including "0042".

    Left raw, answers_equal(42, "0042", "integer") is False and every item
    scores zero. The frozen src/mgsm.py applies int(); the generic loader must
    agree or the two frames measure different things.
    """
    from src.answer_grammar import answers_equal

    spec = load_spec("mgsm")
    rows = [{"question": f"q{index}", "answer_number": str(index)} for index in range(250)]
    rows[0]["answer_number"] = "0042"
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))
    items = load_items(spec, "de")
    assert items[0].gold == 42
    assert isinstance(items[0].gold, int)
    assert answers_equal(42, items[0].gold, "integer")


def test_mmath_local_json_loader_excludes_the_complete_cnmo_subset():
    spec = load_spec("mmath")
    raw = json.loads(Path("data/mmath/zh.json").read_text(encoding="utf-8"))
    items = load_items(spec, "zh")

    assert len(raw) == 374
    assert sum(row["data_source"] == "CNMO" for row in raw) == 18
    assert len(items) == 356
    assert len(raw) - len(items) == 18
    assert Counter(
        row["data_source"] for row in raw if row["data_source"] != "CNMO"
    ) == {"AIME2024": 30, "AIME2025": 15, "MATH500": 311}
    excluded_ids = {
        str(row["gid"]) for row in raw if row["data_source"] == "CNMO"
    }
    assert excluded_ids.isdisjoint({item.item_id for item in items})


def test_mmath_languages_remain_gid_aligned_after_exclusion():
    spec = load_spec("mmath")
    ids_by_language = [
        [item.item_id for item in load_items(spec, language)]
        for language in ("zh", "es", "th")
    ]
    assert ids_by_language[0] == ids_by_language[1] == ids_by_language[2]


def test_mmath_numeric_gold_is_normalised_to_fraction():
    items = load_items(load_spec("mmath"), "es")
    assert all(isinstance(item.gold, Fraction) for item in items)
    assert items[0].gold == Fraction(204)


def test_multiple_choice_fields_are_assembled_with_one_indexed_options(monkeypatch):
    spec = dataclasses.replace(load_spec("belebele"), expected_items=1)
    rows = [{
        "flores_passage": "passage",
        "question": "question",
        "mc_answer1": "first",
        "mc_answer2": "second",
        "mc_answer3": "third",
        "mc_answer4": "fourth",
        "correct_answer_num": "3",
    }]
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))

    item = load_items(spec, "de")[0]

    assert item.question == (
        "passage\n\nquestion\n\n"
        "1. first\n2. second\n3. third\n4. fourth"
    )
    assert item.gold == 3


def test_zero_based_dataset_gold_maps_to_the_numbered_option(monkeypatch):
    """The off-by-one guard, kept after XCOPA was dropped.

    XCOPA was the only benchmark shipping a 0-based gold index. It is gone, but
    the mapping is the kind of error that scores an entire benchmark wrong while
    looking plausible, so the guard is retained against a synthetic spec rather
    than deleted with its only user.
    """
    spec = dataclasses.replace(
        load_spec("belebele"),
        expected_items=1,
        gold_source_encoding="index0",
        gold_field="label",
        passage_field=None,
        question_field="premise",
        option_fields=("choice1", "choice2"),
    )
    rows = [{
        "premise": "question",
        "choice1": "first",
        "choice2": "second",
        "label": 1,
    }]
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))

    item = load_items(spec, "sw")[0]
    # 0-based label 1 is the SECOND option, displayed as 2.
    assert item.gold == 2


def test_letter_dataset_gold_maps_to_the_numbered_option(monkeypatch):
    spec = dataclasses.replace(load_spec("global_mmlu_lite"), expected_items=1)
    rows = [
        {
            "question": "question",
            "option_a": "first",
            "option_b": "second",
            "option_c": "third",
            "option_d": "fourth",
            "answer": "C",
        }
    ]
    monkeypatch.setattr("src.benchmark_data._load_split", _fake_loader(rows))

    item = load_items(spec, "de")[0]

    assert item.gold == 3
