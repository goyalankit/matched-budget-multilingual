import hashlib

import pytest

from src.seeds import seed


def test_seed_matches_hardcoded_known_answer() -> None:
    assert seed(12345, "item-007", 2) == 17_388_007_408_136_205_327


@pytest.mark.parametrize(
    ("base_seed", "item_id", "sample_index"),
    [
        (0, "0", 0),
        (987654321, "gsm8k/train/42", 7),
        (11, "โจทย์-๓", 3),
    ],
)
def test_seed_matches_preregistered_hash_construction(
    base_seed: int, item_id: str, sample_index: int
) -> None:
    payload = b"\x1f".join(
        value.encode("utf-8")
        for value in (str(base_seed), item_id, str(sample_index))
    )
    expected = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

    assert seed(base_seed, item_id, sample_index) == expected
