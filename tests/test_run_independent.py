from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock

import pytest

from src.engine import GenerationResult
from src.generate import (
    LedgerVerificationError,
    read_ledger,
    record_id,
    verify_ledger,
)
from src.mgsm import MgsmQuestion
from src.seeds import budget_seed, seed

_ROOT = Path(__file__).resolve().parents[1]


class RecordingEngine:
    """Engine that echoes its seed and honours the cap."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []
        self._lock = Lock()

    def generate(
        self, prompt: str, generation_seed: int, max_tokens: int
    ) -> GenerationResult:
        with self._lock:
            self.calls.append((generation_seed, max_tokens))
        text = f"seed={generation_seed}"
        token_ids = list(text.encode("utf-8"))[:max_tokens]
        return GenerationResult(token_ids=token_ids, text=text[:max_tokens], eos=True)


def _questions(language: str) -> list[MgsmQuestion]:
    return [
        MgsmQuestion(str(index), f"{language} problem {index}") for index in range(3)
    ]


# --- seed derivation -------------------------------------------------------


def test_budget_seed_matches_documented_hash_construction() -> None:
    payload = b"\x1f".join(
        value.encode("utf-8") for value in ("20260726", "item-007", "2", "256")
    )
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

    assert budget_seed(20260726, "item-007", 2, 256) == expected


def test_budget_seed_differs_across_budgets() -> None:
    """The whole experiment rests on this.

    If budgets shared a seed, vLLM would regenerate one trajectory and truncate
    it, which is prefix replay -- exactly what E1 exists to rule out.
    """
    seeds = {budget_seed(20260726, "item-1", 0, b) for b in (64, 128, 256, 512)}

    assert len(seeds) == 4


def test_budget_seed_is_shared_across_arms_at_one_budget() -> None:
    """Cross-arm pairing is preserved: the derivation has no arm field."""
    assert budget_seed(20260726, "item-1", 0, 256) == budget_seed(
        20260726, "item-1", 0, 256
    )


def test_budget_seed_is_distinct_from_the_frozen_derivation() -> None:
    assert budget_seed(20260724, "item-1", 0, 4096) != seed(20260724, "item-1", 0)


def test_budget_seed_rejects_nonpositive_budget() -> None:
    with pytest.raises(ValueError):
        budget_seed(20260726, "item-1", 0, 0)


# --- record_id -------------------------------------------------------------


def test_record_id_without_budget_is_unchanged() -> None:
    """Frozen-ledger IDs must not shift when the budget field is added."""
    assert record_id("m", "de", "native", "1", 6) == "m\x1fde\x1fnative\x1f1\x1f6"


def test_record_id_with_budget_disambiguates_caps() -> None:
    base = record_id("m", "de", "native", "1", 6)
    tagged = record_id("m", "de", "native", "1", 6, 256)

    assert tagged == base + "\x1fB256"
    assert tagged != record_id("m", "de", "native", "1", 6, 512)


# --- cap-set derivation ----------------------------------------------------


def test_cap_set_matches_frozen_premiums() -> None:
    import src.run_independent as run_independent

    premiums = json.loads((_ROOT / "configs" / "premiums.json").read_text())["models"]
    for model_key, entry in premiums.items():
        for language, values in entry["premiums"].items():
            ratio = values["ratio"]
            expected = sorted(
                set(run_independent.BUDGET_GRID)
                | {int(ratio * b) for b in run_independent.BUDGET_GRID}
            )
            assert (
                list(
                    run_independent.cap_set(model_key, language, run_independent.NATIVE)
                )
                == expected
            )


def test_only_native_receives_premium_caps() -> None:
    import src.run_independent as run_independent

    for arm in (
        run_independent.TRANSLATE_ACT,
        run_independent.PIVOT,
        run_independent.CODE_SWITCHED,
    ):
        assert run_independent.cap_set("qwen3_8b", "th", arm) == tuple(
            run_independent.BUDGET_GRID
        )


def test_grid_contains_the_budgets_the_protocol_predictions_need() -> None:
    """Qwen-de and Llama-th peaks sit at 192; omitting it makes them untestable."""
    import src.run_independent as run_independent

    assert {192, 384, 768} <= set(run_independent.BUDGET_GRID)


def test_shard_count_matches_the_frozen_protocol() -> None:
    import src.run_independent as run_independent

    premiums = json.loads((_ROOT / "configs" / "premiums.json").read_text())["models"]
    total = sum(
        len(run_independent.cap_set(model_key, language, arm))
        for model_key, entry in premiums.items()
        for language in entry["premiums"]
        for arm in run_independent.ALL_ARMS
    )

    assert total == 270


# --- driver ----------------------------------------------------------------


def _run(monkeypatch, tmp_path, **kwargs):
    import src.run_independent as run_independent

    monkeypatch.setattr(run_independent, "load_mgsm_questions", _questions)
    monkeypatch.setattr(run_independent, "load_premium", lambda *_: 2.0)
    engine = RecordingEngine()
    report = run_independent.run_model_independent(
        "mock_model",
        engine,
        languages=("de",),
        arms=(run_independent.NATIVE, run_independent.TRANSLATE_ACT),
        grid=(8, 16),
        n_items=2,
        k=2,
        concurrency=4,
        out_dir=tmp_path,
        **kwargs,
    )
    return run_independent, engine, report


def test_driver_partitions_shards_by_cap(monkeypatch, tmp_path) -> None:
    run_independent, _, report = _run(monkeypatch, tmp_path)

    # native: {8,16} | {16,32} = 8,16,32 ; translate_act: 8,16
    assert {s["budget"] for s in report["shards"] if s["arm"] == "native"} == {
        8,
        16,
        32,
    }
    assert {s["budget"] for s in report["shards"] if s["arm"] == "translate_act"} == {
        8,
        16,
    }
    assert report["total_units"] == 5 * 2 * 2


def test_every_record_lands_in_its_own_cap_shard(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)

    for path in tmp_path.rglob("shard.jsonl"):
        cap = int(path.parent.name.removeprefix("B"))
        for record in read_ledger(path):
            assert record["budget"] == cap
            assert record["output_token_count"] <= cap


def test_engine_receives_the_cap_as_max_tokens(monkeypatch, tmp_path) -> None:
    _, engine, _ = _run(monkeypatch, tmp_path)

    assert {cap for _, cap in engine.calls} == {8, 16, 32}


def test_resume_is_idempotent(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)
    _, engine, report = _run(monkeypatch, tmp_path)

    assert report["generated_this_run"] == 0
    assert engine.calls == []


def test_verify_ledger_rejects_a_record_from_the_wrong_cap(tmp_path) -> None:
    path = tmp_path / "shard.jsonl"
    record = {
        "record_id": record_id("m", "de", "native", "1", 0, 256),
        "model_id": "m",
        "language": "de",
        "arm": "native",
        "item_id": "1",
        "sample_index": 0,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": [1, 2],
        "output_token_count": 2,
        "text": "hi",
        "eos": True,
        "started_at": "t",
        "completed_at": "t",
        "budget": 512,
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(LedgerVerificationError, match="budget"):
        verify_ledger(path, 1, expected_budget=256)


def test_verify_ledger_rejects_a_trace_longer_than_its_cap(tmp_path) -> None:
    path = tmp_path / "shard.jsonl"
    record = {
        "record_id": record_id("m", "de", "native", "1", 0, 2),
        "model_id": "m",
        "language": "de",
        "arm": "native",
        "item_id": "1",
        "sample_index": 0,
        "seed": 1,
        "input_token_ids": [1],
        "input_token_count": 1,
        "output_token_ids": [1, 2, 3],
        "output_token_count": 3,
        "text": "hi",
        "eos": True,
        "started_at": "t",
        "completed_at": "t",
        "budget": 2,
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(LedgerVerificationError, match="exceeded its cap"):
        verify_ledger(path, 1, expected_budget=2)
