"""Neutral, source-agnostic repeater-spec contract model."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "RepeaterMode",
    "RepeaterSpec",
    "schema_path",
    "write_schema",
)

import json
from datetime import date  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


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


class RepeaterSpec(BaseModel):
    """One programmable radio channel, derived from a repeater.

    Carries absolute rx/tx frequencies so the consuming radio owns the
    duplex/offset derivation. Multi-mode repeaters expand to one intent per mode.
    """

    name: str
    callsign: str | None
    rx_frequency_mhz: Decimal
    tx_frequency_mhz: Decimal
    mode: RepeaterMode
    ctcss_tx_hz: Decimal | None
    ctcss_rx_hz: Decimal | None
    dcs_code: str | None
    latitude: Decimal
    longitude: Decimal
    distance_km: float | None
    operational_status: str
    use: str
    band: str | None
    notes: str | None
    last_update: date
    source: str = "repeaterbook"
    source_id: str


def schema_path() -> Path:
    """Return the path to the published repeater-spec JSON Schema."""
    return Path(__file__).parent / "schemas" / "repeater_spec.schema.json"


def write_schema() -> None:
    """Regenerate the published JSON Schema from the model."""
    path = schema_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(RepeaterSpec.model_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )
