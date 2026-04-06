"""CSV export functionality for RepeaterBook data."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "YES",
    "csv_row_to_model",
    "csv_to_models",
)

import csv
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Final, cast

from repeaterbook.models import Repeater, RepeaterCSV, Status, Use

if TYPE_CHECKING:
    import io


YES: Final = "Yes"


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
            ares=c["ARES"] or None,
            races=c["RACES"] or None,
            skywarn=c["SKYWARN"] or None,
            canwarn=c["CANWARN"] or None,
            allstar_node=c["AllStar Node"] or None,
            echolink_node=c["EchoLink Node"] or None,
            irlp_node=c["IRLP Node"] or None,
            wires_node=c["WIRES-X Node"] or None,
            analog_capable=c["FM (analog)"] == YES,
            dmr_capable=c["DMR"] == YES,
            dmr_color_code=c["DMR Color Code"],
            d_star_capable=c["D-STAR Node"] == YES,
            nxdn_capable=c["NXDN"] == YES,
            apco_p_25_capable=c["P25"] == YES,
            p_25_nac=c["P25 NAC"] or None,
            tetra_capable=c["TETRA"] == YES,
            yaesu_system_fusion_capable=c["System Fusion"] == YES,
            m17_capable=c["M17"] == YES,
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
