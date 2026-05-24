# Contributing

This project uses [PDM](https://pdm-project.org/) for dependency management, linting, type checking, and testing.

## Development setup

```bash
bin/install        # first-time setup (installs PDM and dependencies)
pdm install -G dev # subsequent dependency updates
pdm run lint       # ruff check
pdm run typecheck  # mypy
pdm run test       # pytest
pdm build
```

## Release workflow

Releases follow a three-channel model:

| Channel | Tag format             | Moving tag   | Index    |
|---------|------------------------|--------------|----------|
| dev     | —                      | —            | —        |
| rc      | `v<x.y.z>-rc.<n>`     | `rc-latest`  | TestPyPI |
| prod    | `v<x.y.z>`             | `prod-latest`| PyPI     |

`main` always carries `X.Y.Z-dev.N`. Releases are driven entirely by tags —
no `rc` or `prod` branches are created.

### Bump the dev version

```bash
bin/bump-dev [dev|patch|minor|major]   # edits pyproject.toml, does not commit
```

| `bump_type` | Example |
|-------------|---------|
| `dev`       | `1.0.0-dev.1` → `1.0.0-dev.2` |
| `patch`     | `1.0.0-dev.2` → `1.0.1-dev.1` |
| `minor`     | `1.0.0-dev.2` → `1.1.0-dev.1` |
| `major`     | `1.0.0-dev.2` → `2.0.0-dev.1` |

Commit and push to `main` before cutting a release.

### Cut a release candidate

Run from `main`:

```bash
bin/cut-rc
```

Reads `X.Y.Z-dev.N` from `pyproject.toml`, finds the next unused rc counter
from existing `v<x.y.z>-rc.*` tags, sets the version to `X.Y.Z-rc.N` in a
worktree, tags the commit `v<x.y.z>-rc.<n>`, and pushes the tag —
triggering `Publish TestPyPI`.

After a successful publish the workflow updates the `rc-latest` tag.

### Cut a production release

Run from anywhere on the repo:

```bash
bin/cut-prod [--force] [RC_REF]
```

`RC_REF` is optional. Resolution order:
1. Explicit argument (tag, sha, or bare version like `1.0.5-rc.1`).
2. `HEAD`, if `pyproject.toml` in the working tree carries an `X.Y.Z-rc.N` version.
3. The `rc-latest` tag (the most recently published rc).

Strips the rc qualifier, commits to a worktree, tags the commit `v<x.y.z>`,
and pushes the tag — triggering `Publish`, which updates `prod-latest` and
auto-bumps `main` to `X.Y.(Z+1)-dev.1` after a successful PyPI push.

Use `--force` on either script to overwrite an existing tag and retry a failed publish.

### Guards

Both publish workflows validate that:

- The version in `pyproject.toml` matches the expected format for the target index.
- The version does not already exist on the target index.
- Lint, type checks, and tests pass.

### Smoke test

Use the **Install Smoke Test** workflow to verify an install without publishing:

```bash
# From GitHub source
gh workflow run install-smoke.yml --field source=github --field git_ref=main

# From TestPyPI
gh workflow run install-smoke.yml --field source=testpypi --field version=1.0.0rc1
```
