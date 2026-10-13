# Changelog

All notable changes to grkit. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project uses [semantic versioning](https://semver.org/).

## [Unreleased]

### Added
- The logo: a growling dog, `GRrrrKIT`, and a guardrail. "Grrrr, don't forget the guardrails!"
- Open-source project files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, this changelog, issue and pull
  request templates, and CI on GitHub Actions running `scripts/test.sh`.

### Changed
- The README, rewritten to explain what grkit is and why it exists.

## [0.1.1] — 2026-10-13

### Fixed
- The package could not be installed from git: `pyproject.toml` read a README outside the package directory, which
  setuptools refuses. The package now has its own README.

### Added
- `scripts/test.sh` installs the package from a copy of the whole repo, the way pip does from git. Copying
  `python/` alone would not have caught the bug above.

## [0.1.0] — 2026-10-13 — do not use, not installable from git

### Added
- The method, the runtime guard contract, the change gate and the adoption guide (`docs/`).
- The `grkit` package: `verdict`, `client`, `modes`, `pipeline`, `checks`.
- The Copier template: an `AGENTS.md` core, a definition of done, and the `check-required-docs.sh` guard with
  its tests.

[Unreleased]: https://github.com/edtbl76/grkit/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/edtbl76/grkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/edtbl76/grkit/releases/tag/v0.1.0
