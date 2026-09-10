"""Service layer orchestrating the RepeaterBook library for the MCP tools."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "ClearResult",
    "SyncResult",
    "clear",
    "get_by_id",
    "search",
    "sync",
)

from decimal import Decimal
from typing import TYPE_CHECKING

from anyio import to_thread
from haversine import Unit, haversine  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from repeaterbook.models import Repeater, Status, Use
from repeaterbook.queries import band, band_of, filter_radius, square
from repeaterbook.spec import RepeaterStatus, RepeaterUse, repeater_to_specs
from repeaterbook.utils import Radius

if TYPE_CHECKING:
    from repeaterbook.database import RepeaterBook
    from repeaterbook.exceptions import RepeaterBookRowError
    from repeaterbook.models import ExportQuery
    from repeaterbook.queries import BandName
    from repeaterbook.services import RepeaterBookAPI
    from repeaterbook.spec import RepeaterMode, RepeaterSpec
    from repeaterbook.utils import LatLon


class SyncResult(BaseModel):
    """Outcome of a sync, including whether the API truncated the response."""

    count: int = Field(description="Repeaters downloaded and stored.")
    truncated: bool = Field(
        description=(
            "True when the response hit RepeaterBook's per-response limit, "
            "meaning rows were almost certainly dropped."
        )
    )
    skipped: int = Field(
        default=0,
        description=(
            "Rows RepeaterBook served that could not be modelled and were "
            "skipped. Community-maintained data occasionally contains these."
        ),
    )
    detail: str | None = Field(
        default=None, description="How to narrow the scope, when truncated."
    )


async def sync(
    api: RepeaterBookAPI,
    db: RepeaterBook,
    query: ExportQuery,
) -> SyncResult:
    """Download repeaters for a query and merge them into the local DB."""
    skipped: list[RepeaterBookRowError] = []
    repeaters = await api.download(query, skipped=skipped)
    db.populate(repeaters)
    # The API caps a response and says nothing about it, so a query at the
    # limit has almost certainly lost rows. The library logs this, but a log
    # line is invisible to an MCP caller: report it in the result instead.
    # Count against rows served, not rows modelled: a skipped row still
    # consumed a slot against the cap, so using len(repeaters) here would
    # under-report truncation for any capped response containing a bad row.
    truncated = len(repeaters) + len(skipped) >= api.max_count
    return SyncResult(
        count=len(repeaters),
        truncated=truncated,
        skipped=len(skipped),
        detail=(
            f"RepeaterBook returned {len(repeaters) + len(skipped)} rows, its "
            "per-response limit, so this scope is very likely incomplete. "
            "Narrow it (for the US, Canada and Mexico, sync one state at a "
            "time)."
            if truncated
            else None
        ),
    )


class ClearResult(BaseModel):
    """Outcome of clearing the local data: what was removed from where."""

    repeaters: int = Field(
        description="Repeaters deleted from the local store. It is now empty."
    )
    cached_responses: int = Field(
        description=(
            "Cached API responses deleted. The next sync of any scope will "
            "download from RepeaterBook rather than re-read a cached copy."
        )
    )


async def clear(api: RepeaterBookAPI, db: RepeaterBook) -> ClearResult:
    """Empty the local store and the API response cache together.

    The two are separate on disk and clearing only the store is a trap: a
    response younger than `max_cache_age` (an hour by default) would be served
    again on the next sync, refilling the store with exactly the data the
    caller just asked to be rid of. Clearing both is the only way to make the
    next sync a genuine download.

    Idempotent and safe on a never-populated working directory: nothing to
    clear reports as zeros rather than failing.
    """
    # Cache first, so that a failure there leaves the store intact: an
    # inconsistent "cleared" state is worse than a fully reported failure.
    cached_responses = await api.clear_cache()
    # A blocking SQLite write; keep it off the event loop like the other
    # database calls the tools make.
    repeaters = await to_thread.run_sync(db.truncate)
    return ClearResult(repeaters=repeaters, cached_responses=cached_responses)


def search(  # noqa: PLR0913 - keyword-only filters mirror the MCP tool's params
    db: RepeaterBook,
    origin: LatLon,
    radius_km: float,
    *,
    bands: set[BandName] | None = None,
    modes: set[RepeaterMode] | None = None,
    statuses: set[RepeaterStatus] | None = None,
    uses: set[RepeaterUse] | None = None,
) -> list[RepeaterSpec]:
    """Search the local DB and return distance-sorted repeater-specs."""
    radius = Radius(origin, radius_km, Unit.KILOMETERS)
    where = [square(radius)]
    if bands:
        where.append(band(*(band_of(b) for b in bands)))

    rows = db.query(*where)
    nearby = filter_radius(rows, radius)

    # The DB stores the core Status/Use enums; the wire vocabulary is the
    # spec's StrEnums. Translate the filters once, up front, rather than
    # per row.
    status_set = {Status[s.name] for s in statuses} if statuses else None
    use_set = {Use[u.name] for u in uses} if uses else None

    specs: list[RepeaterSpec] = []
    for rep in nearby:
        if status_set is not None and rep.operational_status not in status_set:
            continue
        if use_set is not None and rep.use_membership not in use_set:
            continue
        distance = haversine(
            origin, (float(rep.latitude), float(rep.longitude)), unit=Unit.KILOMETERS
        )
        specs.extend(
            spec
            for spec in repeater_to_specs(rep, distance_km=Decimal(str(distance)))
            if modes is None or spec.mode in modes
        )
    return specs


def get_by_id(db: RepeaterBook, source_id: str) -> list[RepeaterSpec]:
    """Return repeater-specs for a single repeater by its source id."""
    state_id, _, raw_id = source_id.partition(":")
    if not raw_id.isdigit():
        return []
    rows = db.query(
        Repeater.state_id == state_id,
        Repeater.repeater_id == int(raw_id),
    )
    return [spec for rep in rows for spec in repeater_to_specs(rep)]
