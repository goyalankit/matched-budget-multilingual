"""Structural comparison for old/new analysis-pipeline outputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isnan
from typing import Any

_MISSING = "<missing>"


def _field(path: str) -> str:
    return path or "<root>"


def _equal(old: Any, new: Any) -> bool:
    if isinstance(old, float) and isinstance(new, float):
        return old == new or (isnan(old) and isnan(new))
    return old == new


def _walk(old: Any, new: Any, path: str, mismatches: list[dict[str, Any]]) -> None:
    if isinstance(old, Mapping) and isinstance(new, Mapping):
        for key in sorted(old.keys() | new.keys(), key=str):
            child = f"{path}.{key}" if path else str(key)
            if key not in old:
                mismatches.append(
                    {"field": child, "old": _MISSING, "new": new[key]}
                )
            elif key not in new:
                mismatches.append(
                    {"field": child, "old": old[key], "new": _MISSING}
                )
            else:
                _walk(old[key], new[key], child, mismatches)
        return

    old_sequence = isinstance(old, Sequence) and not isinstance(
        old, (str, bytes, bytearray)
    )
    new_sequence = isinstance(new, Sequence) and not isinstance(
        new, (str, bytes, bytearray)
    )
    if old_sequence and new_sequence:
        if len(old) != len(new):
            mismatches.append(
                {
                    "field": f"{_field(path)}.length",
                    "old": len(old),
                    "new": len(new),
                }
            )
        for index in range(min(len(old), len(new))):
            _walk(old[index], new[index], f"{path}[{index}]", mismatches)
        for index in range(len(new), len(old)):
            mismatches.append(
                {
                    "field": f"{path}[{index}]",
                    "old": old[index],
                    "new": _MISSING,
                }
            )
        for index in range(len(old), len(new)):
            mismatches.append(
                {
                    "field": f"{path}[{index}]",
                    "old": _MISSING,
                    "new": new[index],
                }
            )
        return

    if type(old) is not type(new) or not _equal(old, new):
        mismatches.append({"field": _field(path), "old": old, "new": new})


def compare_pipelines(old: Mapping, new: Mapping) -> dict[str, Any]:
    """Return every structural/value difference between two pipeline outputs."""
    mismatches: list[dict[str, Any]] = []
    _walk(old, new, "", mismatches)
    return {"equivalent": not mismatches, "mismatches": mismatches}
