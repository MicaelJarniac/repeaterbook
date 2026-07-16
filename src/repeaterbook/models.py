"""Models."""
# ruff: noqa: TC003

from __future__ import annotations

__all__: tuple[str, ...] = (
    "Emergency",
    "EmergencyJSON",
    "ErrorJSON",
    "ExportBaseQuery",
    "ExportErrorJSON",
    "ExportJSON",
    "ExportNorthAmericaQuery",
    "ExportQuery",
    "ExportWorldQuery",
    "Mode",
    "ModeJSON",
    "Repeater",
    "RepeaterJSON",
    "ServiceType",
    "ServiceTypeJSON",
    "Status",
    "StatusJSON",
    "Use",
    "UseJSON",
    "YesNoJSON",
    "ZeroOneJSON",
)

from datetime import date
from decimal import Decimal
from enum import Enum, auto
from typing import Literal, TypeAlias, TypedDict

import attrs
from pycountry.db import Country  # noqa: TC002
from pydantic import field_validator
from sqlmodel import Field, SQLModel

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

# Core models


class Status(Enum):
    """Status."""

    OFF_AIR = auto()
    ON_AIR = auto()
    UNKNOWN = auto()


class Use(Enum):
    """Use."""

    OPEN = auto()
    PRIVATE = auto()
    CLOSED = auto()


class Mode(Enum):
    """Mode."""

    ANALOG = auto()
    DMR = auto()
    NXDN = auto()
    P25 = auto()
    TETRA = auto()


class Emergency(Enum):
    """Emergency."""

    ARES = auto()
    RACES = auto()
    SKYWARN = auto()
    CANWARN = auto()


class ServiceType(Enum):
    """Service type."""

    GMRS = auto()


class Repeater(SQLModel, table=True):
    """Repeater."""

    state_id: str = Field(primary_key=True)
    repeater_id: int = Field(primary_key=True)
    frequency: Decimal = Field(index=True)
    input_frequency: Decimal = Field(index=True)
    pl_ctcss_uplink: str | None
    pl_ctcss_tsq_downlink: str | None
    location_nearest_city: str
    landmark: str | None
    region: str | None
    country: str | None = Field(index=True)
    county: str | None
    state: str | None
    latitude: Decimal = Field(index=True)
    longitude: Decimal = Field(index=True)
    precise: bool
    callsign: str | None
    use_membership: Use = Field(index=True)
    operational_status: Status = Field(index=True)
    ares: str | None
    races: str | None
    skywarn: str | None
    canwarn: str | None
    allstar_node: str | None
    echolink_node: str | None
    irlp_node: str | None
    wires_node: str | None
    dmr_capable: bool = Field(index=True)
    dmr_id: str | None
    dmr_color_code: str | None
    d_star_capable: bool = Field(index=True)
    nxdn_capable: bool = Field(index=True)
    apco_p_25_capable: bool = Field(index=True)
    p_25_nac: str | None
    m17_capable: bool = Field(index=True)
    m17_can: str | None
    tetra_capable: bool = Field(index=True)
    tetra_mcc: str | None
    tetra_mnc: str | None
    yaesu_system_fusion_capable: bool = Field(index=True)
    ysf_digital_id_uplink: str | None
    ysf_digital_id_downlink: str | None
    ysf_dsc: str | None
    analog_capable: bool = Field(index=True)
    fm_bandwidth: Decimal | None
    notes: str | None
    last_update: date

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: Decimal) -> Decimal:
        """Validate latitude is within valid range."""
        if not Decimal(-90) <= v <= Decimal(90):
            msg = f"Latitude must be between -90 and 90, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: Decimal) -> Decimal:
        """Validate longitude is within valid range."""
        if not Decimal(-180) <= v <= Decimal(180):
            msg = f"Longitude must be between -180 and 180, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("frequency", "input_frequency")
    @classmethod
    def validate_frequency(cls, v: Decimal) -> Decimal:
        """Validate frequency is positive."""
        if v <= 0:
            msg = f"Frequency must be positive, got {v}"
            raise ValueError(msg)
        return v

    @property
    def fm(self) -> FmParams | None:
        """FM parameters, or None if not FM-capable."""
        if not self.analog_capable:
            return None
        return FmParams(bandwidth_khz=self.fm_bandwidth)

    @property
    def dmr(self) -> DmrParams | None:
        """DMR parameters, or None if not DMR-capable."""
        if not self.dmr_capable:
            return None
        return DmrParams(dmr_id=self.dmr_id, color_code=self.dmr_color_code)

    @property
    def dstar(self) -> DStarParams | None:
        """D-STAR parameters, or None if not D-STAR-capable."""
        return DStarParams() if self.d_star_capable else None

    @property
    def fusion(self) -> FusionParams | None:
        """System Fusion parameters, or None if not Fusion-capable."""
        if not self.yaesu_system_fusion_capable:
            return None
        return FusionParams(
            digital_id_uplink=self.ysf_digital_id_uplink,
            digital_id_downlink=self.ysf_digital_id_downlink,
            dsc=self.ysf_dsc,
        )

    @property
    def p25(self) -> P25Params | None:
        """P25 parameters, or None if not P25-capable."""
        return P25Params(nac=self.p_25_nac) if self.apco_p_25_capable else None

    @property
    def nxdn(self) -> NxdnParams | None:
        """NXDN parameters, or None if not NXDN-capable."""
        return NxdnParams() if self.nxdn_capable else None

    @property
    def tetra(self) -> TetraParams | None:
        """TETRA parameters, or None if not TETRA-capable."""
        if not self.tetra_capable:
            return None
        return TetraParams(mcc=self.tetra_mcc, mnc=self.tetra_mnc)

    @property
    def m17(self) -> M17Params | None:
        """M17 parameters, or None if not M17-capable."""
        return M17Params(can=self.m17_can) if self.m17_capable else None

    @property
    def modes(self) -> frozenset[RepeaterMode]:
        """The set of modes this repeater supports."""
        pairs = (
            (self.analog_capable, RepeaterMode.FM),
            (self.dmr_capable, RepeaterMode.DMR),
            (self.d_star_capable, RepeaterMode.DSTAR),
            (self.yaesu_system_fusion_capable, RepeaterMode.FUSION),
            (self.apco_p_25_capable, RepeaterMode.P25),
            (self.nxdn_capable, RepeaterMode.NXDN),
            (self.tetra_capable, RepeaterMode.TETRA),
            (self.m17_capable, RepeaterMode.M17),
        )
        return frozenset(mode for capable, mode in pairs if capable)


# JSON models


ZeroOneJSON: TypeAlias = Literal[
    0,
    1,
]
YesNoJSON: TypeAlias = Literal[
    "Yes",
    "No",
]
UseJSON: TypeAlias = Literal[
    "OPEN",
    "PRIVATE",
    "CLOSED",
]
StatusJSON: TypeAlias = Literal[
    "Off-air",
    "On-air",
    "Unknown",
]
ErrorJSON: TypeAlias = Literal["error"]
ModeJSON: TypeAlias = Literal[
    "analog",
    "DMR",
    "NXDN",
    "P25",
    "tetra",
]
EmergencyJSON: TypeAlias = Literal[
    "ARES",
    "RACES",
    "SKYWARN",
    "CANWARN",
]
ServiceTypeJSON: TypeAlias = Literal["GMRS"]


# RepeaterBook has some variability between North America vs ROW exports.
# In practice, fields can appear/disappear (e.g. NA includes County/ARES/... and
# omits Region; ROW can include extra keys like "sponsor").
#
# Keep this TypedDict intentionally permissive for runtime robustness.
RepeaterJSON = TypedDict(
    "RepeaterJSON",
    {
        "State ID": str,
        "Rptr ID": int,
        "Frequency": str,
        "Input Freq": str,
        "PL": str,
        "TSQ": str,
        "Nearest City": str,
        "Landmark": str,
        "Region": str | None,
        "State": str,
        "Country": str,
        "County": str,
        "ARES": str,
        "RACES": str,
        "SKYWARN": str,
        "CANWARN": str,
        "Lat": str,
        "Long": str,
        "Precise": ZeroOneJSON,
        "Callsign": str,
        "Use": UseJSON,
        "Operational Status": StatusJSON,
        "AllStar Node": str,
        "EchoLink Node": str | int,
        "IRLP Node": str,
        "Wires Node": str,
        "FM Analog": YesNoJSON,
        "FM Bandwidth": str,
        "DMR": YesNoJSON,
        "DMR Color Code": str,
        "DMR ID": str | int,
        "D-Star": YesNoJSON,
        "NXDN": YesNoJSON,
        "APCO P-25": YesNoJSON,
        "P-25 NAC": str,
        "M17": YesNoJSON,
        "M17 CAN": str,
        "Tetra": YesNoJSON,
        "Tetra MCC": str,
        "Tetra MNC": str,
        "System Fusion": YesNoJSON,
        "Notes": str,
        "Last Update": str,
        "sponsor": object,
    },
    total=False,
)


class ExportJSON(TypedDict):
    """RepeaterBook API export response."""

    count: int
    results: list[RepeaterJSON]


class ExportErrorJSON(TypedDict):
    """RepeaterBook API export error response."""

    status: ErrorJSON
    message: str


class ExportBaseQuery(TypedDict, total=False):
    """RepeaterBook API export query.

    `%` - wildcard
    """

    callsign: list[str]
    """Repeater callsign."""
    city: list[str]
    """Repeater city."""
    landmark: list[str]
    country: list[str]
    """Repeater country."""
    frequency: list[str]
    """Repeater frequency."""
    mode: list[ModeJSON]
    """Repeater operating mode (analog, DMR, NXDN, P25, tetra)."""


class ExportNorthAmericaQuery(ExportBaseQuery, total=False):
    """RepeaterBook API export North America query.

    `%` - wildcard
    """

    state_id: list[str]
    """State / province."""
    county: list[str]
    """Repeater county."""
    emcomm: list[EmergencyJSON]
    """ARES, RACES, SKYWARN, CANWARN."""
    stype: list[ServiceTypeJSON]
    """Service type. Only required when searching for GMRS repeaters."""


class ExportWorldQuery(ExportBaseQuery, total=False):
    """RepeaterBook API export World query.

    `%` - wildcard
    """

    region: list[str]
    """Repeater region (if available)."""


@attrs.frozen
class ExportQuery:
    """RepeaterBook API export query.

    `%` - wildcard
    """

    callsigns: frozenset[str] = frozenset()
    cities: frozenset[str] = frozenset()
    landmarks: frozenset[str] = frozenset()
    countries: frozenset[Country] = frozenset()
    frequencies: frozenset[Decimal] = frozenset()
    modes: frozenset[Mode] = frozenset()
    state_ids: frozenset[str] = frozenset()
    counties: frozenset[str] = frozenset()
    emergency_services: frozenset[Emergency] = frozenset()
    service_types: frozenset[ServiceType] = frozenset()
    regions: frozenset[str] = frozenset()


# CSV models


RepeaterCSV = TypedDict(
    "RepeaterCSV",
    {
        "Callsign": str,
        "Frequency (MHz)": str,
        "Input Frequency (MHz)": str,
        "Offset (MHz)": str,
        "Tone": str,
        "City": str,
        "County": str,
        "State": str,
        "Country": str,
        "Landmark": str,
        "Latitude": str,
        "Longitude": str,
        "ARES": str,
        "RACES": str,
        "SKYWARN": str,
        "CANWARN": str,
        "AllStar Node": str,
        "EchoLink Node": str,
        "IRLP Node": str,
        "WIRES-X Node": str,
        "WIRES-X": str,
        "FM (analog)": str,
        "ATV": str,
        "DMR": str,
        "DMR Color Code": str,
        "D-STAR Node": str,
        "D-STAR Service": str,
        "NXDN": str,
        "NXDN RAN": str,
        "P25": str,
        "P25 NAC": str,
        "TETRA": str,
        "System Fusion": str,
        "M17": str,
        "Wide Area": str,
        "PL Tone": str,
        "TSQ Tone": str,
    },
)
