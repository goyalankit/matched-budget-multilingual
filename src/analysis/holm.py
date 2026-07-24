"""Holm step-down correction for preregistration §7.7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class HolmDecision:
    """One hypothesis's raw p-value, local alpha, and rejection decision."""

    p_value: float
    local_alpha: float
    reject: bool


def holm_step_down(
    p_values: Mapping[str, float], alpha: float = 0.05
) -> dict[str, HolmDecision]:
    """Apply Holm correction and return decisions in input-key order."""
    if not p_values:
        raise ValueError("p_values must not be empty")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    if any(value < 0 or value > 1 for value in p_values.values()):
        raise ValueError("p-values must be between zero and one")

    ordered = sorted(p_values.items(), key=lambda item: item[1])
    decisions: dict[str, HolmDecision] = {}
    still_rejecting = True
    family_size = len(ordered)
    for rank, (name, p_value) in enumerate(ordered):
        local_alpha = alpha / (family_size - rank)
        reject = still_rejecting and p_value <= local_alpha
        if not reject:
            still_rejecting = False
        decisions[name] = HolmDecision(p_value, local_alpha, reject)
    return {name: decisions[name] for name in p_values}

