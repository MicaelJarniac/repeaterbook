"""Tests for utils module."""

from __future__ import annotations

import pytest
from haversine import Unit, haversine  # type: ignore[import-untyped]

from repeaterbook.utils import LatLon, Radius, SquareBounds, square_bounds


def _contains(bounds: SquareBounds, point: LatLon) -> bool:
    """Whether `point` falls inside `bounds`, the way `queries.square` tests it."""
    return (
        bounds.south <= point.lat <= bounds.north
        and bounds.west <= point.lon <= bounds.east
    )


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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "square_bounds only handles the past-the-antipode case. A radius that "
            "crosses a pole produces a box that excludes the origin itself: the "
            "great circle north from 89N comes back down the far side, so the "
            "'north' bound lands *below* the origin. "
            "https://github.com/MicaelJarniac/repeaterbook/issues/77"
        ),
    )
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

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "square_bounds does not wrap longitude at the antimeridian: from "
            "179E the 'east' bound comes out as 183.5, a longitude no stored "
            "repeater can have, so anything between -180 and -176.5 is dropped. "
            "https://github.com/MicaelJarniac/repeaterbook/issues/77"
        ),
    )
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
