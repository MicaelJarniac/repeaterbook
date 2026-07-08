"""Tests for the RepeaterSpec contract model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from repeaterbook.mcp.models import RepeaterMode, RepeaterSpec


def test_repeater_spec_minimal_construction() -> None:
    """Test construction of a RepeaterSpec with minimal required fields."""
    spec = RepeaterSpec(
        name="VK4RBN",
        callsign="VK4RBN",
        rx_frequency_mhz=Decimal("146.700"),
        tx_frequency_mhz=Decimal("146.100"),
        mode=RepeaterMode.FM,
        ctcss_tx_hz=Decimal("91.5"),
        ctcss_rx_hz=None,
        dcs_code=None,
        latitude=Decimal("-27.47"),
        longitude=Decimal("153.02"),
        distance_km=12.3,
        operational_status="ON_AIR",
        use="OPEN",
        band="M_2",
        notes=None,
        last_update=date(2026, 1, 1),
        source_id="QLD:42",
    )
    assert spec.source == "repeaterbook"
    assert spec.mode is RepeaterMode.FM


def test_channel_mode_values() -> None:
    """Test that RepeaterMode enum has all expected members."""
    assert {m.value for m in RepeaterMode} == {
        "FM",
        "DMR",
        "DSTAR",
        "FUSION",
        "P25",
        "NXDN",
        "TETRA",
        "M17",
    }
