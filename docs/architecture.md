# Architecture

How the **RepeaterBook Python Client** is put together, and why.

This page explains structure and rationale. It deliberately does not restate
function signatures or field lists — those live in the
[API Reference](api.md), generated from the source, and duplicating them here
is how this page previously drifted out of date.

## The shape of the problem

RepeaterBook publishes community-maintained repeater data through an HTTP API
that has a few awkward properties, and most of this library's design follows
from them:

- **Two endpoints with different payloads.** North America is served by
  `export.php`, the rest of the world by `exportROW.php`. They disagree about
  which fields exist.
- **Responses are capped.** The API truncates at 3500 results and does not say
  so. A query that hits the cap silently returns a partial answer.
- **Rows are uneven.** Fields go missing, booleans arrive as either `"Yes"`/`"No"`
  or `1`/`0`, and an occasional row cannot be modelled at all.
- **Requests must be authenticated and identified.** Since RepeaterBook's
  2026-03-03 API policy, every export needs a per-user token *and* a
  `User-Agent` matching the application the token was issued for.
- **It is somebody else's server.** Repeated identical queries are rude and
  slow.

So the library caches aggressively, tolerates bad rows, routes queries to the
right endpoint, and keeps a local database you can query offline.

## Layers

```
                    ┌────────────────────┐
   Your code ──────►│  repeaterbook      │   Repeater, RepeaterBook,
                    │  (public exports)  │   exception hierarchy
                    └─────────┬──────────┘
                              │
      ┌───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
┌───────────┐          ┌────────────┐          ┌────────────┐
│ services  │          │  database  │          │  queries   │
│ API client│          │  SQLite    │          │  filters   │
└─────┬─────┘          └──────┬─────┘          └──────┬─────┘
      │  RepeaterBook.com            SQLModel /       │
      │  HTTP + file cache           SQLAlchemy       │
      ▼                              ▼                ▼
┌──────────────────────────────────────────────────────────┐
│ models — Repeater (ORM row) + the API's JSON TypedDicts  │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │     spec      │  RepeaterSpec: the neutral,
                   │  public wire  │  published output contract
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │      mcp      │  optional; agent-facing tools
                   └───────────────┘
```

Two things are worth reading off that diagram.

**`models.Repeater` is the internal shape; `spec.RepeaterSpec` is the external
one.** `Repeater` mirrors RepeaterBook's own columns, warts included.
`RepeaterSpec` is what the library publishes to consumers. Keeping them
separate means RepeaterBook's quirks are not baked into the contract.

**The `mcp` subpackage is a consumer of the library, not part of its core.** It
lives behind an optional extra and depends inward; nothing in the core imports
it.

## Modules

| Module | Responsibility |
|---|---|
| `models.py` | The `Repeater` ORM row, the API's JSON `TypedDict`s, and `ExportQuery` |
| `services.py` | HTTP client, caching, endpoint routing, JSON → `Repeater` conversion |
| `database.py` | SQLite persistence: populate, query, truncate |
| `queries.py` | Composable SQL filter builders (bounding box, band) plus the in-memory radius filter |
| `spec.py` | `RepeaterSpec`: the neutral output contract and its published JSON Schema |
| `utils.py` | Geographic types and the constrained numeric aliases used across the contract |
| `exceptions.py` | The error hierarchy |
| `na_states.py` | RepeaterBook's bespoke North American `state_id` vocabulary |
| `csv_export.py` | Reads RepeaterBook's CSV export format into `Repeater` rows |
| `mcp/` | Optional MCP server exposing the library to agents |

### models

`Repeater` is a SQLModel class, so one declaration is both the Pydantic
validation model and the SQLAlchemy table.

Two decisions matter here:

**The primary key is composite — `state_id` plus `repeater_id`.** RepeaterBook
numbers repeaters within a state, so neither half is unique alone. There is no
surrogate `id` column. This is what makes `populate()` idempotent: re-importing
overlapping regions updates rows rather than duplicating them.

**Frequencies and coordinates are `Decimal`, never `float`.** Repeater
frequencies are exact quantities where a binary rounding error is a real bug,
and the same reasoning extends to coordinates. This is why they serialize as
decimal *strings* on the wire, and why you must cast before handing them to
numeric libraries like pandas or numpy.

The JSON payloads are described by `TypedDict`s whose keys match the API
literally — `"State ID"`, `"Rptr ID"`, spaces and all. `RepeaterJSON` is
declared `total=False` on purpose: every key is optional because the two
endpoints genuinely disagree about which ones they send.

`Status`, `Use`, and `Mode` are plain enums built with `auto()`, so their
`.value` is an integer with no external meaning. Use `.name` for a label — and
see [spec](#spec) for why the published contract uses separate string enums.

### services

The API client is a frozen attrs class holding the base URL, the application
identity (name, version, contact), an optional token, and cache settings.

**Identity is not yours to change.** RepeaterBook matches an approved
application's `User-Agent` literally, so the defaults correspond to this
library's registration — App #114. Overriding any part of it, even the contact
address, invalidates a token issued against that registration. The version in
the `User-Agent` is hard-coded rather than read from the package version,
precisely so ordinary releases don't break approved tokens.

The token is held as a `SecretStr` and the attrs field is `repr=False`, so it
stays out of logs and tracebacks by two independent mechanisms.

#### Endpoint routing

`urls_export()` decides which endpoint(s) a query needs, and returns a *set* of
URLs — a query with no routing hints legitimately fans out to both:

- NA-only fields (`state_id`, `county`, `emcomm`, `stype`) → North America only
- ROW-only fields (`region`) → rest of world only
- Countries given → whichever endpoints those countries fall under
- No hints → both

#### Caching

`fetch_json()` keys the cache on a SHA-256 of the full request URL, storing
`api_cache_<hash>.json` under `.repeaterbook_cache/` inside the working
directory. Because the key is the URL, a query that fans out to both endpoints
produces two entries.

Writes go to a `.tmp` file and are then renamed. The rename is atomic, so a
concurrent reader either sees the previous complete entry or the new complete
one — never a half-written file.

A cache entry that is missing or unparseable is treated as a miss and refetched.
(`RepeaterBookCacheError` exists in the hierarchy for cache failures but is not
currently raised.)

#### Row-level resilience

A row that cannot be modelled — a zero input frequency, an out-of-range
coordinate — is a data problem, not a response problem. `json_to_models()`
therefore isolates failures to the row that caused them, rather than letting one
bad record discard a good response.

`ROW_ERRORS` is deliberately narrow (`ValueError`, `InvalidOperation`,
`TypeError`, `LookupError`) rather than a bare `Exception`: bad *data* is
skipped, but a bug in the mapping code still surfaces loudly instead of quietly
costing the caller records.

Callers choose the policy:

- **Default (lenient)** — skip and warn. Pass `skipped=[]` to collect a
  `RepeaterBookRowError` per dropped row, each carrying the raw payload and a
  `label` like `48:24371 (W5AW)`.
- **`strict=True`** — raise on the first bad row.

### database

`RepeaterBook` is a thin, frozen wrapper over a SQLModel engine. It owns a
working directory and a database filename; the engine is a `cached_property`,
so it is built once on first use and not at construction.

`populate()` merges rather than inserts, keying on the composite primary key,
which makes repeated imports of overlapping regions safe. Sessions are opened
per call and not exposed as attributes — when you need a statement the wrapper
cannot express, construct a `Session` against its `engine` yourself.

Schema creation is explicit (`init_db()`), and `populate()` calls it for you.

!!! warning "One handle per database file"
    SQLite locking makes concurrent `RepeaterBook` instances against the same
    file a source of intermittent failures. Share one.

### queries

Query helpers return SQLAlchemy boolean expressions, so they compose with each
other and with anything you write by hand.

The important structural point is the **two-stage geographic search**:

```
All repeaters
     │  square(radius) — indexed SQL bounding box, runs in the DB
     ▼
Candidates
     │  filter_radius(...) — haversine per row, runs in Python
     ▼
Results, sorted by true distance
```

`square()` is a cheap, indexed pre-filter over a bounding box. `filter_radius()`
then computes real great-circle distances over that small candidate set and
sorts by them. Running `filter_radius()` alone is a full-table scan with a
trigonometric computation per row — always pre-filter with `square()`.

`Bands` carries each band's bounds as a `Decimal` pair. `BandName` mirrors it as
a plain string vocabulary, because the bounds render in JSON Schema as a
meaningless two-number array for a consumer that only wants to name a band; a
test keeps the two in step.

### spec

`RepeaterSpec` is the library's published output contract, and the reason it
exists separately from `Repeater` is worth spelling out:

- **One spec is one programmable radio channel.** A multi-mode repeater expands
  to one spec per mode, which is what a radio actually needs.
- **`params` is a union discriminated on `mode`**, with `extra="forbid"` on each
  variant, so a mode/params mismatch is impossible by construction. The
  top-level `mode` is a computed field derived from `params`, so the two cannot
  disagree.
- **Its enums are `StrEnum`s.** The core `Status`/`Use` use `auto()`, whose
  integers would otherwise leak into a published contract. `RepeaterStatus` and
  `RepeaterUse` mirror them as strings.
- **Linking node IDs sit at the top level**, not in `params`: AllStar, EchoLink,
  IRLP and Wires-X are not RF modes and don't change how a channel is
  programmed.

The mapper also normalizes two RepeaterBook habits. Tone fields mix CTCSS
frequencies and DCS codes in one string, so `parse_tone()` splits them. Absent
linking nodes are spelled variously as a missing key, an empty string, or the
literal `"0"`; `parse_node_id()` folds all of them to `None`, so a non-null node
field genuinely implies a dialable node.

The JSON Schema is generated from the model in *serialization* mode — validation
mode would omit the computed `mode` field — and committed to the repository. A
pre-commit hook and a CI check regenerate it, so the published contract cannot
drift from the model.

### na_states

RepeaterBook scopes North American queries with a `state_id` drawn from its own
vocabulary: two-digit FIPS codes for the US, and undocumented `CA##`/`MX##`
numbering for Canada and Mexico. These are not ISO 3166-2 and cannot be derived
from it, so a general-purpose library is no help.

This module exists because the values are both unforgiving and undiscoverable:
`"6"` is not `"06"` and returns an empty result rather than an error, and
because responses truncate at 3500 rows you cannot reliably learn the
identifiers by downloading a country and reading them back.

## Data flow

A typical session runs in two independent phases.

**Ingest** — `download()` builds the URL set, fetches each (cache first),
validates the envelope, converts rows to `Repeater` models while skipping
unmodellable ones, and hands back a list. `populate()` merges that into SQLite.

**Query** — `query()` runs your composed filters in SQL; `filter_radius()`
refines geographically in Python; `repeater_to_specs()` converts to the public
`RepeaterSpec` shape if you need the neutral contract.

The phases are separate on purpose: once populated, querying needs no network
access at all.

## Error model

Everything inherits from `RepeaterBookError`, so one `except` clause catches the
library.

```
RepeaterBookError
├── RepeaterBookAPIError            HTTP 4xx/5xx, or a 200 whose body reports an error
│   ├── RepeaterBookUnauthorizedError   401 — missing/invalid token
│   ├── RepeaterBookForbiddenError      403 — User-Agent or scope denied
│   └── RepeaterBookRateLimitError      429 — carries retry_after
├── RepeaterBookValidationError     malformed response or data
│   └── RepeaterBookRowError            one export row; carries the raw row and a label
└── RepeaterBookCacheError         reserved for cache failures; not currently raised
```

Because the HTTP-status errors are subclasses of `RepeaterBookAPIError`, order
your `except` clauses most-specific first.

## MCP server

The optional `mcp` subpackage exposes three tools — `sync_repeaters`,
`search_repeaters`, `get_repeater` — over the Model Context Protocol.

It is split in two: `server.py` handles protocol concerns, configuration, and
tool declarations, while `service.py` orchestrates the library. The split keeps
the orchestration testable without a protocol client.

Configuration comes from `REPEATERBOOK_*` environment variables. The token is
required and validated at startup, so a misconfigured server fails immediately
rather than advertising tools that error on first use.

Two details are specific to serving an agent rather than a human. Truncation is
reported *in the result* — the library logs it, but a log line is invisible to
an MCP caller, so `SyncResult` carries a `truncated` flag and advice on
narrowing scope. And blocking work (SQLite reads plus the haversine pass) is
dispatched to a worker thread so concurrent tool calls aren't serialized behind
it.

## Testing

Tests mirror the source layout one-to-one, with `tests/mcp/` covering the
optional subpackage and `tests/integration/` holding tests that hit the live
API. Integration tests are marked `@pytest.mark.integration` and excluded by
default; `tests/conftest.py` spins up a local aiohttp server so the HTTP paths
can be exercised without the network.

The project targets 100% coverage.

```bash
uv run pytest              # unit tests
uv run pytest --cov        # with coverage
uv run pytest -m integration   # live API
```

## Extending

Query helpers are ordinary functions returning SQLAlchemy expressions, so your
own compose with the built-ins:

```python
from repeaterbook import Repeater
from repeaterbook.queries import square

def callsign_prefix(prefix: str):
    """Match repeaters whose callsign starts with a prefix."""
    return Repeater.callsign.startswith(prefix)

results = rb.query(square(radius), callsign_prefix("W6"))
```

For a different data source, target `RepeaterSpec` rather than `Repeater`: it is
the source-agnostic contract, and reusing it means existing consumers work
unchanged.

## Related

- [Usage Guide](usage.md) — comprehensive examples
- [MCP Server](mcp.md) — running the agent-facing server
- [API Reference](api.md) — generated symbol documentation
- [FAQ](faq.md) — troubleshooting
