"""FastMCP server exposing RepeaterBook lookup tools to agents."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "get_repeater",
    "main",
    "mcp",
    "search_repeaters",
    "sync_repeaters",
)

import os

import attrs
from anyio import Path
from mcp.server.fastmcp import FastMCP
from pycountry import countries
from pycountry.db import Country  # noqa: TC002

from repeaterbook.database import RepeaterBook
from repeaterbook.exceptions import RepeaterBookUnauthorizedError
from repeaterbook.mcp import service
from repeaterbook.mcp.models import (
    RepeaterMode,
    RepeaterSpec,
)
from repeaterbook.models import ExportQuery, Mode
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.utils import LatLon

mcp = FastMCP("repeaterbook")

_MODE_TO_API: dict[RepeaterMode, Mode] = {
    RepeaterMode.FM: Mode.ANALOG,
    RepeaterMode.DMR: Mode.DMR,
    RepeaterMode.P25: Mode.P25,
    RepeaterMode.NXDN: Mode.NXDN,
    RepeaterMode.TETRA: Mode.TETRA,
    # DSTAR / FUSION / M17: no RepeaterBook API mode filter -> local filtering only
}


@attrs.frozen
class _Context:
    """Shared API client + DB built from environment configuration."""

    api: RepeaterBookAPI
    db: RepeaterBook


_context: _Context | None = None


def _get_context() -> _Context:
    global _context  # noqa: PLW0603
    if _context is None:
        working_dir = Path(os.environ.get("REPEATERBOOK_WORKING_DIR", "."))
        contact = os.environ.get("REPEATERBOOK_APP_CONTACT", "unknown@example.com")
        token = os.environ.get("REPEATERBOOK_APP_TOKEN") or None
        api = RepeaterBookAPI(
            app_contact=contact, app_token=token, working_dir=working_dir
        )
        db = RepeaterBook(working_dir=working_dir)
        db.init_db()
        _context = _Context(api=api, db=db)
    return _context


def _reset_context_for_tests() -> None:
    """Clear the cached context so env changes take effect (tests only)."""
    global _context  # noqa: PLW0603
    _context = None


def _api_modes(modes: list[str] | None) -> frozenset[Mode]:
    """Translate RepeaterMode names into the library's API-filterable Modes.

    Unknown names raise ValueError. Modes the API can't scope (DSTAR/FUSION/M17)
    are simply omitted from the result; local filtering still applies to them.
    """
    if not modes:
        return frozenset()
    result: set[Mode] = set()
    for name in modes:
        try:
            rmode = RepeaterMode(name)
        except ValueError as exc:
            valid = ", ".join(m.value for m in RepeaterMode)
            msg = f"unknown mode: {name!r}; valid modes: {valid}"
            raise ValueError(msg) from exc
        api = _MODE_TO_API.get(rmode)
        if api is not None:
            result.add(api)
    return frozenset(result)


def _build_query(
    country: str | None,
    state_id: str | None,
    region: str | None,
    modes: list[str] | None,
) -> ExportQuery:
    """Build an ExportQuery from a scope, raising ValueError on bad input."""
    country_set: frozenset[Country] = frozenset()
    if country is not None:
        found = countries.get(name=country)
        if found is None:
            msg = f"unknown country: {country!r}"
            raise ValueError(msg)
        country_set = frozenset({found})
    return ExportQuery(
        countries=country_set,
        state_ids=frozenset({state_id}) if state_id else frozenset(),
        regions=frozenset({region}) if region else frozenset(),
        modes=_api_modes(modes),
    )


@mcp.tool()
async def sync_repeaters(
    country: str | None = None,
    state_id: str | None = None,
    region: str | None = None,
    modes: list[str] | None = None,
) -> int:
    """Download repeaters for a region into the local store; returns the count."""
    ctx = _get_context()
    query = _build_query(country, state_id, region, modes)
    try:
        return await service.sync(ctx.api, ctx.db, query)
    except RepeaterBookUnauthorizedError as exc:
        msg = "RepeaterBook auth failed; check REPEATERBOOK_APP_TOKEN"
        raise ValueError(msg) from exc


@mcp.tool()
async def search_repeaters(  # noqa: PLR0913
    lat: float,
    lon: float,
    radius_km: float,
    country: str | None = None,
    state_id: str | None = None,
    region: str | None = None,
    bands: list[str] | None = None,
    modes: list[str] | None = None,
    status: list[str] | None = None,
    use: list[str] | None = None,
) -> list[RepeaterSpec]:
    """Find nearby repeaters as repeater-specs, auto-syncing the region."""
    ctx = _get_context()
    if country or state_id or region:
        await sync_repeaters(country, state_id, region, modes)
    elif not ctx.db.query():
        msg = "no local data; provide a country/region or call sync_repeaters first"
        raise ValueError(msg)
    return service.search(
        ctx.db,
        LatLon(lat, lon),
        radius_km,
        bands=bands,
        modes=modes,
        statuses=status,
        uses=use,
    )


@mcp.tool()
async def get_repeater(source_id: str) -> list[RepeaterSpec]:
    """Return repeater-specs for a single repeater by its source id."""
    ctx = _get_context()
    return service.get_by_id(ctx.db, source_id)


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
