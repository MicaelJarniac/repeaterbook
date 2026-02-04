"""Live API integration tests.

These hit repeaterbook.com over the network, so they are disabled by default.

Enable with:

  REPEATERBOOK_LIVE=1 uv run pytest -q -m integration
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pycountry
import pytest

if TYPE_CHECKING:
    from pathlib import Path as StdPath

from anyio import Path
from yarl import URL

from repeaterbook.models import ExportQuery, Mode
from repeaterbook.services import RepeaterBookAPI, json_to_model

# Limit parsed rows in NA test to keep runtime reasonable.
_NA_SAMPLE_SIZE = 200


def _live_enabled() -> bool:
    return os.environ.get("REPEATERBOOK_LIVE", "").lower() in {"1", "true", "yes"}


pytestmark = pytest.mark.skipif(
    not _live_enabled(), reason="Set REPEATERBOOK_LIVE=1 to run live integration tests"
)


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_row_brazil_downloads_and_parses(
    tmp_path: StdPath,
) -> None:
    """Brazil repeaters download and parse correctly from ROW endpoint."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    # Brazil is served by ROW endpoint.
    q = ExportQuery(countries=frozenset({pycountry.countries.lookup("Brazil")}))
    reps = await api.download(q)

    assert len(reps) > 0
    assert all(r.country for r in reps)


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_north_america_payload_parses_first_rows(
    tmp_path: StdPath,
) -> None:
    """NA payload shape differs; ensure json_to_model handles it.

    We don't route NA through urls_export() yet, so we call export.php directly.
    """
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    url = URL("https://repeaterbook.com/api/export.php") % {
        "state_id": "06",  # California
        "country": "United States",
    }

    payload = await api.export_json(url)
    assert payload["count"] == len(payload["results"])
    assert payload["count"] > 0

    # Parse a small sample so the test stays fast.
    for row in payload["results"][:_NA_SAMPLE_SIZE]:
        rep = json_to_model(row)
        assert rep.country in {"United States", "USA", "United States of America"}


# Smart routing tests


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_na_only_via_state_id(tmp_path: StdPath) -> None:
    """Query with state_id routes only to NA endpoint."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    # state_id is NA-specific, so only NA endpoint should be queried
    q = ExportQuery(state_ids=frozenset({"06"}))  # California
    urls = api.urls_export(q)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "export.php" in url_str
    assert "exportROW" not in url_str
    assert "state_id=06" in url_str

    # Verify it actually works
    reps = await api.download(q)
    assert len(reps) > 0
    # All results should be from California
    assert all(r.state_id == "06" for r in reps)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_row_only_via_region(tmp_path: StdPath) -> None:
    """Query with region routes only to ROW endpoint."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    # region is ROW-specific, so only ROW endpoint should be queried
    q = ExportQuery(regions=frozenset({"South America"}))
    urls = api.urls_export(q)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "exportROW.php" in url_str
    assert "export.php?" not in url_str  # not confused with exportROW.php
    assert "South+America" in url_str

    # Verify it actually works
    reps = await api.download(q)
    assert len(reps) > 0


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_na_country_only(tmp_path: StdPath) -> None:
    """Query with NA country routes only to NA endpoint."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    us = pycountry.countries.lookup("United States")
    q = ExportQuery(
        countries=frozenset({us}),
        state_ids=frozenset({"48"}),  # Texas - smaller result set
    )
    urls = api.urls_export(q)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "export.php" in url_str
    assert "exportROW" not in url_str


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_row_country_only(tmp_path: StdPath) -> None:
    """Query with ROW country routes only to ROW endpoint."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    germany = pycountry.countries.lookup("Germany")
    q = ExportQuery(countries=frozenset({germany}))
    urls = api.urls_export(q)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "exportROW.php" in url_str

    # Verify it actually works
    reps = await api.download(q)
    assert len(reps) > 0


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_mixed_countries_both_endpoints(tmp_path: StdPath) -> None:
    """Query with both NA and ROW countries routes to both endpoints."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    us = pycountry.countries.lookup("United States")
    germany = pycountry.countries.lookup("Germany")
    q = ExportQuery(countries=frozenset({us, germany}))
    urls = api.urls_export(q)

    # Should route to both endpoints
    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert any("export.php" in u and "exportROW" not in u for u in url_strs)
    assert any("exportROW.php" in u for u in url_strs)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_empty_query_both_endpoints(tmp_path: StdPath) -> None:
    """Empty query routes to both endpoints."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    q = ExportQuery()  # Empty query
    urls = api.urls_export(q)

    # Should query both endpoints
    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert any("export.php" in u and "exportROW" not in u for u in url_strs)
    assert any("exportROW.php" in u for u in url_strs)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_mode_filter_both_endpoints(tmp_path: StdPath) -> None:
    """Query with only mode (common filter) routes to both endpoints."""
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    # Mode is a common filter, not NA or ROW-specific
    q = ExportQuery(modes=frozenset({Mode.DMR}))
    urls = api.urls_export(q)

    # Should query both endpoints since mode is common
    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert all("DMR" in u for u in url_strs)
