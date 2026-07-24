"""Strict locale-aware answer parsing from preregistration §4."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

_LOCALE_DIR = Path(__file__).resolve().parents[1] / "configs" / "locales"
_ANSWER_LINE = re.compile(r"^[ \t]*####[ \t]+(.*?)[ \t]*$")
_ARM_ANSWER_LANGUAGE = {
    "native": "input",
    "pivot": "input",
    "translate_act": "en",
    "code_switched": "en",
}


@lru_cache(maxsize=None)
def _load_grammar(language: str) -> Dict[str, Any]:
    path = _LOCALE_DIR / f"{language}.json"
    if not path.is_file():
        raise ValueError(f"unsupported answer language: {language}")
    with path.open(encoding="utf-8") as grammar_file:
        return json.load(grammar_file)


def _answer_language(input_language: str, arm: str) -> str:
    try:
        configured_language = _ARM_ANSWER_LANGUAGE[arm]
    except KeyError as error:
        raise ValueError(f"unsupported arm: {arm}") from error
    return input_language if configured_language == "input" else configured_language


def _normalize_digits(value: str, grammar: Dict[str, Any]) -> str:
    normalized = []
    for character in value:
        replacement = character
        for digit_range in grammar["digit_ranges"]:
            start = ord(digit_range["start"])
            end = ord(digit_range["end"])
            if start <= ord(character) <= end:
                replacement = chr(
                    ord(digit_range["ascii_start"]) + ord(character) - start
                )
                break
        normalized.append(replacement)
    return "".join(normalized)


def _integer_digits(value: str, grammar: Dict[str, Any]) -> Optional[str]:
    if value and all("0" <= digit <= "9" for digit in value):
        return value

    grouping = grammar["grouping"]
    separators = [
        separator for separator in grouping["separators"] if separator in value
    ]
    if len(separators) != 1:
        return None

    groups = value.split(separators[0])
    first_group = groups[0]
    if not (
        grouping["first_group_min_digits"]
        <= len(first_group)
        <= grouping["first_group_max_digits"]
    ):
        return None
    if not first_group.isascii() or not first_group.isdigit():
        return None

    following_size = grouping["following_group_digits"]
    if len(groups) < 2 or any(
        len(group) != following_size or not group.isascii() or not group.isdigit()
        for group in groups[1:]
    ):
        return None
    return "".join(groups)


def parse_answer(text_prefix: str, input_language: str, arm: str) -> Optional[int]:
    """Return the last canonical integer answer, or ``None`` for REJECT."""
    candidate = None
    for line in text_prefix.splitlines():
        match = _ANSWER_LINE.fullmatch(line)
        if match:
            candidate = match.group(1)

    if candidate is None:
        return None

    grammar = _load_grammar(_answer_language(input_language, arm))
    normalized = _normalize_digits(candidate, grammar)
    sign = ""
    if normalized and normalized[0] in grammar["sign_characters"]:
        sign, normalized = normalized[0], normalized[1:]

    decimal_separator = grammar["decimal_separator"]
    if decimal_separator in normalized:
        if normalized.count(decimal_separator) != 1:
            return None
        integer_part, fraction = normalized.split(decimal_separator)
        if not fraction or any(digit != "0" for digit in fraction):
            return None
    else:
        integer_part = normalized

    integer_digits = _integer_digits(integer_part, grammar)
    if integer_digits is None:
        return None

    value = int(integer_digits)
    return -value if sign in ("-", "−") else value
