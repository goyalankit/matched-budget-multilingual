"""Deterministic per-item seed derivation from preregistration §§4 and 10."""

from hashlib import sha256

_FIELD_SEPARATOR = b"\x1f"


def seed(base_seed: int, item_id: str, sample_index: int) -> int:
    """Derive a paired unsigned 64-bit seed for one item and sample."""
    fields = (str(base_seed), item_id, str(sample_index))
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)


def budget_seed(base_seed: int, item_id: str, sample_index: int, budget: int) -> int:
    """Derive a per-budget seed for the independent-decoding protocol (E1 §5).

    Independent decoding requires a *different* trajectory at every cap. vLLM's
    ``max_tokens`` never conditions the model, so reusing :func:`seed` across caps
    would regenerate one trajectory and truncate it — prefix replay by another
    name, and the exact failure mode this study exists to rule out.

    The budget is therefore part of the hash payload. The seed remains shared
    across arms at a given ``(item_id, sample_index, budget)``, preserving the
    cross-arm pairing of the frozen design, and is independent across budgets.
    """
    if budget <= 0:
        raise ValueError("budget must be positive")
    fields = (str(base_seed), item_id, str(sample_index), str(budget))
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)
