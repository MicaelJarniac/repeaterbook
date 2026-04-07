# CHANGELOG


## v0.6.0 (2026-04-07)

### Chores

- **deps**: Bump aiohttp from 3.13.3 to 3.13.4
  ([`24b513c`](https://github.com/MicaelJarniac/repeaterbook/commit/24b513c2b7893b43a18ec374758abc7e03fa5e23))

--- updated-dependencies: - dependency-name: aiohttp dependency-version: 3.13.4

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump requests from 2.32.5 to 2.33.0
  ([`0e47556`](https://github.com/MicaelJarniac/repeaterbook/commit/0e47556f129ae47c5398f8bcefb0bee8a2bcdbdb))

Bumps [requests](https://github.com/psf/requests) from 2.32.5 to 2.33.0. - [Release
  notes](https://github.com/psf/requests/releases) -
  [Changelog](https://github.com/psf/requests/blob/main/HISTORY.md) -
  [Commits](https://github.com/psf/requests/compare/v2.32.5...v2.33.0)

--- updated-dependencies: - dependency-name: requests dependency-version: 2.33.0

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

### Features

- Truncate
  ([`f1d70f6`](https://github.com/MicaelJarniac/repeaterbook/commit/f1d70f6356e0d7f37d5480a494905480f1ce8400))


## v0.5.1 (2026-04-06)

### Bug Fixes

- Remove Py 3.10, add 3.14
  ([`51b5cb9`](https://github.com/MicaelJarniac/repeaterbook/commit/51b5cb93f0e02c12821bdec61c3a74b46acd4b4f))


## v0.5.0 (2026-04-06)

### Chores

- **deps**: Bump tornado from 6.5.4 to 6.5.5
  ([`49e0d7b`](https://github.com/MicaelJarniac/repeaterbook/commit/49e0d7b98382ceeeba2be96e4fc77c517440e899))

Bumps [tornado](https://github.com/tornadoweb/tornado) from 6.5.4 to 6.5.5. -
  [Changelog](https://github.com/tornadoweb/tornado/blob/master/docs/releases.rst) -
  [Commits](https://github.com/tornadoweb/tornado/compare/v6.5.4...v6.5.5)

--- updated-dependencies: - dependency-name: tornado dependency-version: 6.5.5

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

### Documentation

- Add AGENTS.md project knowledge base
  ([`d1a63e4`](https://github.com/MicaelJarniac/repeaterbook/commit/d1a63e41b528c4a52a2b20dd94c4cbfeb3dd9044))

### Features

- Import from CSV export
  ([`4e569a2`](https://github.com/MicaelJarniac/repeaterbook/commit/4e569a2d2f7b01548bedd0e5fea478255b1d9e2d))


## v0.4.2 (2026-03-04)

### Bug Fixes

- Support auth
  ([`fbdcf71`](https://github.com/MicaelJarniac/repeaterbook/commit/fbdcf715e6a32ba91d9c4c8db36ba0963acc6f48))

### Chores

- Format
  ([`9e71ff4`](https://github.com/MicaelJarniac/repeaterbook/commit/9e71ff44e570e491c67760ca0d7208a42d699f85))


## v0.4.1 (2026-03-04)

### Bug Fixes

- Handle API errors
  ([`e676c5b`](https://github.com/MicaelJarniac/repeaterbook/commit/e676c5bb1cf0ae232d62a2d34cd8d85abc644aeb))

### Documentation

- Add comprehensive documentation ([#12](https://github.com/MicaelJarniac/repeaterbook/pull/12),
  [`457a003`](https://github.com/MicaelJarniac/repeaterbook/commit/457a00322ed0816a39219817b8fa4c8b38dda8f8))

* docs: add comprehensive documentation

Add extensive documentation covering all aspects of the RepeaterBook library:

- getting-started.md: Complete tutorial for beginners with quick start examples - usage.md:
  Comprehensive usage guide covering API client, database operations, geographic queries, frequency
  filtering, digital modes, and data export - architecture.md: Technical architecture documentation
  with diagrams, data flow explanations, design decisions, and extensibility guide - examples.md:
  Real-world examples including web apps, codeplug generation, coverage maps, statistics dashboards,
  travel planning, and network analysis - faq.md: Extensive FAQ covering installation, usage,
  performance, troubleshooting, and integration questions - README.md: Enhanced with better
  introduction, features list, quick example, and clear navigation to all documentation sections -
  mkdocs.yml: Updated navigation structure to include all new documentation pages

This significantly improves the developer experience by providing clear, comprehensive documentation
  with practical examples for common use cases.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

* fix: regenerate corrupted uv.lock file

The uv.lock file had a corruption with typing-extensions dependency missing source field.
  Regenerated the lock file to resolve the issue.

* fix: correct all field names and API usage in documentation examples

Fixed all code examples across documentation to use correct field names and proper API patterns:

- Changed LatLon(latitude=, longitude=) to LatLon(lat=, lon=) - Updated field names to match actual
  model: - location → location_nearest_city - input_ctcss → pl_ctcss_uplink - output_ctcss →
  pl_ctcss_tsq_downlink - p25_capable → apco_p_25_capable - p25_nac → p_25_nac - Fixed distance
  handling: filter_radius() returns sorted repeaters but doesn't add distance attribute, must
  calculate manually with haversine - Changed states= to state_ids= in ExportQuery - Removed
  references to non-existent fields (input_dcs, output_dcs, nxdn_ran, trustee) - Fixed emergency
  services to use actual fields (ares, races, skywarn, canwarn) instead of non-existent
  Emergency.YES/NO enum - Removed incorrect rb.session usage

All examples now work correctly with the actual codebase.

* fix: infinite CI

* chore: update cruft

* build(CI): fix pre-commit

* chore: cruft update

* docs: update documentation for v0.4.0 features

- Updated API configuration to use max_cache_age (timedelta) instead of cache_ttl - Added
  documentation for custom exceptions: - RepeaterBookError (base) - RepeaterBookAPIError -
  RepeaterBookValidationError - RepeaterBookCacheError - Documented model validation (latitude,
  longitude, frequency) - Added error handling examples to usage guide and FAQ - Added timedelta,
  haversine, frozenset to wordlist

- Changed LatLon(latitude=, longitude=) to LatLon(lat=, lon=) - Removed non-existent .distance
  attribute access - Added inline haversine calculation for distance display - filter_radius()
  returns sorted repeaters without distance attribute

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

* fix: remove non-existent field references and update API patterns

- Remove rep.network references (field doesn't exist in Repeater model) - Update cache_ttl to
  max_cache_age (timedelta) in examples - Fix filter_radius documentation to not set
  repeater.distance - Fix square_bounds call signature - Rename Example 7 from network analysis to
  DMR analysis

* fix: use FIPS codes for state_ids instead of state names

The state_ids parameter requires numeric FIPS codes (e.g., "06" for California, "48" for Texas), not
  state names. Updated all documentation examples to use correct FIPS codes.

Examples: - California: "06" - Nevada: "32" - Oregon: "41" - Washington: "53" - Texas: "48" -
  Oklahoma: "40" - New Mexico: "35" - Florida: "12" - Arizona: "04" - Utah: "49"

* fix: use keyword argument for RepeaterBook database parameter

RepeaterBook's first positional arg is working_dir, not database. Fixed all examples to use
  database= keyword argument.

Also removed incorrect :memory: example - the current implementation doesn't support in-memory
  databases as it always constructs a file path.

* chore: mkdocs cfg place

---------

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>


## v0.4.0 (2026-02-04)

### Features

- Comprehensive codebase improvements ([#8](https://github.com/MicaelJarniac/repeaterbook/pull/8),
  [`c893c4b`](https://github.com/MicaelJarniac/repeaterbook/commit/c893c4b39125d4f843d11cb06f633122b809b769))

* feat: comprehensive codebase improvements

- Add custom exception classes (RepeaterBookError, RepeaterBookAPIError, RepeaterBookCacheError,
  RepeaterBookValidationError) - Enable North America endpoint in urls_export() - Fix cache race
  conditions with atomic write pattern - Add model validation for latitude, longitude, and frequency
  fields - Replace MD5 with SHA256 for cache key generation - Make configuration injectable
  (max_cache_age, max_count) - Remove commented-out operating_mode field - Improve type safety with
  explanatory comments for casts - Optimize cache stat calls (single stat instead of exists + stat)

Test suite expansion: - Add test_exceptions.py for exception hierarchy - Add test_services.py for
  services module - Add test_models.py for model validation - Add test_queries.py for query builders
  - Add test_database.py for database operations - Add test_utils.py for utility functions - Expand
  test_repeaterbook.py for public API

Total: 108 tests passing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

* feat: add smart routing for NA/ROW endpoints

Implement intelligent endpoint routing in urls_export(): - NA-specific fields (state_id, county,
  emcomm, stype) route to NA only - ROW-specific fields (region) route to ROW only - NA countries
  (US, Canada, Mexico) route to NA only - ROW countries route to ROW only - Mixed or common-only
  queries route to both

This prevents redundant API calls and avoids unfiltered queries that could return thousands of
  irrelevant results.

Added tests for all routing scenarios.

* test: add comprehensive smart routing integration tests

Add live API integration tests to verify smart routing behavior: - NA-only queries (state_id) route
  to export.php only - ROW-only queries (region) route to exportROW.php only - NA country queries
  route to NA endpoint - ROW country queries route to ROW endpoint - Mixed country queries route to
  both endpoints - Empty queries route to both endpoints - Mode-only queries route to both endpoints

Also fix linting warnings (use next(iter()) instead of list()[0]).

---------

Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>


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
