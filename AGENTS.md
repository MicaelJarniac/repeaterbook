# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-05
**Commit:** 23eae00
**Branch:** main

## OVERVIEW

Python library for querying and caching ham radio repeater data from RepeaterBook.com. Core stack: aiohttp (async HTTP), SQLModel (ORM), attrs (immutable config), pydantic (validation).

## STRUCTURE

```
repeaterbook/
├── src/repeaterbook/        # Library source (6 modules, ~1100 LOC)
│   ├── __init__.py          # Public API: Repeater, RepeaterBook, exceptions
│   ├── models.py            # SQLModel ORM + TypedDicts for API JSON + query types
│   ├── services.py          # API client, HTTP fetching, JSON→model conversion
│   ├── database.py          # SQLite persistence via SQLModel/SQLAlchemy
│   ├── queries.py           # Geo-spatial query builders (square, radius, band filters)
│   ├── exceptions.py        # 5-class hierarchy: RepeaterBookError base
│   └── utils.py             # LatLon, Radius, SquareBounds helpers
├── tests/                   # Pytest suite (1:1 with src modules)
│   ├── conftest.py          # anyio_backend fixture, local aiohttp test server
│   └── integration/         # Live API tests (@pytest.mark.integration)
├── docs/                    # MkDocs Material source
├── benchmarks/              # ASV benchmarking (scaffold only)
├── playground/              # Jupyter notebooks for experimentation
└── noxfile.py               # Automation: lint, format, type-check, test, docs
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/modify repeater fields | `models.py` → `Repeater` class | SQLModel table + pydantic validators |
| Change API parsing logic | `services.py` → `json_to_model()` | Handle NA vs ROW payload differences |
| Modify API endpoints/routing | `services.py` → `RepeaterBookAPI.urls_export()` | NA vs ROW smart routing |
| Add query filters | `queries.py` | Returns `ColumnElement[bool]` for SQLAlchemy |
| Change caching behavior | `services.py` → `fetch_json()` | Atomic temp→rename write pattern |
| Database operations | `database.py` → `RepeaterBook` | `populate()`, `query()` |
| Add new exception types | `exceptions.py` | Inherit from `RepeaterBookError` |
| Geo calculations | `utils.py` | Uses haversine library |
| Async test fixtures | `tests/conftest.py` | `local_server()` spins up ephemeral aiohttp |
| CI pipeline | `.github/workflows/ci.yml` | Dynamic Nox session matrix |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Repeater` | SQLModel | `models.py:82` | Core ORM model — 35+ fields, lat/lon/freq validators |
| `RepeaterBook` | attrs frozen | `database.py:27` | Main user-facing class — SQLite init, populate, query |
| `RepeaterBookAPI` | attrs frozen | `services.py:265` | API client — URL routing, export, download |
| `fetch_json()` | async fn | `services.py:75` | Cached streaming HTTP fetch with progress bar |
| `json_to_model()` | fn | `services.py:167` | JSON→Repeater conversion (resilient to NA/ROW diffs) |
| `ExportQuery` | attrs frozen | `models.py:312` | Type-safe query builder with frozensets |
| `square()` | fn | `queries.py:30` | SQL indexed bounding-box filter |
| `filter_radius()` | fn | `queries.py:44` | In-memory haversine distance filter + sort |
| `band()` | fn | `queries.py:105` | Frequency band filter (2m, 70cm, etc.) |
| `Bands` | Enum | `queries.py:91` | Standard amateur bands with Decimal bounds |

## CONVENTIONS

- **All ruff rules enabled** (`select = ["ALL"]`), Google docstrings, line-length 88
- **Strict mypy** on all files including tests and noxfile
- **`from __future__ import annotations`** in every file
- **`__all__`** tuple explicitly defined in every module
- **attrs frozen classes** for immutable config/API objects (not dataclasses)
- **SQLModel** for ORM models (not raw SQLAlchemy)
- **`type: ignore[import-untyped]`** only for `haversine` (untyped third-party)
- **Ruff per-file ignores**: tests may use `assert` (S101) and magic numbers (PLR2004)
- **Builtins allowlist**: `id`, `type` — shadowing permitted
- **Inline-snapshot** formatted with ruff

## ANTI-PATTERNS (THIS PROJECT)

- **NEVER** `filter_radius()` without `square()` first — full-table scan otherwise
- **NEVER** instantiate multiple `RepeaterBook` against same `.db` file — SQLite locking
- **NEVER** abuse RepeaterBook.com API — use built-in caching (default 1hr TTL)
- **DO NOT** assume all `Repeater` fields are populated — community-maintained data, check for `None`
- **DO NOT** suppress type errors with `as any` / `@ts-ignore` / `@ts-expect-error`
- **DO NOT** add `ERA001` to fixable rules — commented-out code is intentionally unfixable
- Zero `TODO`/`FIXME`/`HACK` in source — keep it that way

## UNIQUE STYLES

- **NA vs ROW endpoint routing**: `urls_export()` auto-routes to `export.php` or `exportROW.php` based on query fields and country classification
- **Atomic cache writes**: `fetch_json()` writes to `.tmp` then renames — prevents partial reads
- **Boolean field parsing**: RepeaterBook mixes `"Yes"/"No"` strings and `1/0` ints — `BOOL_MAP` handles both
- **Decimal everywhere**: Frequencies, coordinates use `Decimal` (not float) for precision
- **Nox dynamic CI matrix**: `nox --json -l | jq` generates GitHub Actions matrix at runtime
- **Dependency groups** (not extras): tests, typing, linting, docs etc. as separate groups

## COMMANDS

```bash
# Development
nox -s test_code-3.13          # Run tests (single version)
nox -s type_check_code-3.13    # Type check (single version)
nox -s lint_files              # Lint + autofix
nox -s format_files            # Format
nox -s pre_commit              # Pre-commit hooks
nox -s docs                    # Build docs
nox -s docs_serve              # Live docs server
nox                            # Run ALL default sessions

# Direct tool access
uv run pytest                  # Tests
uv run pytest --cov            # Tests + coverage
uv run mypy                    # Type check
uv run ruff check . --fix      # Lint
uv run ruff format             # Format

# Integration tests (hits live API)
uv run pytest -m integration

# Dependencies
uv lock                        # Regenerate lockfile
uv sync                        # Install from lockfile
```

## NOTES

- `RepeaterJSON` TypedDict is intentionally permissive (`total=False`) — API payloads vary between NA and ROW endpoints
- `sponsor` field in `RepeaterJSON` is typed as `object` — undocumented API field
- `conftest.py` accesses `site._server.sockets[0]` (private API) to get ephemeral port — has `# noqa: SLF001`
- `max_count` default (3500) is API's hard limit — responses at this count may be truncated
- `.cruft.json` present — project scaffolded from a template, `src/tests/benchmarks` dirs excluded from template updates
- Commit messages must follow Conventional Commits (enforced by semantic-release)
- 100% test coverage expected
