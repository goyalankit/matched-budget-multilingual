import json
from pathlib import Path

from src.parser import parse_answer
from src.rehearsal import _trace, run_rehearsal

_ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_trace_realizes_answer_emission_prefix() -> None:
    text, eos = _trace(42, True, 1500.0, "native")
    assert eos
    assert len(text) == 1500
    assert parse_answer(text[:1024], "de", "native") is None
    assert parse_answer(text, "de", "native") == 42


def test_small_rehearsal_produces_complete_outputs(tmp_path) -> None:
    study = json.loads(
        (_ROOT / "configs" / "synthetic" / "study.json").read_text(
            encoding="utf-8"
        )
    )
    power = json.loads(
        (_ROOT / "configs" / "power_sim.json").read_text(encoding="utf-8")
    )
    study.update({"n_items": 8, "k": 4, "n_boot": 129})

    report = run_rehearsal(
        study,
        power,
        tmp_path / "runs-synthetic",
        tmp_path / "analysis-out",
    )

    assert set(report["scenarios"]) == {"null", "alternative"}
    for scenario in report["scenarios"].values():
        assert len(scenario["holm_family"]) == 6
        assert set(scenario["h3"]) == {"de", "th", "sw"}
        assert "h1_existence" in scenario["h1"]
        assert "h1_sesoi" in scenario["h1"]
    assert (tmp_path / "analysis-out" / "rehearsal_confirmatory.json").is_file()
    assert (tmp_path / "analysis-out" / "rehearsal_table.md").is_file()
    assert (tmp_path / "analysis-out" / "rehearsal_table.csv").is_file()
    for scenario in ("null", "alternative"):
        ledger = tmp_path / "runs-synthetic" / scenario / "shard-000.jsonl"
        assert len(ledger.read_text(encoding="utf-8").splitlines()) == 384
