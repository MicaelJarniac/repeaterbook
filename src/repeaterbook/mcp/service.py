"""Service layer orchestrating the RepeaterBook library for the MCP tools."""

from __future__ import annotations

__all__: tuple[str, ...] = ("get_by_id", "search", "sync")

from enum import Enum
from typing import TYPE_CHECKING, TypeVar

from haversine import Unit, haversine  # type: ignore[import-untyped]

from repeaterbook.models import Repeater, Status, Use
from repeaterbook.queries import Bands, band, filter_radius, square
from repeaterbook.spec import RepeaterMode, repeater_to_specs
from repeaterbook.utils import LatLon, Radius

if TYPE_CHECKING:
    from repeaterbook.database import RepeaterBook
    from repeaterbook.models import ExportQuery
    from repeaterbook.services import RepeaterBookAPI
    from repeaterbook.spec import RepeaterSpec

_EnumT = TypeVar("_EnumT", bound=Enum)


def _lookup(enum: type[_EnumT], name: str, label: str) -> _EnumT:
    """Resolve `name` as a member of `enum`, raising a clean ValueError.

    `enum[name]` raises a raw KeyError on a typo'd filter value; this wraps
    that into a ValueError naming the valid options instead.
    """
    try:
        return enum[name]
    except KeyError as exc:
        valid = ", ".join(e.name for e in enum)
        msg = f"unknown {label}: {name!r}; valid: {valid}"
        raise ValueError(msg) from exc


def _validate_modes(modes: list[str] | None) -> set[str] | None:
    """Validate `modes` against RepeaterMode values, raising ValueError on unknown."""
    if not modes:
        return None
    valid_modes = {m.value for m in RepeaterMode}
    for name in modes:
        if name not in valid_modes:
            valid = ", ".join(sorted(valid_modes))
            msg = f"unknown mode: {name!r}; valid modes: {valid}"
            raise ValueError(msg)
    return set(modes)


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
    bands: list[str] | None = None,
    modes: list[str] | None = None,
    statuses: list[str] | None = None,
    uses: list[str] | None = None,
) -> list[RepeaterSpec]:
    """Search the local DB and return distance-sorted repeater-specs."""
    radius = Radius(origin, radius_km, Unit.KILOMETERS)
    where = [square(radius)]
    if bands:
        where.append(band(*(_lookup(Bands, name, "band").value for name in bands)))

    rows = db.query(*where)
    nearby = filter_radius(rows, radius)

    status_set = (
        {_lookup(Status, name, "status") for name in statuses} if statuses else None
    )
    use_set = {_lookup(Use, name, "use") for name in uses} if uses else None
    mode_set = _validate_modes(modes)

    intents: list[RepeaterSpec] = []
    for rep in nearby:
        if status_set is not None and rep.operational_status not in status_set:
            continue
        if use_set is not None and rep.use_membership not in use_set:
            continue
        distance = haversine(
            origin, (float(rep.latitude), float(rep.longitude)), unit=Unit.KILOMETERS
        )
        intents.extend(
            spec
            for spec in repeater_to_specs(rep, distance_km=distance)
            if mode_set is None or spec.mode.value in mode_set
        )
    return intents


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
