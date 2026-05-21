# gaussian-rational

[![CI](https://github.com/mckelvie-org/gaussian-rational/actions/workflows/ci.yml/badge.svg)](https://github.com/mckelvie-org/gaussian-rational/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/gaussian-rational.svg)](https://pypi.org/project/gaussian-rational/)
[![Python versions](https://img.shields.io/pypi/pyversions/gaussian-rational.svg)](https://pypi.org/project/gaussian-rational/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

`gaussian-rational` provides an exact, immutable complex-like scalar where both
components are rational numbers (`fractions.Fraction`).

Use `GaussianRational` when you want complex arithmetic without intermediate
floating-point rounding in the real and imaginary parts.

## Highlights

- Exact real and imaginary components (`Fraction`-backed).
- Immutable value type, safe to share across threads.
- Complex-style arithmetic (`+`, `-`, `*`, `/`, integer `**`).
- Compatible real equality/hash behavior for purely real values.
- Flexible string parsing and formatting.
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

print(z + w)          # 7/3-3j/5
print(z * w)          # 16/15+7j/15
print(z / w)          # 4/15+j/3
print(z.conjugate())  # 1/3-2j/5
print(z.real, z.imag) # Fraction(1, 3) Fraction(2, 5)
print(complex(z))     # (0.3333333333333333+0.4j)
print(z.arg())        # atan2(float(imag), float(real))
```

## Construction

`GaussianRational` normalizes several input forms:

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

GaussianRational(3, 4)                           # a=3, b=4
GaussianRational((Fraction(1, 2), Fraction(2)))  # tuple input
GaussianRational(5)                              # purely real, imag=0
GaussianRational(GaussianRational(1, 2))         # identity/upcast
GaussianRational("1/2+2j")                       # string parse
```

Accepted component types are `int` and `Fraction`.

## API Summary

### Numeric operations

- `+`, `-`, unary `-`
- `*`, `/`
- Integer exponentiation `**n` for `n: int`
- `abs(x)` returns `float`
- `complex(x)` returns built-in `complex` using `float` casts of both parts

### Properties and helpers

- `real`, `imag` — rational components, mirroring `complex`
- `conjugate()` — complex conjugate `a - bi`
- `arg()` — phase angle in radians (`atan2(imag, real)`)
- `as_tuple()` — explicit `(real, imag)` tuple
- `abs_squared()` — exact norm-squared as `Fraction`
- Predicates: `is_real`, `is_imaginary`, `is_zero_or_imaginary`, `is_composite`, `is_zero`
- Parsing: `GaussianRational.parse(...)`
- Formatting: `format(...)`, `str(...)`, `repr(...)`

If you want deterministic ordering, sort explicitly with `as_tuple()`:

```python
sorted_values = sorted(values, key=lambda z: z.as_tuple())
```

## String Formatting

`GaussianRational` provides three string surfaces:

| Surface | Description |
|---|---|
| `str(z)` | Calls `z.format()`. |
| `z.format(...)` | Configurable exact symbolic output. |
| `format(z, spec)` / f-strings | Empty spec → symbolic; non-empty spec → float-based `complex` semantics. |
| `repr(z)` | Eval-safe constructor form, for example `GaussianRational(Fraction(1, 2), 3)`. |

Formatting rules:

- Real-only values print as rational scalars (for example `3`, `-1/2`).
- Imaginary-only values print with `j` attached (for example `j`, `-2j`, `j/3`, `-5j/7`).
- Composite values print as `a+bj` or `a-bj` with no spaces.
- `force_sign=True` adds a leading `+` for non-negative outputs.
- `parens_if_composite=True` wraps composite outputs in parentheses; for
  non-composite values, rational fractions are parenthesized instead.
- `imag_char` overrides the symbol per call (for example `imag_char="i"`).
- `GaussianRational.default_imag_char` sets the class-wide default.
- For `format(z, spec)`: non-empty `spec` uses `complex` formatting semantics,
  mapping the imaginary symbol to the class default.

Examples:

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

str(GaussianRational(3, 0))                               # "3"
str(GaussianRational(0, 1))                               # "j"
str(GaussianRational(1, -2))                              # "1-2j"
GaussianRational(1, 2).format(force_sign=True)            # "+1+2j"
GaussianRational(Fraction(1, 2), Fraction(1, 3)).format(
    parens_if_composite=True,
)                                                         # "(1/2+j/3)"
GaussianRational(1, 2).format(imag_char="i")              # "1+2i"
repr(GaussianRational(Fraction(1, 2), Fraction(-3, 4)))   # "GaussianRational(Fraction(1, 2), Fraction(-3, 4))"
f"{GaussianRational(Fraction(1, 2), Fraction(-5, 3)):.2f}" # "0.50-1.67j"
```

`repr(z)` is an eval-safe round-trip given `from fractions import Fraction` and
`from gaussian_rational import GaussianRational` in scope.

## Parsing String Literals

`GaussianRational.parse` parses symbolic literals and is also used by
`GaussianRational("...")`.

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

GaussianRational.parse("1+2j")                 # GaussianRational(1, 2)
GaussianRational.parse("(2/3)j")               # GaussianRational(0, Fraction(2, 3))
GaussianRational.parse("2j/3")                 # GaussianRational(0, Fraction(2, 3))
GaussianRational.parse(" 1/2 + 3 i ", imag_char=("i", "j"))
GaussianRational.parse("2/3j", interpret_slash_j_as_j_slash=True)
```

Parsing notes:

- Embedded spaces are ignored.
- `imag_char` accepts a single character or a tuple of aliases.
- By default, ambiguous `2/3j` is rejected; set
  `interpret_slash_j_as_j_slash=True` to accept it as `2j/3`.
- `GaussianRationalLike` intentionally excludes `str`, so arithmetic dunder
  upcasting never treats arbitrary strings as numeric.

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

### Division remains exact

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
print(z ** 2)   # 2j
print(z ** -1)  # 1/2-j/2
```

### Interop with built-in complex

```python
from fractions import Fraction
from gaussian_rational import GaussianRational

z = GaussianRational(Fraction(1, 3), Fraction(5, 2))
c = complex(z)

print(c)        # (0.3333333333333333+2.5j)
print(type(c))  # <class 'complex'>
```

## Semantics and Compatibility

`GaussianRational` is designed to feel close to `complex` while preserving
exact rational components.

- Truthiness matches numeric convention: only `GaussianRational(0, 0)` is false.
- Equality accepts `GaussianRational`, `int`, and `Fraction` values.
- Equality intentionally does not accept tuples:
  `GaussianRational(1, 2) == (1, 2)` is `False`.
- Hashing is aligned for purely real values so equality and hash stay consistent
  with compatible real scalars.
- Instances are immutable and safe to share across threads.

Current intentional limitation:

- Exponentiation supports integer powers only.

## Type Hints

This package ships inline type hints and a `py.typed` marker (PEP 561).

Public typing aliases:

- `FractionLike = Fraction | int`
- `GaussianRationalLike = GaussianRational | tuple[FractionLike, FractionLike] | FractionLike`

## Advanced Usage

### Subclassing

`GaussianRational` is immutable and uses `__slots__` for compact instances.
Subclassing is supported with a few rules:

- Do not assign attributes normally (`self.x = ...`) after construction; use
  `object.__setattr__` in `__new__` instead.
- If your subclass adds fields, declare its own `__slots__`.
- Keep `type(self)(a, b)` compatible with your subclass constructor, since
  arithmetic results are constructed that way.

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

Subclass contract for `repr` round-trips:

`__repr__` is implemented as `f"{type(self).__name__}({self.format()!r})"`.
A subclass that adds state beyond the `real` and `imag` slots must override both `format()`
(to encode that state in the string) and `parse()` (to decode it), so that
`eval(repr(z))` remains a valid round-trip.

Common pitfalls:

- Forgetting `__slots__` on the subclass, which reintroduces `__dict__`.
- Changing constructor semantics so `type(self)(a, b)` no longer works.
- Adding mutable fields while keeping hashing enabled (invalidates hash
  contract if mutable fields affect equality).

## Development

This project uses [PDM](https://pdm-project.org/) for dependency management,
linting, type checking, and testing.

```bash
pdm install -G dev
pdm run lint       # ruff check
pdm run typecheck  # mypy
pdm run test       # pytest
pdm build
```

## Publishing

Releases are managed through GitHub Actions using a three-channel model:

| Channel | Branch | Tag format | Index |
|---|---|---|---|
| dev | `main` | — (no publish) | — |
| rc | `rc/<x.y.z>` | `rc-v<x.y.z>-rc.<n>` | TestPyPI |
| prod | `prod/<x.y.z>` | `v<x.y.z>` | PyPI |

### Version invariant

`main` always carries `X.Y.Z-dev.N`.  The `x.y.z` portion of any RC or
production release always matches the commit on `main` from which it was cut —
only the qualifier suffix changes.

### Release workflow

**Bump dev version** — increment the version on `main`.

```bash
bin/bump-dev [dev|patch|minor|major]   # edits pyproject.toml, does not commit
```

| `bump_type` | Example |
|---|---|
| `dev` | `1.0.0-dev.1` → `1.0.0-dev.2` |
| `patch` | `1.0.0-dev.2` → `1.0.1-dev.1` |
| `minor` | `1.0.0-dev.2` → `1.1.0-dev.1` |
| `major` | `1.0.0-dev.2` → `2.0.0-dev.1` |

Also available remotely via `Actions → Bump dev version → Run workflow` for
cases where a local checkout is not convenient.

**`bin/cut-rc`** (run on `main`) — create a release candidate.

Reads `X.Y.Z-dev.N` from `pyproject.toml`, auto-increments the rc counter
from existing tags, creates branch `rc/X.Y.Z` with version `X.Y.Z-rc.N`,
and pushes — triggering `Publish TestPyPI`.

**`bin/cut-prod`** (run on `rc/<x.y.z>`) — promote to production.

Strips the rc qualifier, creates branch `prod/X.Y.Z` with the clean `X.Y.Z`
version, and pushes — triggering `Publish`, which tags the commit `vX.Y.Z`
and auto-bumps `main` to `X.Y.(Z+1)-dev.1` after a successful PyPI push.

### Guards

Both publish workflows validate that:

- The branch version matches `pyproject.toml`'s version.
- The version format matches the target index (stable for PyPI, `-rc.N` for
  TestPyPI).
- The version does not already exist on the target index.
- Lint, type checks, and tests pass.

### Install-path smoke test

Use the **Install Smoke Test** workflow to verify an install without publishing
or bumping a version:

- `source=github` with a `git_ref` — installs directly from the repository.
- `source=testpypi` with a `version` — installs an already-uploaded TestPyPI
  build.

## Supported Python Versions

Python 3.10 and later.

## License

MIT. See [LICENSE](LICENSE).
