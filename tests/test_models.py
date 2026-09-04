"""Tests for models module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

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
    parse_yes_no,
)
from repeaterbook.spec import (
    DmrParams,
    DStarParams,
    FmParams,
    FusionParams,
    M17Params,
    NxdnParams,
    P25Params,
    RepeaterMode,
    TetraParams,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from repeaterbook.spec import _ParamsUnion
    from tests._types import SampleRepeaterFactory


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
            ares=True,
            races=False,
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
        assert sample_repeater.skywarn is None

    def test_emergency_fields_are_tri_state(self, sample_repeater: Repeater) -> None:
        """Emergency fields distinguish supported, unsupported, and unknown."""
        assert sample_repeater.ares is True
        assert sample_repeater.races is False
        assert sample_repeater.skywarn is None

    def test_emergency_services_collects_only_supported(
        self, sample_repeater: Repeater
    ) -> None:
        """Only True lands in the set; False and None are both left out."""
        assert sample_repeater.emergency_services == frozenset({Emergency.ARES})


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


def test_repeater_dmr_accessor_returns_none_when_incapable(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """The dmr accessor should be None when the repeater isn't DMR-capable."""
    rep = sample_repeater(dmr_capable=False, dmr_color_code="1")
    assert rep.dmr is None


def test_repeater_dmr_accessor_populates_params(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """The dmr accessor should carry the DMR ID and color code."""
    rep = sample_repeater(dmr_capable=True, dmr_id="5051", dmr_color_code="1")
    assert rep.dmr == DmrParams(dmr_id="5051", color_code="1")


def test_repeater_fm_accessor_carries_bandwidth(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """The fm accessor should carry the FM bandwidth."""
    rep = sample_repeater(analog_capable=True, fm_bandwidth=Decimal("12.5"))
    assert rep.fm == FmParams(bandwidth_khz=Decimal("12.5"))


# One row per mode accessor: the capability flag that gates it, the accessor,
# and the params it should produce when the flag is set (given the identifying
# fields below). Kept as a table so every accessor gets *both* branches -- the
# multi-line `if not capable: return None` bodies in `fusion` and `tetra` were
# the last uncovered lines in `models.py`, and the one-line ternaries in
# `dstar`/`p25`/`nxdn`/`m17` have no branch arc for coverage to even notice.
_ACCESSOR_CASES: list[tuple[str, Callable[[Repeater], _ParamsUnion | None], object]] = [
    ("analog_capable", lambda r: r.fm, FmParams(bandwidth_khz=Decimal("25.0"))),
    ("dmr_capable", lambda r: r.dmr, DmrParams(dmr_id="5051", color_code="1")),
    ("d_star_capable", lambda r: r.dstar, DStarParams()),
    (
        "yaesu_system_fusion_capable",
        lambda r: r.fusion,
        FusionParams(digital_id_uplink="1", digital_id_downlink="2", dsc="3"),
    ),
    ("apco_p_25_capable", lambda r: r.p25, P25Params(nac="293")),
    ("nxdn_capable", lambda r: r.nxdn, NxdnParams()),
    ("tetra_capable", lambda r: r.tetra, TetraParams(mcc="724", mnc="01")),
    ("m17_capable", lambda r: r.m17, M17Params(can="7")),
]

# The mode-specific identifiers, set on every case so an accessor that leaks
# them despite the flag being off is caught rather than hidden by their absence.
_MODE_IDENTIFIERS: dict[str, object] = {
    "fm_bandwidth": Decimal("25.0"),
    "dmr_id": "5051",
    "dmr_color_code": "1",
    "ysf_digital_id_uplink": "1",
    "ysf_digital_id_downlink": "2",
    "ysf_dsc": "3",
    "p_25_nac": "293",
    "tetra_mcc": "724",
    "tetra_mnc": "01",
    "m17_can": "7",
}


@pytest.mark.parametrize(
    ("flag", "accessor", "expected"),
    _ACCESSOR_CASES,
    ids=[flag for flag, _, _ in _ACCESSOR_CASES],
)
def test_mode_accessor_returns_none_when_incapable(
    sample_repeater: SampleRepeaterFactory,
    flag: str,
    accessor: Callable[[Repeater], _ParamsUnion | None],
    expected: object,
) -> None:
    """Each mode accessor is None when its flag is off, whatever else is set."""
    del expected
    rep = sample_repeater(**{**_MODE_IDENTIFIERS, flag: False})
    assert accessor(rep) is None


@pytest.mark.parametrize(
    ("flag", "accessor", "expected"),
    _ACCESSOR_CASES,
    ids=[flag for flag, _, _ in _ACCESSOR_CASES],
)
def test_mode_accessor_carries_params_when_capable(
    sample_repeater: SampleRepeaterFactory,
    flag: str,
    accessor: Callable[[Repeater], _ParamsUnion | None],
    expected: object,
) -> None:
    """Each mode accessor carries its mode's identifiers when the flag is on."""
    rep = sample_repeater(**{**_MODE_IDENTIFIERS, flag: True})
    assert accessor(rep) == expected


def test_repeater_modes_reflects_capabilities(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Modes should reflect exactly the capability flags that are set."""
    rep = sample_repeater(analog_capable=True, yaesu_system_fusion_capable=True)
    assert rep.modes == frozenset({RepeaterMode.FM, RepeaterMode.FUSION})


def test_accessors_do_not_change_persistence_surface(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """The accessors must be invisible to SQL/pydantic: no new column, no field."""
    # SQLModel exposes __table__ at runtime; the type stubs don't declare it.
    table = Repeater.__table__  # type: ignore[attr-defined]
    columns = {c.name for c in table.columns}
    assert "dmr" not in columns
    assert "fm" not in columns
    assert "modes" not in columns
    assert "emergency_services" not in columns
    assert "dmr" not in Repeater.model_fields
    assert "emergency_services" not in Repeater.model_fields
    rep = sample_repeater(dmr_capable=True, dmr_id="5051")
    assert "dmr" not in rep.model_dump()
    assert "emergency_services" not in rep.model_dump()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Yes", True),
        ("No", False),
        # Whitespace shows up in community-maintained data.
        (" Yes ", True),
        # Absent, blank, and unrecognized are all "unknown" rather than False:
        # the export declining to say is not the export saying no.
        ("", None),
        (None, None),
        ("Maybe", None),
        # Case-sensitive on purpose: RepeaterBook only ever sends "Yes"/"No",
        # so anything else is unrecognized rather than quietly reinterpreted.
        ("yes", None),
        # Non-strings cannot be a Yes/No answer. Notably 1/0, which the
        # capability flags do use -- these four fields never do.
        (1, None),
        (0, None),
    ],
)
def test_parse_yes_no(raw: object, expected: bool | None) -> None:  # noqa: FBT001
    """parse_yes_no maps the wire vocabulary to a tri-state boolean."""
    assert parse_yes_no(raw) is expected


def test_emergency_services_empty_when_all_unknown(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """A rest-of-world repeater reports no known services, not False ones."""
    rep = sample_repeater(ares=None, races=None, skywarn=None, canwarn=None)
    assert rep.emergency_services == frozenset()


def test_emergency_services_covers_every_enum_member(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Every Emergency member is reachable, so a new one cannot be forgotten."""
    rep = sample_repeater(ares=True, races=True, skywarn=True, canwarn=True)
    assert rep.emergency_services == frozenset(Emergency)
