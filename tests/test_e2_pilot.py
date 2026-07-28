"""E2 manipulation pilot (`prereg-budget-aware.md` §8.6, decision D8).

The pilot is a gate on the protocol, so the tests fix what makes it one: it runs
exactly four shards in one cell, it cannot write into the study ledger, it never
scores accuracy, and TAG's direction alone decides confirmatory versus
exploratory.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

import pytest

from src.e2_pilot import (
    GATING_CONDITION,
    PILOT_ANNOUNCED,
    PILOT_ARM,
    PILOT_CAP,
    PILOT_CONDITIONS,
    PILOT_LANGUAGE,
    PILOT_MODEL,
    PILOT_OUT_DIR,
    _reject_the_study_ledger,
    readout,
    readout_markdown,
    run_pilot,
)
from src.engine import GenerationResult
from src.generate import AWARE, TAG, LedgerVerificationError
from src.mgsm import MgsmQuestion
from src.run_independent import E2_DECOUPLED_CAP, shard_path


class _Engine:
    """Emits a trace whose length falls with the announced budget."""

    def __init__(self, responsive: bool = True) -> None:
        self.calls: list[tuple[str, int, int]] = []
        self.responsive = responsive
        self._lock = Lock()

    def generate(self, prompt, generation_seed, max_tokens):
        with self._lock:
            self.calls.append((prompt, generation_seed, max_tokens))
        announced = 2048
        for candidate in PILOT_ANNOUNCED:
            if f"TOKEN_BUDGET: {candidate}" in prompt or f"höchstens {candidate} " in prompt:
                announced = candidate
        length = (4 if announced == 128 else 8) if self.responsive else 8
        text = "x" * length
        return GenerationResult(
            token_ids=list(range(length)), text=text, eos=True
        )


def _run(monkeypatch, tmp_path, responsive=True, **kwargs):
    import src.run_independent as run_independent

    monkeypatch.setattr(
        run_independent,
        "load_mgsm_questions",
        lambda language: [MgsmQuestion(str(i), f"q{i}") for i in range(2)],
    )
    monkeypatch.setattr(run_independent, "load_premium", lambda *_: 2.0)
    engine = _Engine(responsive=responsive)
    report = run_pilot(
        engine, n_items=2, k=2, concurrency=2, out_dir=tmp_path, **kwargs
    )
    return engine, report


# --- what the pilot runs ----------------------------------------------------


def test_the_pilot_matches_the_protocol() -> None:
    assert PILOT_MODEL == "qwen3_8b"
    assert PILOT_LANGUAGE == "de"
    assert PILOT_ARM == "native"
    assert PILOT_CONDITIONS == (TAG, AWARE)
    assert GATING_CONDITION == TAG
    assert PILOT_ANNOUNCED == (128, 2048)
    assert PILOT_CAP == E2_DECOUPLED_CAP == 2048
    assert PILOT_OUT_DIR == "runs-e2-pilot"


def test_the_pilot_runs_four_shards_in_one_cell(monkeypatch, tmp_path) -> None:
    """250 x 8 x 2 announced x 2 conditions = 8,000 generations at full size."""
    _, report = _run(monkeypatch, tmp_path)

    assert len(report["shards"]) == 4
    assert {shard["condition"] for shard in report["shards"]} == {TAG, AWARE}
    assert {shard["language"] for shard in report["shards"]} == {"de"}
    assert {shard["arm"] for shard in report["shards"]} == {"native"}


def test_the_pilot_holds_the_cap_and_moves_only_the_announcement(
    monkeypatch, tmp_path
) -> None:
    engine, report = _run(monkeypatch, tmp_path)

    assert {shard["budget"] for shard in report["shards"]} == {PILOT_CAP}
    assert {cap for *_, cap in engine.calls} == {PILOT_CAP}
    assert {shard["announced_budget"] for shard in report["shards"]} == {128, 2048}


def test_the_pilot_generates_no_coupled_cell(monkeypatch, tmp_path) -> None:
    """`conditions=()` is what keeps the pilot from producing a study cell."""
    _run(monkeypatch, tmp_path)

    caps = {
        path.parent.name.split("_")[0]
        for path in Path(tmp_path).rglob("shard.jsonl")
    }
    assert caps == {f"B{PILOT_CAP:05d}"}


def test_the_pilot_refuses_to_write_into_the_study_ledger() -> None:
    with pytest.raises(ValueError, match="never scored as data"):
        run_pilot(_Engine(), out_dir="runs-e2")


def test_the_pilot_refuses_to_write_into_the_study_ledger_with_a_slash() -> None:
    with pytest.raises(ValueError, match="never scored as data"):
        run_pilot(_Engine(), out_dir="runs-e2/")


@pytest.mark.parametrize(
    "candidate",
    ["runs-e2/.", "runs-e2/pilot", "runs-e2/a/b", "../runs-e2", "/tmp/runs-e2/x"],
)
def test_the_pilot_refuses_a_path_inside_the_study_ledger(candidate) -> None:
    """A suffix test is not enough: these all write into the frozen ledger."""
    with pytest.raises(ValueError, match="never scored as data"):
        run_pilot(_Engine(), out_dir=candidate)


def test_the_pilot_allows_its_own_root() -> None:
    """The guard must not reject the directory the pilot is supposed to use."""
    assert _reject_the_study_ledger(PILOT_OUT_DIR) == Path(PILOT_OUT_DIR).resolve()


# --- the readout will not decide on a partial shard -------------------------


def test_the_readout_refuses_a_partial_shard(monkeypatch, tmp_path) -> None:
    """The pilot decides the freeze; four records must not be able to."""
    _run(monkeypatch, tmp_path, responsive=True)
    path = shard_path(
        Path(tmp_path), PILOT_MODEL, "de", "native", PILOT_CAP, TAG, 128
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(LedgerVerificationError):
        readout(out_dir=tmp_path, n_items=2, k=2)


def test_the_readout_refuses_a_shard_from_another_cell(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path, responsive=True)
    path = shard_path(
        Path(tmp_path), PILOT_MODEL, "de", "native", PILOT_CAP, TAG, 128
    )
    records = [json.loads(line) for line in path.read_text().splitlines()]
    records[0]["language"] = "th"
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="different cell"):
        readout(out_dir=tmp_path, n_items=2, k=2)


# --- the decision rule ------------------------------------------------------


def test_a_responsive_manipulation_freezes_the_confirmatory_family(
    monkeypatch, tmp_path
) -> None:
    _run(monkeypatch, tmp_path, responsive=True)

    report = readout(out_dir=tmp_path, n_items=2, k=2)

    assert report["verdict"] == "confirmatory"
    assert report["passed"]
    assert report["conditions"][TAG]["moves_in_the_predicted_direction"]
    assert report["conditions"][TAG]["reduction"] == pytest.approx(4.0)
    assert report["conditions"][TAG]["reduction_share"] == pytest.approx(0.5)


def test_an_inert_manipulation_freezes_e2_as_exploratory(
    monkeypatch, tmp_path
) -> None:
    """D8's actual point: an inert instrument must not carry a frozen family."""
    _run(monkeypatch, tmp_path, responsive=False)

    report = readout(out_dir=tmp_path, n_items=2, k=2)

    assert report["verdict"] == "exploratory"
    assert not report["passed"]
    assert report["conditions"][TAG]["reduction"] == 0.0


def test_only_tag_gates_the_family(monkeypatch, tmp_path) -> None:
    """§8.3/D6: TAG is the family's instrument, so AWARE reports but never gates."""
    _run(monkeypatch, tmp_path, responsive=True)

    report = readout(out_dir=tmp_path, gating_condition=AWARE, n_items=2, k=2)
    assert report["gating_condition"] == AWARE

    tag_gated = readout(out_dir=tmp_path, n_items=2, k=2)
    assert tag_gated["gating_condition"] == TAG
    assert AWARE in tag_gated["conditions"], "AWARE is still reported"


def test_the_gating_condition_must_have_been_run(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="must be among"):
        readout(out_dir=tmp_path, conditions=(AWARE,), gating_condition=TAG, n_items=2, k=2)


def test_the_readout_never_scores_accuracy(monkeypatch, tmp_path) -> None:
    """§8.6: the pilot's records are never scored as study data."""
    _run(monkeypatch, tmp_path)

    report = readout(out_dir=tmp_path, n_items=2, k=2)

    payload = json.dumps(report)
    assert "accuracy" not in payload
    assert "parsed" not in payload
    for entry in report["conditions"].values():
        for cell in entry["cells"]:
            assert set(cell) == {
                "condition",
                "announced_budget",
                "records",
                "median_output_tokens",
                "mean_output_tokens",
                "censoring_share",
                "path",
            }


def test_the_readout_reads_the_shards_the_pilot_wrote(monkeypatch, tmp_path) -> None:
    _run(monkeypatch, tmp_path)

    report = readout(out_dir=tmp_path, n_items=2, k=2)

    expected = shard_path(
        Path(tmp_path), PILOT_MODEL, "de", "native", PILOT_CAP, TAG, 128
    )
    assert report["conditions"][TAG]["cells"][0]["path"] == str(expected)
    assert expected.is_file()


def test_the_readout_refuses_the_study_ledger(tmp_path) -> None:
    """`--readout-only` must not be able to gate the freeze on study records."""
    with pytest.raises(ValueError, match="never scored as data"):
        readout(out_dir="runs-e2")

    with pytest.raises(ValueError, match="never scored as data"):
        readout(out_dir="runs-e2/pilot")


def test_the_readout_fails_loudly_on_a_missing_shard(tmp_path) -> None:
    with pytest.raises(ValueError, match="no records"):
        readout(out_dir=tmp_path, n_items=2, k=2)


# --- report -----------------------------------------------------------------


def test_the_report_states_the_verdict_and_which_condition_gates(
    monkeypatch, tmp_path
) -> None:
    _run(monkeypatch, tmp_path, responsive=True)

    text = readout_markdown(readout(out_dir=tmp_path, n_items=2, k=2))

    assert "freeze E2 as confirmatory" in text
    assert "tag (gates)" in text
    assert "never scored as study data" in text.lower()


def test_the_report_says_so_when_the_instrument_did_not_work(
    monkeypatch, tmp_path
) -> None:
    _run(monkeypatch, tmp_path, responsive=False)

    text = readout_markdown(readout(out_dir=tmp_path, n_items=2, k=2))

    assert "freeze E2 as exploratory" in text
    assert "not as predicted" in text
