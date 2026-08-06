"""Neutral, source-agnostic repeater-spec contract and its mapper.

One RepeaterSpec is one programmable radio channel. A multi-mode repeater
expands to one spec per mode. `params` is a union discriminated on its own
`mode` field, and `extra="forbid"` on each params model is what makes a
mode/params mismatch illegal by construction. `RepeaterSpec.mode` re-exposes
`params.mode` at the top level, so the two can never disagree.
"""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "DStarParams",
    "DmrParams",
    "FmParams",
    "FusionParams",
    "M17Params",
    "NxdnParams",
    "P25Params",
    "Params",
    "RepeaterMode",
    "RepeaterSpec",
    "StatusName",
    "TetraParams",
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

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, computed_field

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
    mode: Literal[RepeaterMode.FM] = RepeaterMode.FM
    bandwidth_khz: Decimal | None = None


class DmrParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mode: Literal[RepeaterMode.DMR] = RepeaterMode.DMR
    dmr_id: str | None = None
    color_code: str | None = None


class DStarParams(_Params):
    """RepeaterBook carries no D-STAR parameters; intentionally empty."""

    mode: Literal[RepeaterMode.DSTAR] = RepeaterMode.DSTAR


class FusionParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mode: Literal[RepeaterMode.FUSION] = RepeaterMode.FUSION
    digital_id_uplink: str | None = None
    digital_id_downlink: str | None = None
    dsc: str | None = None


class P25Params(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mode: Literal[RepeaterMode.P25] = RepeaterMode.P25
    nac: str | None = None


class NxdnParams(_Params):
    """RepeaterBook carries no NXDN parameters; intentionally empty."""

    mode: Literal[RepeaterMode.NXDN] = RepeaterMode.NXDN


class TetraParams(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mode: Literal[RepeaterMode.TETRA] = RepeaterMode.TETRA
    mcc: str | None = None
    mnc: str | None = None


class M17Params(_Params):  # noqa: D101 -- docstring would leak into the committed JSON Schema
    mode: Literal[RepeaterMode.M17] = RepeaterMode.M17
    can: str | None = None


_ParamsUnion: TypeAlias = (
    FmParams
    | DmrParams
    | DStarParams
    | FusionParams
    | P25Params
    | NxdnParams
    | TetraParams
    | M17Params
)

Params: TypeAlias = Annotated[_ParamsUnion, Field(discriminator="mode")]


class RepeaterSpec(BaseModel):
    """One programmable radio channel; `params` is discriminated on its mode."""

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
    params: Params

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mode(self) -> RepeaterMode:
        """The channel's mode, derived from `params` so the two cannot disagree."""
        return self.params.mode


_ADAPTER: TypeAdapter[RepeaterSpec] = TypeAdapter(RepeaterSpec)


def repeater_spec_json_schema() -> dict[str, object]:
    """Return the JSON Schema for RepeaterSpec, as it appears on the wire.

    Generated in serialization mode on purpose: `mode` is a computed field, and
    Pydantic emits computed fields only into the serialization schema. The
    default validation mode would publish a contract missing the top-level
    `mode` key that this model actually serializes.
    """
    return _ADAPTER.json_schema(mode="serialization")


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


# Maps a mode to the Repeater accessor returning that mode's params.
_ACCESSOR: dict[RepeaterMode, str] = {
    RepeaterMode.FM: "fm",
    RepeaterMode.DMR: "dmr",
    RepeaterMode.DSTAR: "dstar",
    RepeaterMode.FUSION: "fusion",
    RepeaterMode.P25: "p25",
    RepeaterMode.NXDN: "nxdn",
    RepeaterMode.TETRA: "tetra",
    RepeaterMode.M17: "m17",
}

# Fallback params per mode. `mode` is derived from `params`, so falling back to a
# single shared default (e.g. always FmParams) would silently relabel a channel's
# mode instead of failing. Keep these mode-correct.
_DEFAULT_PARAMS: dict[RepeaterMode, type[_ParamsUnion]] = {
    RepeaterMode.FM: FmParams,
    RepeaterMode.DMR: DmrParams,
    RepeaterMode.DSTAR: DStarParams,
    RepeaterMode.FUSION: FusionParams,
    RepeaterMode.P25: P25Params,
    RepeaterMode.NXDN: NxdnParams,
    RepeaterMode.TETRA: TetraParams,
    RepeaterMode.M17: M17Params,
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
    modes = rep.modes or frozenset({RepeaterMode.FM})
    return [
        RepeaterSpec(
            **common,  # type: ignore[arg-type]
            params=getattr(rep, _ACCESSOR[mode]) or _DEFAULT_PARAMS[mode](),
        )
        for mode in modes
    ]
