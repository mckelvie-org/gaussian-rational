"""Exact complex-like scalar with rational real and imaginary parts.

The :class:`GaussianRational` type represents values of the form ``a + bi`` where
``a`` and ``b`` are :class:`fractions.Fraction` values.
"""

from __future__ import annotations

import math
from fractions import Fraction
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from types import NotImplementedType
from typing import (
    Any,
    Self,
    overload,
    override,
)

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

type FractionLike = Fraction | int
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

def format_fraction(
    num: FractionLike,
    is_imaginary: bool = False,
    force_sign: bool = False,
    parens_if_fraction: bool = False,
) -> str:
    """Returns a string representation of a real or imaginary Fraction, optionally requiring a sign prefix.
        If force_sign is True, the result will always include a sign, even if the value is positive.
        If the value is a an imaginary fraction, "i" will be included in the numerator portion of the fraction.
        If parens_if_fraction is True, the result after the sign (if any) will be enclosed in parentheses if it is a fraction
            (i.e. if the denominator is not 1). This is useful for ensuring correct operation ordering and readability when the result
            is used as the coefficient in an expression term.
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
            n_str = "i"
        elif num.denominator == 1:
            n_str = f"{num.numerator}i"
        else:
            if num.numerator == 1:
                n_str = f"i/{num.denominator}"
            else:
                n_str = f"{num.numerator}i/{num.denominator}"
    else:
        n_str = str(num)
    if include_parens:
        n_str = f"({n_str})"
    return sign_prefix + n_str

type GaussianRationalLike = GaussianRational | tuple[FractionLike, FractionLike] | FractionLike
"""A Value that can be upcast to a GaussianRational. This includes GaussianRational values, tuples of the form (real_part, imaginary_part)
     where the parts are FractionLike, and any FractionLike value which is interpreted as a purely real number
     with no imaginary part."""

class GaussianRational:
    """Represents an immutable complex value with rational parts of the form a + bi, where a and b are rational numbers represented as Fractions,
       and i is the imaginary unit sqrt(-1).
    """
    
    # __slots__ keeps instances compact and enforces a fixed attribute set.
    __slots__ = ("a", "b")
    
    a: Fraction
    """The rational real part of the number."""
    
    b: Fraction
    """The rational imaginary part of the number."""

    # Enforce immutability
    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"'{self.__class__.__name__}' object is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"'{self.__class__.__name__}' object is immutable")
    
    def __new__(cls, v: GaussianRationalLike, v2: FractionLike | None = None) -> Self:
        """Normalizing constructor for GaussianRational. Supports any of the following forms of input:
           - GaussianRational(a, b) where a and b are Fractions or ints. This is the standard form of input.
           - GaussianRational((a, b)) where a and b are Fractions or ints. This is an alternative form of input that allows the
             real and imaginary parts to be specified as a tuple.
           - GaussianRational(a) where a is a Fraction or int. This is a shorthand form of input that allows a purely real number
             to be specified without needing to include an imaginary part of 0.
           - GaussianRational(v) where v is a GaussianRational. This is an identity constructor that is included to simplify upcasting.
        """
        a_raw: FractionLike
        b_raw: FractionLike

        if isinstance(v, GaussianRational):
            if v2 is not None:
                raise ValueError("Invalid GaussianRational constructor: if the first argument is a GaussianRational, the second argument must be None.")
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
            a_raw = v.a
            b_raw = v.b
        elif isinstance(v, tuple):
            # v is a (real_part, imaginary_part) tuple. v2 must be None in this case.
            if v2 is not None:
                raise ValueError("Invalid GaussianRational constructor: if the first argument is a tuple, the second argument must be None.")
            if len(v) != 2:
                raise ValueError("Invalid GaussianRational constructor: if the first argument is a tuple, it must have length 2.")
            a_raw, b_raw = v
        else:
            # v is FractionLike and represents the real part, and the imaginary part is 0.
            a_raw = v
            b_raw = 0 if v2 is None else v2

        # upcast a and b to Fractions.
        a = upcast_fraction(a_raw)
        b = upcast_fraction(b_raw)
        
        # Set the attributes using object.__setattr__ to bypass the immutability enforcement in __setattr__.
        object.__setattr__(self, "a", a)
        object.__setattr__(self, "b", b)
        return self
    
    def __hash__(self) -> int:
        """Return a hash consistent with numeric equality.

        For purely real values, this matches ``hash(self.a)`` so values equal to
        real scalars (for example ``Fraction(3)`` or ``3``) hash identically.
        """
        if self.b == 0:
            return hash(self.a)
        return hash((self.a, self.b))

    @classmethod
    def _upcast(cls, other: object) -> Self | None:
        """Helper method that upcasts other to cls type. Returns None if NotImplemented should be returned."""
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
        return type(self)(self.a + u_other.a, self.b + u_other.b)

    @overload  # type: ignore[misc]
    def __radd__(self, other: GaussianRationalLike) -> Self: ...
    def __radd__(self, other: object) -> Self | NotImplementedType:
        # Addition is commutative, so we can compute from the upcasted left operand.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(u_other.a + self.a, u_other.b + self.b)
    
    def __neg__(self) -> Self:
        return type(self)(-self.a, -self.b)

    def __pos__(self) -> Self:
        return self
    
    @overload  # type: ignore[misc]
    def __sub__(self, other: GaussianRationalLike) -> Self: ...
    def __sub__(self, other: object) -> Self | NotImplementedType:
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(self.a - u_other.a, self.b - u_other.b)

    @overload  # type: ignore[misc]
    def __rsub__(self, other: GaussianRationalLike) -> Self: ...
    def __rsub__(self, other: object) -> Self | NotImplementedType:
        # Subtraction is not commutative, so we need to start with other.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(u_other.a - self.a, u_other.b - self.b)

    @overload  # type: ignore[misc]
    def __mul__(self, other: GaussianRationalLike) -> Self: ...
    def __mul__(self, other: object) -> Self | NotImplementedType:
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        # (a + bi)(c + di) == (ac - bd) + (ad + bc)i
        return type(self)(self.a * u_other.a - self.b * u_other.b, self.a * u_other.b + self.b * u_other.a)

    @overload  # type: ignore[misc]
    def __rmul__(self, other: GaussianRationalLike) -> Self: ...
    def __rmul__(self, other: object) -> Self | NotImplementedType:
        # Multiplication is commutative, so we can compute from the upcasted left operand.
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        return type(self)(
            u_other.a * self.a - u_other.b * self.b,
            u_other.a * self.b + u_other.b * self.a,
        )

    @overload  # type: ignore[misc]
    def __truediv__(self, other: GaussianRationalLike) -> Self: ...
    def __truediv__(self, other: object) -> Self | NotImplementedType:
        # (a1 + b1i) / (a2 + b2i) == ((a1 + b1i) * (a2 - b2i)) /  (a2^2 + b2^2))
        u_other = self._upcast(other)
        if u_other is None:
            return NotImplemented
        denom = u_other.a * u_other.a + u_other.b * u_other.b
        if denom == 0:
            raise ZeroDivisionError("GaussianRational division by 0")
        return type(self)((self.a * u_other.a + self.b * u_other.b) / denom, (self.b * u_other.a - self.a * u_other.b) / denom)

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
        """Raises this GaussianRational to the power of other, where other is an integer, returning a new GaussianRational representing the result.
           Negative powers are supported, in which case the result is 1 / (this GaussianRational raised to the power of -other).
           The result is computed using recursive squaring; complexity is O(log2(abs(n))) and stack depth grows to log2(abs(n))."""
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
        """Returns the squared absolute value of this GaussianRational as a Fraction, which is a^2 + b^2."""
        return self.a * self.a + self.b * self.b

    def __abs__(self) -> float:
        """Returns the absolute value of this GaussianRational (its length) as a floating point value, which is sqrt(a^2 + b^2)."""
        return math.sqrt(float(self.abs_squared()))

    def __complex__(self) -> complex:
        """Return a built-in complex value by casting both parts to float."""
        return complex(float(self.a), float(self.b))

    def __format__(self, format_spec: str) -> str:
        """Format this value for f-strings and ``format``.

        - Empty format spec uses exact symbolic formatting (``a+bi`` style).
        - Non-empty specs follow built-in ``complex`` formatting semantics after
          casting parts to float, with ``j`` replaced by ``i``.
        """
        if format_spec == "":
            return self.format()
        return format(complex(self), format_spec).replace("j", "i")
    
    def __bool__(self) -> bool:
        """Return ``False`` only for the exact numeric zero."""
        return not self.is_zero

    @override
    def __eq__(self, other: Any) -> bool:
        u_other = self._upcast_comparable(other)
        if u_other is None:
            # We consider comparison to any type that can't be upcast to be unequal.
            return False
        return self.a == u_other.a and self.b == u_other.b

    @property
    def real(self) -> Fraction:
        """Real component, mirroring :class:`complex.real`."""
        return self.a

    @property
    def imag(self) -> Fraction:
        """Imaginary component, mirroring :class:`complex.imag`."""
        return self.b

    def conjugate(self) -> Self:
        """Return the complex conjugate ``a - bi``."""
        return type(self)(self.a, -self.b)
    
    @property
    def is_real(self) -> bool:
        """Returns True if this GaussianRational is purely real (i.e. has no imaginary part), or False otherwise."""
        return self.b == 0
    
    @property
    def is_imaginary(self) -> bool:
        """Returns True if this GaussianRational is purely imaginary (i.e. has an imaginary part but no real part), or False otherwise.
           Note that this does not include the number 0, which could be processed as real or imaginary, but by definition is real."""
        return self.a == 0 and self.b != 0
    
    @property
    def is_zero_or_imaginary(self) -> bool:
        """Returns True if this GaussianRational has no real part, or False otherwise.
           Note that this includes both purely imaginary numbers and the number 0, which has no real or imaginary part."""
        return self.a == 0
    
    @property
    def is_composite(self) -> bool:
        """Returns True if this GaussianRational has both a nonzero real part and a nonzero imaginary part, or False otherwise."""
        return self.a != 0 and self.b != 0
    
    @property
    def is_zero(self) -> bool:
        """Returns True if this GaussianRational is exactly 0."""
        return self.a == 0 and self.b == 0
    
    def format(self, force_sign: bool = False, parens_if_composite: bool = False) -> str:
        """Returns a string representation of this GaussianRational, optionally requiring a sign prefix.
           If the imaginary part is zero, then the real part is output as an ordinary Fraction.
           Otherwise, if the real part is zero, then the imaginary part is output as a Fraction with an included "i".
           Otherwise, both parts are output in the form "a+bi" or "a-{abs(b)}i", where a and b are the real and imaginary parts.
           If force_sign is True, the result will always include a leading sign, even if the first value is positive.
           If parens_if_composite is True and the value has both a real and imaginary part, then the value is enclosed in parentheses
              and the sign of the composite expression is considered "+" for the purposes of force_sign processing.
           If parens_if_composite is True and the value does not have both a real and imaginary part, then parens_if_composite
              is used as parens_if_fraction for the single part that is output.
           If force_sign is True, the result will always include a leading sign, even if the value is
               parenthesized or the first value is positive.
        """
        if self.is_real:
            return format_fraction(self.a, is_imaginary=False, force_sign=force_sign, parens_if_fraction=parens_if_composite)
        if self.is_imaginary:
            return format_fraction(self.b, is_imaginary=True, force_sign=force_sign, parens_if_fraction=parens_if_composite)
        # composite value with both real and imaginary parts. We will format this as "a + bi" or "a - {abs(b)}i", where a and b are the real and imaginary parts.
        if parens_if_composite:
            sign_prefix = "+" if force_sign else ""
            return f"{sign_prefix}({format_fraction(self.a)}{format_fraction(self.b, force_sign=True, is_imaginary=True)})"
        return f"{format_fraction(self.a, force_sign=force_sign)}{format_fraction(self.b, force_sign=True, is_imaginary=True)}"
    
    def __str__(self) -> str:
        return self.format()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.a}, {self.b})"

