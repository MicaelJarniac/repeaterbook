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
| `REPEATERBOOK_WORKING_DIR` | Where the SQLite DB + cache live | `.` |
| `REPEATERBOOK_APP_CONTACT` | Contact string for the API `User-Agent` (required by terms) | `unknown@example.com` |
| `REPEATERBOOK_APP_TOKEN` | Optional API token | unset |

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
- `search_repeaters(lat, lon, radius_km, country?, state_id?, region?, bands?, modes?, status?, use?) -> [RepeaterSpec]` — nearby repeaters, distance-sorted; auto-syncs when a scope is given.
- `get_repeater(source_id) -> [RepeaterSpec]` — one repeater by `"state_id:repeater_id"`.

Filter values: bands use library enum names `M_2`/`CM_70`/…, status `ON_AIR`/`OFF_AIR`/`UNKNOWN`, use `OPEN`/`PRIVATE`/`CLOSED`. `modes` uses a single vocabulary for both tools: `FM`/`DMR`/`DSTAR`/`FUSION`/`P25`/`NXDN`/`TETRA`/`M17`. For `sync_repeaters`, DSTAR/FUSION/M17 don't narrow the server-side download (the RepeaterBook API has no filter for them) and are instead filtered locally during `search_repeaters`.

## The repeater-spec contract

Tools return **repeater-spec** rows — a neutral, source-agnostic shape carrying
absolute rx/tx frequencies (the consuming radio derives duplex/offset). The JSON
Schema is published at `repeaterbook/mcp/schemas/repeater_spec.schema.json`.

### Regenerating the schema

The schema is generated from the `RepeaterSpec` model. After changing the model,
regenerate the committed file from your editable dev environment with:

```bash
repeaterbook-write-schema      # or: nox -s schema -- --write
```

A pre-commit hook regenerates it automatically when you commit a change to
`models.py` or the schema file, and CI fails if the committed schema is out of
date.
