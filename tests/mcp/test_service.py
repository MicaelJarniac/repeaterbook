"""Tests for the mcp service layer against a local aiohttp server."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pytest
from aiohttp import web
from anyio import Path as AsyncPath
from pycountry import countries
from yarl import URL

from repeaterbook.database import RepeaterBook
from repeaterbook.mcp.service import get_by_id, search, sync
from repeaterbook.models import ExportQuery, Repeater, Status, Use
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.utils import LatLon

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.anyio


_ROW_RESULT: dict[str, Any] = {
    "State ID": "QLD",
    "Rptr ID": 42,
    "Frequency": "146.700",
    "Input Freq": "146.100",
    "PL": "91.5",
    "TSQ": "",
    "Nearest City": "Brisbane",
    "Landmark": "",
    "Region": "Queensland",
    "State": "Queensland",
    "Country": "Australia",
    "Lat": "-27.47",
    "Long": "153.02",
    "Precise": 1,
    "Callsign": "VK4RBN",
    "Use": "OPEN",
    "Operational Status": "On-air",
    "FM Analog": "Yes",
    "FM Bandwidth": "25 kHz",
    "System Fusion": "Yes",
    "Last Update": "2026-01-01",
}


async def _row_handler(_: web.Request) -> web.Response:
    return web.json_response({"count": 1, "results": [_ROW_RESULT]})


async def test_sync_downloads_and_populates(
    local_server: Any,  # noqa: ANN401
    tmp_path: Path,
) -> None:
    """Test sync downloads repeaters from the ROW endpoint and populates the DB."""
    async with local_server(_row_handler, path="/api/exportROW.php") as url:
        base = URL.build(scheme=url.scheme, host=url.host, port=url.port)
        api = RepeaterBookAPI(base_url=base, working_dir=AsyncPath(tmp_path))
        db = RepeaterBook(working_dir=AsyncPath(tmp_path))
        query = ExportQuery(countries=frozenset({countries.get(name="Australia")}))

        count = await sync(api, db, query)

    assert count == 1
    rows = db.query()
    assert len(rows) == 1
    assert rows[0].callsign == "VK4RBN"


def _make_repeater(rid: int, lat: str, lon: str, **overrides: object) -> Repeater:
    base: dict[str, object] = {
        "state_id": "QLD",
        "repeater_id": rid,
        "frequency": Decimal("146.700"),
        "input_frequency": Decimal("146.100"),
        "pl_ctcss_uplink": "91.5",
        "pl_ctcss_tsq_downlink": None,
        "location_nearest_city": "Brisbane",
        "landmark": None,
        "region": None,
        "country": "Australia",
        "county": None,
        "state": "Queensland",
        "latitude": Decimal(lat),
        "longitude": Decimal(lon),
        "precise": True,
        "callsign": f"VK4R{rid}",
        "use_membership": Use.OPEN,
        "operational_status": Status.ON_AIR,
        "ares": None,
        "races": None,
        "skywarn": None,
        "canwarn": None,
        "allstar_node": None,
        "echolink_node": None,
        "irlp_node": None,
        "wires_node": None,
        "dmr_capable": False,
        "dmr_id": None,
        "dmr_color_code": None,
        "d_star_capable": False,
        "nxdn_capable": False,
        "apco_p_25_capable": False,
        "p_25_nac": None,
        "m17_capable": False,
        "m17_can": None,
        "tetra_capable": False,
        "tetra_mcc": None,
        "tetra_mnc": None,
        "yaesu_system_fusion_capable": False,
        "ysf_digital_id_uplink": None,
        "ysf_digital_id_downlink": None,
        "ysf_dsc": None,
        "analog_capable": True,
        "fm_bandwidth": Decimal("25.0"),
        "notes": None,
        "last_update": date(2026, 1, 1),
    }
    base.update(overrides)
    return Repeater(**base)


def test_search_orders_by_distance_and_clips_radius(tmp_path: Path) -> None:
    """Test search sorts by distance and excludes repeaters outside the radius."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.populate(
        [
            _make_repeater(1, "-27.47", "153.02"),  # ~0 km from origin
            _make_repeater(2, "-27.60", "153.02"),  # ~14 km south
            _make_repeater(3, "-28.50", "153.02"),  # ~114 km south (outside)
        ]
    )
    origin = LatLon(-27.47, 153.02)

    intents = search(db, origin, radius_km=40.0)

    assert [spec.source_id for spec in intents] == ["QLD:1", "QLD:2"]
    assert intents[0].distance_km is not None
    assert intents[0].distance_km <= intents[1].distance_km


def test_search_filters_by_mode(tmp_path: Path) -> None:
    """Test search only returns repeater-specs matching the requested modes."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.populate(
        [
            _make_repeater(
                1,
                "-27.47",
                "153.02",
                analog_capable=True,
                yaesu_system_fusion_capable=True,
            ),
        ]
    )
    origin = LatLon(-27.47, 153.02)

    intents = search(db, origin, radius_km=40.0, modes=["FUSION"])

    assert [spec.mode.value for spec in intents] == ["FUSION"]


def test_search_filters_by_band(tmp_path: Path) -> None:
    """Test search restricts results to repeaters within the requested band."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.populate(
        [
            _make_repeater(1, "-27.47", "153.02"),  # 146.700 -> M_2
            _make_repeater(
                2, "-27.47", "153.02", frequency=Decimal("438.000")
            ),  # CM_70
        ]
    )
    origin = LatLon(-27.47, 153.02)

    intents = search(db, origin, radius_km=40.0, bands=["M_2"])

    assert intents
    assert all(spec.band == "M_2" for spec in intents)
    assert "QLD:2" not in {spec.source_id for spec in intents}


def test_search_filters_by_status_and_use(tmp_path: Path) -> None:
    """Test search excludes repeaters not matching requested status and use."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.populate(
        [
            _make_repeater(1, "-27.47", "153.02"),  # ON_AIR / OPEN (defaults)
            _make_repeater(
                2,
                "-27.47",
                "153.02",
                operational_status=Status.OFF_AIR,
                use_membership=Use.CLOSED,
            ),
        ]
    )
    origin = LatLon(-27.47, 153.02)

    intents = search(db, origin, radius_km=40.0, statuses=["ON_AIR"], uses=["OPEN"])

    assert {spec.source_id for spec in intents} == {"QLD:1"}
    assert all(spec.operational_status == "ON_AIR" for spec in intents)
    assert all(spec.use == "OPEN" for spec in intents)


def test_search_unknown_mode_raises(tmp_path: Path) -> None:
    """Test search raises ValueError (not KeyError) for an unknown mode name."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.init_db()
    origin = LatLon(-27.47, 153.02)

    with pytest.raises(ValueError, match="mode"):
        search(db, origin, radius_km=40.0, modes=["NOTAMODE"])


def test_search_unknown_band_raises(tmp_path: Path) -> None:
    """Test search raises ValueError (not KeyError) for a typo'd band name."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.init_db()
    origin = LatLon(-27.47, 153.02)

    with pytest.raises(ValueError, match="band"):
        search(db, origin, radius_km=40.0, bands=["2m"])


def test_search_unknown_status_raises(tmp_path: Path) -> None:
    """Test search raises ValueError (not KeyError) for a typo'd status name."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.init_db()
    origin = LatLon(-27.47, 153.02)

    with pytest.raises(ValueError, match="status"):
        search(db, origin, radius_km=40.0, statuses=["on_air"])


def test_get_by_id_returns_intents(tmp_path: Path) -> None:
    """Test get_by_id returns specs for an existing repeater."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.populate([_make_repeater(7, "-27.47", "153.02")])

    intents = get_by_id(db, "QLD:7")

    assert len(intents) == 1
    assert intents[0].source_id == "QLD:7"


def test_get_by_id_missing_returns_empty(tmp_path: Path) -> None:
    """Test get_by_id returns empty list for a missing repeater."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.init_db()

    assert get_by_id(db, "QLD:999") == []


def test_get_by_id_malformed_id_returns_empty(tmp_path: Path) -> None:
    """Test get_by_id returns empty list for a non-numeric repeater id."""
    db = RepeaterBook(working_dir=AsyncPath(tmp_path))
    db.init_db()

    assert get_by_id(db, "garbage") == []
    assert get_by_id(db, "QLD:abc") == []
