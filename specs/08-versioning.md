# Versioning

The port follows [Semantic Versioning 2.0.0](https://semver.org/):
`MAJOR.MINOR.PATCH`, optionally with a `-prerelease` / `+build` suffix.

The project is feature-complete at **1.0.0**.

## Bump rules

| Change | Bump | Examples |
|---|---|---|
| Breaking change | **MAJOR** | incompatible save/config format; removing a feature or CLI option |
| New feature (backwards-compatible) | **MINOR** | new difficulty setting; new screen; new QoL feature |
| Bug fix / internal only (backwards-compatible) | **PATCH** | crash fix; visual fix; performance |

Pre-releases (if ever needed) use `X.Y.Z-alpha.N`, `-beta.N`, or `-rc.N`.

## Process

1. When a change is finished, the **coding agent proposes** the next version and
   the rationale (e.g. "1.1.0 — adds X").
2. The **maintainer approves** (or adjusts) it.
3. Only then is the version updated, and the build + tests are run.

The agent must never bump the version without approval.

## Where the version is declared

Single source of truth:

- `src/congen2/__init__.py` → `__version__ = "X.Y.Z"`.

Derived automatically (never hard-code these):

- `pyproject.toml` reads the version via setuptools dynamic metadata:
  `[tool.setuptools.dynamic] version = {attr = "congen2.__version__"}`.
- The packaged Windows executable's file-version resource is generated from
  `__version__` by `tools/build.py` (PyInstaller `--version-file`).

Shown to the player (all derived from `__version__`):

- Window title bar: `Congeneration 2 vX.Y.Z`.
- Launch menu, bottom-right: `vX.Y.Z` (HITECH font, white).
- Pause screen, bottom-right: `vX.Y.Z` (HITECH font, white).

## Guard

`tests/test_version.py` checks that `__version__` is valid SemVer and matches the
installed package metadata, so the dynamic `pyproject.toml` derivation cannot
silently drift.
