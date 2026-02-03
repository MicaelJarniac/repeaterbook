# CHANGELOG


## v0.3.0 (2026-02-03)

### Chores

- **deps**: Bump aiohttp from 3.11.14 to 3.13.3
  ([#6](https://github.com/MicaelJarniac/repeaterbook/pull/6),
  [`5ac6362`](https://github.com/MicaelJarniac/repeaterbook/commit/5ac63626172f12e422fc4025d1eb3fbfcfe87d5f))

--- updated-dependencies: - dependency-name: aiohttp dependency-version: 3.13.3

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump filelock from 3.18.0 to 3.20.3
  ([#4](https://github.com/MicaelJarniac/repeaterbook/pull/4),
  [`00e7717`](https://github.com/MicaelJarniac/repeaterbook/commit/00e7717186b77a8510ee6e0580bd1f13a4d495d6))

Bumps [filelock](https://github.com/tox-dev/py-filelock) from 3.18.0 to 3.20.3. - [Release
  notes](https://github.com/tox-dev/py-filelock/releases) -
  [Changelog](https://github.com/tox-dev/filelock/blob/main/docs/changelog.rst) -
  [Commits](https://github.com/tox-dev/py-filelock/compare/3.18.0...3.20.3)

--- updated-dependencies: - dependency-name: filelock dependency-version: 3.20.3

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump urllib3 from 2.3.0 to 2.6.3
  ([#5](https://github.com/MicaelJarniac/repeaterbook/pull/5),
  [`6870e08`](https://github.com/MicaelJarniac/repeaterbook/commit/6870e0894ef62164124096a7eba2a65d0da7637f))

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.3.0 to 2.6.3. - [Release
  notes](https://github.com/urllib3/urllib3/releases) -
  [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst) -
  [Commits](https://github.com/urllib3/urllib3/compare/2.3.0...2.6.3)

--- updated-dependencies: - dependency-name: urllib3 dependency-version: 2.6.3

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump virtualenv from 20.29.3 to 20.36.1
  ([#3](https://github.com/MicaelJarniac/repeaterbook/pull/3),
  [`89b2aa3`](https://github.com/MicaelJarniac/repeaterbook/commit/89b2aa32f1c18b988dac0e1894456fd4576930b7))

Bumps [virtualenv](https://github.com/pypa/virtualenv) from 20.29.3 to 20.36.1. - [Release
  notes](https://github.com/pypa/virtualenv/releases) -
  [Changelog](https://github.com/pypa/virtualenv/blob/main/docs/changelog.rst) -
  [Commits](https://github.com/pypa/virtualenv/compare/20.29.3...20.36.1)

--- updated-dependencies: - dependency-name: virtualenv dependency-version: 20.36.1

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Features

- Update Cruft ([#11](https://github.com/MicaelJarniac/repeaterbook/pull/11),
  [`0c7c471`](https://github.com/MicaelJarniac/repeaterbook/commit/0c7c471d559a8814018a645767bd34dbe381b58f))

* feat: update Cruft

* chore: update Cruft

### Testing

- Add cache tests + opt-in live API integration
  ([#7](https://github.com/MicaelJarniac/repeaterbook/pull/7),
  [`804cedd`](https://github.com/MicaelJarniac/repeaterbook/commit/804cedd0a0abd51d6ea31653f893db9cecef454f))

* test: add offline cache tests and opt-in live API integration tests

* refactor: fix linting and type checking issues in tests

- Add missing __init__.py to tests/integration/ package - Replace Any with proper StdPath type
  annotations for tmp_path - Add missing docstring to test function - Fix line length violations (88
  char limit) - Use more specific type:ignore[union-attr] for mypy - Extract magic number to named
  constant - Move pathlib imports to TYPE_CHECKING block

All linting (ruff) and type checking (mypy) now pass.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

* refactor(tests): extract local server fixture and clean up test code

- Add local_server fixture in conftest.py to reduce test duplication - Simplify _live_enabled() with
  case-insensitive comparison - Move pycountry import to module level in test_live_api.py - Extract
  _NA_SAMPLE_SIZE constant for magic number 200 - Fix import organization (blank lines after
  TYPE_CHECKING blocks)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

---------

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>


## v0.2.2 (2026-01-31)

### Bug Fixes

- Tolerate RepeaterBook API drift ([#2](https://github.com/MicaelJarniac/repeaterbook/pull/2),
  [`665d78e`](https://github.com/MicaelJarniac/repeaterbook/commit/665d78ee38ca856a242b8f5f6289c441f00193a2))

* fix: tolerate RepeaterBook API drift (sponsor, NA fields, empty Use)

* refactor: simplify Region parsing (use .get)

* refactor: add b() helper for Yes/No + 1/0 fields


## v0.2.1 (2025-04-09)

### Chores

- Links
  ([`1d93cdb`](https://github.com/MicaelJarniac/repeaterbook/commit/1d93cdb5ae7dff17a6cb9943e66b2111f39617b5))


## v0.2.0 (2025-04-08)

### Bug Fixes

- Use `and_` for `square` query
  ([`9c09b5e`](https://github.com/MicaelJarniac/repeaterbook/commit/9c09b5eff8a2a4cef3dda91d5fa4d44001b0f241))

### Features

- Queries
  ([`78972e5`](https://github.com/MicaelJarniac/repeaterbook/commit/78972e5cbdcd150dd9e6435d5dd5c759bb22f96b))


## v0.1.1 (2025-04-03)

### Bug Fixes

- Merge instead of add to local DB
  ([`f6dfcbf`](https://github.com/MicaelJarniac/repeaterbook/commit/f6dfcbf242c9af07578d5a2e8e19047ee2db96b9))

### Chores

- Dunder all as tuples
  ([`2dfb808`](https://github.com/MicaelJarniac/repeaterbook/commit/2dfb8089fee6db5fc26b9d3ea986fe8f9ce86cd3))

- Simpler working dir default
  ([`fecdd43`](https://github.com/MicaelJarniac/repeaterbook/commit/fecdd4353fb37f46d42de3b6da69d7d402b76742))


## v0.1.0 (2025-03-31)

### Features

- Initial release
  ([`2a257dd`](https://github.com/MicaelJarniac/repeaterbook/commit/2a257ddaada98ffa6871e607a868aabf6556bae1))


## v0.0.0 (2025-03-21)
