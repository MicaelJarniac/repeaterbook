"""Neutral, source-agnostic repeater-spec contract and its mapper.

One RepeaterSpec is one programmable radio channel. A multi-mode repeater
expands to one spec per mode. `mode` discriminates a union whose `params`
object carries exactly that mode's parameters; `extra="forbid"` on each
params model is what makes a mode/params mismatch illegal by construction.
"""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "DStarParams",
    "DStarSpec",
    "DmrParams",
    "DmrSpec",
    "FmParams",
    "FmSpec",
    "FusionParams",
    "FusionSpec",
    "M17Params",
    "M17Spec",
    "NxdnParams",
    "NxdnSpec",
    "P25Params",
    "P25Spec",
    "RepeaterMode",
    "RepeaterSpec",
    "StatusName",
    "TetraParams",
    "TetraSpec",
    "UseName",
    "freq_to_band",
    "parse_tone",
    "repeater_spec_json_schema",
    "repeater_to_specs",
    "schema_path",
    "write_schema",
)

import json
from datetime import date  # noqa: TC003
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

if TYPE_CHECKING:
    from repeaterbook.models import Repeater


class RepeaterMode(StrEnum):
    """A single radio operating mode for one programmable channel."""

    FM = "FM"
    DMR = "DMR"
    DSTAR = "DSTAR"
    FUSION = "FUSION"
    P25 = "P25"
    NXDN = "NXDN"
    TETRA = "TETRA"
    M17 = "M17"


# Wire uses the *names* of the core Status/Use enums (e.g. "ON_AIR", "OPEN").
# Typing these as the enums themselves would serialize their integer auto()
# values instead; test_status_use_literals_match_enums guards against drift.
StatusName: TypeAlias = Literal["OFF_AIR", "ON_AIR", "UNKNOWN"]
UseName: TypeAlias = Literal["OPEN", "PRIVATE", "CLOSED"]


class _Params(BaseModel):
    """Base for per-mode parameter blocks. Forbids unknown keys."""

    model_config = ConfigDict(extra="forbid")


class FmParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    bandwidth_khz: Decimal | None = None


class DmrParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    dmr_id: str | None = None
    color_code: str | None = None


class DStarParams(_Params):
    """RepeaterBook carries no D-STAR parameters; intentionally empty."""


class FusionParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    digital_id_uplink: str | None = None
    digital_id_downlink: str | None = None
    dsc: str | None = None


class P25Params(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    nac: str | None = None


class NxdnParams(_Params):
    """RepeaterBook carries no NXDN parameters; intentionally empty."""


class TetraParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mcc: str | None = None
    mnc: str | None = None


class M17Params(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    can: str | None = None


class _BaseSpec(BaseModel):
    """Fields common to every mode."""

    name: str
    callsign: str | None
    rx_frequency_mhz: Decimal
    tx_frequency_mhz: Decimal
    ctcss_tx_hz: Decimal | None
    ctcss_rx_hz: Decimal | None
    dcs_code: str | None
    latitude: Decimal
    longitude: Decimal
    distance_km: float | None
    operational_status: StatusName
    use: UseName
    band: str | None
    notes: str | None
    last_update: date
    source: str = "repeaterbook"
    source_id: str


# Spec subclasses intentionally have no docstrings: BaseModel puts a class's
# docstring into the JSON Schema "description" for that $def, and the schema
# is a committed, drift-checked artifact (test_committed_schema_matches_model).


class FmSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.FM] = RepeaterMode.FM
    params: FmParams = FmParams()


class DmrSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.DMR] = RepeaterMode.DMR
    params: DmrParams = DmrParams()


class DStarSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.DSTAR] = RepeaterMode.DSTAR
    params: DStarParams = DStarParams()


class FusionSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.FUSION] = RepeaterMode.FUSION
    params: FusionParams = FusionParams()


class P25Spec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.P25] = RepeaterMode.P25
    params: P25Params = P25Params()


class NxdnSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.NXDN] = RepeaterMode.NXDN
    params: NxdnParams = NxdnParams()


class TetraSpec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.TETRA] = RepeaterMode.TETRA
    params: TetraParams = TetraParams()


class M17Spec(_BaseSpec):  # noqa: D101
    mode: Literal[RepeaterMode.M17] = RepeaterMode.M17
    params: M17Params = M17Params()


RepeaterSpec: TypeAlias = Annotated[
    FmSpec
    | DmrSpec
    | DStarSpec
    | FusionSpec
    | P25Spec
    | NxdnSpec
    | TetraSpec
    | M17Spec,
    Field(discriminator="mode"),
]

_ADAPTER: TypeAdapter[RepeaterSpec] = TypeAdapter(RepeaterSpec)


def repeater_spec_json_schema() -> dict[str, object]:
    """Return the JSON Schema for the RepeaterSpec union."""
    return _ADAPTER.json_schema()


def schema_path() -> Path:
    """Return the path to the published repeater-spec JSON Schema."""
    return Path(__file__).parent / "schemas" / "repeater_spec.schema.json"


def write_schema() -> None:
    """Regenerate the published JSON Schema from the model."""
    path = schema_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(repeater_spec_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )


def parse_tone(raw: str | None) -> tuple[Decimal | None, str | None]:
    """Split a RepeaterBook tone string into (ctcss_hz, dcs_code).

    RepeaterBook mixes CTCSS frequencies and DCS codes in one string field.
    Rule: "." -> CTCSS Decimal; "D"/"d" prefix -> DCS (letter stripped+uppercased);
    all-digits -> DCS; else (None, None).
    """
    if raw is None or not (value := raw.strip()):
        return (None, None)
    if "." in value:
        try:
            return (Decimal(value), None)
        except InvalidOperation:
            return (None, None)
    if value[0] in {"D", "d"}:
        return (None, value[1:].upper())
    if value.isdigit():
        return (None, value)
    return (None, None)


def freq_to_band(freq: Decimal) -> str | None:
    """Return the amateur band name for a frequency, or None if unknown."""
    # Lazy import: breaks a models<->spec import cycle.
    from repeaterbook.queries import Bands  # noqa: PLC0415

    for b in Bands:
        if b.low <= freq <= b.high:
            return b.name
    return None


# Maps a mode to (Spec subclass, Repeater accessor attribute).
_MODE_DISPATCH: dict[RepeaterMode, tuple[type[_BaseSpec], str]] = {
    RepeaterMode.FM: (FmSpec, "fm"),
    RepeaterMode.DMR: (DmrSpec, "dmr"),
    RepeaterMode.DSTAR: (DStarSpec, "dstar"),
    RepeaterMode.FUSION: (FusionSpec, "fusion"),
    RepeaterMode.P25: (P25Spec, "p25"),
    RepeaterMode.NXDN: (NxdnSpec, "nxdn"),
    RepeaterMode.TETRA: (TetraSpec, "tetra"),
    RepeaterMode.M17: (M17Spec, "m17"),
}


def repeater_to_specs(
    rep: Repeater,
    distance_km: float | None = None,
) -> list[RepeaterSpec]:
    """Expand one repeater into one spec per supported mode."""
    ctcss_tx, dcs_tx = parse_tone(rep.pl_ctcss_uplink)
    ctcss_rx, dcs_rx = parse_tone(rep.pl_ctcss_tsq_downlink)
    common: dict[str, object] = {
        "name": rep.callsign or rep.location_nearest_city,
        "callsign": rep.callsign,
        "rx_frequency_mhz": rep.frequency,
        "tx_frequency_mhz": rep.input_frequency,
        "ctcss_tx_hz": ctcss_tx,
        "ctcss_rx_hz": ctcss_rx,
        "dcs_code": dcs_tx or dcs_rx,
        "latitude": rep.latitude,
        "longitude": rep.longitude,
        "distance_km": distance_km,
        "operational_status": rep.operational_status.name,
        "use": rep.use_membership.name,
        "band": freq_to_band(rep.frequency),
        "notes": rep.notes,
        "last_update": rep.last_update,
        "source_id": f"{rep.state_id}:{rep.repeater_id}",
    }
    modes = list(rep.modes) or [RepeaterMode.FM]
    specs: list[RepeaterSpec] = []
    for mode in modes:
        spec_cls, accessor = _MODE_DISPATCH[mode]
        params = getattr(rep, accessor) or spec_cls.model_fields["params"].default
        spec_data = {**common, "mode": mode, "params": params}
        specs.append(_ADAPTER.validate_python(spec_data))
    return specs
