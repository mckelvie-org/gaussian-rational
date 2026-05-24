"""Exact complex-like scalar with rational real and imaginary parts.

The :class:`GaussianRational` type represents values of the form ``a + bi``
where ``a`` and ``b`` are :class:`fractions.Fraction` values, providing exact
complex arithmetic without floating-point rounding in the components.

Author:
    Samuel J. McKelvie

License:
    MIT — see the LICENSE file in the project root for details.
"""

from __future__ import annotations

import math
import re
import sys
from fractions import Fraction
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from types import NotImplementedType
from typing import (
    Any,
    ClassVar,
    TypeAlias,
    overload,
)

if sys.version_info >= (3, 12):
    from typing import Self, override
else:
    from typing_extensions import Self, override

try:
    __version__ = package_version("gaussian-rational")
except PackageNotFoundError:
    # Source tree import before installation.
    __version__ = "0.0.0"

__all__ = [
    "FractionLike",
    "GaussianRationalLike",
    "GaussianRational",
    "format_fraction",
    "upcast_fraction",
    "__version__",
]

FractionLike: TypeAlias = Fraction | int
"""A value that can be losslessly converted to :class:`Fraction`."""

def upcast_fraction(num: FractionLike) -> Fraction:
    """Return ``num`` as a :class:`Fraction`.

    Raises ``TypeError`` if ``num`` is not ``int`` or ``Fraction``.
    """
    if not isinstance(num, Fraction):
        if not isinstance(num, int):
            raise TypeError(f"upcast_fraction: Value must be a Fraction or int, got {type(num)}.")
        num = Fraction(num)
    return num


def _strip_wrapping_parens(text: str) -> str:
    """Strip balanced outer parentheses from a token.

    Parameters
    ----------
    text:
        Input token that may be wrapped in one or more balanced outer
        parenthesis layers.

    Returns
    -------
    str
        ``text`` with removable outer parenthesis layers stripped.
    """
    s = text
    while len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        depth = 0
        balanced = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    balanced = False
                    break
            if depth == 0 and i != len(s) - 1:
                balanced = False
                break
        if not balanced or depth != 0:
            break
        s = s[1:-1]
    return s


def _split_additive_terms(expr: str) -> list[str]:
    """Split an expression into top-level additive terms.

    Parameters
    ----------
    expr:
        Canonicalized additive expression (for example ``"1+2j-3/4"``).

    Returns
    -------
    list[str]
        A list of signed terms preserving order.

    Raises
    ------
    ValueError
        If parentheses are unbalanced.
    """
    terms: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(expr):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unbalanced ')' in expression: {expr!r}")
        elif ch in "+-" and depth == 0 and i > 0:
            terms.append(expr[start:i])
            start = i
    if depth != 0:
        raise ValueError(f"Unbalanced '(' in expression: {expr!r}")
    terms.append(expr[start:])
    return terms


def _parse_integer_token(token: str) -> int:
    """Parse an integer token.

    Parameters
    ----------
    token:
        Token that should represent an integer with optional sign and optional
        removable outer parentheses.

    Returns
    -------
    int
        Parsed integer value.

    Raises
    ------
    ValueError
        If ``token`` is not a valid integer literal.
    """
    token = _strip_wrapping_parens(token)
    if not re.fullmatch(r"[+-]?\d+", token):
        raise ValueError(f"Invalid integer token: {token!r}")
    return int(token)


def _parse_fraction_token(token: str) -> Fraction:
    """Parse a rational token into :class:`Fraction`.

    Parameters
    ----------
    token:
        Token that should represent ``int`` or ``int/int`` with optional sign.
        Sign may appear outside parentheses (for example ``"-(2/3)"``).

    Returns
    -------
    Fraction
        Parsed rational value.

    Raises
    ------
    ValueError
        If ``token`` is not a supported rational literal.
    """
    sign = ""
    if token.startswith(("+", "-")):
        sign = token[0]
        token = token[1:]
    token = _strip_wrapping_parens(token)
    token = sign + token
    if not re.fullmatch(r"[+-]?\d+(?:/\d+)?", token):
        raise ValueError(f"Invalid fraction token: {token!r}")
    return Fraction(token)


def format_fraction(
    num: FractionLike,
    is_imaginary: bool = False,
    force_sign: bool = False,
    parens_if_fraction: bool = False,
    imag_char: str = "j",
) -> str:
    """Format a real or imaginary :class:`Fraction` value as a string.

    Parameters
    ----------
    num:
        The rational value to format.
    is_imaginary:
        If ``True``, attach ``imag_char`` to the numerator to produce an
        imaginary term (for example ``"3j"`` or ``"j/2"``).
    force_sign:
        If ``True``, always include a leading sign even for positive values.
    parens_if_fraction:
        If ``True``, wrap the output in parentheses when the denominator is
        not 1.  Useful for coefficient terms inside larger expressions.
    imag_char:
        Symbol used for the imaginary unit.

    Returns
    -------
    str
        Formatted string.
    """
    num = upcast_fraction(num)
    if num >= 0:
        sign_prefix = "+" if force_sign else ""
    else:
        sign_prefix = "-"
        num = -num
    include_parens = parens_if_fraction and num.denominator != 1
    if is_imaginary:
        if num == 1:
            n_str = imag_char
        elif num.denominator == 1:
            n_str = f"{num.numerator}{imag_char}"
        else:
            if num.numerator == 1:
                n_str = f"{imag_char}/{num.denominator}"
            else:
                n_str = f"{num.numerator}{imag_char}/{num.denominator}"
    else:
        n_str = str(num)
    if include_parens:
        n_str = f"({n_str})"
    return sign_prefix + n_str


GaussianRationalLike: TypeAlias = "GaussianRational | tuple[FractionLike, FractionLike] | FractionLike"
"""Value that can be upcast to ``GaussianRational``.

Includes ``GaussianRational`` values, ``(real, imag)`` tuples with
``FractionLike`` parts, and ``FractionLike`` real scalars interpreted as
imaginary part ``0``.
"""


class GaussianRational:
    """Immutable complex-like value with rational parts ``a + bi``.

    Both ``a`` and ``b`` are stored as :class:`fractions.Fraction`.
    """
    
    # __slots__ keeps instances compact and enforces a fixed attribute set.
    __slots__ = ("real", "imag")

    # Default symbol used when formatting imaginary values.
    default_imag_char: ClassVar[str] = "j"
    
    real: Fraction
    """The rational real part, mirroring :attr:`complex.real`."""

    imag: Fraction
    """The rational imaginary part, mirroring :attr:`complex.imag`."""

    # Enforce immutability
    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"'{self.__class__.__name__}' object is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"'{self.__class__.__name__}' object is immutable")

    def __new__(cls, v: GaussianRationalLike | str, v2: FractionLike | None = None) -> Self:
        """Create an immutable ``GaussianRational`` from normalized inputs.

        Parameters
        ----------
        v:
            Primary value to construct from. Accepted forms are:
            ``GaussianRational`` (identity/upcast), ``(real, imag)`` tuple,
            ``FractionLike`` real scalar, or ``str`` parseable by
            :meth:`GaussianRational.parse`.
        v2:
            Optional imaginary component used only when ``v`` is a real scalar.

        Returns
        -------
        Self
            Constructed immutable value.

        Raises
        ------
        ValueError
            If an invalid parameter combination is provided (for example,
            tuple/string input with non-``None`` ``v2``).
        TypeError
            If scalar components are not ``int`` or ``Fraction`` after
            normalization.
        """
        a_raw: FractionLike
        b_raw: FractionLike

        if isinstance(v, str):
            if v2 is not None:
                raise ValueError(
                    "Invalid GaussianRational constructor: if the first argument is a "
                    "string, the second argument must be None."
                )
            return cls.parse(v)

        if isinstance(v, GaussianRational):
            if v2 is not None:
                raise ValueError(
                    "Invalid GaussianRational constructor: if the first argument is a "
                    "GaussianRational, the second argument must be None."
                )
            if isinstance(v, cls):
                # v is already a GaussianRational of the correct subclass, so we can just return it directly without creating a copy.
                return v
            # Fall through for cross-casting from a GaussianRational of a different subclass.

        self = super().__new__(cls)
        if isinstance(v, GaussianRational):
            # This is the case where v is a GaussianRational but not of subclass cls.
            # We want to allow this to support upcasting from GaussianRational to subclasses of GaussianRational, but we need to make
            # sure to create a copy rather than just returning v.
            # We already verified that v2 is None
            a_raw = v.real
            b_raw = v.imag
        elif isinstance(v, tuple):
            # v is a (real_part, imaginary_part) tuple. v2 must be None in this case.
            if v2 is not None:
                raise ValueError(
                    "Invalid GaussianRational constructor: if the first argument is a "
                    "tuple, the second argument must be None."
                )
            if len(v) != 2:
                raise ValueError(
                    "Invalid GaussianRational constructor: if the first argument is a "
                    "tuple, it must have length 2."
                )
            a_raw, b_raw = v
        else:
            # v is FractionLike and represents the real part, and the imaginary part is 0.
            a_raw = v
            b_raw = 0 if v2 is None else v2

        # upcast a and b to Fractions.
        a = upcast_fraction(a_raw)
        b = upcast_fraction(b_raw)

        # Set the attributes using object.__setattr__ to bypass the immutability enforcement in __setattr__.
        object.__setattr__(self, "real", a)
        object.__setattr__(self, "imag", b)
        return self

    @classmethod
    def parse(
        cls,
        value: str,
        imag_char: str | tuple[str, ...] | None = None,
        *,
        interpret_slash_j_as_j_slash: bool = False,
    ) -> Self:
        """Parse a ``GaussianRational`` from a literal string.

        Parameters
        ----------
        value:
            Input literal to parse. Embedded whitespace is ignored.
        imag_char:
            Imaginary-unit character(s) accepted in ``value``. If ``None``, the
            class default ``default_imag_char`` is used. Pass a single-character
            string (for example ``"j"``) or a tuple of single-character aliases
            (for example ``("i", "j")``).
        interpret_slash_j_as_j_slash:
            If ``False`` (default), ambiguous forms like ``"2/3j"`` are
            rejected. If ``True``, they are interpreted as ``"2j/3"``.

        Returns
        -------
        Self
            Parsed ``GaussianRational`` value.

        Raises
        ------
        TypeError
            If ``value`` is not a string.
        ValueError
            If ``value`` cannot be parsed under the chosen options.

        Notes
        -----
        Accepted syntax includes values produced by :meth:`format`,
        ``complex``-style integer-part forms, parenthesized forms such as
        ``"(2/3)j"``, and ``"aj/b"`` forms.
        """
        if not isinstance(value, str):
            raise TypeError(f"parse expects str, got {type(value)}")

        imag_chars: tuple[str, ...]
        if imag_char is None:
            imag_chars = (cls.default_imag_char,)
        elif isinstance(imag_char, str):
            imag_chars = (imag_char,)
        else:
            imag_chars = imag_char

        if len(imag_chars) == 0 or any(len(ch) != 1 for ch in imag_chars):
            raise ValueError("imag_char must be a single character or tuple of single characters")

        text = "".join(value.split())
        if text == "":
            raise ValueError("Cannot parse empty GaussianRational string")
        text = _strip_wrapping_parens(text)

        allowed_chars = set("0123456789+-/()") | set(imag_chars)
        bad_chars = sorted({ch for ch in text if ch not in allowed_chars})
        if bad_chars:
            raise ValueError(f"Unsupported characters in GaussianRational string: {''.join(bad_chars)!r}")

        canonical = text
        for ch in imag_chars:
            canonical = canonical.replace(ch, "j")

        terms = _split_additive_terms(canonical)
        a = Fraction(0)
        b = Fraction(0)

        for raw_term in terms:
            if raw_term in ("", "+", "-"):
                raise ValueError(f"Invalid term in GaussianRational string: {raw_term!r}")

            term = _strip_wrapping_parens(raw_term)
            j_count = term.count("j")
            if j_count == 0:
                a += _parse_fraction_token(term)
                continue
            if j_count != 1:
                raise ValueError(f"Invalid imaginary term: {raw_term!r}")

            # "j/" and "endswith j" are mutually exclusive given j_count == 1:
            # a single j cannot be both followed by "/" and the last character.
            if "j/" in term:
                j_pos = term.index("j")
                left = term[:j_pos]
                right = term[j_pos + 2 :]
                if right == "":
                    raise ValueError(f"Missing denominator in imaginary term: {raw_term!r}")

                if left in ("", "+", "-"):
                    left_coeff = Fraction(-1 if left == "-" else 1)
                else:
                    left_coeff = _parse_fraction_token(left)
                b += left_coeff / _parse_integer_token(right)
                continue

            if not term.endswith("j"):
                raise ValueError(f"Invalid imaginary term: {raw_term!r}")

            left = term[:-1]
            if left in ("", "+", "-"):
                b += Fraction(-1 if left == "-" else 1)
                continue

            if "/" in left:
                unsigned_left = left[1:] if left.startswith(("+", "-")) else left
                wrapped = unsigned_left.startswith("(") and unsigned_left.endswith(")")
                if not wrapped and not interpret_slash_j_as_j_slash:
                    raise ValueError(
                        f"Ambiguous fraction-imaginary term {raw_term!r}; use '(a/b)j', 'aj/b', or set interpret_slash_j_as_j_slash=True"
                    )
            b += _parse_fraction_token(left)

        return cls(a, b)
    
    def __hash__(self) -> int:
        """Return a hash consistent with numeric equality.

        For purely real values, this matches ``hash(self.real)`` so values equal to
        real scalars (for example ``Fraction(3)`` or ``3``) hash identically.
        """
        if self.imag == 0:
            return hash(self.real)
        return hash((self.real, self.imag))

    @classmethod
    def _upcast(cls, other: object) -> Self | None:
        """Upcast ``other`` to ``cls`` when supported.

        Returns ``None`` when arithmetic dunder methods should propagate
        ``NotImplemented``.
        """
        if isinstance(other, cls):
            return other
        if isinstance(other, (GaussianRational, tuple, Fraction, int)):
            return cls(other)
        return None

    @classmethod
    def _upcast_comparable(cls, other: object) -> Self | None:
        """Coerce ``other`` for equality checks.

        Equality accepts GaussianRational values and real scalar values (``int``
        and ``Fraction``). Tuple coercion is intentionally not accepted for
        equality to match Python's ``complex`` behavior more closely.
        """
        if isinstance(other, cls):
            return other
        if isinstance(other, (GaussianRational, Fraction, int)):
            return cls(other)
        return None
    
    @overload  # type: ignore[misc]
    def __add__(self, other: GaussianRationalLike) -> Self: ...
    def __add__(self, other: object) -> Self | NotImplementedType:
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(self.real + u_other.real, self.imag + u_other.imag)

    @overload  # type: ignore[misc]
    def __radd__(self, other: GaussianRationalLike) -> Self: ...
    def __radd__(self, other: object) -> Self | NotImplementedType:
        # Addition is commutative, so we can compute from the upcasted left operand.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(u_other.real + self.real, u_other.imag + self.imag)
    
    def __neg__(self) -> Self:
        return type(self)(-self.real, -self.imag)

    def __pos__(self) -> Self:
        return self
    
    @overload  # type: ignore[misc]
    def __sub__(self, other: GaussianRationalLike) -> Self: ...
    def __sub__(self, other: object) -> Self | NotImplementedType:
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(self.real - u_other.real, self.imag - u_other.imag)

    @overload  # type: ignore[misc]
    def __rsub__(self, other: GaussianRationalLike) -> Self: ...
    def __rsub__(self, other: object) -> Self | NotImplementedType:
        # Subtraction is not commutative, so we need to start with other.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(u_other.real - self.real, u_other.imag - self.imag)

    @overload  # type: ignore[misc]
    def __mul__(self, other: GaussianRationalLike) -> Self: ...
    def __mul__(self, other: object) -> Self | NotImplementedType:
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        # (a + bi)(c + di) == (ac - bd) + (ad + bc)i
        return type(self)(self.real * u_other.real - self.imag * u_other.imag, self.real * u_other.imag + self.imag * u_other.real)

    @overload  # type: ignore[misc]
    def __rmul__(self, other: GaussianRationalLike) -> Self: ...
    def __rmul__(self, other: object) -> Self | NotImplementedType:
        # Multiplication is commutative, so we can compute from the upcasted left operand.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(
            u_other.real * self.real - u_other.imag * self.imag,
            u_other.real * self.imag + u_other.imag * self.real,
        )

    @overload  # type: ignore[misc]
    def __truediv__(self, other: GaussianRationalLike) -> Self: ...
    def __truediv__(self, other: object) -> Self | NotImplementedType:
        # (a1 + b1i) / (a2 + b2i) == ((a1 + b1i) * (a2 - b2i)) /  (a2^2 + b2^2))
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        denom = u_other.real * u_other.real + u_other.imag * u_other.imag
        if denom == 0:
            raise ZeroDivisionError("GaussianRational division by 0")
        return type(self)((self.real * u_other.real + self.imag * u_other.imag) / denom, (self.imag * u_other.real - self.real * u_other.imag) / denom)

    @overload  # type: ignore[misc]
    def __rtruediv__(self, other: GaussianRationalLike) -> Self: ...
    def __rtruediv__(self, other: object) -> Self | NotImplementedType:
        # Division is not commutative, so we need to start with other.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(u_other) / self

    @overload  # type: ignore[misc]
    def __pow__(self, other: int) -> Self: ...
    def __pow__(self, other: object) -> Self | NotImplementedType:
        """Raise this value to an integer power.

        Negative powers are supported via reciprocal. The implementation uses
        recursive exponentiation by squaring, with time complexity
        ``O(log2(abs(n)))`` and recursion depth ``log2(abs(n))``.
        """
        if not isinstance(other, int):
            return NotImplemented
        if other < 0:
            return type(self)(1) / (self ** (-other))
        if other == 0:
            return type(self)(1)
        if other == 1:
            return self
        # We can use recursive exponentiation by squaring to compute the result efficiently.
        # Each time we square, we divide other by 2, so we only need O(log n) multiplications to compute the result.
        result = self ** (other // 2)   # compute self^(other//2) recursively.
        result = result * result        # square the result to get self^(other//2 * 2) == self^(other - other%2)
        if other % 2 != 0:
            # If other is odd, we need to multiply by self one more time to account for the odd exponent.
            result = result * self
        return result
    
    def abs_squared(self) -> Fraction:
        """Return the exact squared magnitude ``a² + b²`` as a :class:`Fraction`."""
        return self.real * self.real + self.imag * self.imag

    def __abs__(self) -> float:
        """Return the magnitude ``sqrt(a² + b²)`` as a :class:`float`."""
        return math.sqrt(float(self.abs_squared()))

    def __complex__(self) -> complex:
        """Return a :class:`complex` value by casting both parts to :class:`float`."""
        return complex(float(self.real), float(self.imag))

    def __format__(self, format_spec: str) -> str:
        """Format this value for f-strings and ``format``.

        - Empty format spec uses exact symbolic formatting (``a+bj`` style).
        - Non-empty specs follow built-in ``complex`` formatting semantics after
          casting parts to float, then map ``j`` to ``default_imag_char``.
        """
        if format_spec == "":
            return self.format()
        c_str = format(complex(self), format_spec)
        if self.default_imag_char == "j":
            return c_str
        return c_str.replace("j", self.default_imag_char)
    
    def __bool__(self) -> bool:
        """Return ``False`` only for the exact numeric zero."""
        return not self.is_zero

    @override
    def __eq__(self, other: Any) -> bool:
        u_other = self._upcast_comparable(other)
        if u_other is None:
            # We consider comparison to any type that can't be upcast to be unequal.
            return False
        return self.real == u_other.real and self.imag == u_other.imag

    def conjugate(self) -> Self:
        """Return the complex conjugate ``a - bi``."""
        return type(self)(self.real, -self.imag)

    def arg(self) -> float:
        """Return the counterclockwise angle from the positive real axis.

        The result is in radians and follows ``atan2(imag, real)`` semantics.
        """
        return math.atan2(float(self.imag), float(self.real))

    def as_tuple(self) -> tuple[Fraction, Fraction]:
        """Return ``(real, imag)`` as a tuple of Fractions."""
        return (self.real, self.imag)
    
    @property
    def is_real(self) -> bool:
        """``True`` if the imaginary part is zero."""
        return self.imag == 0

    @property
    def is_imaginary(self) -> bool:
        """``True`` if the real part is zero and the imaginary part is nonzero."""
        return self.real == 0 and self.imag != 0

    @property
    def is_zero_or_imaginary(self) -> bool:
        """``True`` if the real part is zero (includes the value 0 itself)."""
        return self.real == 0

    @property
    def is_composite(self) -> bool:
        """``True`` if both the real and imaginary parts are nonzero."""
        return self.real != 0 and self.imag != 0

    @property
    def is_zero(self) -> bool:
        """``True`` if both parts are exactly zero."""
        return self.real == 0 and self.imag == 0
    
    def format(
        self,
        force_sign: bool = False,
        parens_if_composite: bool = False,
        imag_char: str | None = None,
    ) -> str:
        """Return a symbolic string representation of this value.

        Parameters
        ----------
        force_sign:
            If ``True``, always include a leading sign even for positive values.
        parens_if_composite:
            If ``True`` and the value has both real and imaginary parts, wrap
            the result in parentheses.  For purely real or purely imaginary
            values, acts as ``parens_if_fraction`` on the single term instead.
        imag_char:
            Symbol used for the imaginary unit; defaults to
            :attr:`default_imag_char`.

        Returns
        -------
        str
            Exact symbolic string, for example ``"1/2-5j/3"`` or
            ``"(1/2+j/3)"``.
        """
        imag_char = self.default_imag_char if imag_char is None else imag_char
        if self.is_real:
            return format_fraction(
                self.real,
                is_imaginary=False,
                force_sign=force_sign,
                parens_if_fraction=parens_if_composite,
                imag_char=imag_char,
            )
        if self.is_imaginary:
            return format_fraction(
                self.imag,
                is_imaginary=True,
                force_sign=force_sign,
                parens_if_fraction=parens_if_composite,
                imag_char=imag_char,
            )
        # Composite value with both real and imaginary parts: format as
        # "a+bi" or "a-{abs(b)}i".
        if parens_if_composite:
            sign_prefix = "+" if force_sign else ""
            return (
                f"{sign_prefix}("
                f"{format_fraction(self.real, imag_char=imag_char)}"
                f"{format_fraction(self.imag, force_sign=True, is_imaginary=True, imag_char=imag_char)}"
                ")"
            )
        return (
            f"{format_fraction(self.real, force_sign=force_sign, imag_char=imag_char)}"
            f"{format_fraction(self.imag, force_sign=True, is_imaginary=True, imag_char=imag_char)}"
        )
    
    def __str__(self) -> str:
        return self.format()
    
    def __repr__(self) -> str:
        # Subclasses that add state should override format() and parse() to
        # keep this round-trip eval-safe.
        return f"{type(self).__name__}({self.format()!r})"

