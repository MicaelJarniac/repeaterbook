"""Tests for the core RepeaterSpec contract."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import jsonschema
import pytest
from pydantic import ValidationError

from repeaterbook.models import Status, Use
from repeaterbook.queries import BandName, Bands
from repeaterbook.spec import (
    _ACCESSOR,
    _DEFAULT_PARAMS,
    DmrParams,
    FmParams,
    RepeaterMode,
    RepeaterSpec,
    RepeaterStatus,
    RepeaterUse,
    Tone,
    freq_to_band,
    parse_tone,
    repeater_spec_json_schema,
    repeater_to_specs,
    schema_path,
    write_schema,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests._types import SampleRepeaterFactory


def _spec(**overrides: object) -> RepeaterSpec:
    """Build a valid RepeaterSpec, overriding any field by keyword."""
    base: dict[str, object] = {
        "name": "VK4RBN",
        "callsign": "VK4RBN",
        "nearest_city": "Brisbane",
        "rx_frequency_mhz": Decimal("146.700"),
        "tx_frequency_mhz": Decimal("146.100"),
        "ctcss_tx_hz": Decimal("91.5"),
        "ctcss_rx_hz": None,
        "dcs_tx_code": None,
        "dcs_rx_code": None,
        "latitude": Decimal("-27.47"),
        "longitude": Decimal("153.02"),
        "distance_km": Decimal("12.3"),
        "operational_status": RepeaterStatus.ON_AIR,
        "use": RepeaterUse.OPEN,
        "band": "M_2",
        "notes": None,
        "last_update": datetime(2026, 1, 1, tzinfo=UTC),
        "source_id": "QLD:42",
        "params": FmParams(bandwidth_khz=Decimal("25.0")),
    }
    base.update(overrides)
    return RepeaterSpec(**base)  # type: ignore[arg-type]


def test_repeater_mode_members() -> None:
    """RepeaterMode should have exactly the eight supported wire modes."""
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


def test_status_use_enums_mirror_core() -> None:
    """The spec's StrEnums should track the core Status/Use enum member names."""
    assert {s.name for s in RepeaterStatus} == {s.name for s in Status}
    assert {u.name for u in RepeaterUse} == {u.name for u in Use}
    # The wire value *is* the member name, so no int leaks into the contract.
    assert all(s.value == s.name for s in RepeaterStatus)
    assert all(u.value == u.name for u in RepeaterUse)


def test_band_name_matches_bands() -> None:
    """BandName should mirror Bands member-for-member."""
    assert {b.name for b in BandName} == {b.name for b in Bands}
    assert all(b.value == b.name for b in BandName)


def test_fm_spec_defaults_and_wire_shape() -> None:
    """RepeaterSpec should derive mode from params and serialize names, not ints."""
    payload = json.loads(_spec().model_dump_json())
    assert payload["mode"] == "FM"
    assert payload["source"] == "repeaterbook"
    assert payload["operational_status"] == "ON_AIR"  # name, NOT an int
    assert payload["use"] == "OPEN"
    # `mode` rides inside params too: it is the discriminator.
    assert payload["params"] == {"mode": "FM", "bandwidth_khz": "25.0"}


def test_dmr_spec_carries_color_code() -> None:
    """RepeaterSpec should round-trip DMR-specific params."""
    spec = _spec(params=DmrParams(dmr_id="5051", color_code="1"))
    assert isinstance(spec.params, DmrParams)
    assert spec.params.color_code == "1"
    assert spec.mode is RepeaterMode.DMR


def test_spec_round_trips_through_json() -> None:
    """A serialized spec should parse back into an equal model."""
    spec = _spec()
    assert RepeaterSpec.model_validate_json(spec.model_dump_json()) == spec


def test_extra_key_on_params_is_rejected() -> None:
    """Params models forbid unknown keys, e.g. a color code on FmParams."""
    with pytest.raises(ValidationError) as excinfo:
        FmParams(color_code="1")  # type: ignore[call-arg]
    assert excinfo.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rx_frequency_mhz", Decimal(-1)),
        ("rx_frequency_mhz", Decimal(0)),
        ("latitude", Decimal(91)),
        ("latitude", Decimal(-91)),
        ("longitude", Decimal(181)),
        ("ctcss_tx_hz", Decimal("66.9")),
        ("ctcss_tx_hz", Decimal(255)),
        ("distance_km", Decimal(-1)),
    ],
)
def test_quantity_constraints_are_enforced(field: str, value: Decimal) -> None:
    """The named quantity aliases should reject out-of-range values."""
    with pytest.raises(ValidationError):
        _spec(**{field: value})


def test_schema_rejects_mode_params_mismatch() -> None:
    """The published JSON Schema should reject a mode/params mismatch.

    `mode` at the root is required (it's a `readOnly` computed field, but
    `readOnly` does not exempt a key from `required` in JSON Schema), so it
    must still be present here or validation fails at the root before the
    params union is ever consulted. Asserting the error's `absolute_path`
    is `["params"]` pins the rejection to the union discriminator doing its
    job, not to a missing top-level key.
    """
    schema = repeater_spec_json_schema()
    bad = json.loads(_spec().model_dump_json())
    bad["params"] = {"mode": "FM", "color_code": "1"}  # FM can't have a color code
    with pytest.raises(jsonschema.ValidationError) as excinfo:
        jsonschema.validate(bad, schema)
    assert list(excinfo.value.absolute_path) == ["params"]


def test_committed_schema_matches_model() -> None:
    """The committed schema file should match the model-derived schema."""
    committed = json.loads(schema_path().read_text(encoding="utf-8"))
    assert committed == repeater_spec_json_schema()


def test_schema_shares_quantity_definitions() -> None:
    """Quantities should be emitted once under `$defs` and referenced, not inlined."""
    schema = repeater_spec_json_schema()
    defs = schema["$defs"]
    assert isinstance(defs, dict)
    for name in ("FrequencyMHz", "CtcssToneHz", "LatitudeDeg", "LongitudeDeg"):
        assert name in defs, f"{name} should be a shared definition"

    props = schema["properties"]
    assert isinstance(props, dict)
    assert props["rx_frequency_mhz"] == {"$ref": "#/$defs/FrequencyMHz"}
    assert props["tx_frequency_mhz"] == {"$ref": "#/$defs/FrequencyMHz"}
    assert props["latitude"] == {"$ref": "#/$defs/LatitudeDeg"}
    assert props["longitude"] == {"$ref": "#/$defs/LongitudeDeg"}


def test_committed_schema_documents_wire_shape(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """The published schema must describe the payload the library actually emits.

    Guards a Pydantic footgun: a `mode` exposed via @computed_field lands only in
    the *serialization* schema, so generating the committed file in the default
    validation mode would silently drop the top-level `mode` key that dict
    consumers (e.g. the FTM-150 exporter) read.
    """
    committed = json.loads(schema_path().read_text(encoding="utf-8"))
    assert "mode" in committed["properties"], (
        "published schema lost its top-level `mode` property"
    )

    spec = repeater_to_specs(sample_repeater(), distance_km=Decimal("5.0"))[0]
    wire = json.loads(spec.model_dump_json())
    assert wire["mode"] == "FM"
    jsonschema.validate(wire, committed)


def test_freq_to_band() -> None:
    """freq_to_band should map known frequencies and reject unknown ones."""
    assert freq_to_band(Decimal("146.700")) == "M_2"
    assert freq_to_band(Decimal("438.000")) == "CM_70"
    assert freq_to_band(Decimal("27.000")) is None


def test_single_mode_expansion(sample_repeater: SampleRepeaterFactory) -> None:
    """A single-mode repeater should expand to exactly one RepeaterSpec."""
    specs = repeater_to_specs(sample_repeater(), distance_km=Decimal("5.0"))
    assert len(specs) == 1
    spec = specs[0]
    assert spec.mode is RepeaterMode.FM
    assert spec.name == "VK4RBN"
    assert spec.nearest_city == "Brisbane"
    assert spec.rx_frequency_mhz == Decimal("146.700")
    assert spec.tx_frequency_mhz == Decimal("146.100")
    assert spec.ctcss_tx_hz == Decimal("91.5")
    assert spec.band == "M_2"
    assert spec.distance_km == Decimal("5.0")
    assert spec.source_id == "QLD:42"
    assert spec.operational_status is RepeaterStatus.ON_AIR
    assert spec.use is RepeaterUse.OPEN
    assert isinstance(spec.params, FmParams)
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
    assert isinstance(dmr.params, DmrParams)
    assert isinstance(fm.params, FmParams)
    assert dmr.params.color_code == "1"
    assert fm.params.bandwidth_khz == Decimal("25.0")


def test_no_capability_defaults_to_fm(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """A repeater with no capability flags set should default to FM."""
    specs = repeater_to_specs(sample_repeater(analog_capable=False))
    assert [s.mode for s in specs] == [RepeaterMode.FM]


# Maps a mode to the Repeater capability flag that enables it. Flag names are
# not derivable from the mode name (e.g. DSTAR -> d_star_capable, FUSION ->
# yaesu_system_fusion_capable), so this has to be spelled out by hand; the
# *set of modes under test* below does not, and comes straight from the enum.
_MODE_FLAGS: dict[RepeaterMode, str] = {
    RepeaterMode.FM: "analog_capable",
    RepeaterMode.DMR: "dmr_capable",
    RepeaterMode.DSTAR: "d_star_capable",
    RepeaterMode.FUSION: "yaesu_system_fusion_capable",
    RepeaterMode.P25: "apco_p_25_capable",
    RepeaterMode.NXDN: "nxdn_capable",
    RepeaterMode.TETRA: "tetra_capable",
    RepeaterMode.M17: "m17_capable",
}


@pytest.mark.parametrize("mode", list(RepeaterMode))
def test_repeater_to_specs_covers_every_mode(
    sample_repeater: SampleRepeaterFactory,
    mode: RepeaterMode,
) -> None:
    """repeater_to_specs, `_ACCESSOR`, and `_DEFAULT_PARAMS` must cover every mode.

    Parametrizing over `list(RepeaterMode)` (rather than a hand-written list of
    the eight current mode names) means a ninth mode added to the enum shows up
    here automatically -- as a failure, via the KeyError in `_MODE_FLAGS`, until
    the mapper's tables are updated to match.
    """
    flags: dict[str, object] = {"analog_capable": False}
    flags[_MODE_FLAGS[mode]] = True
    specs = repeater_to_specs(sample_repeater(**flags))
    assert len(specs) == 1
    spec = specs[0]
    assert spec.mode is mode
    assert spec.mode is spec.params.mode


@pytest.mark.parametrize("mode", list(RepeaterMode))
def test_accessor_and_default_params_agree_on_mode(
    sample_repeater: SampleRepeaterFactory,
    mode: RepeaterMode,
) -> None:
    """`_ACCESSOR` and `_DEFAULT_PARAMS` must map every mode to the same params type.

    Both tables are keyed by `RepeaterMode` independently, so nothing but a test
    stops one from drifting from the other: a cross-wired accessor lambda (e.g.
    `NXDN: lambda r: r.tetra`) type-checks fine since every accessor returns the
    same `_ParamsUnion | None`, and a corrupted `_DEFAULT_PARAMS` entry is masked
    by `or _DEFAULT_PARAMS[mode]()` whenever the accessor already returns a real
    object. Parametrizing over `list(RepeaterMode)` means a ninth mode gets a
    case automatically.
    """
    default = _DEFAULT_PARAMS[mode]()
    assert default.mode is mode

    flags: dict[str, object] = {"analog_capable": False}
    flags[_MODE_FLAGS[mode]] = True
    rep = sample_repeater(**flags)
    result = _ACCESSOR[mode](rep)
    assert result is not None
    assert type(result) is _DEFAULT_PARAMS[mode]


def test_name_falls_back_to_city(sample_repeater: SampleRepeaterFactory) -> None:
    """The spec name should fall back to the nearest city when callsign is None."""
    specs = repeater_to_specs(sample_repeater(callsign=None))
    assert specs[0].name == "Brisbane"


def test_uplink_and_downlink_dcs_are_kept_apart(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Each direction's DCS code should survive independently.

    A single merged `dcs_code` would silently drop the downlink code whenever
    the uplink also carried one.
    """
    specs = repeater_to_specs(
        sample_repeater(pl_ctcss_uplink="D023", pl_ctcss_tsq_downlink="D047"),
    )
    assert specs[0].dcs_tx_code == "023"
    assert specs[0].dcs_rx_code == "047"


def test_uplink_and_downlink_ctcss_are_kept_apart(
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Each direction's CTCSS tone should survive independently."""
    specs = repeater_to_specs(
        sample_repeater(pl_ctcss_uplink="91.5", pl_ctcss_tsq_downlink="88.5"),
    )
    assert specs[0].ctcss_tx_hz == Decimal("91.5")
    assert specs[0].ctcss_rx_hz == Decimal("88.5")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("91.5", Tone(Decimal("91.5"), None)),
        ("100.0", Tone(Decimal("100.0"), None)),
        ("D023", Tone(None, "023")),
        ("023", Tone(None, "023")),
        ("D023N", Tone(None, "023N")),
        ("", Tone(None, None)),
        ("   ", Tone(None, None)),
        (None, Tone(None, None)),
        ("garbage", Tone(None, None)),
        # Looks like a CTCSS value (has a dot) but isn't parseable.
        ("1.2.3", Tone(None, None)),
        (".", Tone(None, None)),
    ],
)
def test_parse_tone(raw: str | None, expected: Tone) -> None:
    """parse_tone should split RepeaterBook tone strings into ctcss/dcs."""
    assert parse_tone(raw) == expected


def test_parse_tone_returns_named_fields() -> None:
    """The Tone result should be addressable by name, not just position."""
    tone = parse_tone("91.5")
    assert tone.ctcss == Decimal("91.5")
    assert tone.dcs is None


def test_write_schema_round_trips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """write_schema should create its parent dir and emit the model's schema."""
    target = tmp_path / "nested" / "repeater_spec.schema.json"
    monkeypatch.setattr("repeaterbook.spec.schema_path", lambda: target)

    write_schema()

    assert json.loads(target.read_text(encoding="utf-8")) == repeater_spec_json_schema()
    assert target.read_text(encoding="utf-8").endswith("\n")
