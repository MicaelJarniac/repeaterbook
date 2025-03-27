"""Models."""
# ruff: noqa: TC003

from __future__ import annotations

__all__: list[str] = [
    "ExportJson",
    "Repeater",
    "RepeaterJson",
    "Status",
    "Use",
    "YesNo",
]

from datetime import date
from decimal import Decimal
from enum import Enum, auto
from typing import Literal, TypeAlias, TypedDict

from sqlmodel import Field, SQLModel


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


class NorthAmerica(str, Enum):
    UNITED_STATES = "United States"
    CANADA = "Canada"
    MEXICO = "Mexico"


class Europe(str, Enum):
    ALBANIA = "Albania"
    ANDORRA = "Andorra"
    AUSTRIA = "Austria"
    BELARUS = "Belarus"
    BELGIUM = "Belgium"
    BOSNIA_AND_HERZEGOVINA = "Bosnia and Herzegovina"
    BULGARIA = "Bulgaria"
    CROATIA = "Croatia"
    CYPRUS = "Cyprus"
    CZECH_REPUBLIC = "Czech Republic"
    DENMARK = "Denmark"
    ESTONIA = "Estonia"
    FAROE_ISLANDS = "Faroe Islands"
    FINLAND = "Finland"
    FRANCE = "France"
    GEORGIA = "Georgia"
    GERMANY = "Germany"
    GIBRALTAR = "Gibraltar"
    GUERNSEY = "Guernsey"
    GREECE = "Greece"
    HUNGARY = "Hungary"
    ICELAND = "Iceland"
    ISLE_OF_MAN = "Isle of Man"
    IRELAND = "Ireland"
    ITALY = "Italy"
    JERSEY = "Jersey"
    KOSOVO = "Kosovo"
    LATVIA = "Latvia"
    LIECHTENSTEIN = "Liechtenstein"
    LITHUANIA = "Lithuania"
    LUXEMBOURG = "Luxembourg"
    MALTA = "Malta"
    MOLDOVA = "Moldova"
    NETHERLANDS = "Netherlands"
    NORWAY = "Norway"
    NORTH_MACEDONIA = "North Macedonia"
    POLAND = "Poland"
    PORTUGAL = "Portugal"
    ROMANIA = "Romania"
    RUSSIAN_FEDERATION = "Russian Federation"
    SAN_MARINO = "San Marino"
    SERBIA = "Serbia"
    SLOVAKIA = "Slovakia"
    SLOVENIA = "Slovenia"
    SPAIN = "Spain"
    SWEDEN = "Sweden"
    SWITZERLAND = "Switzerland"
    UKRAINE = "Ukraine"
    UNITED_KINGDOM = "United Kingdom"


class Eurasia(str, Enum):
    AZERBAIJAN = "Azerbaijan"


class Asia(str, Enum):
    CHINA = "China"
    INDIA = "India"
    INDONESIA = "Indonesia"
    ISRAEL = "Israel"
    JAPAN = "Japan"
    JORDAN = "Jordan"
    KUWAIT = "Kuwait"
    MALAYSIA = "Malaysia"
    NEPAL = "Nepal"
    OMAN = "Oman"
    PAKISTAN = "Pakistan"
    PHILIPPINES = "Philippines"
    SINGAPORE = "Singapore"
    SOUTH_KOREA = "South Korea"
    SRI_LANKA = "Sri Lanka"
    THAILAND = "Thailand"
    TURKEY = "Turkey"
    TAIWAN = "Taiwan"
    UNITED_ARAB_EMIRATES = "United Arab Emirates"


class SouthAmerica(str, Enum):
    ARGENTINA = "Argentina"
    BOLIVIA = "Bolivia"
    BRAZIL = "Brazil"
    CARIBBEAN_NETHERLANDS = "Caribbean Netherlands"
    CHILE = "Chile"
    COLOMBIA = "Colombia"
    CURACAO = "Curacao"
    ECUADOR = "Ecuador"
    PARAGUAY = "Paraguay"
    PERU = "Peru"
    URUGUAY = "Uruguay"
    VENEZUELA = "Venezuela"


class Australia(str, Enum):
    AUSTRALIA = "Australia"


class Africa(str, Enum):
    MOROCCO = "Morocco"
    NAMIBIA = "Namibia"
    SOUTH_AFRICA = "South Africa"


class Panama(str, Enum):
    PANAMA = "Panama"


class Oceania(str, Enum):
    NEW_ZEALAND = "New Zealand"


class Hispanola(str, Enum):
    DOMINICAN_REPUBLIC = "Dominican Republic"


class Caribbean(str, Enum):
    ANGUILLA = "Anguilla"
    ANTIGUA_AND_BARBUDA = "Antigua and Barbuda"
    BAHAMAS = "Bahamas"
    BARBADOS = "Barbados"
    BELIZE = "Belize"
    COSTA_RICA = "Costa Rica"
    CAYMAN_ISLANDS = "Cayman Islands"
    DOMINICA = "Dominica"
    EL_SALVADOR = "El Salvador"
    GRENADA = "Grenada"
    GUATEMALA = "Guatemala"
    HAITI = "Haiti"
    HONDURAS = "Honduras"
    JAMAICA = "Jamaica"
    MONTSERRAT = "Montserrat"
    NICARAGUA = "Nicaragua"
    SAINT_KITTS_AND_NEVIS = "Saint Kitts and Nevis"
    SAINT_VINCENT_AND_THE_GRENADINES = "Saint Vincent and the Grenadines"
    SINT_MAARTEN = "Sint Maarten"
    TRINIDAD_AND_TOBAGO = "Trinidad and Tobago"


class Repeater(SQLModel, table=True):
    """Repeater."""

    state_id: str = Field(primary_key=True)
    repeater_id: int = Field(primary_key=True)
    frequency: Decimal
    input_frequency: Decimal
    pl_ctcss_uplink: str | None
    pl_ctcss_tsq_downlink: str | None
    location_nearest_city: str
    landmark: str | None
    region: str | None
    country: str | None
    county: str | None
    state: str | None
    latitude: Decimal
    longitude: Decimal
    precise: bool
    callsign: str | None
    use_membership: Use
    operational_status: Status
    ares: str | None
    races: str | None
    skywarn: str | None
    canwarn: str | None
    #' operating_mode: str
    allstar_node: str | None
    echolink_node: str | None
    irlp_node: str | None
    wires_node: str | None
    dmr_capable: bool
    dmr_id: str | None
    dmr_color_code: str | None
    d_star_capable: bool
    nxdn_capable: bool
    apco_p_25_capable: bool
    p_25_nac: str | None
    m17_capable: bool
    m17_can: str | None
    tetra_capable: bool
    tetra_mcc: str | None
    tetra_mnc: str | None
    yaesu_system_fusion_capable: bool
    ysf_digital_id_uplink: str | None
    ysf_digital_id_downlink: str | None
    ysf_dsc: str | None
    analog_capable: bool
    fm_bandwidth: Decimal | None
    notes: str | None
    last_update: date


YesNo: TypeAlias = Literal["Yes", "No"]


RepeaterJson = TypedDict(
    "RepeaterJson",
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
        "Lat": str,
        "Long": str,
        "Precise": Literal[0, 1],
        "Callsign": str,
        "Use": Literal["OPEN", "PRIVATE", "CLOSED"],
        "Operational Status": Literal["Off-air", "On-air", "Unknown"],
        "AllStar Node": str,
        "EchoLink Node": str | int,
        "IRLP Node": str,
        "Wires Node": str,
        "FM Analog": YesNo,
        "FM Bandwidth": str,
        "DMR": YesNo,
        "DMR Color Code": str,
        "DMR ID": str | int,
        "D-Star": YesNo,
        "NXDN": YesNo,
        "APCO P-25": YesNo,
        "P-25 NAC": str,
        "M17": YesNo,
        "M17 CAN": str,
        "Tetra": YesNo,
        "Tetra MCC": str,
        "Tetra MNC": str,
        "System Fusion": YesNo,
        "Notes": str,
        "Last Update": str,
    },
)


class ExportJson(TypedDict, total=False):
    """RepeaterBook API export response."""

    count: int
    results: list[RepeaterJson]
    status: Literal["error"]
    message: str
