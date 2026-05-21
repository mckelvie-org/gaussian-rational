from __future__ import annotations

import math
from fractions import Fraction

import pytest

from gaussian_rational import GaussianRational, format_fraction


def _naive_pow(base: GaussianRational, exponent: int) -> GaussianRational:
    """Reference implementation using repeated multiplication."""
    if exponent == 0:
        return GaussianRational(1)
    if exponent < 0:
        return GaussianRational(1) / _naive_pow(base, -exponent)

    result = GaussianRational(1)
    for _ in range(exponent):
        result = result * base
    return result


def test_constructor_normalizes_inputs() -> None:
    assert GaussianRational(2).real == Fraction(2)
    assert GaussianRational((3, 4)).imag == Fraction(4)
    assert GaussianRational(Fraction(5, 7), 1).real == Fraction(5, 7)


def test_arithmetic_operations() -> None:
    x = GaussianRational(1, 2)
    y = GaussianRational(3, -4)

    assert x + y == GaussianRational(4, -2)
    assert x - y == GaussianRational(-2, 6)
    assert x * y == GaussianRational(11, 2)
    assert x / y == GaussianRational(Fraction(-1, 5), Fraction(2, 5))


def test_unary_plus_returns_same_value() -> None:
    x = GaussianRational(Fraction(2, 3), Fraction(-5, 7))
    assert +x == x


def test_reverse_operations_with_int() -> None:
    x = GaussianRational(2, 3)

    assert 5 + x == GaussianRational(7, 3)
    assert 5 - x == GaussianRational(3, -3)
    assert 5 * x == GaussianRational(10, 15)
    assert 5 / x == GaussianRational(Fraction(10, 13), Fraction(-15, 13))


def test_division_by_zero() -> None:
    with pytest.raises(ZeroDivisionError):
        _ = GaussianRational(1, 1) / GaussianRational(0, 0)


def test_immutable_instance() -> None:
    value = GaussianRational(1, 2)
    with pytest.raises(AttributeError):
        value.real = Fraction(3)


def test_bool_semantics_match_complex() -> None:
    assert bool(GaussianRational(0, 0)) is False
    assert bool(GaussianRational(1, 0)) is True
    assert bool(GaussianRational(0, 1)) is True


def test_hash_alignment_for_pure_real_values() -> None:
    pure_real = GaussianRational(3, 0)
    assert pure_real == 3
    assert pure_real == Fraction(3)
    assert hash(pure_real) == hash(3)
    assert hash(pure_real) == hash(Fraction(3))


def test_equality_behavior_for_tuple_is_false() -> None:
    value = GaussianRational(1, 2)
    assert (value == (1, 2)) is False


def test_real_imag_and_conjugate() -> None:
    value = GaussianRational(Fraction(2, 3), Fraction(-5, 7))
    assert value.real == Fraction(2, 3)
    assert value.imag == Fraction(-5, 7)
    assert value.conjugate() == GaussianRational(Fraction(2, 3), Fraction(5, 7))


def test_as_tuple_returns_fraction_components() -> None:
    value = GaussianRational(Fraction(2, 3), Fraction(-5, 7))
    assert value.as_tuple() == (Fraction(2, 3), Fraction(-5, 7))


def test_arg_matches_atan2_for_general_value() -> None:
    value = GaussianRational(Fraction(1, 3), Fraction(-5, 2))
    assert value.arg() == pytest.approx(math.atan2(-2.5, 1 / 3))


def test_arg_handles_axis_aligned_values() -> None:
    assert GaussianRational(0, 0).arg() == pytest.approx(0.0)
    assert GaussianRational(1, 0).arg() == pytest.approx(0.0)
    assert GaussianRational(-1, 0).arg() == pytest.approx(math.pi)
    assert GaussianRational(0, 1).arg() == pytest.approx(math.pi / 2)
    assert GaussianRational(0, -1).arg() == pytest.approx(-math.pi / 2)


def test_complex_conversion_casts_fraction_parts_to_float() -> None:
    value = GaussianRational(Fraction(1, 3), Fraction(-5, 2))
    c_value = complex(value)
    assert c_value.real == float(Fraction(1, 3))
    assert c_value.imag == float(Fraction(-5, 2))


def test_parse_accepts_format_roundtrip_default() -> None:
    value = GaussianRational(Fraction(2, 3), Fraction(-5, 7))
    assert GaussianRational.parse(value.format()) == value


def test_parse_accepts_imag_char_tuple_and_spaces() -> None:
    assert GaussianRational.parse(" 1/2 + 3 i ", imag_char=("i", "j")) == GaussianRational(
        Fraction(1, 2),
        3,
    )
    assert GaussianRational.parse("( 1/2 - j/3 )", imag_char=("i", "j")) == GaussianRational(
        Fraction(1, 2),
        Fraction(-1, 3),
    )


def test_parse_accepts_parenthesized_fraction_imag() -> None:
    assert GaussianRational.parse("(2/3)j") == GaussianRational(0, Fraction(2, 3))
    assert GaussianRational.parse("-(2/3)j") == GaussianRational(0, Fraction(-2, 3))


def test_parse_optionally_accepts_slash_before_imag() -> None:
    with pytest.raises(ValueError):
        GaussianRational.parse("2/3j")
    assert GaussianRational.parse("2/3j", interpret_slash_j_as_j_slash=True) == GaussianRational(
        0,
        Fraction(2, 3),
    )


def test_parse_accepts_complex_style_with_integer_parts() -> None:
    assert GaussianRational.parse("1+2j") == GaussianRational(1, 2)
    assert GaussianRational.parse("2j+1") == GaussianRational(1, 2)
    assert GaussianRational.parse("(1-2j)") == GaussianRational(1, -2)


def test_constructor_accepts_string_and_uses_parse_defaults() -> None:
    assert GaussianRational("1/2+3j") == GaussianRational(Fraction(1, 2), 3)
    with pytest.raises(ValueError):
        GaussianRational("1+2j", 0)


def test_format_empty_spec_uses_symbolic_output() -> None:
    value = GaussianRational(Fraction(1, 2), Fraction(-5, 3))
    assert format(value, "") == "1/2-5j/3"


def test_format_numeric_spec_uses_float_parts_with_default_imag_suffix() -> None:
    value = GaussianRational(Fraction(1, 2), Fraction(-5, 3))
    assert format(value, ".2f") == "0.50-1.67j"
    assert format(value, "+.1f") == "+0.5-1.7j"


def test_format_can_override_imag_char() -> None:
    value = GaussianRational(Fraction(1, 2), Fraction(-5, 3))
    assert value.format(imag_char="i") == "1/2-5i/3"


def test_format_fraction_can_override_imag_char() -> None:
    assert format_fraction(Fraction(1, 3), is_imaginary=True, imag_char="i") == "i/3"


def test_integer_power() -> None:
    value = GaussianRational(1, 1)
    assert value**0 == GaussianRational(1)
    assert value**2 == GaussianRational(0, 2)
    assert value**-1 == GaussianRational(Fraction(1, 2), Fraction(-1, 2))


def test_higher_integer_powers_match_naive_reference() -> None:
    value = GaussianRational(Fraction(2, 3), Fraction(-1, 4))

    for exponent in (5, 6, 7, 8, 11, 12, -5, -7, -10):
        assert value**exponent == _naive_pow(value, exponent)
