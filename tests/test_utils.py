"""Tests for utils module."""

from __future__ import annotations

import math

from haversine import Unit, haversine, inverse_haversine  # type: ignore[import-untyped]
from hypothesis import given
from hypothesis import strategies as st

from repeaterbook.utils import LatLon, Radius, SquareBounds, square_bounds


def _contains(bounds: SquareBounds, point: LatLon) -> bool:
    """Whether `point` falls inside `bounds`, the way `queries.square` tests it."""
    return (
        bounds.south <= point.lat <= bounds.north
        and bounds.west <= point.lon <= bounds.east
    )


def _point_towards(radius: Radius, bearing: float, fraction: float = 1.0) -> LatLon:
    """The point `fraction` of the way to the rim of `radius` along `bearing`.

    Normalised into the domain `Repeater` coordinates are stored in, so it is
    exactly what `queries.square` would be asked to match.
    """
    lat, lon = inverse_haversine(
        radius.origin,
        radius.distance * fraction,
        bearing,
        unit=radius.unit,
        normalize_output=True,
    )
    return LatLon(lat=max(-90.0, min(90.0, lat)), lon=max(-180.0, min(180.0, lon)))


def _in_range(radius: Radius, point: LatLon) -> bool:
    """Whether `filter_radius` would keep `point`."""
    return bool(haversine(radius.origin, point, unit=radius.unit) <= radius.distance)


class TestLatLon:
    """Tests for LatLon NamedTuple."""

    def test_creation(self) -> None:
        """LatLon should be created with lat and lon."""
        ll = LatLon(lat=34.0522, lon=-118.2437)
        assert ll.lat == 34.0522
        assert ll.lon == -118.2437

    def test_unpacking(self) -> None:
        """LatLon should support tuple unpacking."""
        ll = LatLon(lat=34.0522, lon=-118.2437)
        lat, lon = ll
        assert lat == 34.0522
        assert lon == -118.2437


class TestRadius:
    """Tests for Radius NamedTuple."""

    def test_creation_with_defaults(self) -> None:
        """Radius should default to kilometers."""
        origin = LatLon(lat=34.0522, lon=-118.2437)
        r = Radius(origin=origin, distance=100)
        assert r.origin == origin
        assert r.distance == 100
        assert r.unit == Unit.KILOMETERS

    def test_creation_with_custom_unit(self) -> None:
        """Radius should accept custom units."""
        origin = LatLon(lat=34.0522, lon=-118.2437)
        r = Radius(origin=origin, distance=100, unit=Unit.MILES)
        assert r.unit == Unit.MILES


class TestSquareBounds:
    """Tests for SquareBounds NamedTuple."""

    def test_creation(self) -> None:
        """SquareBounds should be created with cardinal bounds."""
        sb = SquareBounds(north=35.0, south=33.0, east=-117.0, west=-119.0)
        assert sb.north == 35.0
        assert sb.south == 33.0
        assert sb.east == -117.0
        assert sb.west == -119.0


class TestSquareBoundsFunction:
    """Tests for square_bounds() function."""

    def test_normal_case(self) -> None:
        """square_bounds should return reasonable bounds for normal case."""
        la = LatLon(lat=34.0522, lon=-118.2437)
        radius = Radius(origin=la, distance=100, unit=Unit.KILOMETERS)
        bounds = square_bounds(radius)

        # Bounds should be roughly 1 degree in each direction (~111km at equator)
        assert bounds.north > la.lat
        assert bounds.south < la.lat
        assert bounds.east > la.lon
        assert bounds.west < la.lon

    def test_small_radius(self) -> None:
        """square_bounds should work with small radius."""
        origin = LatLon(lat=0.0, lon=0.0)
        radius = Radius(origin=origin, distance=1, unit=Unit.KILOMETERS)
        bounds = square_bounds(radius)

        # Should be very close to origin
        assert abs(bounds.north - origin.lat) < 0.1
        assert abs(bounds.south - origin.lat) < 0.1

    def test_radius_past_the_antipode_opens_to_the_whole_globe(self) -> None:
        """Beyond half the circumference every point is in range: bound nothing.

        Past ~20,015 km the four great-circle destinations have all gone
        through the antipode and come back, so "north" lands south of "south"
        and "east" west of "west". A box drawn from those would be inside-out;
        the function opens it to the full globe instead.
        """
        origin = LatLon(lat=0.0, lon=0.0)
        radius = Radius(origin=origin, distance=25_000, unit=Unit.KILOMETERS)

        bounds = square_bounds(radius)

        assert bounds == SquareBounds(north=90.0, south=-90.0, east=180.0, west=-180.0)

    def test_radius_crossing_a_pole_keeps_nearby_points_inside(self) -> None:
        """A bounding box must contain the origin and everything within the radius.

        `queries.square` is a coarse pre-filter for `filter_radius`, so
        over-approximating is fine and under-approximating loses repeaters.
        """
        origin = LatLon(lat=89.0, lon=0.0)
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        # Just over the pole, on the far side. Well inside the radius.
        across_the_pole = LatLon(lat=89.5, lon=180.0)
        assert haversine(origin, across_the_pole, unit=Unit.KILOMETERS) < 500

        bounds = square_bounds(radius)

        assert _contains(bounds, origin)
        assert _contains(bounds, across_the_pole)

    def test_radius_crossing_a_pole_opens_longitude_and_clamps_latitude(
        self,
    ) -> None:
        """A circle enclosing a pole spans every longitude; latitude stops at 90."""
        radius = Radius(origin=LatLon(lat=89.0, lon=0.0), distance=500)

        bounds = square_bounds(radius)

        assert bounds.north == 90.0
        assert bounds.south < 89.0
        assert (bounds.west, bounds.east) == (-180.0, 180.0)

    def test_radius_crossing_the_south_pole_is_symmetric(self) -> None:
        """The south pole is handled like the north pole, clamped at -90."""
        radius = Radius(origin=LatLon(lat=-89.0, lon=0.0), distance=500)

        bounds = square_bounds(radius)

        assert bounds.south == -90.0
        assert bounds.north > -89.0
        assert (bounds.west, bounds.east) == (-180.0, 180.0)

    def test_radius_crossing_the_antimeridian_keeps_nearby_points_inside(
        self,
    ) -> None:
        """A bounding box must reach across the date line when the radius does."""
        origin = LatLon(lat=0.0, lon=179.0)
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        # Just across the date line. Well inside the radius.
        across_the_line = LatLon(lat=0.0, lon=-179.5)
        assert haversine(origin, across_the_line, unit=Unit.KILOMETERS) < 500

        bounds = square_bounds(radius)

        assert _contains(bounds, across_the_line)

    def test_radius_crossing_the_antimeridian_westward_keeps_nearby_points_inside(
        self,
    ) -> None:
        """Same as above, approaching the date line from the western hemisphere."""
        origin = LatLon(lat=0.0, lon=-179.0)
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        across_the_line = LatLon(lat=0.0, lon=179.5)
        assert haversine(origin, across_the_line, unit=Unit.KILOMETERS) < 500

        bounds = square_bounds(radius)

        assert _contains(bounds, across_the_line)
        assert -180.0 <= bounds.west <= bounds.east <= 180.0

    def test_longitude_bulges_poleward_of_the_origin(self) -> None:
        """The widest point of a circle is not due east of its centre.

        Away from the equator meridians converge, so the meridian tangent to
        the circle touches it a little poleward of the origin, further east
        than the point due east. A box that only reaches the due-east point
        clips that bulge and drops in-range repeaters.
        """
        origin = LatLon(lat=60.0, lon=0.0)
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        # Slightly north of the origin, further east than the due-east point,
        # and just inside the radius.
        in_the_bulge = LatLon(lat=60.3, lon=9.0)
        assert haversine(origin, in_the_bulge, unit=Unit.KILOMETERS) < 500
        due_east = _point_towards(radius, bearing=math.pi / 2)
        assert in_the_bulge.lon > due_east.lon

        bounds = square_bounds(radius)

        assert _contains(bounds, in_the_bulge)

    def test_zero_radius_still_contains_the_origin(self) -> None:
        """No distance: the box shrinks to the origin, padded by a hair.

        Without the padding a repeater at the origin itself could be lost to
        rounding: `haversine`'s own `asin(sin(lat))` round-trip can move a
        point by an ulp, and a box with zero width has no room for that.
        """
        origin = LatLon(lat=34.0522, lon=-118.2437)

        bounds = square_bounds(Radius(origin=origin, distance=0))

        assert _contains(bounds, origin)
        assert bounds.north - bounds.south < 1e-6
        assert bounds.east - bounds.west < 1e-6

    @given(
        lat=st.floats(min_value=-90, max_value=90),
        lon=st.floats(min_value=-180, max_value=180),
        # Up to a bit past the antipode, so every branch is exercised.
        distance=st.floats(min_value=0, max_value=25_000),
        unit=st.sampled_from([Unit.KILOMETERS, Unit.MILES, Unit.METERS]),
        bearing=st.floats(min_value=0, max_value=2 * math.pi),
        # Mostly the rim, where the box is tightest, but the interior too.
        fraction=st.one_of(st.just(1.0), st.floats(min_value=0, max_value=1)),
    )
    def test_box_keeps_everything_filter_radius_would_keep(  # noqa: PLR0913
        self,
        lat: float,
        lon: float,
        distance: float,
        unit: Unit,
        bearing: float,
        fraction: float,
    ) -> None:
        """The property a pre-filter must have: nothing in range is left outside.

        For any origin, radius and unit, the box contains the origin and every
        point that `filter_radius` would then accept. Judging "in range" by the
        same `haversine` call `filter_radius` makes keeps float noise out of
        it: a rim point that lands a few ulps outside the radius is no loss,
        since the exact pass would drop it anyway. The box also stays within
        the domain `Repeater` coordinates are validated against, so a bound
        can never point at a longitude no repeater has.
        """
        radius = Radius(origin=LatLon(lat=lat, lon=lon), distance=distance, unit=unit)
        point = _point_towards(radius, bearing, fraction)

        bounds = square_bounds(radius)

        assert -90.0 <= bounds.south <= bounds.north <= 90.0
        assert -180.0 <= bounds.west <= bounds.east <= 180.0
        assert _contains(bounds, radius.origin)
        assert not _in_range(radius, point) or _contains(bounds, point)

    def test_equator(self) -> None:
        """square_bounds should work at equator."""
        origin = LatLon(lat=0.0, lon=0.0)
        radius = Radius(origin=origin, distance=100, unit=Unit.KILOMETERS)
        bounds = square_bounds(radius)

        # Should be symmetric around origin
        assert bounds.north > 0
        assert bounds.south < 0
        assert bounds.east > 0
        assert bounds.west < 0

    def test_different_units(self) -> None:
        """square_bounds should respect different units."""
        origin = LatLon(lat=34.0522, lon=-118.2437)

        km_radius = Radius(origin=origin, distance=100, unit=Unit.KILOMETERS)
        km_bounds = square_bounds(km_radius)

        miles_radius = Radius(origin=origin, distance=100, unit=Unit.MILES)
        miles_bounds = square_bounds(miles_radius)

        # 100 miles > 100 km, so bounds should be larger
        assert miles_bounds.north > km_bounds.north
        assert miles_bounds.south < km_bounds.south
