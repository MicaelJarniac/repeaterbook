"""Regression tests for RepeaterBook API format drift.

We keep these tests offline by using minimal representative payload fragments.
"""

from __future__ import annotations

import pytest

from repeaterbook.exceptions import RepeaterBookRowError
from repeaterbook.services import json_to_model, json_to_models


def test_json_to_model_accepts_row_payload_with_extra_keys() -> None:
    """ROW export recently started including extra keys like `sponsor`.

    This should not break parsing.
    """
    payload = {
        "State ID": "BR",
        "Rptr ID": 1065,
        "Frequency": "53.750000",
        "Input Freq": "52.15000",
        "PL": "",
        "TSQ": "",
        "Nearest City": "Mateus Leme",
        "Landmark": "",
        "Region": None,
        "State": "Brazil",
        "Country": "Brazil",
        "Lat": "-19.98950005",
        "Long": "-44.43140030",
        "Precise": 0,
        "Callsign": "PY4RAP",
        "Use": "OPEN",
        "Operational Status": "On-air",
        "AllStar Node": "0",
        "EchoLink Node": "0",
        "IRLP Node": "",
        "Wires Node": "",
        "FM Analog": "Yes",
        "FM Bandwidth": "",
        "DMR": "No",
        "DMR Color Code": "",
        "DMR ID": "",
        "D-Star": "No",
        "NXDN": "No",
        "APCO P-25": "No",
        "P-25 NAC": "",
        "M17": "No",
        "M17 CAN": "",
        "Tetra": "No",
        "Tetra MCC": "",
        "Tetra MNC": "",
        "System Fusion": "No",
        "Notes": "",
        "Last Update": "2025-01-01",
        "sponsor": None,
    }

    rep = json_to_model(payload)  # type: ignore[arg-type]
    assert rep.country == "Brazil"


def test_json_to_model_accepts_north_america_payload_without_region() -> None:
    """North America export includes County/ARES/... and may omit Region.

    This used to raise KeyError; it should now parse.
    """
    payload = {
        "State ID": "06",
        "Rptr ID": 1,
        "Frequency": "146.880000",
        "Input Freq": "146.280000",
        "PL": "100.0",
        "TSQ": "100.0",
        "Nearest City": "Somewhere",
        "Landmark": "",
        # No Region key
        "County": "SomeCounty",
        "State": "California",
        "Country": "United States",
        "Lat": "34.0000",
        "Long": "-118.0000",
        "Precise": 1,
        "Callsign": "W6TEST",
        "Use": "OPEN",
        "Operational Status": "On-air",
        "ARES": "",
        "RACES": "",
        "SKYWARN": "",
        "CANWARN": "",
        "AllStar Node": "0",
        "EchoLink Node": "0",
        "IRLP Node": "",
        "Wires Node": "",
        "FM Analog": "Yes",
        "FM Bandwidth": "",
        "DMR": "No",
        "DMR Color Code": "",
        "DMR ID": "",
        "D-Star": "No",
        "NXDN": "No",
        "APCO P-25": "No",
        "P-25 NAC": "",
        "M17": "No",
        "M17 CAN": "",
        "Tetra": "No",
        "Tetra MCC": "",
        "Tetra MNC": "",
        "System Fusion": "No",
        "Notes": "",
        "Last Update": "2025-01-01",
    }

    rep = json_to_model(payload)  # type: ignore[arg-type]
    assert rep.region is None
    assert rep.county == "SomeCounty"


# The real Texas row that made state_id="48" undownloadable: a 1.2 GHz repeater
# published with a zero input frequency. Kept verbatim as the regression seed.
_TEXAS_BAD_ROW = {
    "State ID": "48",
    "Rptr ID": 24371,
    "Callsign": "W5AW",
    "Frequency": "1253.30000",
    "Input Freq": "0.00000",
    "Nearest City": "Brownwood",
    "Lat": "31.7093",
    "Long": "-98.9912",
    "Precise": 1,
    "Use": "OPEN",
    "Operational Status": "On-air",
    "FM Analog": "Yes",
    "Last Update": "2025-01-01",
}

_TEXAS_GOOD_ROW = {
    **_TEXAS_BAD_ROW,
    "Rptr ID": 1000,
    "Callsign": "W5GOOD",
    "Frequency": "146.940000",
    "Input Freq": "146.340000",
}


def test_zero_input_frequency_row_is_skipped_not_fatal() -> None:
    """A zero input frequency must cost one row, not the whole response.

    Regression for the Texas export, where repeater 48:24371 published
    `"Input Freq": "0.00000"` and took all 1668 good rows down with it.
    """
    rows = [_TEXAS_GOOD_ROW, _TEXAS_BAD_ROW, {**_TEXAS_GOOD_ROW, "Rptr ID": 1001}]

    repeaters = json_to_models(rows)  # type: ignore[arg-type]

    assert [rep.repeater_id for rep in repeaters] == [1000, 1001]


def test_zero_input_frequency_row_raises_under_strict() -> None:
    """Strict mode must name the offending row rather than silently dropping it."""
    with pytest.raises(RepeaterBookRowError) as exc:
        json_to_models([_TEXAS_GOOD_ROW, _TEXAS_BAD_ROW], strict=True)  # type: ignore[list-item]

    assert exc.value.label == "48:24371 (W5AW)"
    assert exc.value.row == _TEXAS_BAD_ROW
    assert "Frequency must be positive" in str(exc.value)
