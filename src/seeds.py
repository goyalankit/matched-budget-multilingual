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


def condition_seed(
    base_seed: int,
    item_id: str,
    sample_index: int,
    budget: int,
    condition: str | None = None,
    announced: int | None = None,
) -> int:
    """Derive a per-condition seed for the budget-aware protocol (E2 §5).

    E2 runs several generative conditions at one budget. If they shared a seed
    the AWARE, PLACEBO, and FORCED draws at a given cap would be the same
    trajectory perturbed only by the prompt edit, and a difference between
    conditions could not be separated from a single lucky or unlucky draw.
    ``condition`` therefore joins the hash payload, using the same SHA-256 /
    ``\\x1f`` construction as :func:`seed` and :func:`budget_seed`, which are
    left byte-identical.

    ``condition=None`` is BLIND and delegates to :func:`budget_seed` unchanged,
    so E1's ledger *is* the BLIND arm of E2 and does not need regenerating.

    ``announced`` is the budget the *prompt states*, which E2's decoupled block
    varies while holding the enforced cap fixed (§5). It joins the payload only
    when it differs from ``budget``: in the coupled block the announcement *is*
    the cap, and a coupled cell must keep the seed it would have had before the
    decoupled block existed, or the two blocks would not share their common cell.

    The seed remains shared across arms at a given
    ``(item_id, sample_index, budget, condition, announced)``, preserving the
    cross-arm pairing of the frozen design.
    """
    if condition is None:
        if announced is not None and announced != budget:
            raise ValueError("BLIND announces nothing; `announced` must be None")
        return budget_seed(base_seed, item_id, sample_index, budget)
    if not condition:
        raise ValueError("condition must be a non-empty string or None")
    if budget <= 0:
        raise ValueError("budget must be positive")
    if announced is not None and announced <= 0:
        raise ValueError("announced must be positive")
    fields = [str(base_seed), item_id, str(sample_index), str(budget), condition]
    if announced is not None and announced != budget:
        fields.append(f"A{announced}")
    payload = _FIELD_SEPARATOR.join(field.encode("utf-8") for field in fields)
    return int.from_bytes(sha256(payload).digest()[:8], byteorder="big", signed=False)
