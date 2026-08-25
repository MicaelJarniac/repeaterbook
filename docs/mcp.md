# RepeaterBook MCP server

An optional [Model Context Protocol](https://modelcontextprotocol.io) server —
built on [FastMCP 3](https://gofastmcp.com) — that exposes RepeaterBook lookup to
agents. Install with the extra:

```bash
pip install "repeaterbook[mcp]"
```

## Configuration (environment)

| Variable | Purpose | Default |
|---|---|---|
| `REPEATERBOOK_WORKING_DIR` | Where the SQLite DB + cache live. Created if missing; a leading `~` is expanded. | `.` |
| `REPEATERBOOK_APP_CONTACT` | Contact email for the API `User-Agent`. **Required** | — |
| `REPEATERBOOK_APP_TOKEN` | Optional API token | unset |

`REPEATERBOOK_APP_CONTACT` has no default: RepeaterBook's terms of use oblige
callers to identify themselves, and a placeholder address would quietly
misidentify every request. The server refuses to start without a valid one.

## Register with an MCP client

```json
{
  "mcpServers": {
    "repeaterbook": {
      "command": "repeaterbook-mcp",
      "env": {
        "REPEATERBOOK_WORKING_DIR": "~/.repeaterbook",
        "REPEATERBOOK_APP_CONTACT": "you@example.com"
      }
    }
  }
}
```

## Tools

- `sync_repeaters(country?, state_id?, region?, modes?) -> int` — download a region into the local store.
- `search_repeaters(lat, lon, radius_km, country?, state_id?, region?, bands?, modes?, status?, use?, refresh?) -> [RepeaterSpec]` — nearby repeaters, distance-sorted.
- `get_repeater(source_id) -> [RepeaterSpec]` — one repeater by `"state_id:repeater_id"`.

Every filter is an enum, so its allowed values ride in the tool schema and a
client sees them without consulting these docs:

| Filter | Values |
|---|---|
| `bands` | `M_10` `M_6` `M_4` `M_2` `CM_70` `CM_33` `CM_23` `CM_13` `CM_3` |
| `modes` | `FM` `DMR` `DSTAR` `FUSION` `P25` `NXDN` `TETRA` `M17` |
| `status` | `ON_AIR` `OFF_AIR` `UNKNOWN` |
| `use` | `OPEN` `PRIVATE` `CLOSED` |

`modes` is one vocabulary across both tools. For `sync_repeaters`, DSTAR/FUSION/M17
don't narrow the server-side download (the RepeaterBook API has no filter for
them) and are instead filtered locally during `search_repeaters`.

### Syncing

`search_repeaters` reads the local store. When you pass a country/state/region
and the store is empty, it downloads that scope first; otherwise it searches
what's already there. Pass `refresh=True` to force a re-download — syncing
re-parses the whole regional payload and re-merges thousands of rows, so it is
not something to do on every search.

## The repeater-spec contract

Tools return **repeater-spec** rows — a neutral, source-agnostic shape carrying
absolute rx/tx frequencies (the consuming radio derives duplex/offset). The JSON
Schema is published at `repeaterbook/schemas/repeater_spec.schema.json`.

### Spec wire shape

Each spec is one programmable channel. Mode-specific fields live in `params`,
which is a union discriminated on its own `mode` field:

```json
{
  "name": "VK4RDM",
  "rx_frequency_mhz": "439.000000",
  "tx_frequency_mhz": "434.000000",
  "ctcss_tx_hz": null,
  "ctcss_rx_hz": null,
  "dcs_tx_code": null,
  "dcs_rx_code": null,
  "latitude": "-27.470000",
  "longitude": "153.020000",
  "distance_km": "12.345",
  "operational_status": "ON_AIR",
  "use": "OPEN",
  "last_update": "2026-01-01T00:00:00",
  "mode": "DMR",
  "params": { "mode": "DMR", "dmr_id": "5051", "color_code": "1" }
}
```

Uplink and downlink tones are carried separately — `ctcss_tx_hz`/`dcs_tx_code`
for the uplink, `ctcss_rx_hz`/`dcs_rx_code` for the downlink. A repeater can use
a different tone in each direction, so collapsing them into one field would
silently drop one.

Frequencies, tones, coordinates and distances are `Decimal`, serialized as
decimal **strings** to avoid binary-float rounding. Each is a named type with a
range constraint, emitted once under `$defs` (`FrequencyMHz`, `CtcssToneHz`,
`LatitudeDeg`, `LongitudeDeg`, `DistanceKm`) and referenced by every field that
uses it, so a consumer can generate one type per quantity.

`mode` appears twice by design. The copy inside `params` is the discriminator —
it is what makes an FM channel carrying a DMR colour code invalid against the
schema. The top-level copy is computed from `params.mode`, so the two are always
consistent, and dict consumers can read `spec["mode"]` without descending into
`params`.

One consequence: JSON Schema expresses no constraint tying the two `mode`
values together, so the published schema does not cross-check them and a
hand-written payload with contradictory `mode` and `params.mode` will
validate. Payloads this library produces are consistent by construction,
and payloads it parses ignore the top-level value and recompute it from
`params.mode`.

The schema is generated in Pydantic's **serialization** mode. `mode` is a
computed field, and Pydantic emits computed fields only into the serialization
schema — the default validation mode would publish a contract missing a key that
every response actually carries.

### Regenerating the schema

The schema is generated from the `RepeaterSpec` model. After changing the model,
regenerate the committed file from your editable dev environment with:

```bash
repeaterbook-write-schema      # or: nox -s schema -- --write
```

A pre-commit hook regenerates it automatically when you commit a change to
`spec.py`, `utils.py`, or the schema file. CI runs `nox -s schema`, which fails
if the committed file has drifted from the model.
