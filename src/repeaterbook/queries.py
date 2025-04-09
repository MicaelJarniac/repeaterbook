"""Queries."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "Band",
    "Bands",
    "band",
    "filter_radius",
    "square",
)

from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from haversine import haversine  # type: ignore[import-untyped]
from loguru import logger
from sqlmodel import and_, or_

from repeaterbook.models import Repeater
from repeaterbook.utils import Radius, square_bounds

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

    from sqlalchemy.sql.elements import ColumnElement


def square(radius: Radius) -> ColumnElement[bool]:
    """Return a query for repeaters within a given square.

    Note: This is a square, not a circle. Use `filter_radius` afterwards.
    """
    bounds = square_bounds(radius=radius)
    return and_(
        Repeater.latitude >= bounds.south,
        Repeater.latitude <= bounds.north,
        Repeater.longitude >= bounds.west,
        Repeater.longitude <= bounds.east,
    )


def filter_radius(
    repeaters: Iterable[Repeater],
    radius: Radius,
) -> list[Repeater]:
    """Filter repeaters within a given radius, and sort by distance.

    Use after `square` to limit the number of repeaters to check.
    This is a brute-force search, so it should be used with care.
    """

    class RepDist(NamedTuple):
        """Repeater distance."""

        repeater: Repeater
        distance: float

    rep_dists: list[RepDist] = []
    for repeater in repeaters:
        # Calculate the distance to the repeater.
        distance = haversine(
            radius.origin,
            (repeater.latitude, repeater.longitude),
            unit=radius.unit,
        )

        if distance <= radius.distance:
            rep_dists.append(RepDist(repeater=repeater, distance=distance))

    # Sort by distance.
    rep_dists.sort(key=lambda x: x.distance)

    # Log the number of repeaters found.
    logger.info(
        f"Found {len(rep_dists)} repeaters within {radius.distance} {radius.unit.name}."
    )

    # Convert to a list of repeaters.
    return [rep_dist.repeater for rep_dist in rep_dists]


class Band(NamedTuple):
    """Band."""

    low: Decimal
    high: Decimal


class Bands(Band, Enum):
    """Bands."""

    M_10 = Band(low=Decimal("28.0"), high=Decimal("29.7"))
    M_6 = Band(low=Decimal("50.0"), high=Decimal("54.0"))
    M_4 = Band(low=Decimal("70.0"), high=Decimal("72.0"))
    M_2 = Band(low=Decimal("144.0"), high=Decimal("148.0"))
    CM_70 = Band(low=Decimal("420.0"), high=Decimal("450.0"))
    CM_33 = Band(low=Decimal("902.0"), high=Decimal("928.0"))
    CM_23 = Band(low=Decimal("1240.0"), high=Decimal("1300.0"))
    CM_13 = Band(low=Decimal("2300.0"), high=Decimal("2450.0"))
    CM_3 = Band(low=Decimal("10000.0"), high=Decimal("10500.0"))


def band(*bands: Band) -> ColumnElement[bool]:
    """Return a query for repeaters within a given band."""
    return or_(
        *(
            (Repeater.frequency >= band.low) & (Repeater.frequency <= band.high)
            for band in bands
        )
    )
