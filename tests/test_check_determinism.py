from src.engine import _to_signed_int64


def test_unsigned_seed_is_represented_as_signed_int64() -> None:
    assert _to_signed_int64(0) == 0
    assert _to_signed_int64(2**63 - 1) == 2**63 - 1
    assert _to_signed_int64(2**63) == -(2**63)
    assert _to_signed_int64(2**64 - 1) == -1


def test_signed_int64_mapping_is_idempotent() -> None:
    # An already-signed value must transport unchanged (the engine may see it twice).
    for value in (0, 2**63 - 1, 2**63, 2**64 - 1):
        signed = _to_signed_int64(value)
        assert _to_signed_int64(signed) == signed
