"""Tests for queries module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from haversine import Unit  # type: ignore[import-untyped]

from repeaterbook.models import Repeater, Status, Use
from repeaterbook.queries import Band, Bands, band, filter_radius, square
from repeaterbook.utils import LatLon, Radius


@pytest.fixture
def sample_repeaters() -> list[Repeater]:
    """Create sample repeaters for testing."""
    base = {
        "pl_ctcss_uplink": None,
        "pl_ctcss_tsq_downlink": None,
        "location_nearest_city": "Test City",
        "landmark": None,
        "region": None,
        "country": "United States",
        "county": None,
        "state": "California",
        "precise": True,
        "callsign": "W6TEST",
        "use_membership": Use.OPEN,
        "operational_status": Status.ON_AIR,
        "ares": None,
        "races": None,
        "skywarn": None,
        "canwarn": None,
        "allstar_node": None,
        "echolink_node": None,
        "irlp_node": None,
        "wires_node": None,
        "dmr_capable": False,
        "dmr_id": None,
        "dmr_color_code": None,
        "d_star_capable": False,
        "nxdn_capable": False,
        "apco_p_25_capable": False,
        "p_25_nac": None,
        "m17_capable": False,
        "m17_can": None,
        "tetra_capable": False,
        "tetra_mcc": None,
        "tetra_mnc": None,
        "yaesu_system_fusion_capable": False,
        "ysf_digital_id_uplink": None,
        "ysf_digital_id_downlink": None,
        "ysf_dsc": None,
        "analog_capable": True,
        "fm_bandwidth": None,
        "notes": None,
        "last_update": date(2024, 1, 1),
    }
    return [
        # Repeater at LA
        Repeater(
            state_id="06",
            repeater_id=1,
            frequency=Decimal("146.940"),
            input_frequency=Decimal("146.340"),
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437"),
            **base,
        ),
        # Repeater at SF (about 550km from LA)
        Repeater(
            state_id="06",
            repeater_id=2,
            frequency=Decimal("440.100"),
            input_frequency=Decimal("445.100"),
            latitude=Decimal("37.7749"),
            longitude=Decimal("-122.4194"),
            **base,
        ),
        # Repeater at San Diego (about 180km from LA)
        Repeater(
            state_id="06",
            repeater_id=3,
            frequency=Decimal("147.150"),
            input_frequency=Decimal("147.750"),
            latitude=Decimal("32.7157"),
            longitude=Decimal("-117.1611"),
            **base,
        ),
    ]


class TestSquareQuery:
    """Tests for square() query builder."""

    def test_square_returns_column_element(self) -> None:
        """square() should return a SQLAlchemy ColumnElement."""
        la = LatLon(lat=34.0522, lon=-118.2437)
        radius = Radius(origin=la, distance=100, unit=Unit.KILOMETERS)
        result = square(radius)
        # Should be a BinaryExpression (and_ result)
        assert result is not None


class TestFilterRadius:
    """Tests for filter_radius() function."""

    def test_filter_radius_within_distance(
        self, sample_repeaters: list[Repeater]
    ) -> None:
        """filter_radius should return repeaters within the specified distance."""
        la = LatLon(lat=34.0522, lon=-118.2437)
        # 200km should include San Diego but not SF
        radius = Radius(origin=la, distance=200, unit=Unit.KILOMETERS)
        result = filter_radius(sample_repeaters, radius)
        # Should include LA (0km) and San Diego (~180km), but not SF (~550km)
        assert len(result) == 2
        repeater_ids = [r.repeater_id for r in result]
        assert 1 in repeater_ids  # LA
        assert 3 in repeater_ids  # San Diego
        assert 2 not in repeater_ids  # SF

    def test_filter_radius_sorted_by_distance(
        self, sample_repeaters: list[Repeater]
    ) -> None:
        """filter_radius should sort results by distance (closest first)."""
        la = LatLon(lat=34.0522, lon=-118.2437)
        radius = Radius(origin=la, distance=600, unit=Unit.KILOMETERS)
        result = filter_radius(sample_repeaters, radius)
        # Should be sorted: LA (0km), San Diego (~180km), SF (~550km)
        assert len(result) == 3
        assert result[0].repeater_id == 1  # LA (closest)
        assert result[1].repeater_id == 3  # San Diego
        assert result[2].repeater_id == 2  # SF (furthest)

    def test_filter_radius_empty_result(
        self, sample_repeaters: list[Repeater]
    ) -> None:
        """filter_radius should return empty list if no repeaters in range."""
        # Point in the Atlantic Ocean
        atlantic = LatLon(lat=30.0, lon=-40.0)
        radius = Radius(origin=atlantic, distance=100, unit=Unit.KILOMETERS)
        result = filter_radius(sample_repeaters, radius)
        assert len(result) == 0


class TestBandNamedTuple:
    """Tests for Band NamedTuple."""

    def test_band_creation(self) -> None:
        """Band should be created with low and high values."""
        b = Band(low=Decimal("144.0"), high=Decimal("148.0"))
        assert b.low == Decimal("144.0")
        assert b.high == Decimal("148.0")


class TestBandsEnum:
    """Tests for Bands enum."""

    def test_2m_band(self) -> None:
        """M_2 band should have correct range."""
        assert Bands.M_2.low == Decimal("144.0")
        assert Bands.M_2.high == Decimal("148.0")

    def test_70cm_band(self) -> None:
        """CM_70 band should have correct range."""
        assert Bands.CM_70.low == Decimal("420.0")
        assert Bands.CM_70.high == Decimal("450.0")

    def test_all_bands_defined(self) -> None:
        """All expected bands should be defined."""
        expected_bands = [
            "M_10", "M_6", "M_4", "M_2", "CM_70", "CM_33", "CM_23", "CM_13", "CM_3"
        ]
        for band_name in expected_bands:
            assert hasattr(Bands, band_name)


class TestBandQuery:
    """Tests for band() query builder."""

    def test_band_single(self) -> None:
        """band() should work with a single band."""
        result = band(Bands.M_2.value)
        assert result is not None

    def test_band_multiple(self) -> None:
        """band() should work with multiple bands."""
        result = band(Bands.M_2.value, Bands.CM_70.value)
        assert result is not None
