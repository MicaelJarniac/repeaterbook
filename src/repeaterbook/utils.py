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

import math
from decimal import Decimal
from typing import Annotated, Final, NamedTuple

from annotated_types import Ge, Gt, Le, MultipleOf
from annotated_types import Unit as UnitOf
from haversine import Unit, haversine  # type: ignore[import-untyped]
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


# Nudge every bound outward by this much (about 0.1 mm on the ground) so a
# repeater sitting exactly on the rim is not lost to floating-point noise in
# the trigonometry. Far below any coordinate's precision, far above an ulp.
_PADDING_DEG: Final[float] = 1e-9


def _angular_radius(radius: Radius) -> float:
    """Convert a surface distance to the angle it subtends at the Earth's centre.

    Derived from `haversine` itself, so the conversion uses the same Earth
    radius and per-unit scale as `filter_radius`. Half a turn along the
    equator is exactly pi radians of arc, whatever the unit.
    """
    half_turn: float = haversine((0.0, 0.0), (0.0, 180.0), unit=radius.unit)
    return math.pi * radius.distance / half_turn


def square_bounds(radius: Radius) -> SquareBounds:
    """Get the lat/lon box that contains every point within `radius`.

    This is the coarse pre-filter behind `queries.square`, so it must never
    exclude a point that is actually in range; `filter_radius` does the exact
    check afterwards. Over-approximating is harmless, under-approximating
    silently drops repeaters. The bounds are therefore the true extremes of the
    circle, not merely the points due north/south/east/west of the origin, and
    are padded by a hair against rounding:

    * Latitude spans `lat ± r` (`r` in degrees of arc) and is clamped to the
      poles. A circle that reaches a pole wraps around it and covers every
      longitude, so the box is opened east-west.
    * Longitude is widest where a meridian is tangent to the circle, which
      lies poleward of the origin, not due east/west of it. Spherical
      trigonometry gives that half-width as `asin(sin r / cos lat)`.
    * A circle that straddles the antimeridian would need two boxes.
      `Repeater.longitude` is stored in `[-180, 180]`, so a bound pushed past
      either edge would exclude the far side; the box is opened east-west
      instead, and the exact pass tightens it.
    * Past half the circumference the whole globe is in range.
    """
    lat, lon = radius.origin
    arc = _angular_radius(radius)
    if arc >= math.pi:
        return SquareBounds(north=90.0, south=-90.0, east=180.0, west=-180.0)

    delta = math.degrees(arc) + _PADDING_DEG
    north = lat + delta
    south = lat - delta
    if north >= 90.0 or south <= -90.0:  # noqa: PLR2004 - the poles
        return SquareBounds(
            north=min(north, 90.0), south=max(south, -90.0), east=180.0, west=-180.0
        )

    # Neither pole is reached, so the circle lies strictly between them and
    # `cos(lat) > sin(arc)` holds: the ratio is inside `asin`'s domain. `min`
    # only absorbs rounding when both sides are within an ulp of 1.
    ratio = min(1.0, math.sin(arc) / math.cos(math.radians(lat)))
    half_width = math.degrees(math.asin(ratio)) + _PADDING_DEG
    east = lon + half_width
    west = lon - half_width
    if east > 180.0 or west < -180.0:  # noqa: PLR2004 - the antimeridian
        east = 180.0
        west = -180.0

    return SquareBounds(north=north, south=south, east=east, west=west)
