"""Pure mapping from RepeaterBook rows to repeater-spec rows."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "freq_to_band",
    "parse_tone",
    "repeater_to_specs",
)

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from repeaterbook.mcp.models import RepeaterMode, RepeaterSpec
from repeaterbook.queries import Bands

if TYPE_CHECKING:
    from repeaterbook.models import Repeater

_CAPABILITY_MODES: tuple[tuple[str, RepeaterMode], ...] = (
    ("analog_capable", RepeaterMode.FM),
    ("dmr_capable", RepeaterMode.DMR),
    ("d_star_capable", RepeaterMode.DSTAR),
    ("yaesu_system_fusion_capable", RepeaterMode.FUSION),
    ("apco_p_25_capable", RepeaterMode.P25),
    ("nxdn_capable", RepeaterMode.NXDN),
    ("tetra_capable", RepeaterMode.TETRA),
    ("m17_capable", RepeaterMode.M17),
)


def parse_tone(raw: str | None) -> tuple[Decimal | None, str | None]:
    """Split a RepeaterBook tone string into (ctcss_hz, dcs_code).

    RepeaterBook mixes CTCSS frequencies and DCS codes in one string field.
    Rule: "." → CTCSS Decimal; "D"/"d" prefix → DCS (letter stripped+uppercased);
    all-digits → DCS; else (None, None).
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
    for b in Bands:
        if b.low <= freq <= b.high:
            return b.name
    return None


def repeater_to_specs(
    rep: Repeater,
    distance_km: float | None = None,
) -> list[RepeaterSpec]:
    """Expand one repeater into one repeater-spec per supported mode."""
    ctcss_tx, dcs_tx = parse_tone(rep.pl_ctcss_uplink)
    ctcss_rx, dcs_rx = parse_tone(rep.pl_ctcss_tsq_downlink)
    modes = [mode for attr, mode in _CAPABILITY_MODES if getattr(rep, attr)]
    if not modes:
        modes = [RepeaterMode.FM]
    return [
        RepeaterSpec(
            name=rep.callsign or rep.location_nearest_city,
            callsign=rep.callsign,
            rx_frequency_mhz=rep.frequency,
            tx_frequency_mhz=rep.input_frequency,
            mode=mode,
            ctcss_tx_hz=ctcss_tx,
            ctcss_rx_hz=ctcss_rx,
            dcs_code=dcs_tx or dcs_rx,
            latitude=rep.latitude,
            longitude=rep.longitude,
            distance_km=distance_km,
            operational_status=rep.operational_status.name,
            use=rep.use_membership.name,
            band=freq_to_band(rep.frequency),
            notes=rep.notes,
            last_update=rep.last_update,
            source_id=f"{rep.state_id}:{rep.repeater_id}",
        )
        for mode in modes
    ]
