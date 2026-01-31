"""Regression tests for RepeaterBook API format drift.

We keep these tests offline by using minimal representative payload fragments.
"""

from __future__ import annotations

from repeaterbook.services import json_to_model


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
