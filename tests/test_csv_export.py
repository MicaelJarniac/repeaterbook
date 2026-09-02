"""Tests for the CSV ingest path.

The CSV export is a second, independent way into `Repeater`, and it carries
the same ARES/RACES/SKYWARN/CANWARN columns as the JSON export. It is easy to
fix one path and leave the other behind, so the emergency-field cases here
deliberately mirror those in `test_api_format.py`.
"""

from __future__ import annotations

import csv
import io
from typing import cast

from repeaterbook.csv_export import csv_row_to_model, csv_to_models
from repeaterbook.models import Emergency, RepeaterCSV

# The real header emitted by RepeaterBook's "All Columns" CSV download, kept
# verbatim so a column rename shows up as a failure here.
_HEADER = (
    'Callsign,"Frequency (MHz)","Input Frequency (MHz)","Offset (MHz)",Tone,'
    "City,County,State,Country,Landmark,Latitude,Longitude,"
    "ARES,RACES,SKYWARN,CANWARN,"
    '"AllStar Node","EchoLink Node","IRLP Node","WIRES-X Node",WIRES-X,'
    '"FM (analog)",ATV,DMR,"DMR Color Code","D-STAR Node","D-STAR Service",'
    'NXDN,"NXDN RAN",P25,"P25 NAC",TETRA,"System Fusion",M17,"Wide Area",'
    '"PL Tone","TSQ Tone"'
)


def _csv(*rows: str) -> io.StringIO:
    """Build a CSV file object from the real header and the given rows."""
    return io.StringIO("\n".join((_HEADER, *rows)) + "\n")


# A North American row, which is where these columns are populated.
_NORTH_AMERICA_ROW = (
    "W1HDN,147.045000,147.645000,0.6,CSQ,"
    "West Warwick,Kent,RI,US,,41.62850189,-71.66380310,"
    "Yes,No,Yes,No,"
    ",,,,,Yes,,,0,,,,,,,,,,,CSQ,CSQ"
)

# A Brazilian row, taken from a real download: the four columns are blank,
# exactly as the rest-of-world JSON export omits them.
_REST_OF_WORLD_ROW = (
    "PY4PWR,29.680000,29.580000,-0.1,CSQ,"
    "Poços de Caldas,,BR,BR,,-21.78840065,-46.56280136,"
    ",,,,"
    ",,,,,Yes,,,0,,,,,,,,,,,CSQ,CSQ"
)


def test_csv_emergency_fields_decode_to_booleans() -> None:
    """`"Yes"`/`"No"` in the CSV decode the same way as in the JSON export."""
    (rep,) = csv_to_models(_csv(_NORTH_AMERICA_ROW))

    assert rep.ares is True
    assert rep.races is False
    assert rep.skywarn is True
    assert rep.canwarn is False
    assert rep.emergency_services == frozenset({Emergency.ARES, Emergency.SKYWARN})


def test_csv_blank_emergency_fields_are_unknown() -> None:
    """A blank column is unknown, not "not supported"."""
    (rep,) = csv_to_models(_csv(_REST_OF_WORLD_ROW))

    assert rep.ares is None
    assert rep.races is None
    assert rep.skywarn is None
    assert rep.canwarn is None
    assert rep.emergency_services == frozenset()


def test_csv_to_models_assigns_ids_from_order_and_state() -> None:
    """Row order supplies the missing repeater id, and State the state id."""
    repeaters = csv_to_models(_csv(_NORTH_AMERICA_ROW, _REST_OF_WORLD_ROW))

    assert [rep.repeater_id for rep in repeaters] == [1, 2]
    assert [rep.state_id for rep in repeaters] == ["RI", "BR"]


def test_csv_row_to_model_parses_core_fields() -> None:
    """A single row maps onto the core columns."""
    (row,) = csv_to_models(_csv(_NORTH_AMERICA_ROW))

    assert row.callsign == "W1HDN"
    assert row.location_nearest_city == "West Warwick"
    assert row.county == "Kent"
    assert row.analog_capable is True
    assert row.dmr_capable is False
    # "CSQ" means no tone, and is folded to None rather than stored verbatim.
    assert row.pl_ctcss_uplink is None
    assert row.pl_ctcss_tsq_downlink is None


def test_csv_row_to_model_is_reachable_directly() -> None:
    """The per-row helper is public API, so exercise it without the reader."""
    reader = csv.DictReader(_csv(_NORTH_AMERICA_ROW))
    row = csv_row_to_model(cast("RepeaterCSV", next(iter(reader))))

    assert row.ares is True
    assert row.races is False
    # csv_row_to_model alone cannot know these; csv_to_models fills them in.
    assert row.state_id == ""
    assert row.repeater_id == 0
