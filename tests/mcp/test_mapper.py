"""Tests for the pure Repeater -> RepeaterSpec mapper."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from repeaterbook.mcp.mapper import freq_to_band, parse_tone, repeater_to_specs
from repeaterbook.mcp.models import RepeaterMode
from repeaterbook.models import Repeater, Status, Use


def _repeater(**overrides: object) -> Repeater:
    base: dict[str, object] = {
        "state_id": "QLD",
        "repeater_id": 42,
        "frequency": Decimal("146.700"),
        "input_frequency": Decimal("146.100"),
        "pl_ctcss_uplink": "91.5",
        "pl_ctcss_tsq_downlink": None,
        "location_nearest_city": "Brisbane",
        "landmark": None,
        "region": None,
        "country": "Australia",
        "county": None,
        "state": "Queensland",
        "latitude": Decimal("-27.47"),
        "longitude": Decimal("153.02"),
        "precise": True,
        "callsign": "VK4RBN",
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
        "fm_bandwidth": Decimal("25.0"),
        "notes": None,
        "last_update": date(2026, 1, 1),
    }
    base.update(overrides)
    return Repeater(**base)


def test_freq_to_band() -> None:
    """Test freq_to_band maps known frequencies and rejects unknown ones."""
    assert freq_to_band(Decimal("146.700")) == "M_2"
    assert freq_to_band(Decimal("438.000")) == "CM_70"
    assert freq_to_band(Decimal("27.000")) is None


def test_single_mode_expansion() -> None:
    """Test a single-mode repeater expands to exactly one RepeaterSpec."""
    intents = repeater_to_specs(_repeater(), distance_km=5.0)
    assert len(intents) == 1
    spec = intents[0]
    assert spec.mode is RepeaterMode.FM
    assert spec.name == "VK4RBN"
    assert spec.rx_frequency_mhz == Decimal("146.700")
    assert spec.tx_frequency_mhz == Decimal("146.100")
    assert spec.ctcss_tx_hz == Decimal("91.5")
    assert spec.band == "M_2"
    assert spec.distance_km == 5.0
    assert spec.source_id == "QLD:42"
    assert spec.operational_status == "ON_AIR"
    assert spec.use == "OPEN"


def test_multi_mode_expansion() -> None:
    """Test a multi-mode repeater expands to one spec per supported mode."""
    intents = repeater_to_specs(
        _repeater(analog_capable=True, yaesu_system_fusion_capable=True)
    )
    assert len(intents) == 2
    assert {spec.mode for spec in intents} == {RepeaterMode.FM, RepeaterMode.FUSION}


def test_no_capability_defaults_to_fm() -> None:
    """Test a repeater with no capability flags set defaults to FM."""
    intents = repeater_to_specs(_repeater(analog_capable=False))
    assert [spec.mode for spec in intents] == [RepeaterMode.FM]


def test_name_falls_back_to_city() -> None:
    """Test spec name falls back to nearest city when callsign is missing."""
    intents = repeater_to_specs(_repeater(callsign=None))
    assert intents[0].name == "Brisbane"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("91.5", (Decimal("91.5"), None)),
        ("100.0", (Decimal("100.0"), None)),
        ("D023", (None, "023")),
        ("023", (None, "023")),
        ("D023N", (None, "023N")),
        ("", (None, None)),
        (None, (None, None)),
        ("garbage", (None, None)),
    ],
)
def test_parse_tone(
    raw: str | None, expected: tuple[Decimal | None, str | None]
) -> None:
    """Test parse_tone splits RepeaterBook tone strings into ctcss/dcs."""
    assert parse_tone(raw) == expected
