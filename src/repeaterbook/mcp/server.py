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
from typing import Annotated, cast

import attrs
from anyio import Path, to_thread
from fastmcp import FastMCP
from loguru import logger
from pycountry import countries
from pycountry.db import Country  # noqa: TC002
from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from repeaterbook.database import RepeaterBook
from repeaterbook.exceptions import RepeaterBookUnauthorizedError
from repeaterbook.mcp import service
from repeaterbook.models import ExportQuery, Mode
from repeaterbook.na_states import NAState, state_country
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

    app_token: SecretStr
    """Per-user RepeaterBook API token.

    Required: as of RepeaterBook's 2026-03-03 API policy every export needs
    an approved ``rbuapp_`` token, and an unauthenticated request is refused
    with ``401 auth_missing``. Demanding it up front turns that into a
    startup error rather than a failure on the first tool call.
    """

    @field_validator("working_dir")
    @classmethod
    def _expand(cls, value: pathlib.Path) -> pathlib.Path:
        """Expand a leading ``~``, which the shell does not expand inside env vars."""
        return value.expanduser()

    @field_validator("app_token")
    @classmethod
    def _reject_blank_token(cls, value: SecretStr) -> SecretStr:
        """Reject an empty or whitespace-only token.

        An env var set to the empty string is a misconfiguration, not a
        request to run unauthenticated -- and running unauthenticated is not
        possible anyway.
        """
        if not value.get_secret_value().strip():
            msg = "must not be empty"
            raise ValueError(msg)
        return value


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


def _resolve_country(name: str) -> Country:
    """Resolve a country name, tolerating the aliases people actually use.

    An exact match wins outright. Otherwise fall back to pycountry's fuzzy
    search, which handles "USA", "South Korea" and "Russia" -- none of which
    match by name. Fuzzy results are ranked, and the top hit is not always
    right ("USA" also matches Indonesia and Azerbaijan), so an ambiguous
    match reports its candidates rather than silently picking one.
    """
    exact = countries.get(name=name)
    if exact is not None:
        return cast("Country", exact)
    try:
        matches = cast("list[Country]", countries.search_fuzzy(name))
    except LookupError:
        matches = []
    if not matches:
        msg = f"unknown country: {name!r}"
        raise ValueError(msg)
    best = matches[0]
    if len(matches) > 1:
        alternatives = ", ".join(repr(c.name) for c in matches[1:4])
        logger.info(
            f"Country {name!r} resolved to {best.name!r} "
            f"(other candidates: {alternatives})"
        )
    return best


def _check_scope(
    country: Country | None,
    state: NAState | None,
    region: str | None,
) -> None:
    """Reject scope combinations the API answers with silence.

    ``state_id`` only exists on the North America endpoint and ``region``
    only on the rest-of-world one, so pairing either with the wrong country
    produces an empty result set rather than an error -- indistinguishable
    from a region that genuinely has no repeaters.
    """
    if state is not None:
        expected = state_country(state)
        if country is not None and country.name != expected:
            msg = (
                f"{state.name} is a {expected} subdivision, but country is "
                f"{country.name!r}. Pass country={expected!r}, or drop the "
                f"state to search {country.name} as a whole."
            )
            raise ValueError(msg)
        if region is not None:
            msg = (
                "state and region cannot be combined: state scopes the North "
                "America endpoint, region scopes the rest-of-world one."
            )
            raise ValueError(msg)
    elif (
        region is not None
        and country is not None
        and country.name in RepeaterBookAPI.NA_COUNTRIES
    ):
        msg = (
            f"region is not supported for {country.name!r}, which is served by "
            f"the North America endpoint. Use a state instead."
        )
        raise ValueError(msg)


def _build_query(
    country: str | None,
    state: NAState | None,
    region: str | None,
    modes: set[RepeaterMode] | None,
) -> ExportQuery:
    """Build an ExportQuery from a scope, raising ValueError on bad input."""
    resolved = _resolve_country(country) if country is not None else None
    _check_scope(resolved, state, region)
    return ExportQuery(
        countries=frozenset({resolved}) if resolved is not None else frozenset(),
        state_ids=frozenset({state.value}) if state is not None else frozenset(),
        regions=frozenset({region}) if region else frozenset(),
        modes=_api_modes(modes),
    )


_Country = Annotated[
    str | None,
    Field(
        description=(
            "Country name, e.g. 'United States' or 'Switzerland'. Common "
            "aliases such as 'USA' are resolved where unambiguous."
        )
    ),
]

_State = Annotated[
    NAState | None,
    Field(
        description=(
            "State, province or territory, for the United States, Canada and "
            "Mexico only. Strongly recommended for these countries: the API "
            "returns at most 3500 rows, so a whole-country query is silently "
            "truncated. Use `region` elsewhere."
        )
    ),
]

_Region = Annotated[
    str | None,
    Field(
        description=(
            "Region within a country outside North America, where the source "
            "provides one. Use `state` for the US, Canada and Mexico."
        )
    ),
]


@mcp.tool()
async def sync_repeaters(
    country: _Country = None,
    state: _State = None,
    region: _Region = None,
    modes: set[RepeaterMode] | None = None,
) -> service.SyncResult:
    """Download repeaters for a region into the local store.

    Scope the download as narrowly as you can. RepeaterBook caps a response at
    3500 rows and gives no indication when it truncates, so large scopes
    quietly return partial data. The result flags this when it happens.
    """
    ctx = _get_context()
    query = _build_query(country, state, region, modes)
    try:
        return await service.sync(ctx.api, ctx.db, query)
    except RepeaterBookUnauthorizedError as exc:
        # A token is required to start, so reaching here means the one we have
        # is wrong rather than absent: expired, revoked, or issued for another
        # application or User-Agent.
        msg = (
            f"RepeaterBook rejected the API token ({exc}). Check that "
            "REPEATERBOOK_APP_TOKEN is current and issued for this "
            "application."
        )
        raise ValueError(msg) from exc


@mcp.tool()
async def search_repeaters(  # noqa: PLR0913
    lat: Annotated[float, Field(ge=-90, le=90)],
    lon: Annotated[float, Field(ge=-180, le=180)],
    radius_km: Annotated[float, Field(gt=0)],
    country: _Country = None,
    state: _State = None,
    region: _Region = None,
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
    scoped = bool(country or state or region)
    # Syncing re-parses the whole regional payload and re-merges thousands of
    # rows, so don't do it on every search: only when asked, or when we have
    # nothing to search.
    empty = not await to_thread.run_sync(ctx.db.query)
    if scoped and (refresh or empty):
        await sync_repeaters(country, state, region, modes)
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
