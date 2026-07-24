import pytest

from src.parser import parse_answer


def test_native_english_plain_integer() -> None:
    assert parse_answer("work\n#### 42\n", input_language="en", arm="native") == 42


@pytest.mark.parametrize(
    ("language", "number", "expected"),
    [
        ("en", "1,234,567", 1_234_567),
        ("de", "1.234.567", 1_234_567),
        ("sw", "1,234,567", 1_234_567),
        ("th", "๑,๒๓๔,๕๖๗", 1_234_567),
        ("th", "๑๒๓๔", 1_234),
    ],
)
def test_native_locale_accepts_grouped_and_ungrouped_integers(
    language: str, number: str, expected: int
) -> None:
    assert (
        parse_answer(f"#### {number}", input_language=language, arm="native")
        == expected
    )


@pytest.mark.parametrize(
    ("language", "number", "expected"),
    [
        ("en", "1.0", 1),
        ("de", "1,0", 1),
        ("sw", "12,000.000", 12_000),
        ("th", "๑,๒๓๔.๐๐", 1_234),
    ],
)
def test_native_locale_accepts_only_zero_fraction_decimal_forms(
    language: str, number: str, expected: int
) -> None:
    assert (
        parse_answer(f"#### {number}", input_language=language, arm="native")
        == expected
    )


@pytest.mark.parametrize(
    ("language", "number"),
    [
        ("en", "1.00.0"),
        ("en", "12,34"),
        ("en", "1,234.5"),
        ("de", "1.00.0"),
        ("de", "12,34"),
        ("de", "1.234,5"),
        ("sw", "1.00.0"),
        ("sw", "12,34"),
        ("th", "๑.๐๐.๐"),
        ("th", "๑๒,๓๔"),
    ],
)
def test_native_locale_rejects_malformed_grouping_and_nonzero_fractions(
    language: str, number: str
) -> None:
    assert parse_answer(f"#### {number}", input_language=language, arm="native") is None


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        ("+12", 12),
        ("-12", -12),
        ("−12", -12),
        ("-0", 0),
    ],
)
def test_parser_handles_frozen_sign_characters(number: str, expected: int) -> None:
    assert parse_answer(f"#### {number}", input_language="en", arm="native") == expected


def test_last_answer_line_wins() -> None:
    prefix = "#### 10\nintermediate work\n#### -20\n"
    assert parse_answer(prefix, input_language="en", arm="native") == -20


def test_malformed_last_answer_does_not_fall_back_to_an_earlier_answer() -> None:
    prefix = "#### 10\nintermediate work\n#### 12,34\n"
    assert parse_answer(prefix, input_language="en", arm="native") is None


def test_prefix_without_answer_line_is_rejected() -> None:
    assert parse_answer("work only\nanswer is 42", input_language="en", arm="native") is None


@pytest.mark.parametrize("arm", ["translate_act", "code_switched"])
def test_english_answer_arms_use_english_grammar_for_non_english_input(
    arm: str,
) -> None:
    assert parse_answer("#### 1,234", input_language="de", arm=arm) == 1_234
    assert parse_answer("#### 1.234", input_language="de", arm=arm) is None


def test_pivot_uses_input_language_grammar() -> None:
    assert parse_answer("#### 1.234", input_language="de", arm="pivot") == 1_234
