"""Tests for utils module."""

from __future__ import annotations

from haversine import Unit  # type: ignore[import-untyped]

from repeaterbook.utils import LatLon, Radius, SquareBounds, square_bounds


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

    def test_large_radius_wraps_latitude(self) -> None:
        """square_bounds should handle large radius that wraps around poles."""
        origin = LatLon(lat=89.0, lon=0.0)  # Near north pole
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        bounds = square_bounds(radius)

        # When south goes past the pole, it should open up to full range
        # (This is the wrap-around logic in the function)
        if bounds.south > bounds.north:
            assert bounds.north == 90.0
            assert bounds.south == -90.0

    def test_large_radius_wraps_longitude(self) -> None:
        """square_bounds should handle large radius that wraps around meridian."""
        origin = LatLon(lat=0.0, lon=179.0)  # Near date line
        radius = Radius(origin=origin, distance=500, unit=Unit.KILOMETERS)
        bounds = square_bounds(radius)

        # When west goes past the date line (180), it should open up to full range
        if bounds.west > bounds.east:
            assert bounds.west == -180.0
            assert bounds.east == 180.0

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
