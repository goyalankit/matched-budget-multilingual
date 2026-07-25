import sys
from types import ModuleType

import pytest

import src.mgsm as mgsm
from src.mgsm import MgsmItem


def _items(*golds: int) -> list[MgsmItem]:
    return [
        MgsmItem(str(index), f"question {index}", gold)
        for index, gold in enumerate(golds)
    ]


def test_verify_parallelism_accepts_aligned_gold_sequences(monkeypatch) -> None:
    fixtures = {
        "de": _items(10, 20, 30),
        "th": _items(10, 20, 30),
        "sw": _items(10, 20, 30),
    }
    monkeypatch.setattr(mgsm, "load_mgsm", fixtures.__getitem__)

    assert mgsm.verify_parallelism() == {
        "parallel": True,
        "n_items": 3,
        "first_mismatch_index": None,
        "n_mismatches": 0,
    }


def test_verify_parallelism_reports_exact_first_mismatch(monkeypatch) -> None:
    fixtures = {
        "de": _items(10, 20, 30, 40),
        "th": _items(10, 99, 30, 41),
        "sw": _items(10, 20, 30, 40),
    }
    monkeypatch.setattr(mgsm, "load_mgsm", fixtures.__getitem__)

    assert mgsm.verify_parallelism() == {
        "parallel": False,
        "n_items": 4,
        "first_mismatch_index": 1,
        "n_mismatches": 2,
    }


def test_load_mgsm_parses_answer_number_as_int(monkeypatch) -> None:
    calls = []
    rows = [
        {"question": f"problem {index}", "answer_number": str(index)}
        for index in range(250)
    ]
    rows[0]["answer_number"] = "0042"
    fake_datasets = ModuleType("datasets")

    def fake_load_dataset(name: str, language: str, split: str):
        calls.append((name, language, split))
        return rows

    fake_datasets.load_dataset = fake_load_dataset
    monkeypatch.setitem(sys.modules, "datasets", fake_datasets)

    items = mgsm.load_mgsm("de")

    assert calls == [("juletxara/mgsm", "de", "test")]
    assert items[0] == MgsmItem(item_id="0", question="problem 0", gold=42)
    assert items[-1].item_id == "249"


def test_load_mgsm_rejects_unexpected_item_count(monkeypatch) -> None:
    fake_datasets = ModuleType("datasets")
    fake_datasets.load_dataset = lambda *args, **kwargs: []
    monkeypatch.setitem(sys.modules, "datasets", fake_datasets)

    with pytest.raises(ValueError, match="expected 250 MGSM items"):
        mgsm.load_mgsm("de")
