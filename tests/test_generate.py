import json

from src.engine import GenerationResult, MockEngine
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


def test_generation_ledger_uses_engine_prefill_tokenization(tmp_path) -> None:
    class PrefillEngine:
        def generate(
            self, prompt: str, seed: int, max_tokens: int
        ) -> GenerationResult:
            return GenerationResult(
                token_ids=[20, 21],
                text="ok",
                eos=True,
                input_token_ids=[10, 11, 12],
                input_token_count=3,
            )

    shard = tmp_path / "shard.jsonl"
    generate_shard(
        PrefillEngine(),
        shard,
        "real",
        "en",
        "native",
        {"x": "prompt"},
        1,
        2,
        tokenize_prompt=lambda _: (_ for _ in ()).throw(
            AssertionError("fallback tokenizer should not run")
        ),
    )

    record = read_ledger(shard)[0]
    assert record["input_token_ids"] == [10, 11, 12]
    assert record["input_token_count"] == 3


def test_ledger_accepts_authoritative_prefill_count_without_token_ids(
    tmp_path,
) -> None:
    class CountOnlyPrefillEngine:
        def generate(
            self, prompt: str, seed: int, max_tokens: int
        ) -> GenerationResult:
            return GenerationResult(
                token_ids=[20],
                text="ok",
                eos=True,
                input_token_count=4,
            )

    shard = tmp_path / "shard.jsonl"
    generate_shard(
        CountOnlyPrefillEngine(),
        shard,
        "real",
        "en",
        "native",
        {"x": "prompt"},
        1,
        2,
    )

    record = read_ledger(shard)[0]
    assert record["input_token_ids"] == []
    assert record["input_token_count"] == 4
    assert verify_ledger(shard, expected_count=1)["record_count"] == 1
