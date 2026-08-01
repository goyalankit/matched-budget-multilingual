from fractions import Fraction

from src.answer_grammar import answers_equal, parse_for_kind

INTEGER = {"kind": "integer"}
NUMERIC = {"kind": "numeric", "equality": "exact_rational"}
CHOICE = {"kind": "choice", "labels": ["A", "B", "C", "D"]}


def test_integer_kind_delegates_to_the_frozen_parser():
    from src.parser import parse_answer

    text = "reasoning\n#### 42"
    assert parse_for_kind(text, "de", "native", "integer", INTEGER) == 42
    assert parse_for_kind(text, "de", "native", "integer", INTEGER) == parse_answer(
        text, "de", "native"
    )


def test_integer_kind_preserves_locale_digit_handling():
    # Thai digits, via the frozen locale grammar.
    assert parse_for_kind("#### ๔๒", "th", "native", "integer", INTEGER) == 42


def test_numeric_parses_decimal_and_fraction_to_the_same_value():
    # Decimal form must use the ANSWER LANGUAGE's separator: "," in German,
    # "." in English. Asserting "0.5" here for German was the ASCII assumption
    # that made this module mis-parse; see the locale section below.
    assert parse_for_kind("#### 0,5", "de", "native", "numeric", NUMERIC) == Fraction(
        1, 2
    )
    assert parse_for_kind("#### 1/2", "de", "native", "numeric", NUMERIC) == Fraction(
        1, 2
    )
    assert parse_for_kind("#### 0.5", "en", "native", "numeric", NUMERIC) == Fraction(
        1, 2
    )


def test_numeric_rejects_non_numeric():
    assert parse_for_kind("#### x", "de", "native", "numeric", NUMERIC) is None


def test_numeric_takes_the_last_answer_line():
    assert parse_for_kind(
        "#### 1\nmore\n#### 2", "de", "native", "numeric", NUMERIC
    ) == Fraction(2)


def test_choice_accepts_a_declared_label():
    assert parse_for_kind("#### C", "th", "native", "choice", CHOICE) == "C"


def test_choice_is_case_insensitive_but_canonicalises_upward():
    assert parse_for_kind("#### c", "th", "native", "choice", CHOICE) == "C"


def test_choice_rejects_an_undeclared_label():
    assert parse_for_kind("#### E", "th", "native", "choice", CHOICE) is None


def test_choice_rejects_a_letter_with_trailing_prose():
    assert parse_for_kind("#### C is correct", "th", "native", "choice", CHOICE) is None


def test_missing_answer_line_is_none_for_every_kind():
    for kind, grammar in (
        ("integer", INTEGER),
        ("numeric", NUMERIC),
        ("choice", CHOICE),
    ):
        assert parse_for_kind("no answer here", "de", "native", kind, grammar) is None


def test_answers_equal_uses_exact_rational_equality():
    assert answers_equal(Fraction(1, 2), 0.5, "numeric")
    assert not answers_equal(Fraction(1, 3), 0.333, "numeric")
    assert answers_equal(42, 42, "integer")
    assert answers_equal("C", "C", "choice")


# --- Locale-aware numeric parsing -------------------------------------------
# The first version of this module used an ASCII regex. It rejected valid
# German answers and, worse, SILENTLY MIS-PARSED them: in German "." is a
# grouping separator, so "1.234" is 1234, not 1.234. The frozen integer path
# already knew this; the numeric path did not, so one string parsed to two
# different values depending on answer_kind.


def test_german_decimal_comma_is_the_decimal_separator():
    assert parse_for_kind("#### 0,5", "de", "native", "numeric", NUMERIC) == Fraction(
        1, 2
    )


def test_german_dot_is_a_grouping_separator_not_a_decimal_point():
    """The mis-parse that motivated this: 1.234 is one thousand two hundred
    thirty-four in German, and must agree with the frozen integer parser."""
    from src.parser import parse_answer

    parsed = parse_for_kind("#### 1.234", "de", "native", "numeric", NUMERIC)
    assert parsed == Fraction(1234)
    assert parsed == parse_answer("#### 1.234", "de", "native")


def test_german_rejects_a_dot_used_as_a_decimal_point():
    # "0.5" is malformed in German: a following group must have three digits.
    assert parse_for_kind("#### 0.5", "de", "native", "numeric", NUMERIC) is None


def test_thai_digits_and_thai_decimal_point():
    assert parse_for_kind("#### ๐.๕", "th", "native", "numeric", NUMERIC) == Fraction(
        1, 2
    )


def test_thai_grouping_separator_is_a_comma():
    assert parse_for_kind("#### 1,234", "th", "native", "numeric", NUMERIC) == Fraction(
        1234
    )


def test_translate_act_answers_use_the_english_grammar():
    """Arm, not input language, selects the answer grammar (frozen §4 rule)."""
    assert parse_for_kind(
        "#### 0.5", "de", "translate_act", "numeric", NUMERIC
    ) == Fraction(1, 2)


def test_negative_and_unicode_minus_are_handled():
    assert parse_for_kind("#### -0,5", "de", "native", "numeric", NUMERIC) == Fraction(
        -1, 2
    )
    assert parse_for_kind("#### −0,5", "de", "native", "numeric", NUMERIC) == Fraction(
        -1, 2
    )


def test_fraction_answers_respect_the_locale_too():
    assert parse_for_kind("#### 3/4", "de", "native", "numeric", NUMERIC) == Fraction(
        3, 4
    )
    assert parse_for_kind("#### -3/4", "de", "native", "numeric", NUMERIC) == Fraction(
        -3, 4
    )
    assert parse_for_kind("#### 3/0", "de", "native", "numeric", NUMERIC) is None


def test_two_decimal_separators_are_rejected():
    assert parse_for_kind("#### 0,5,5", "de", "native", "numeric", NUMERIC) is None


def test_numeric_still_rejects_prose():
    assert parse_for_kind("#### about 3", "de", "native", "numeric", NUMERIC) is None


def test_normalize_gold_coerces_per_kind():
    from fractions import Fraction as F

    from src.answer_grammar import normalize_gold

    assert normalize_gold("0042", "integer") == 42
    assert normalize_gold(42, "integer") == 42
    assert normalize_gold("0.5", "numeric") == F(1, 2)
    assert normalize_gold(" c ", "choice") == "C"
