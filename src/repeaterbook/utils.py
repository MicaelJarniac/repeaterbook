"""Utilities."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "CtcssToneHz",
    "DistanceKm",
    "FrequencyMHz",
    "LatLon",
    "LatitudeDeg",
    "LongitudeDeg",
    "Radius",
    "SquareBounds",
    "square_bounds",
)

from decimal import Decimal
from typing import Annotated, NamedTuple

from annotated_types import Ge, Gt, Le, MultipleOf
from annotated_types import Unit as UnitOf
from haversine import Direction, Unit, inverse_haversine  # type: ignore[import-untyped]
from pydantic import Field
from typing_extensions import TypeAliasType

# Physical quantities shared across the public contract.
#
# Each is a *named* alias so Pydantic emits a single `$defs` entry and every
# field that uses it becomes a `$ref`, rather than duplicating the same
# constraint blob inline. Decimal (not float) keeps frequencies and coordinates
# exact; the JSON wire form is a decimal *string* for the same reason.

FrequencyMHz = TypeAliasType(
    "FrequencyMHz",
    Annotated[
        Decimal,
        Gt(Decimal(0)),
        MultipleOf(Decimal("0.000001")),
        UnitOf("MHz"),
        Field(
            allow_inf_nan=False,
            description=(
                "Positive radio frequency in megahertz. Use a decimal string to "
                "preserve exactness; increments are 0.000001 MHz (1 Hz)."
            ),
            examples=["145.550000", "438.500000"],
            json_schema_extra={"unit": "MHz"},
        ),
    ],
)

_CtcssToneValueHz = Annotated[
    Decimal,
    Ge(Decimal("67.0")),
    Le(Decimal("254.1")),
    MultipleOf(Decimal("0.1")),
    UnitOf("Hz"),
]

CtcssToneHz = TypeAliasType(
    "CtcssToneHz",
    Annotated[
        _CtcssToneValueHz | None,
        Field(
            allow_inf_nan=False,
            description=(
                "CTCSS tone frequency in hertz for one signal direction. Null "
                "means CTCSS is disabled for that direction. Use a decimal "
                "string to preserve exactness; increments are 0.1 Hz."
            ),
            examples=["88.5"],
            json_schema_extra={"unit": "Hz"},
        ),
    ],
)

LatitudeDeg = TypeAliasType(
    "LatitudeDeg",
    Annotated[
        Decimal,
        Ge(Decimal(-90)),
        Le(Decimal(90)),
        UnitOf("deg"),
        Field(
            allow_inf_nan=False,
            description=(
                "Latitude in decimal degrees from -90 to 90. Positive values "
                "are north and negative values are south. Use a decimal string "
                "to preserve exactness."
            ),
            examples=["-23.550520"],
            json_schema_extra={"unit": "deg"},
        ),
    ],
)

LongitudeDeg = TypeAliasType(
    "LongitudeDeg",
    Annotated[
        Decimal,
        Ge(Decimal(-180)),
        Le(Decimal(180)),
        UnitOf("deg"),
        Field(
            allow_inf_nan=False,
            description=(
                "Longitude in decimal degrees from -180 to 180. Positive values "
                "are east and negative values are west. Use a decimal string to "
                "preserve exactness."
            ),
            examples=["-46.633308"],
            json_schema_extra={"unit": "deg"},
        ),
    ],
)

DistanceKm = TypeAliasType(
    "DistanceKm",
    Annotated[
        Decimal,
        Ge(Decimal(0)),
        UnitOf("km"),
        Field(
            allow_inf_nan=False,
            description=(
                "Non-negative distance in kilometers. Use a decimal string to "
                "preserve exactness."
            ),
            examples=["12.345"],
            json_schema_extra={"unit": "km"},
        ),
    ],
)


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
