"""Tests for the core RepeaterSpec contract."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, get_args

import jsonschema
import pytest
from pydantic import ValidationError

from repeaterbook.models import Status, Use
from repeaterbook.spec import (
    DmrParams,
    DmrSpec,
    FmParams,
    FmSpec,
    RepeaterMode,
    StatusName,
    UseName,
    freq_to_band,
    parse_tone,
    repeater_spec_json_schema,
    repeater_to_specs,
    schema_path,
)

if TYPE_CHECKING:
    from tests._types import SampleRepeaterFactory


def test_repeater_mode_members() -> None:
    """RepeaterMode should have exactly the eight supported wire modes."""
    assert {m.value for m in RepeaterMode} == {
        "FM", "DMR", "DSTAR", "FUSION", "P25", "NXDN", "TETRA", "M17",
    }


def test_status_use_literals_match_enums() -> None:
    """StatusName/UseName literals should track the Status/Use enum names."""
    # The wire uses the enum *names*; guard against drift.
    assert set(get_args(StatusName)) == {s.name for s in Status}
    assert set(get_args(UseName)) == {u.name for u in Use}


def test_fm_spec_defaults_and_wire_shape() -> None:
    """FmSpec should default mode/source and serialize status/use as names."""
    spec = FmSpec(
        name="VK4RBN",
        callsign="VK4RBN",
        rx_frequency_mhz=Decimal("146.700"),
        tx_frequency_mhz=Decimal("146.100"),
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
        params=FmParams(bandwidth_khz=Decimal("25.0")),
    )
    payload = json.loads(spec.model_dump_json())
    assert payload["mode"] == "FM"
    assert payload["source"] == "repeaterbook"
    assert payload["operational_status"] == "ON_AIR"  # name, NOT an int
    assert payload["params"] == {"bandwidth_khz": "25.0"}


def test_dmr_spec_carries_color_code() -> None:
    """DmrSpec should round-trip DMR-specific params."""
    spec = DmrSpec(
        name="VK4RDM",
        callsign="VK4RDM",
        rx_frequency_mhz=Decimal("439.000"),
        tx_frequency_mhz=Decimal("434.000"),
        ctcss_tx_hz=None,
        ctcss_rx_hz=None,
        dcs_code=None,
        latitude=Decimal("-27.5"),
        longitude=Decimal("153.0"),
        distance_km=None,
        operational_status="ON_AIR",
        use="OPEN",
        band="CM_70",
        notes=None,
        last_update=date(2026, 1, 1),
        source_id="QLD:99",
        params=DmrParams(dmr_id="5051", color_code="1"),
    )
    assert spec.params.color_code == "1"


def test_extra_key_on_params_is_rejected() -> None:
    """Params models forbid unknown keys, e.g. a color code on FmParams."""
    with pytest.raises(ValidationError):
        FmParams(color_code="1")  # type: ignore[call-arg]


def test_schema_rejects_mode_params_mismatch() -> None:
    """The published JSON Schema should reject a mode/params mismatch."""
    schema = repeater_spec_json_schema()
    bad = {
        "name": "x", "callsign": None,
        "rx_frequency_mhz": "146.7", "tx_frequency_mhz": "146.1",
        "ctcss_tx_hz": None, "ctcss_rx_hz": None, "dcs_code": None,
        "latitude": "-27.4", "longitude": "153.0", "distance_km": None,
        "operational_status": "ON_AIR", "use": "OPEN", "band": "M_2",
        "notes": None, "last_update": "2026-01-01", "source_id": "QLD:1",
        "mode": "FM", "params": {"color_code": "1"},  # FM can't have a color code
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_committed_schema_matches_model() -> None:
    """The committed schema file should match the model-derived schema."""
    committed = json.loads(schema_path().read_text(encoding="utf-8"))
    assert committed == repeater_spec_json_schema()


def test_freq_to_band() -> None:
    """freq_to_band should map known frequencies and reject unknown ones."""
    assert freq_to_band(Decimal("146.700")) == "M_2"
    assert freq_to_band(Decimal("438.000")) == "CM_70"
    assert freq_to_band(Decimal("27.000")) is None


def test_single_mode_expansion(sample_repeater: SampleRepeaterFactory) -> None:
    """A single-mode repeater should expand to exactly one RepeaterSpec."""
    specs = repeater_to_specs(sample_repeater(), distance_km=5.0)
    assert len(specs) == 1
    spec = specs[0]
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
    assert spec.params.bandwidth_khz == Decimal("25.0")


def test_multi_mode_expansion_carries_per_mode_params(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """A multi-mode repeater should carry each mode's own params block."""
    specs = repeater_to_specs(
        sample_repeater(
            analog_capable=True,
            dmr_capable=True,
            dmr_id="5051",
            dmr_color_code="1",
        ),
    )
    by_mode = {s.mode: s for s in specs}
    assert set(by_mode) == {RepeaterMode.FM, RepeaterMode.DMR}
    dmr = by_mode[RepeaterMode.DMR]
    fm = by_mode[RepeaterMode.FM]
    assert isinstance(dmr, DmrSpec)
    assert isinstance(fm, FmSpec)
    assert dmr.params.color_code == "1"
    assert fm.params.bandwidth_khz == Decimal("25.0")


def test_no_capability_defaults_to_fm(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """A repeater with no capability flags set should default to FM."""
    specs = repeater_to_specs(sample_repeater(analog_capable=False))
    assert [s.mode for s in specs] == [RepeaterMode.FM]


def test_name_falls_back_to_city(sample_repeater: SampleRepeaterFactory) -> None:
    """The spec name should fall back to the nearest city when callsign is None."""
    specs = repeater_to_specs(sample_repeater(callsign=None))
    assert specs[0].name == "Brisbane"


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
    raw: str | None, expected: tuple[Decimal | None, str | None],
) -> None:
    """parse_tone should split RepeaterBook tone strings into ctcss/dcs."""
    assert parse_tone(raw) == expected
