"""Utilities."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "LatLon",
    "Radius",
    "SquareBounds",
    "square_bounds",
)

from typing import NamedTuple

from haversine import Direction, Unit, inverse_haversine  # type: ignore[import-untyped]


class LatLon(NamedTuple):
    """Latitude and Longitude."""

    lat: float
    lon: float


class Radius(NamedTuple):
    """Radius."""

    origin: LatLon
    distance: float
    unit: Unit = Unit.KILOMETERS


class SquareBounds(NamedTuple):
    """Square bounds."""

    north: float
    south: float
    east: float
    west: float


def square_bounds(radius: Radius) -> SquareBounds:
    """Get square bounds around a point."""
    north = inverse_haversine(
        radius.origin, radius.distance, Direction.NORTH, unit=radius.unit
    )[0]
    south = inverse_haversine(
        radius.origin, radius.distance, Direction.SOUTH, unit=radius.unit
    )[0]
    east = inverse_haversine(
        radius.origin, radius.distance, Direction.EAST, unit=radius.unit
    )[1]
    west = inverse_haversine(
        radius.origin, radius.distance, Direction.WEST, unit=radius.unit
    )[1]

    # If we've gone all the way around, things get messy. Just open it up to everything.
    if south > north:
        north = 90.0
        south = -90.0
    if west > east:
        west = -180.0
        east = 180.0

    return SquareBounds(north=north, south=south, east=east, west=west)
