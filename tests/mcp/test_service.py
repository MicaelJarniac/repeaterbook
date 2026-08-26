"""Tests for the mcp service layer against a local aiohttp server."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pytest
from aiohttp import web
from anyio import Path as AsyncPath
from pycountry import countries
from yarl import URL

from repeaterbook.database import RepeaterBook
from repeaterbook.mcp.service import get_by_id, search, sync
from repeaterbook.models import ExportQuery, Status, Use
from repeaterbook.queries import BandName
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.spec import RepeaterMode, RepeaterStatus, RepeaterUse
from repeaterbook.utils import LatLon

if TYPE_CHECKING:
    from pathlib import Path

    from repeaterbook.models import Repeater
    from tests._types import PopulatedDbFactory, SampleRepeaterFactory

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

_ORIGIN = LatLon(-27.47, 153.02)


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

        result = await sync(api, db, query)

    assert result.count == 1
    assert result.truncated is False
    rows = db.query()
    assert len(rows) == 1
    assert rows[0].callsign == "VK4RBN"


@pytest.fixture
def populated_db(tmp_path: Path) -> PopulatedDbFactory:
    """Return a factory that builds a DB pre-populated with the given repeaters."""

    def _populate(*repeaters: Repeater) -> RepeaterBook:
        db = RepeaterBook(working_dir=AsyncPath(tmp_path))
        if repeaters:
            db.populate(repeaters)
        else:
            db.init_db()
        return db

    return _populate


def test_search_orders_by_distance_and_clips_radius(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test search sorts by distance and excludes repeaters outside the radius."""
    db = populated_db(
        sample_repeater(repeater_id=1),  # ~0 km from origin
        sample_repeater(repeater_id=2, latitude=Decimal("-27.60")),  # ~14 km
        sample_repeater(repeater_id=3, latitude=Decimal("-28.50")),  # ~114 km
    )

    specs = search(db, _ORIGIN, radius_km=40.0)

    assert [spec.source_id for spec in specs] == ["QLD:1", "QLD:2"]
    first, second = specs[0].distance_km, specs[1].distance_km
    assert first is not None
    assert second is not None
    assert first <= second


def test_search_filters_by_mode(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test search only returns repeater-specs matching the requested modes."""
    db = populated_db(
        sample_repeater(
            repeater_id=1,
            analog_capable=True,
            yaesu_system_fusion_capable=True,
        ),
    )

    specs = search(db, _ORIGIN, radius_km=40.0, modes={RepeaterMode.FUSION})

    assert [spec.mode for spec in specs] == [RepeaterMode.FUSION]


def test_search_filters_by_band(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test search restricts results to repeaters within the requested band."""
    db = populated_db(
        sample_repeater(repeater_id=1),  # 146.700 -> M_2
        sample_repeater(repeater_id=2, frequency=Decimal("438.000")),  # CM_70
    )

    specs = search(db, _ORIGIN, radius_km=40.0, bands={BandName.M_2})

    assert specs
    assert all(spec.band == "M_2" for spec in specs)
    assert "QLD:2" not in {spec.source_id for spec in specs}


def test_search_filters_by_status_and_use(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test search excludes repeaters not matching requested status and use."""
    db = populated_db(
        sample_repeater(repeater_id=1),  # ON_AIR / OPEN (defaults)
        sample_repeater(
            repeater_id=2,
            operational_status=Status.OFF_AIR,
            use_membership=Use.CLOSED,
        ),
    )

    specs = search(
        db,
        _ORIGIN,
        radius_km=40.0,
        statuses={RepeaterStatus.ON_AIR},
        uses={RepeaterUse.OPEN},
    )

    assert {spec.source_id for spec in specs} == {"QLD:1"}
    assert all(spec.operational_status is RepeaterStatus.ON_AIR for spec in specs)
    assert all(spec.use is RepeaterUse.OPEN for spec in specs)


def test_search_reports_distance_from_origin(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test the spec's distance_km reflects the true distance from the origin."""
    db = populated_db(sample_repeater(repeater_id=1, latitude=Decimal("-27.60")))

    specs = search(db, _ORIGIN, radius_km=40.0)

    distance = specs[0].distance_km
    assert distance is not None
    # ~14.5 km due south; allow slack for the haversine model.
    assert Decimal(13) < distance < Decimal(16)


def test_get_by_id_returns_specs(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test get_by_id returns specs for an existing repeater."""
    db = populated_db(sample_repeater(repeater_id=7))

    specs = get_by_id(db, "QLD:7")

    assert len(specs) == 1
    assert specs[0].source_id == "QLD:7"
    # Not produced by a radius search, so there is no origin to measure from.
    assert specs[0].distance_km is None


def test_get_by_id_missing_returns_empty(
    populated_db: PopulatedDbFactory,
) -> None:
    """Test get_by_id returns empty list for a missing repeater."""
    assert get_by_id(populated_db(), "QLD:999") == []


def test_get_by_id_malformed_id_returns_empty(
    populated_db: PopulatedDbFactory,
) -> None:
    """Test get_by_id returns empty list for a non-numeric repeater id."""
    db = populated_db()
    assert get_by_id(db, "garbage") == []
    assert get_by_id(db, "QLD:abc") == []


def test_search_filters_by_use_alone(
    populated_db: PopulatedDbFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test the use filter applies independently of the status filter."""
    db = populated_db(
        sample_repeater(repeater_id=1),  # OPEN (default)
        sample_repeater(repeater_id=2, use_membership=Use.PRIVATE),
    )

    specs = search(db, _ORIGIN, radius_km=40.0, uses={RepeaterUse.OPEN})

    assert {spec.source_id for spec in specs} == {"QLD:1"}


async def test_sync_flags_a_truncated_response(
    local_server: Any,  # noqa: ANN401
    tmp_path: Path,
) -> None:
    """A response at the API's cap must be reported as probably incomplete.

    RepeaterBook silently truncates at max_count, so a caller that only sees
    a row count cannot tell a complete small region from a clipped large one.
    """

    async def _handler(_: web.Request) -> web.Response:
        rows = [{**_ROW_RESULT, "Rptr ID": i} for i in range(3)]
        return web.json_response({"count": len(rows), "results": rows})

    async with local_server(_handler, path="/api/exportROW.php") as url:
        base = URL.build(scheme=url.scheme, host=url.host, port=url.port)
        # max_count=3 makes the cap reachable without inventing 3500 rows.
        api = RepeaterBookAPI(
            base_url=base, working_dir=AsyncPath(tmp_path), max_count=3
        )
        db = RepeaterBook(working_dir=AsyncPath(tmp_path))
        query = ExportQuery(countries=frozenset({countries.get(name="Australia")}))

        result = await sync(api, db, query)

    assert result.count == 3
    assert result.truncated is True
    assert result.detail is not None
    assert "Narrow it" in result.detail


async def test_sync_reports_skipped_rows(
    local_server: Any,  # noqa: ANN401
    tmp_path: Path,
) -> None:
    """An unmodellable row must be counted, not silently dropped from the total."""

    async def _handler(_: web.Request) -> web.Response:
        rows = [
            _ROW_RESULT,
            # Zero input frequency: unmodellable, as seen in the Texas export.
            {**_ROW_RESULT, "Rptr ID": 43, "Input Freq": "0.00000"},
        ]
        return web.json_response({"count": len(rows), "results": rows})

    async with local_server(_handler, path="/api/exportROW.php") as url:
        base = URL.build(scheme=url.scheme, host=url.host, port=url.port)
        api = RepeaterBookAPI(base_url=base, working_dir=AsyncPath(tmp_path))
        db = RepeaterBook(working_dir=AsyncPath(tmp_path))
        query = ExportQuery(countries=frozenset({countries.get(name="Australia")}))

        result = await sync(api, db, query)

    assert result.count == 1
    assert result.skipped == 1
    assert result.truncated is False
    assert len(db.query()) == 1


async def test_sync_counts_skipped_rows_towards_truncation(
    local_server: Any,  # noqa: ANN401
    tmp_path: Path,
) -> None:
    """A skipped row still consumed a slot against the API's cap.

    Counting only the modelled rows would let a capped response containing a
    bad row report itself as complete, hiding real data loss.
    """

    async def _handler(_: web.Request) -> web.Response:
        rows = [
            {**_ROW_RESULT, "Rptr ID": 1},
            {**_ROW_RESULT, "Rptr ID": 2},
            {**_ROW_RESULT, "Rptr ID": 3, "Input Freq": "0.00000"},
        ]
        return web.json_response({"count": len(rows), "results": rows})

    async with local_server(_handler, path="/api/exportROW.php") as url:
        base = URL.build(scheme=url.scheme, host=url.host, port=url.port)
        api = RepeaterBookAPI(
            base_url=base, working_dir=AsyncPath(tmp_path), max_count=3
        )
        db = RepeaterBook(working_dir=AsyncPath(tmp_path))
        query = ExportQuery(countries=frozenset({countries.get(name="Australia")}))

        result = await sync(api, db, query)

    assert result.count == 2
    assert result.skipped == 1
    assert result.truncated is True
