"""FastMCP server exposing RepeaterBook lookup tools to agents."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "RepeaterBookSettings",
    "get_repeater",
    "main",
    "mcp",
    "search_repeaters",
    "sync_repeaters",
)

import pathlib
from functools import lru_cache
from typing import Annotated

import attrs
from anyio import Path, to_thread
from fastmcp import FastMCP
from pycountry import countries
from pycountry.db import Country  # noqa: TC002
from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from repeaterbook.database import RepeaterBook
from repeaterbook.exceptions import RepeaterBookUnauthorizedError
from repeaterbook.mcp import service
from repeaterbook.models import ExportQuery, Mode
from repeaterbook.queries import BandName  # noqa: TC001
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.spec import (
    RepeaterMode,
    RepeaterSpec,
    RepeaterStatus,
    RepeaterUse,
)
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


class RepeaterBookSettings(BaseSettings):
    """MCP server configuration, read from ``REPEATERBOOK_*`` environment variables."""

    model_config = SettingsConfigDict(env_prefix="REPEATERBOOK_")

    working_dir: pathlib.Path = pathlib.Path()
    """Where the SQLite DB and HTTP cache live. Created on first use."""

    app_contact: EmailStr
    """Contact address for the API User-Agent.

    Required: RepeaterBook's terms of use oblige callers to identify
    themselves, so there is no honest default to fall back to.
    """

    app_token: SecretStr | None = None
    """Optional RepeaterBook API token."""

    @field_validator("working_dir")
    @classmethod
    def _expand(cls, value: pathlib.Path) -> pathlib.Path:
        """Expand a leading ``~``, which the shell does not expand inside env vars."""
        return value.expanduser()

    @field_validator("app_token")
    @classmethod
    def _empty_token_is_none(cls, value: SecretStr | None) -> SecretStr | None:
        """Treat an empty-string token the same as an unset one."""
        return value or None


@lru_cache(maxsize=1)
def _get_context() -> _Context:
    """Build (once) the API client and DB handle this server's tools share."""
    # `model_validate({})` rather than `RepeaterBookSettings()`: both read the
    # environment, but only this form tells a type checker that the required
    # `app_contact` is supplied at runtime rather than by the caller.
    settings = RepeaterBookSettings.model_validate({})
    # The working dir is this server's to own: it is where we put the SQLite
    # file and the HTTP cache, so create it rather than demanding it exist.
    settings.working_dir.mkdir(parents=True, exist_ok=True)
    working_dir = Path(settings.working_dir)
    api = RepeaterBookAPI(
        app_contact=settings.app_contact,
        # Stays a SecretStr end to end: RepeaterBookAPI masks it in its repr
        # and only unwraps it when building the X-RB-App-Token header.
        app_token=settings.app_token,
        working_dir=working_dir,
    )
    db = RepeaterBook(working_dir=working_dir)
    db.init_db()
    return _Context(api=api, db=db)


def _api_modes(modes: set[RepeaterMode] | None) -> frozenset[Mode]:
    """Translate RepeaterModes into the library's API-filterable Modes.

    Modes the API can't scope (DSTAR/FUSION/M17) are simply omitted from the
    result; local filtering still applies to them.
    """
    if not modes:
        return frozenset()
    return frozenset(
        api for mode in modes if (api := _MODE_TO_API.get(mode)) is not None
    )


def _build_query(
    country: str | None,
    state_id: str | None,
    region: str | None,
    modes: set[RepeaterMode] | None,
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
    modes: set[RepeaterMode] | None = None,
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
    lat: Annotated[float, Field(ge=-90, le=90)],
    lon: Annotated[float, Field(ge=-180, le=180)],
    radius_km: Annotated[float, Field(gt=0)],
    country: str | None = None,
    state_id: str | None = None,
    region: str | None = None,
    bands: set[BandName] | None = None,
    modes: set[RepeaterMode] | None = None,
    status: set[RepeaterStatus] | None = None,
    use: set[RepeaterUse] | None = None,
    *,
    refresh: bool = False,
) -> list[RepeaterSpec]:
    """Find nearby repeaters as repeater-specs.

    Searches the local store. When a country/state/region scope is given and
    the store holds nothing for it yet, the region is downloaded first. Pass
    `refresh=True` to force a re-download of an already-populated scope.
    """
    ctx = _get_context()
    scoped = bool(country or state_id or region)
    # Syncing re-parses the whole regional payload and re-merges thousands of
    # rows, so don't do it on every search: only when asked, or when we have
    # nothing to search.
    empty = not await to_thread.run_sync(ctx.db.query)
    if scoped and (refresh or empty):
        await sync_repeaters(country, state_id, region, modes)
    elif empty:
        msg = "no local data; provide a country/region or call sync_repeaters first"
        raise ValueError(msg)

    def _search() -> list[RepeaterSpec]:
        return service.search(
            ctx.db,
            LatLon(lat, lon),
            radius_km,
            bands=bands,
            modes=modes,
            statuses=status,
            uses=use,
        )

    # SQLite reads plus a haversine pass over every row: run it off the event
    # loop so concurrent tool calls aren't blocked.
    return await to_thread.run_sync(_search)


@mcp.tool()
async def get_repeater(source_id: str) -> list[RepeaterSpec]:
    """Return repeater-specs for a single repeater by its source id."""
    ctx = _get_context()
    return await to_thread.run_sync(service.get_by_id, ctx.db, source_id)


def main() -> None:  # pragma: no cover - process entry point
    """Run the MCP server over stdio."""
    mcp.run()
