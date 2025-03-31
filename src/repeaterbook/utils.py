"""Utilities."""

from __future__ import annotations

__all__: list[str] = [
    "LatLon",
    "SquareBounds",
    "square_bounds",
]

from typing import NamedTuple

from haversine import Direction, Unit, inverse_haversine  # type: ignore[import-untyped]


class LatLon(NamedTuple):
    """Latitude and Longitude."""

    lat: float
    lon: float


class SquareBounds(NamedTuple):
    """Square bounds."""

    north: float
    south: float
    east: float
    west: float


def square_bounds(
    origin: LatLon, distance: float, unit: Unit = Unit.KILOMETERS
) -> SquareBounds:
    """Get square bounds around a point."""
    north = inverse_haversine(origin, distance, Direction.NORTH, unit=unit)[0]
    south = inverse_haversine(origin, distance, Direction.SOUTH, unit=unit)[0]
    east = inverse_haversine(origin, distance, Direction.EAST, unit=unit)[1]
    west = inverse_haversine(origin, distance, Direction.WEST, unit=unit)[1]

    # If we've gone all the way around, things get messy. Just open it up to everything.
    if south > north:
        north = 90.0
        south = -90.0
    if west > east:
        west = -180.0
        east = 180.0

    return SquareBounds(north=north, south=south, east=east, west=west)
