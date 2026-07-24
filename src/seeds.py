"""Deterministic per-item seed derivation from preregistration §§4 and 10."""

from hashlib import sha256

_FIELD_SEPARATOR = b"\x1f"


def seed(base_seed: int, item_id: str, sample_index: int) -> int:
    """Derive a paired unsigned 64-bit seed for one item and sample."""
    fields = (str(base_seed), item_id, str(sample_index))
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)
