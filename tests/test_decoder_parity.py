import json
from pathlib import Path

from src.decoder_parity import (
    audit_decoder_parity,
    decoder_parity_markdown,
    strip_special_markup,
)


class MappingDecoder:
    def __init__(self, texts: dict[tuple[int, ...], str]) -> None:
        self.texts = texts

    def __call__(self, token_ids: list[int]) -> str:
        return self.texts[tuple(token_ids)]

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return [self(sequence) for sequence in sequences]


class LocalSpecialDecoder:
    def __call__(self, token_ids: list[int]) -> str:
        return "".join(chr(token) for token in token_ids if token != 999)

    def decode_many(self, sequences: list[list[int]]) -> list[str]:
        return [self(sequence) for sequence in sequences]


class RawSpecialDecoder(LocalSpecialDecoder):
    def __call__(self, token_ids: list[int]) -> str:
        text = super().__call__(token_ids)
        return text + ("<|im_end|>" if 999 in token_ids else "")


def _write_records(
    root: Path,
    records_by_cell: dict[tuple[str, str], list[dict]],
) -> None:
    for (language, arm), records in records_by_cell.items():
        path = root / "model" / language / arm / "shard.jsonl"
        path.parent.mkdir(parents=True)
        rows = []
        for index, record in enumerate(records):
            output_ids = record["output_token_ids"]
            rows.append(
                {
                    "record_id": f"model-{language}-{arm}-{index}",
                    "model_id": "model",
                    "language": language,
                    "arm": arm,
                    "item_id": str(record.get("item_id", index)),
                    "sample_index": int(record.get("sample_index", 0)),
                    "seed": index,
                    "input_token_ids": [],
                    "input_token_count": 0,
                    "output_token_ids": output_ids,
                    "output_token_count": len(output_ids),
                    "text": record["text"],
                    "eos": True,
                    "started_at": "2026-07-25T00:00:00+00:00",
                    "completed_at": "2026-07-25T00:00:01+00:00",
                }
            )
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )


def test_special_markup_changes_raw_text_but_not_scoring(tmp_path: Path) -> None:
    text = "work\n#### 42"
    ids = [*map(ord, text), 999]
    _write_records(
        tmp_path,
        {("de", "native"): [{"output_token_ids": ids, "text": text}]},
    )

    report = audit_decoder_parity(
        "model",
        tmp_path,
        LocalSpecialDecoder(),
        RawSpecialDecoder(),
        {("de", "0"): 42},
        budgets=(4,),
        traces_per_cell=1,
    )

    assert report["agreement"]["exact_decoded_string"]["matches"] == 1
    assert report["agreement"]["normalized_decoded_string"]["rate"] == 1
    assert report["agreement"]["parsed_answer"]["rate"] == 1
    assert report["agreement"]["correctness_verdict"]["rate"] == 1
    assert report["divergence_counts_by_cause"]["special_tokens"][
        "exact_decoded_string"
    ] == 1
    assert report["stored_text_full_trace_agreement"]["local_exact"]["rate"] == 1
    assert report["stored_text_full_trace_agreement"]["vllm_raw_exact"]["rate"] == 0
    assert report["stored_text_full_trace_agreement"]["vllm_normalized_exact"][
        "rate"
    ] == 1
    assert report["verdict"]["status"] == "PASS"


def test_named_failure_modes_are_attributed_and_can_fail_verdict(
    tmp_path: Path,
) -> None:
    records = [
        {"item_id": "0", "output_token_ids": [10], "text": "#### ๑๒"},
        {"item_id": "1", "output_token_ids": [20, 21], "text": "#### 12\nx"},
        {
            "item_id": "2",
            "output_token_ids": [30],
            "text": "#### 4\n#### nope",
        },
    ]
    _write_records(tmp_path, {("th", "native"): records})
    local = MappingDecoder(
        {
            (10,): "#### ๑๒",
            (20,): "#### 1",
            (20, 21): "#### 12\nx",
            (30,): "#### 4\n#### nope",
        }
    )
    vllm = MappingDecoder(
        {
            (10,): "#### 12",
            (20,): "#### 12",
            (20, 21): "#### 12\nx",
            (30,): "#### 4",
        }
    )

    report = audit_decoder_parity(
        "model",
        tmp_path,
        local,
        vllm,
        {
            ("th", "0"): 12,
            ("th", "1"): 12,
            ("th", "2"): 4,
        },
        budgets=(1,),
        traces_per_cell=3,
    )

    causes = report["divergence_counts_by_cause"]
    assert causes["unicode_digits"]["exact_decoded_string"] == 2
    assert causes["unicode_digits"]["parsed_answer"] == 0
    assert causes["answer_line_cutoff"]["parsed_answer"] == 1
    assert causes["malformed_or_multi_candidate"]["parsed_answer"] == 2
    assert report["agreement"]["parsed_answer"]["matches"] == 3
    assert report["agreement"]["correctness_verdict"]["matches"] == 3
    assert report["verdict"]["status"] == "FAIL"
    assert "rerun both models" in report["verdict"]["cross_model_comparability"]


def test_sampling_is_deterministic_and_stratified(tmp_path: Path) -> None:
    cells = {}
    gold = {}
    decode_map = {}
    for language in ("de", "th"):
        for arm in ("native", "translate_act"):
            records = []
            for index in range(3):
                token = 100 * len(cells) + index + 1
                text = f"#### {index}"
                records.append(
                    {
                        "item_id": str(index),
                        "output_token_ids": [token],
                        "text": text,
                    }
                )
                gold[(language, str(index))] = index
                decode_map[(token,)] = text
            cells[(language, arm)] = records
    _write_records(tmp_path, cells)
    decoder = MappingDecoder(decode_map)

    first = audit_decoder_parity(
        "model",
        tmp_path,
        decoder,
        decoder,
        gold,
        budgets=(1,),
        traces_per_cell=2,
        sample_seed=17,
    )
    second = audit_decoder_parity(
        "model",
        tmp_path,
        decoder,
        decoder,
        gold,
        budgets=(1,),
        traces_per_cell=2,
        sample_seed=17,
    )

    assert first["sampling"]["n_cells"] == 4
    assert first["sampling"]["n_traces"] == 8
    assert first["sampling"]["n_sequence_observations"] == 16
    assert all(
        len(record_ids) == 2
        for record_ids in first["sampling"]["sampled_record_ids"].values()
    )
    assert (
        first["sampling"]["sampled_record_ids"]
        == second["sampling"]["sampled_record_ids"]
    )


def test_markdown_states_rates_causes_and_verdict(tmp_path: Path) -> None:
    text = "#### 7"
    _write_records(
        tmp_path,
        {
            ("de", "native"): [
                {"output_token_ids": list(map(ord, text)), "text": text}
            ]
        },
    )
    decoder = MappingDecoder({tuple(map(ord, text)): text})
    report = audit_decoder_parity(
        "model",
        tmp_path,
        decoder,
        decoder,
        {("de", "0"): 7},
        budgets=(100,),
        traces_per_cell=1,
    )

    markdown = decoder_parity_markdown(report)

    assert "**PASS" in markdown
    assert "Parsed answer" in markdown
    assert "Correctness verdict" in markdown
    assert "unicode_digits" in markdown
    assert "100.0000%" in markdown


def test_special_markup_normalization_matches_llama_policy() -> None:
    assert strip_special_markup("#### 42<|eot_id|>") == "#### 42"
    assert strip_special_markup("<|im_start|>work<|im_end|>") == "work"
