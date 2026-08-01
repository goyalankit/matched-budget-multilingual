from pathlib import Path

from src.benchmark_data import load_items
from src.benchmark_spec import BenchmarkSpec, template_text
from src.engine import MockEngine
from src.generate import generate_shard
from src.pipeline_equivalence import compare_pipelines


def test_identical_inputs_compare_equal():
    old = {"correctness": [[1.0, 0.0]], "emission": [4, None]}
    new = {"correctness": [[1.0, 0.0]], "emission": [4, None]}

    report = compare_pipelines(old, new)

    assert report == {"equivalent": True, "mismatches": []}


def test_a_single_flipped_cell_is_reported():
    old = {"correctness": [[1.0, 0.0]], "emission": [4, None]}
    new = {"correctness": [[1.0, 1.0]], "emission": [4, None]}

    report = compare_pipelines(old, new)

    assert report["equivalent"] is False
    assert report["mismatches"] == [
        {"field": "correctness[0][1]", "old": 0.0, "new": 1.0}
    ]


def test_differing_lengths_report_the_length_and_missing_indices():
    report = compare_pipelines({"values": [1, 2]}, {"values": [1]})

    assert report["equivalent"] is False
    assert report["mismatches"] == [
        {"field": "values.length", "old": 2, "new": 1},
        {"field": "values[1]", "old": 2, "new": "<missing>"},
    ]


def test_spec_driven_mock_shard_is_byte_identical(
    tmp_path, monkeypatch
) -> None:
    benchmark_root = tmp_path / "benchmark"
    templates = benchmark_root / "templates"
    templates.mkdir(parents=True)
    (benchmark_root / "grammar.json").write_text(
        '{"kind": "integer"}\n', encoding="utf-8"
    )
    (templates / "en.txt").write_text(
        "Solve {problem}", encoding="utf-8"
    )
    spec = BenchmarkSpec(
        name="fixture",
        dataset="fixture",
        language_configs={"en": "en"},
        split="test",
        expected_items=1,
        question_field="question",
        passage_field=None,
        option_fields=(),
        gold_field="answer",
        answer_kind="integer",
        gold_encoding="value",
        gold_source_encoding="value",
        generation_caps={"mock": 10},
        root=benchmark_root,
    )
    monkeypatch.setattr(
        "src.benchmark_data._load_split",
        lambda dataset, config, split: [{"question": "2+2", "answer": "0042"}],
    )
    monkeypatch.setattr(
        "src.generate._utc_now", lambda: "2000-01-01T00:00:00+00:00"
    )
    items = load_items(spec, "en")
    prompts = {
        item.item_id: template_text(spec, "en").replace(
            "{problem}", item.question
        )
        for item in items
    }
    shard = tmp_path / "shard.jsonl"

    generate_shard(
        MockEngine(),
        shard,
        model_id="mock",
        language="en",
        arm="native",
        items=prompts,
        samples_per_item=1,
        base_seed=7,
        max_tokens=10,
    )

    golden = Path(__file__).parent / "golden" / "pipeline_equivalence_mock.jsonl"
    assert shard.read_bytes() == golden.read_bytes()
