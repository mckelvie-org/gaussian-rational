# gaussian-rational

`gaussian-rational` provides an exact, immutable complex-like scalar where both
components are rational numbers (`fractions.Fraction`).

Use `GaussianRational` when you want complex arithmetic without intermediate
floating-point rounding in the real and imaginary parts.

## Highlights

- Exact real and imaginary components (`Fraction`-backed).
- Immutable value type.
- Complex-style arithmetic (`+`, `-`, `*`, `/`, integer `**`).
- Compatible real equality/hash behavior for purely real values.
- Fully typed (PEP 561, inline annotations).

## Installation

```bash
pip install gaussian-rational
```

## Quick Start

```python
from fractions import Fraction

from gaussian_rational import GaussianRational

z = GaussianRational(Fraction(1, 3), Fraction(2, 5))
w = GaussianRational(2, -1)

print(z + w)          # 7/3-3/5i
print(z * w)          # 16/15+7/15i
print(z / w)          # 4/15+1/3i
print(z.conjugate())  # 1/3-2/5i
print(z.real, z.imag) # Fraction(1, 3) Fraction(2, 5)
print(complex(z))     # complex(float(real), float(imag))
```

## Construction

`GaussianRational` normalizes several input forms:

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

GaussianRational(3, 4)                          # a=3, b=4
GaussianRational((Fraction(1, 2), Fraction(2))) # tuple input
GaussianRational(5)                             # purely real, imag=0
GaussianRational(GaussianRational(1, 2))        # identity/upcast
```

Accepted component types are `int` and `Fraction`.

## API Summary

### Numeric operations

- `+`, `-`, unary `-`
- `*`, `/`
- integer exponentiation `**n` for `n: int`
- `abs(x)` returns `float`
- `complex(x)` returns built-in `complex` using `float` casts of both parts

### Properties and helpers

- `real`, `imag` (aliasing internal components)
- `conjugate()`
- `abs_squared()` for exact norm-squared as `Fraction`
- predicates: `is_real`, `is_imaginary`, `is_zero_or_imaginary`,
  `is_composite`, `is_zero`
- formatting: `format(...)`, plus `str(...)` and `repr(...)`

## String Formatting Conventions

`GaussianRational` provides three related string surfaces:

- `str(z)` uses `z.format()`.
- `z.format(force_sign=False, parens_if_composite=False)` gives configurable
  display formatting.
- `format(z, spec)` / f-strings use `__format__`.
- `repr(z)` returns a diagnostic constructor-style form.

Formatting rules:

- Real-only values print as rational scalars (for example `3`, `-1/2`).
- Imaginary-only values print with `i` attached (for example `i`, `-2i`,
  `i/3`, `-5i/7`).
- Composite values print without spaces as `a+bi` or `a-bi`.
- `force_sign=True` adds a leading `+` for non-negative outputs.
- `parens_if_composite=True` wraps composite outputs in parentheses; for
  non-composite values, rational fractions are parenthesized.
- For `format(z, spec)`: empty `spec` uses exact symbolic formatting, while
  non-empty `spec` uses float-based `complex` formatting semantics and prints
  `i` instead of `j`.

Examples:

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

str(GaussianRational(3, 0))                               # "3"
str(GaussianRational(0, 1))                               # "i"
str(GaussianRational(1, -2))                              # "1-2i"
GaussianRational(1, 2).format(force_sign=True)           # "+1+2i"
GaussianRational(Fraction(1, 2), Fraction(1, 3)).format(
    parens_if_composite=True,
)                                                        # "(1/2+i/3)"
repr(GaussianRational(Fraction(1, 2), Fraction(-3, 4)))  # "GaussianRational(1/2, -3/4)"
f"{GaussianRational(Fraction(1, 2), Fraction(-5, 3)):.2f}" # "0.50-1.67i"
```

Note: `repr(...)` is primarily for diagnostics/readability and is not a strict
round-trip representation for fractional components.

## Examples

### Conjugate product gives exact norm-squared

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

z = GaussianRational(Fraction(3, 4), Fraction(-5, 6))
prod = z * z.conjugate()

print(prod)             # 181/144
print(prod.is_real)     # True
print(prod.real)        # Fraction(181, 144)
print(z.abs_squared())  # Fraction(181, 144)
```

### Division remains exact in components

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

x = GaussianRational(Fraction(1, 2), Fraction(1, 3))
y = GaussianRational(Fraction(2, 5), Fraction(-1, 7))

q = x / y
print(q.real)  # Fraction(1295, 1222)
print(q.imag)  # Fraction(980, 1833)
```

### Integer powers

```python
from gaussian_rational import GaussianRational

z = GaussianRational(1, 1)
print(z ** 2)   # 2i
print(z ** -1)  # 1/2-1/2i
```

### Interop with built-in complex

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

z = GaussianRational(Fraction(1, 3), Fraction(5, 2))
c = complex(z)

print(c)          # (0.3333333333333333+2.5j)
print(type(c))    # <class 'complex'>
```

## Semantics and Compatibility

`GaussianRational` is designed to feel close to `complex` while preserving exact
rational components.

- Truthiness matches numeric convention: only `GaussianRational(0, 0)` is false.
- Equality accepts `GaussianRational`, `int`, and `Fraction` values.
- Equality intentionally does not treat tuples as numeric values.
  Example: `GaussianRational(1, 2) == (1, 2)` is `False`.
- Hashing is aligned for purely real values so equality/hash stay consistent
  with compatible real scalars.

Current intentional limitation:

- Exponentiation supports integer powers only.

## Type Hints

This package ships inline type hints and a `py.typed` marker (PEP 561).

Public typing aliases:

- `FractionLike = Fraction | int`
- `GaussianRationalLike = GaussianRational | tuple[FractionLike, FractionLike] | FractionLike`

## Advanced Usage

### Subclassing notes

`GaussianRational` is intentionally immutable and uses `__slots__` for compact
instances. Subclassing is supported, but there are a few rules to follow:

- Do not assign attributes normally (`self.x = ...`) after construction.
- If your subclass adds fields, define its own `__slots__`.
- During construction, use `object.__setattr__` for any subclass fields.
- Keep arithmetic constructors returning `type(self)(...)` compatible with your
  subclass constructor signature.

Minimal pattern:

```python
from gaussian_rational import GaussianRational


class TaggedGaussianRational(GaussianRational):
    __slots__ = ("tag",)

    def __new__(cls, v, v2=None, *, tag: str = ""):
        self = super().__new__(cls, v, v2)
        object.__setattr__(self, "tag", tag)
        return self
```

If you do not need extra subclass state, prefer using `GaussianRational`
directly for simpler semantics.

Common pitfalls:

- Forgetting to declare subclass `__slots__`, which can reintroduce a `__dict__`
  and inconsistent memory behavior.
- Assigning subclass attributes with normal assignment instead of
  `object.__setattr__` during `__new__`.
- Changing constructor semantics so `type(self)(a, b)` no longer works,
  which can break arithmetic result construction.
- Adding mutable subclass state while keeping hashing enabled.
  If mutable fields affect equality, hash behavior can become invalid.

## Development

This project uses [PDM](https://pdm-project.org/) for dependency management,
linting, type checking, testing, and builds.

```bash
pdm install -G dev
pdm run lint
pdm run typecheck
pdm run test
pdm build
```

## Publishing

This project uses a single version source in `pyproject.toml` plus
`python-semantic-release` automation.

### Local version helpers

Use these PDM scripts for explicit SemVer bumps:

```bash
pdm run release-print
pdm run release-patch
pdm run release-minor
pdm run release-major
```

These commands update `project.version`, create a release commit and tag, and
are intended for controlled release operations.

### GitHub release workflow (recommended)

- Run the `Release` workflow manually and choose `patch`, `minor`, or `major`.
- It runs lint/typecheck/tests, bumps version with semantic-release, creates a
  tag (`vX.Y.Z`), and pushes commit/tag.
- Tag push triggers the `Publish` workflow.

### Duplicate publish protection

`Publish` includes explicit safeguards:

- Verifies tag version equals `project.version`.
- Checks PyPI for an existing `gaussian-rational==X.Y.Z` and fails if present.

This prevents accidentally republishing the same version.

### Build artifacts manually

```bash
pdm build
```

### Install-path testing without publishing or version bump

Use the `Install Smoke Test` workflow (`workflow_dispatch`) with one of:

- `source=github` with `git_ref` (branch/tag/sha) to test install directly from
  repository path.
- `source=testpypi` with `version` to test an already-uploaded TestPyPI build.

Local equivalents:

```bash
python -m pip install "gaussian-rational @ git+https://github.com/<owner>/<repo>.git@<ref>"
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  "gaussian-rational==<version>"
```

## Supported Python Versions

- Python 3.12+

## License

MIT. See LICENSE.
