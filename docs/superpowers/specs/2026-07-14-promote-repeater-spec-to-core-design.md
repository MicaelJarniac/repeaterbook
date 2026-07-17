# Promote the neutral repeater-spec contract into the core library

**Date:** 2026-07-14
**Status:** Approved, ready for implementation planning
**Repos touched:** `repeaterbook` (producer), `FTM-150_format` (consumer)

## Background

Upstream review feedback on the MCP PR:

> What do you think about promoting this neutral structure out of the MCP subpackage,
> and into the core lib? [...] I initially tried making the Repeater model match
> RepeaterBook API 1:1, but I do see the value in having a more neutral representation
> that might be easier to handle. I can see this neutral contract being useful outside
> the realm of MCP.

`RepeaterSpec` currently lives in `repeaterbook/mcp/models.py`, with its mapper in
`repeaterbook/mcp/mapper.py`. Neither has any dependency on MCP or FastMCP — the
placement is an accident of the order the work was done in, not a design decision.

There is already a second consumer. `FTM-150_format` translates repeater specs into
FTM-150 radio channels (`ftm150/interop/repeater_spec.py`). It deliberately does **not**
depend on `repeaterbook`: it reads specs as plain dicts and validates them against a
vendored copy of the JSON Schema (`ftm150/schemas/repeater_spec.schema.json`). The real
interface between the two projects is therefore **the JSON Schema**, not the Python
class. Any promotion must preserve that; pushing a pydantic import onto FTM-150 would be
a regression.

## Why now

The MCP subpackage is **unreleased**. Version `0.6.0` was tagged at `cfe7649`, which
predates all three MCP commits. `RepeaterSpec` therefore has no released consumers inside
`repeaterbook`, and its only external consumer is a vendored schema copy we control.

This is the cheapest moment this change will ever be available: no deprecation shims, no
migration, no breaking a published contract. After a release that ships
`repeaterbook.mcp.models`, every item below gets more expensive.

## The defect that motivates more than a file move

The contract currently discards **every** mode-specific parameter. `RepeaterSpec` carries
frequencies, tones, location, status and notes — but no `dmr_color_code`, no `p25_nac`,
no `m17_can`, no `tetra_mcc/mnc`, no `ysf_dsc`, and no `fm_bandwidth`.

`repeater_to_specs` (`mcp/mapper.py:68`) reads the eight `*_capable` booleans purely as a
fan-out signal and throws away the parameters hanging off them. The consequence is that
the contract can emit a spec with `mode: "DMR"` that **cannot program a DMR radio**,
because the color code needed to do so was discarded one function earlier.

This is currently invisible: FTM-150 is FM-only and rejects every digital mode at
`repeater_spec.py:71`, so the contract's lossy edge has never been exercised. Promoting
the contract to core without fixing it would bake the loss into a public artifact.

A second, live instance of the same problem: FTM-150's `apply_specs` hardcodes
`ch.narrow = False` (`repeater_spec.py:141`), so it always programs wide FM. RepeaterBook
*has* `fm_bandwidth` on `Repeater` — the information exists, and dies at the contract
boundary. Fixing the contract fixes a real bug in a real consumer.

## Design

### 1. Placement

New module `src/repeaterbook/spec.py` holds the whole contract: `RepeaterMode`, the param
models, `RepeaterSpec`, `repeater_to_specs`, and the schema helpers.

| Before | After |
|---|---|
| `repeaterbook/mcp/models.py` | **deleted** — contents move to `repeaterbook/spec.py` |
| `repeaterbook/mcp/mapper.py` | **deleted** — contents move to `repeaterbook/spec.py` |
| `src/repeaterbook/mcp/schemas/repeater_spec.schema.json` | `src/repeaterbook/schemas/repeater_spec.schema.json` |
| console script → `repeaterbook.mcp.models:write_schema` | → `repeaterbook.spec:write_schema` |

`mcp/service.py`, `mcp/server.py` and `mcp/__init__.py` import from `repeaterbook.spec`.
No back-compat shim: the modules being deleted are unreleased.

The contract goes in its own module rather than `models.py` because `models.py` already
carries the SQL table, the wire TypedDicts, the query models and the CSV shape (~380
lines); and because the contract is now a *published artifact* with a JSON Schema, which
earns it a file.

Hatchling includes package data by default, so relocating the schema directory needs no
`pyproject.toml` packaging change — only the console-script target changes.

### 2. The contract becomes a discriminated union

One spec is one programmable channel, and a channel has already committed to exactly one
mode. That means exactly one cluster of mode parameters is live and the other seven are
unreachable by construction — the shape is a tagged union, and modelling it as one lets
the JSON Schema *document the mode taxonomy* instead of merely transporting values.

```python
class FmParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bandwidth_khz: Decimal | None = None

class DmrParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dmr_id: str | None = None
    color_code: str | None = None

# ... P25Params(nac), M17Params(can), TetraParams(mcc, mnc),
#     FusionParams(digital_id_uplink, digital_id_downlink, dsc)
#     DStarParams(), NxdnParams()   <- intentionally empty, see below

class BaseSpec(BaseModel):
    name: str
    callsign: str | None
    rx_frequency_mhz: Decimal
    tx_frequency_mhz: Decimal
    ctcss_tx_hz: Decimal | None
    ctcss_rx_hz: Decimal | None
    dcs_code: str | None
    latitude: Decimal
    longitude: Decimal
    distance_km: float | None
    operational_status: Status
    use: Use
    band: str | None
    notes: str | None
    last_update: date
    source: str = "repeaterbook"
    source_id: str

class FmSpec(BaseSpec):
    mode: Literal[RepeaterMode.FM] = RepeaterMode.FM
    params: FmParams = FmParams()

class DmrSpec(BaseSpec):
    mode: Literal[RepeaterMode.DMR] = RepeaterMode.DMR
    params: DmrParams = DmrParams()

# ... one thin subclass per mode

RepeaterSpec: TypeAlias = Annotated[
    FmSpec | DmrSpec | DStarSpec | FusionSpec
    | P25Spec | NxdnSpec | TetraSpec | M17Spec,
    Field(discriminator="mode"),
]
```

Wire shape (verified against pydantic, not assumed):

```json
{
  "name": "VK4RDM",
  "mode": "DMR",
  "rx_frequency_mhz": "439.0",
  "tx_frequency_mhz": "434.0",
  "params": { "dmr_id": "5051", "color_code": "1" }
}
```

The generated JSON Schema is a `oneOf` with `discriminator.propertyName == "mode"`.

**`extra="forbid"` on the param models is load-bearing, not stylistic.** Without it,
pydantic silently ignores unknown keys and the generated schema omits
`additionalProperties: false` — so *both* the model and FTM-150's `jsonschema.validate`
accept an FM spec carrying a DMR color code. With it, both reject it. This was verified
empirically; the "illegal by construction" property does not hold otherwise.

**Empty param models for D-STAR and NXDN are deliberate.** RepeaterBook's export carries
`"D-Star": Yes/No` and `"NXDN": Yes/No` with no accompanying node or RAN keys
(`RepeaterJSON` in `models.py`). The empty arm honestly states "this mode is supported and
we have no parameters for it," which is the truth. It also gives those modes a place to
grow if RepeaterBook ever adds the fields.

**Two field cleanups**, taken now because the contract is being rewritten anyway:

- `operational_status` and `use` are currently `str` holding `.name` of the core enums.
  Type them as `Status` and `Use`. The JSON is unchanged (still `"ON_AIR"`, `"OPEN"`), but
  the schema gains an enum constraint, and the producer can no longer emit a typo.
- `distance_km` stays, but is documented as a **search-context** field: it is the distance
  from a radius-query centre and is `null` for any spec not produced by such a query. It
  is not an intrinsic property of the repeater.

### 3. `Repeater` gains derived accessors; its storage is untouched

The eight `*_capable` booleans and their sixteen parameter columns stay exactly as they
are. They are `Field(index=True)` and `queries.py` filters on them; flat columns are the
correct shape for a SQL table, and they preserve the 1:1-with-the-API fidelity upstream
deliberately chose. **No migration.**

What `Repeater` gains is a *read-only, derived* view — the same param models the contract
uses, returned from properties gated on the capability flag:

```python
class Repeater(SQLModel, table=True):
    # ... all columns unchanged ...

    @property
    def dmr(self) -> DmrParams | None:
        if not self.dmr_capable:
            return None
        return DmrParams(dmr_id=self.dmr_id, color_code=self.dmr_color_code)

    @property
    def modes(self) -> frozenset[RepeaterMode]: ...
```

This was verified empirically against the installed SQLModel: a `@property` on a
`table=True` class is invisible to SQLAlchemy's mapper and to pydantic's field collection.
Adding it changes **nothing** observable downstream:

| Surface | Effect |
|---|---|
| SQL columns / emitted DDL | unchanged — no migration |
| `model_fields` | unchanged |
| `model_dump()` | unchanged — identical JSON for existing consumers |
| `model_validate()` (used by `csv_export.py:33`, `services.py:207`) | unchanged |

The only theoretical hazard is a downstream subclass that already defines `.dmr`/`.fm`;
no column is named that today, so nothing has reason to.

Placing the accessors here rather than inside the mapper costs the *same* amount of code —
something must say "`dmr_color_code` belongs to DMR" exactly once either way. The
difference is reach: on `Repeater`, every library user gets the neutral view without
calling a spec-building function, which is the most direct answer to "useful outside the
realm of MCP." `repeater_to_specs` then collapses to iterating `rep.modes` and calling the
matching accessor.

### 4. `Mode` and `RepeaterMode` stay separate

They look like duplicates and are not:

- `Mode` (`ANALOG, DMR, NXDN, P25, TETRA`) is the RepeaterBook API's `mode=` **filter**
  vocabulary. Its values map to the `ModeJSON` wire literals. It is used in exactly one
  place: `ExportQuery.modes`.
- `RepeaterMode` (`FM, DMR, DSTAR, FUSION, P25, NXDN, TETRA, M17`) is the **capability**
  vocabulary, derived from the `*_capable` columns and used to program radios.

The overlap is asymmetric: the API lets you *search* for TETRA but not Fusion; a stored
repeater can *be* Fusion but cannot be filtered for server-side. Merging them would
produce an enum that advertises filters the API does not accept. Keep both; note the
distinction in the PR, since "why are there two?" is the obvious reviewer question.

### 5. FTM-150 consumer changes

1. Re-vendor `ftm150/schemas/repeater_spec.schema.json` from the new generator.
2. Update the two fixtures in `tests/test_schema_contract.py` to carry `params`.
3. `spec_to_fields` reads `spec["params"].get("bandwidth_khz")` and sets `ch.narrow`
   accordingly, replacing the hardcoded `ch.narrow = False` at `repeater_spec.py:141`.
   Absent/unknown bandwidth keeps today's wide default.

Step 3 is the point of the whole exercise: information RepeaterBook already had, which
the contract was silently dropping, now reaches the radio. FTM-150 remains stdlib-only
and takes no dependency on `repeaterbook`.

### 6. Schema publication and drift

`write_schema()` and `schema_path()` move to `repeaterbook.spec`, and the existing
producer-side drift test (`tests/mcp/test_schema_contract.py`, which asserts the committed
schema equals the generated one) moves to `tests/test_spec.py`. It keeps the producer
honest against its own published artifact.

**Decision: no contract version field.** Considered and rejected as unnecessary weight.
The tradeoff, recorded deliberately: a stale FTM-150 handed a newer spec has no way to
know the contract generation changed. In practice it reads specs as dicts with `.get()`,
so it degrades to *ignoring* an unknown `params` shape rather than crashing or
misprogramming. If a future contract change is semantically breaking rather than additive,
revisit this.

## Non-goals

- No version/`spec_version` field (see above).
- No `csv_export` rework. `RepeaterCSV` and `csv_row_to_model` are untouched.
- No storage restructuring: no JSON columns, no side tables, no migration.
- No change to `Mode`, `ExportQuery`, or the query layer.
- No rename to `ChannelSpec`. It is arguably the more honest name — one spec is one
  channel, and a multi-mode repeater fans out to several — but it would force a
  coordinated rename across FTM-150's module, schema and tests, and adds a bikeshed to a
  PR already asking the maintainer for a structural change. Considered and declined.

## Testing

**repeaterbook**

- `tests/test_spec.py` (from `tests/mcp/test_mapper.py` + `test_models.py` +
  `test_schema_contract.py`): tone parsing, band lookup, mode fan-out, one spec per
  capability, FM fallback when no capability is set.
- Each mode's params are populated from the right columns (a DMR spec carries the color
  code; an FM spec carries the bandwidth).
- A mode/params mismatch is rejected by the model **and** by the generated schema via
  `jsonschema` — this guards the `extra="forbid"` property, which is easy to lose in a
  refactor and silent when lost.
- Committed schema equals generated schema (moved drift test).
- `Repeater` accessors: return `None` when the capability flag is false; populated
  otherwise; `modes` matches the capability set.
- Regression guard: adding the accessors leaves `model_dump()`, `model_fields` and the
  emitted DDL unchanged.
- `repeaterbook-write-schema` console script resolves to `repeaterbook.spec:write_schema`.

**FTM-150**

- Existing contract test passes against the re-vendored schema with `params`-carrying
  fixtures.
- A narrow-FM spec (`bandwidth_khz: 12.5`) produces `ch.narrow = True`; a wide or absent
  bandwidth produces `ch.narrow = False`.
- Digital-mode specs still raise `Unrepresentable` (FTM-150 is FM-only) — now with their
  params present, which must not change the rejection.

## Open questions for the upstream maintainer

Framed for the PR discussion rather than settled here:

1. Is `repeaterbook.spec` the module name they want, or would they prefer `contract.py` /
   `channel.py`?
2. Do they want the `Repeater` accessors, or would they rather the mode-grouping knowledge
   stay in `repeater_to_specs`? Same code either way; the accessors are the stronger read
   of "useful outside the realm of MCP", and are verified additive.
3. Is `RepeaterSpec` the right name for a thing that is really one *channel*? This design
   declines the rename (see Non-goals), but surfaces it because it is free now and
   expensive after a release — if the maintainer wants `ChannelSpec`, this is the moment
   to say so.
