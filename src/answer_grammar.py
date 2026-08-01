"""Answer-grammar dispatch across benchmark answer kinds (breadth design §5).

`integer` delegates to the FROZEN src/parser.py so MGSM's parsing path is
unchanged. The other kinds are additive and share only the `#### ` delimiter.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, Mapping

from src.parser import (
    _answer_language,
    _integer_digits,
    _load_grammar,
    _normalize_digits,
    parse_answer,
)

_ANSWER_LINE = re.compile(r"^[ \t]*####[ \t]+(.*?)[ \t]*$")
_FRACTION_SEPARATOR = "/"


def _last_answer_line(text: str) -> str | None:
    candidate = None
    for line in text.splitlines():
        match = _ANSWER_LINE.fullmatch(line)
        if match:
            candidate = match.group(1)
    return candidate


def _split_sign(value: str, grammar: Mapping[str, Any]) -> tuple[int, str]:
    if value and value[0] in grammar["sign_characters"]:
        return (-1 if value[0] in ("-", "−") else 1), value[1:]
    return 1, value


def _unsigned_decimal(value: str, grammar: Mapping[str, Any]) -> Fraction | None:
    """Parse an unsigned decimal under one locale's grammar.

    Digit systems, the decimal separator and the grouping rules all come from
    ``configs/locales/*.json`` -- the same frozen grammars the integer kind
    uses. Hard-coding ASCII here would mis-parse: in German ``.`` is a
    *grouping* separator, so ``1.234`` is 1234 and ``0.5`` is malformed, while
    ``0,5`` is one half.
    """
    separator = grammar["decimal_separator"]
    if separator in value:
        if value.count(separator) != 1:
            return None
        integer_part, fraction_part = value.split(separator)
        normalized_fraction = _normalize_digits(fraction_part, grammar)
        if not normalized_fraction or not (
            normalized_fraction.isascii() and normalized_fraction.isdigit()
        ):
            return None
    else:
        integer_part, normalized_fraction = value, ""

    # An empty integer part (".5") is permitted; the grammar validates the rest.
    if integer_part == "":
        integer_digits = "0"
    else:
        integer_digits = _integer_digits(
            _normalize_digits(integer_part, grammar), grammar
        )
        if integer_digits is None:
            return None

    if not normalized_fraction:
        return Fraction(int(integer_digits))
    scale = 10 ** len(normalized_fraction)
    return Fraction(int(integer_digits) * scale + int(normalized_fraction), scale)


def _parse_numeric(candidate: str, input_language: str, arm: str) -> Fraction | None:
    """Parse a numeric answer under the answer language's locale grammar."""
    grammar = _load_grammar(_answer_language(input_language, arm))

    if _FRACTION_SEPARATOR in candidate:
        numerator_text, _, denominator_text = candidate.partition(_FRACTION_SEPARATOR)
        sign, numerator_text = _split_sign(numerator_text, grammar)
        numerator = _unsigned_decimal(numerator_text, grammar)
        denominator = _unsigned_decimal(denominator_text, grammar)
        if numerator is None or denominator is None or denominator == 0:
            return None
        return sign * numerator / denominator

    sign, unsigned = _split_sign(candidate, grammar)
    value = _unsigned_decimal(unsigned, grammar)
    return None if value is None else sign * value


def _parse_choice(candidate: str, labels: list[str]) -> str | None:
    upper = candidate.strip().upper()
    return upper if upper in {label.upper() for label in labels} else None


def parse_for_kind(
    text: str, language: str, arm: str, kind: str, grammar: Mapping[str, Any]
) -> Any:
    """Parse one trace's answer under the benchmark's answer kind."""
    if kind == "integer":
        return parse_answer(text, language, arm)

    candidate = _last_answer_line(text)
    if candidate is None:
        return None
    if kind == "numeric":
        return _parse_numeric(candidate, language, arm)
    if kind == "choice":
        return _parse_choice(candidate, list(grammar["labels"]))
    raise ValueError(f"unknown answer kind: {kind!r}")


def answers_equal(parsed: Any, gold: Any, kind: str) -> bool:
    """Compare a parsed answer to gold under the kind's equality rule."""
    if parsed is None:
        return False
    if kind == "numeric":
        return Fraction(parsed) == Fraction(str(gold))
    if kind == "choice":
        return str(parsed).upper() == str(gold).upper()
    return parsed == gold
