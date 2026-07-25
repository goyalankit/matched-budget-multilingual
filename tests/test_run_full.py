from __future__ import annotations

import random
import time
from collections import Counter
from threading import Lock

from src.engine import GenerationResult
from src.generate import read_ledger
from src.mgsm import MgsmQuestion
from src.seeds import seed


class RecordingEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int]] = []
        self._lock = Lock()

    def generate(
        self, prompt: str, generation_seed: int, max_tokens: int
    ) -> GenerationResult:
        with self._lock:
            self.calls.append((prompt, generation_seed, max_tokens))
        text = f"seed={generation_seed}"
        return GenerationResult(
            token_ids=list(text.encode("utf-8")),
            text=text,
            eos=True,
        )


def _questions(language: str) -> list[MgsmQuestion]:
    return [
        MgsmQuestion(str(index), f"{language} problem {index}")
        for index in range(3)
    ]


def test_run_model_generates_every_registered_unit_once(monkeypatch, tmp_path) -> None:
    import src.run_full as run_full

    monkeypatch.setattr(run_full, "load_mgsm_questions", _questions)
    engine = RecordingEngine()

    report = run_full.run_model(
        "mock_model",
        engine,
        languages=("de", "th"),
        arms=(run_full.NATIVE, run_full.PIVOT),
        n_items=2,
        k=3,
        max_tokens=123,
        concurrency=4,
        out_dir=tmp_path,
    )

    expected_units = {
        (language, arm, str(item_index), sample_index)
        for language in ("de", "th")
        for arm in (run_full.NATIVE, run_full.PIVOT)
        for item_index in range(2)
        for sample_index in range(3)
    }
    records = [
        record
        for shard in report["shards"]
        for record in read_ledger(tmp_path / shard["path"])
    ]

    assert report["total_units"] == len(expected_units)
    assert report["generated_this_run"] == len(expected_units)
    assert report["already_present"] == 0
    assert len(engine.calls) == len(expected_units)
    assert {
        (
            record["language"],
            record["arm"],
            record["item_id"],
            record["sample_index"],
        )
        for record in records
    } == expected_units
    assert len({record["record_id"] for record in records}) == len(expected_units)
    assert all(record["model_id"] == "mock_model" for record in records)
    assert all(call[2] == 123 for call in engine.calls)
    assert all("{problem}" not in call[0] for call in engine.calls)
    assert sum("de problem 0" in call[0] for call in engine.calls) == 6
    expected_seeds = [
        seed(20260724, item_id, sample_index)
        for _, _, item_id, sample_index in expected_units
    ]
    assert all(
        record["seed"]
        == seed(20260724, record["item_id"], record["sample_index"])
        for record in records
    )
    assert Counter(call[1] for call in engine.calls) == Counter(expected_seeds)


def test_run_model_resumes_only_missing_units(monkeypatch, tmp_path) -> None:
    import src.run_full as run_full

    monkeypatch.setattr(run_full, "load_mgsm_questions", _questions)
    first_engine = RecordingEngine()
    kwargs = {
        "model_key": "mock_model",
        "languages": ("de",),
        "arms": (run_full.NATIVE,),
        "n_items": 2,
        "k": 2,
        "concurrency": 3,
        "out_dir": tmp_path,
    }
    run_full.run_model(engine=first_engine, **kwargs)
    shard = tmp_path / "mock_model/de/native/shard.jsonl"
    complete_lines = shard.read_text(encoding="utf-8").splitlines()
    shard.write_text("\n".join(complete_lines[:3]) + "\n", encoding="utf-8")

    resumed_engine = RecordingEngine()
    report = run_full.run_model(engine=resumed_engine, **kwargs)
    records = read_ledger(shard)

    assert report["total_units"] == 4
    assert report["already_present"] == 3
    assert report["generated_this_run"] == 1
    assert len(resumed_engine.calls) == 1
    assert len(records) == 4
    assert len({record["record_id"] for record in records}) == 4

    no_op_engine = RecordingEngine()
    no_op_report = run_full.run_model(engine=no_op_engine, **kwargs)
    assert no_op_report["already_present"] == 4
    assert no_op_report["generated_this_run"] == 0
    assert no_op_engine.calls == []


def test_concurrent_run_writes_valid_unique_jsonl(monkeypatch, tmp_path) -> None:
    import src.run_full as run_full

    questions = [
        MgsmQuestion(str(index), f"problem {index}") for index in range(12)
    ]
    monkeypatch.setattr(
        run_full, "load_mgsm_questions", lambda _: questions
    )

    class JitterEngine(RecordingEngine):
        def generate(
            self, prompt: str, generation_seed: int, max_tokens: int
        ) -> GenerationResult:
            time.sleep(random.Random(generation_seed).uniform(0.0001, 0.003))
            return super().generate(prompt, generation_seed, max_tokens)

    report = run_full.run_model(
        "mock_model",
        JitterEngine(),
        languages=("sw",),
        arms=(run_full.CODE_SWITCHED,),
        n_items=12,
        k=4,
        concurrency=12,
        out_dir=tmp_path,
    )
    shard = tmp_path / report["shards"][0]["path"]
    records = read_ledger(shard)

    assert len(records) == 48
    assert len({record["record_id"] for record in records}) == 48
    assert report["shards"][0]["record_count"] == 48
    assert report["shards"][0]["unique_count"] == 48
