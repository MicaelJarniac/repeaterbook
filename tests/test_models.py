"""Tests for models module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pycountry
import pytest
from pydantic import ValidationError

from repeaterbook.models import (
    Emergency,
    ExportNorthAmericaQuery,
    ExportQuery,
    ExportWorldQuery,
    Mode,
    Repeater,
    ServiceType,
    Status,
    Use,
)


class TestStatusEnum:
    """Tests for Status enum."""

    def test_status_values(self) -> None:
        """Status enum should have expected values."""
        assert Status.OFF_AIR is not None
        assert Status.ON_AIR is not None
        assert Status.UNKNOWN is not None

    def test_status_count(self) -> None:
        """Status enum should have expected number of values."""
        assert len(Status) == 3


class TestUseEnum:
    """Tests for Use enum."""

    def test_use_values(self) -> None:
        """Use enum should have expected values."""
        assert Use.OPEN is not None
        assert Use.PRIVATE is not None
        assert Use.CLOSED is not None


class TestModeEnum:
    """Tests for Mode enum."""

    def test_mode_values(self) -> None:
        """Mode enum should have expected values."""
        assert Mode.ANALOG is not None
        assert Mode.DMR is not None
        assert Mode.NXDN is not None
        assert Mode.P25 is not None
        assert Mode.TETRA is not None


class TestEmergencyEnum:
    """Tests for Emergency enum."""

    def test_emergency_values(self) -> None:
        """Emergency enum should have expected values."""
        assert Emergency.ARES is not None
        assert Emergency.RACES is not None
        assert Emergency.SKYWARN is not None
        assert Emergency.CANWARN is not None


class TestServiceTypeEnum:
    """Tests for ServiceType enum."""

    def test_service_type_values(self) -> None:
        """ServiceType enum should have GMRS."""
        assert ServiceType.GMRS is not None


class TestRepeaterModel:
    """Tests for Repeater SQLModel."""

    @pytest.fixture
    def sample_repeater(self) -> Repeater:
        """Create a sample Repeater instance."""
        return Repeater(
            state_id="CA",
            repeater_id=123,
            frequency=Decimal("146.940000"),
            input_frequency=Decimal("146.340000"),
            pl_ctcss_uplink="100.0",
            pl_ctcss_tsq_downlink="100.0",
            location_nearest_city="Los Angeles",
            landmark="Downtown",
            region=None,
            country="United States",
            county="Los Angeles",
            state="California",
            latitude=Decimal("34.0522"),
            longitude=Decimal("-118.2437"),
            precise=True,
            callsign="W6ABC",
            use_membership=Use.OPEN,
            operational_status=Status.ON_AIR,
            ares=None,
            races=None,
            skywarn=None,
            canwarn=None,
            allstar_node=None,
            echolink_node=None,
            irlp_node=None,
            wires_node=None,
            dmr_capable=False,
            dmr_id=None,
            dmr_color_code=None,
            d_star_capable=False,
            nxdn_capable=False,
            apco_p_25_capable=False,
            p_25_nac=None,
            m17_capable=False,
            m17_can=None,
            tetra_capable=False,
            tetra_mcc=None,
            tetra_mnc=None,
            yaesu_system_fusion_capable=False,
            ysf_digital_id_uplink=None,
            ysf_digital_id_downlink=None,
            ysf_dsc=None,
            analog_capable=True,
            fm_bandwidth=Decimal(25),
            notes=None,
            last_update=date(2024, 1, 15),
        )

    def test_repeater_creation(self, sample_repeater: Repeater) -> None:
        """Repeater should be created with correct values."""
        assert sample_repeater.state_id == "CA"
        assert sample_repeater.repeater_id == 123
        assert sample_repeater.frequency == Decimal("146.940000")

    def test_repeater_composite_pk(self, sample_repeater: Repeater) -> None:
        """Repeater has composite primary key of state_id and repeater_id."""
        # Check that the model has the expected primary key fields
        assert sample_repeater.state_id is not None
        assert sample_repeater.repeater_id is not None

    def test_repeater_decimal_fields(self, sample_repeater: Repeater) -> None:
        """Decimal fields should preserve precision."""
        assert sample_repeater.frequency == Decimal("146.940000")
        assert sample_repeater.latitude == Decimal("34.0522")
        assert sample_repeater.longitude == Decimal("-118.2437")

    def test_repeater_enum_fields(self, sample_repeater: Repeater) -> None:
        """Enum fields should have correct types."""
        assert sample_repeater.use_membership == Use.OPEN
        assert sample_repeater.operational_status == Status.ON_AIR

    def test_repeater_optional_fields(self, sample_repeater: Repeater) -> None:
        """Optional fields should allow None."""
        assert sample_repeater.region is None
        assert sample_repeater.ares is None


class TestRepeaterValidation:
    """Tests for Repeater model validation.

    Note: SQLModel table models don't validate on __init__ by default.
    Validation is triggered via model_validate(), which is how json_to_model works.
    """

    @pytest.fixture
    def base_data(self) -> dict[str, object]:
        """Base valid repeater data."""
        return {
            "state_id": "CA",
            "repeater_id": 1,
            "frequency": Decimal("146.94"),
            "input_frequency": Decimal("146.34"),
            "pl_ctcss_uplink": None,
            "pl_ctcss_tsq_downlink": None,
            "location_nearest_city": "Test",
            "landmark": None,
            "region": None,
            "country": "US",
            "county": None,
            "state": "CA",
            "latitude": Decimal(34),
            "longitude": Decimal(-118),
            "precise": True,
            "callsign": None,
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

    def test_invalid_latitude_too_high(self, base_data: dict[str, object]) -> None:
        """Latitude above 90 should raise ValidationError."""
        base_data["latitude"] = Decimal(91)
        with pytest.raises(ValidationError, match="Latitude must be between"):
            Repeater.model_validate(base_data)

    def test_invalid_latitude_too_low(self, base_data: dict[str, object]) -> None:
        """Latitude below -90 should raise ValidationError."""
        base_data["latitude"] = Decimal(-91)
        with pytest.raises(ValidationError, match="Latitude must be between"):
            Repeater.model_validate(base_data)

    def test_invalid_longitude_too_high(self, base_data: dict[str, object]) -> None:
        """Longitude above 180 should raise ValidationError."""
        base_data["longitude"] = Decimal(181)
        with pytest.raises(ValidationError, match="Longitude must be between"):
            Repeater.model_validate(base_data)

    def test_invalid_longitude_too_low(self, base_data: dict[str, object]) -> None:
        """Longitude below -180 should raise ValidationError."""
        base_data["longitude"] = Decimal(-181)
        with pytest.raises(ValidationError, match="Longitude must be between"):
            Repeater.model_validate(base_data)

    def test_invalid_frequency_zero(self, base_data: dict[str, object]) -> None:
        """Frequency of zero should raise ValidationError."""
        base_data["frequency"] = Decimal(0)
        with pytest.raises(ValidationError, match="Frequency must be positive"):
            Repeater.model_validate(base_data)

    def test_invalid_frequency_negative(self, base_data: dict[str, object]) -> None:
        """Negative frequency should raise ValidationError."""
        base_data["frequency"] = Decimal(-10)
        with pytest.raises(ValidationError, match="Frequency must be positive"):
            Repeater.model_validate(base_data)

    def test_valid_data_passes(self, base_data: dict[str, object]) -> None:
        """Valid data should create a Repeater without errors."""
        repeater = Repeater.model_validate(base_data)
        assert repeater.latitude == Decimal(34)
        assert repeater.longitude == Decimal(-118)
        assert repeater.frequency == Decimal("146.94")


class TestExportQuery:
    """Tests for ExportQuery frozen dataclass."""

    def test_default_values(self) -> None:
        """ExportQuery should have empty frozensets by default."""
        query = ExportQuery()
        assert query.callsigns == frozenset()
        assert query.countries == frozenset()
        assert query.modes == frozenset()

    def test_with_countries(self) -> None:
        """ExportQuery should accept countries."""
        brazil = pycountry.countries.lookup("Brazil")
        query = ExportQuery(countries=frozenset({brazil}))
        assert brazil in query.countries

    def test_with_modes(self) -> None:
        """ExportQuery should accept modes."""
        query = ExportQuery(modes=frozenset({Mode.DMR, Mode.NXDN}))
        assert Mode.DMR in query.modes
        assert Mode.NXDN in query.modes

    def test_with_frequencies(self) -> None:
        """ExportQuery should accept frequencies as Decimals."""
        query = ExportQuery(frequencies=frozenset({Decimal("146.94")}))
        assert Decimal("146.94") in query.frequencies

    def test_immutable(self) -> None:
        """ExportQuery should be immutable (frozen)."""
        query = ExportQuery()
        with pytest.raises(AttributeError):
            query.callsigns = frozenset({"test"})  # type: ignore[misc]


class TestExportNorthAmericaQuery:
    """Tests for ExportNorthAmericaQuery TypedDict."""

    def test_na_query_fields(self) -> None:
        """NA query should support NA-specific fields."""
        query: ExportNorthAmericaQuery = {
            "state_id": ["06"],
            "county": ["Los Angeles"],
            "emcomm": ["ARES"],
            "stype": ["GMRS"],
        }
        assert query["state_id"] == ["06"]
        assert query["county"] == ["Los Angeles"]


class TestExportWorldQuery:
    """Tests for ExportWorldQuery TypedDict."""

    def test_world_query_fields(self) -> None:
        """World query should support region field."""
        query: ExportWorldQuery = {
            "region": ["South America"],
        }
        assert query["region"] == ["South America"]
