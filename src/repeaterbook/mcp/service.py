"""Service layer orchestrating the RepeaterBook library for the MCP tools."""

from __future__ import annotations

__all__: tuple[str, ...] = ("get_by_id", "search", "sync")

from decimal import Decimal
from typing import TYPE_CHECKING

from haversine import Unit, haversine  # type: ignore[import-untyped]

from repeaterbook.models import Repeater, Status, Use
from repeaterbook.queries import band, band_of, filter_radius, square
from repeaterbook.spec import RepeaterStatus, RepeaterUse, repeater_to_specs
from repeaterbook.utils import Radius

if TYPE_CHECKING:
    from repeaterbook.database import RepeaterBook
    from repeaterbook.models import ExportQuery
    from repeaterbook.queries import BandName
    from repeaterbook.services import RepeaterBookAPI
    from repeaterbook.spec import RepeaterMode, RepeaterSpec
    from repeaterbook.utils import LatLon


async def sync(api: RepeaterBookAPI, db: RepeaterBook, query: ExportQuery) -> int:
    """Download repeaters for a query and merge them into the local DB."""
    repeaters = await api.download(query)
    db.populate(repeaters)
    return len(repeaters)


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
