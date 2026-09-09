"""CSV export functionality for RepeaterBook.com data."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "csv_row_to_model",
    "csv_to_models",
)

import csv
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from repeaterbook.models import (
    Repeater,
    RepeaterCSV,
    Status,
    Use,
    parse_flag,
    parse_yes_no,
)

if TYPE_CHECKING:
    import io


def csv_row_to_model(c: RepeaterCSV, /) -> Repeater:
    """Convert CSV row to Repeater model."""
    d = Decimal

    def parse_tone(t: str) -> str | None:
        """Parse tone, return None if empty."""
        return None if t == "CSQ" else t

    return Repeater.model_validate(
        Repeater(
            callsign=c["Callsign"] or None,
            frequency=d(c["Frequency (MHz)"]),
            input_frequency=d(c["Input Frequency (MHz)"]),
            pl_ctcss_uplink=parse_tone(c["Tone"]),
            location_nearest_city=c["City"],
            county=c["County"] or None,
            state=c["State"] or None,
            country=c["Country"] or None,
            landmark=c["Landmark"] or None,
            latitude=d(c["Latitude"]),
            longitude=d(c["Longitude"]),
            # Tri-state: the CSV leaves these blank outside North America, and
            # blank is "unknown", not "not supported".
            ares=parse_yes_no(c["ARES"]),
            races=parse_yes_no(c["RACES"]),
            skywarn=parse_yes_no(c["SKYWARN"]),
            canwarn=parse_yes_no(c["CANWARN"]),
            allstar_node=c["AllStar Node"] or None,
            echolink_node=c["EchoLink Node"] or None,
            irlp_node=c["IRLP Node"] or None,
            wires_node=c["WIRES-X Node"] or None,
            # Two-state, same decoder as the JSON path. The CSV spells "not
            # supported" as a blank cell rather than "No"; `parse_flag`'s
            # default covers that, so both exports land on False.
            analog_capable=parse_flag(c["FM (analog)"]),
            dmr_capable=parse_flag(c["DMR"]),
            dmr_color_code=c["DMR Color Code"],
            d_star_capable=parse_flag(c["D-STAR Node"]),
            nxdn_capable=parse_flag(c["NXDN"]),
            apco_p_25_capable=parse_flag(c["P25"]),
            p_25_nac=c["P25 NAC"] or None,
            tetra_capable=parse_flag(c["TETRA"]),
            yaesu_system_fusion_capable=parse_flag(c["System Fusion"]),
            m17_capable=parse_flag(c["M17"]),
            pl_ctcss_tsq_downlink=parse_tone(c["TSQ Tone"]),
            # MISSING:
            state_id="",
            repeater_id=0,
            region=None,
            precise=False,
            use_membership=Use.OPEN,
            operational_status=Status.ON_AIR,
            dmr_id=None,
            m17_can=None,
            tetra_mcc=None,
            tetra_mnc=None,
            ysf_digital_id_uplink=None,
            ysf_digital_id_downlink=None,
            ysf_dsc=None,
            fm_bandwidth=Decimal("25.0"),
            notes=None,
            last_update=datetime.now(UTC).date(),
        )
    )


def csv_to_models(file: io.TextIOBase) -> list[Repeater]:
    """Convert CSV file to list of Repeater models.

    CSV does not include repeater ID or state ID, so these fields are populated based
    on the order of the rows and the state field.
    """
    reader = csv.DictReader(file)
    repeaters = [csv_row_to_model(cast("RepeaterCSV", row)) for row in reader]
    for i, repeater in enumerate(repeaters):
        repeater.state_id = f"{repeater.state or 'XX'}"
        repeater.repeater_id = i + 1
    return repeaters
