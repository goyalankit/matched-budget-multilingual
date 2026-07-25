from src.engine import GenerationResult
from src.mgsm import MgsmQuestion
from src.pilot import run_pilot
from src.seeds import seed


class CannedEngine:
    model_id = "mock"

    def __init__(self, traces: list[str]) -> None:
        self._traces = iter(traces)
        self.calls: list[tuple[str, int, int]] = []

    def generate(
        self, prompt: str, seed: int, max_tokens: int
    ) -> GenerationResult:
        self.calls.append((prompt, seed, max_tokens))
        text = next(self._traces)
        return GenerationResult(
            token_ids=list(text.encode("utf-8")),
            text=text,
            eos=True,
        )


def test_pilot_reports_parse_failure_rate(monkeypatch, tmp_path) -> None:
    items = [
        MgsmQuestion(item_id="0", question="Problem zero"),
        MgsmQuestion(item_id="1", question="Problem one"),
    ]
    monkeypatch.setattr("src.pilot.load_mgsm_questions", lambda _: items)

    report = run_pilot(
        CannedEngine(["Reasoning\n#### 7", "No final answer"]),
        items_per_cell=2,
        languages=("de",),
        arms=("native",),
        ledger_path=tmp_path / "pilot.jsonl",
    )

    assert report["cells"] == [
        {
            "language": "de",
            "arm": "native",
            "parse_failure_rate": 0.5,
            "missing_delimiter_rate": 0.0,
            "n": 2,
            "over_10pct": True,
        }
    ]
    assert report["any_cell_over_10pct"] is True


def test_pilot_reports_only_permitted_cell_metrics(monkeypatch, tmp_path) -> None:
    items = [
        MgsmQuestion(item_id=str(index), question=f"Problem {index}")
        for index in range(5)
    ]
    monkeypatch.setattr("src.pilot.load_mgsm_questions", lambda _: items)
    traces = [
        "#### 1",
        "#### 2",
        "#### 3",
        "#### 4",
        "#### 5",
        "Translation\n=== TRANSLATION END ===\n#### 1",
        "Translation\n=== TRANSLATION END ===\nNo answer",
        "Translation without delimiter\n#### 3",
        "Translation\n=== TRANSLATION END ===\n#### 4",
        "Translation\n=== TRANSLATION END ===\n#### 5",
    ]

    report = run_pilot(
        CannedEngine(traces),
        items_per_cell=5,
        languages=("de",),
        arms=("native", "translate_act"),
        ledger_path=tmp_path / "pilot.jsonl",
    )

    native, translate_act = report["cells"]
    assert native["parse_failure_rate"] == 0.0
    assert native["missing_delimiter_rate"] == 0.0
    assert native["over_10pct"] is False
    assert translate_act["parse_failure_rate"] == 0.2
    assert translate_act["missing_delimiter_rate"] == 0.2
    assert translate_act["over_10pct"] is True
    assert report["any_cell_over_10pct"] is True

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value).union(
                *(all_keys(nested) for nested in value.values())
            )
        if isinstance(value, list):
            return set().union(*(all_keys(nested) for nested in value))
        return set()

    assert {"accuracy", "correct", "gold"}.isdisjoint(all_keys(report))


def test_pilot_never_accesses_item_gold(monkeypatch, tmp_path) -> None:
    class GoldTrap:
        item_id = "0"
        question = "Problem"

        @property
        def gold(self) -> int:
            raise AssertionError("pilot must not access gold")

    monkeypatch.setattr(
        "src.pilot.load_mgsm_questions", lambda _: [GoldTrap()]
    )

    report = run_pilot(
        CannedEngine(["#### 9"]),
        items_per_cell=1,
        languages=("de",),
        arms=("native",),
        ledger_path=tmp_path / "pilot.jsonl",
    )

    assert report["cells"][0]["n"] == 1


def test_pilot_uses_first_items_registered_seeds_and_resumes(
    monkeypatch, tmp_path
) -> None:
    items = [
        MgsmQuestion(item_id=str(index), question=f"Problem {index}")
        for index in range(3)
    ]
    monkeypatch.setattr("src.pilot.load_mgsm_questions", lambda _: items)
    ledger_path = tmp_path / "pilot.jsonl"
    engine = CannedEngine(["#### 1", "#### 2"])

    first_report = run_pilot(
        engine,
        items_per_cell=2,
        languages=("de",),
        arms=("native",),
        max_tokens=123,
        ledger_path=ledger_path,
    )

    assert len(engine.calls) == 2
    assert "Problem 0" in engine.calls[0][0]
    assert "Problem 1" in engine.calls[1][0]
    assert all("Problem 2" not in prompt for prompt, _, _ in engine.calls)
    assert [call[1] for call in engine.calls] == [
        seed(base_seed=20260724, item_id="0", sample_index=0),
        seed(base_seed=20260724, item_id="1", sample_index=0),
    ]
    assert [call[2] for call in engine.calls] == [123, 123]

    resumed_engine = CannedEngine([])
    resumed_report = run_pilot(
        resumed_engine,
        items_per_cell=2,
        languages=("de",),
        arms=("native",),
        max_tokens=123,
        ledger_path=ledger_path,
    )
    assert resumed_engine.calls == []
    assert resumed_report == first_report


def test_pilot_threshold_is_strictly_greater_than_ten_percent(
    monkeypatch, tmp_path
) -> None:
    items = [
        MgsmQuestion(item_id=str(index), question=f"Problem {index}")
        for index in range(10)
    ]
    monkeypatch.setattr("src.pilot.load_mgsm_questions", lambda _: items)

    report = run_pilot(
        CannedEngine(["No answer"] + ["#### 1"] * 9),
        items_per_cell=10,
        languages=("de",),
        arms=("native",),
        ledger_path=tmp_path / "pilot.jsonl",
    )

    assert report["cells"][0]["parse_failure_rate"] == 0.1
    assert report["cells"][0]["over_10pct"] is False
    assert report["any_cell_over_10pct"] is False
