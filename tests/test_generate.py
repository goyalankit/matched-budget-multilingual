import json

from src.engine import MockEngine
from src.generate import generate_shard, read_ledger, verify_ledger
from src.parser import parse_answer
from src.prefixes import token_checkpoint_prefix


def test_mock_generation_ledger_end_to_end_and_resume(tmp_path) -> None:
    shard = tmp_path / "shard-000.jsonl"
    items = {f"item-{index}": f"Solve item {index}." for index in range(5)}
    engine = MockEngine()

    for arm in ("native", "translate_act"):
        generate_shard(
            engine,
            shard,
            model_id="mock",
            language="de",
            arm=arm,
            items=items,
            samples_per_item=1,
            base_seed=123,
        )

    assert verify_ledger(shard, expected_count=10)["unique_count"] == 10
    for record in read_ledger(shard):
        prefix_length = token_checkpoint_prefix(
            record["output_token_count"], 512, record["eos"]
        )
        prefix = record["text"][:prefix_length]
        parse_answer(prefix, record["language"], record["arm"])

    lines = shard.read_text(encoding="utf-8").splitlines()
    shard.write_text("\n".join(lines[:5]) + "\n", encoding="utf-8")
    for arm in ("native", "translate_act"):
        generate_shard(
            engine,
            shard,
            model_id="mock",
            language="de",
            arm=arm,
            items=items,
            samples_per_item=1,
            base_seed=123,
        )
    assert verify_ledger(shard, expected_count=10)["record_count"] == 10


def test_generation_resume_skips_complete_records(tmp_path) -> None:
    shard = tmp_path / "shard.jsonl"
    kwargs = {
        "engine": MockEngine(),
        "output_path": shard,
        "model_id": "mock",
        "language": "en",
        "arm": "native",
        "items": {"one": "One prompt"},
        "samples_per_item": 2,
        "base_seed": 5,
    }
    assert generate_shard(**kwargs) == 2
    original = shard.read_text(encoding="utf-8")
    assert generate_shard(**kwargs) == 0
    assert shard.read_text(encoding="utf-8") == original


def test_ledger_is_jsonl_with_exact_count_fields(tmp_path) -> None:
    shard = tmp_path / "shard.jsonl"
    generate_shard(
        MockEngine(), shard, "mock", "en", "native", {"x": "p"}, 1, 2
    )
    record = json.loads(shard.read_text(encoding="utf-8"))
    assert record["input_token_count"] == len(record["input_token_ids"])
    assert record["output_token_count"] == len(record["output_token_ids"])

