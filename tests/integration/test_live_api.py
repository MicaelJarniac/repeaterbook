"""Live API integration tests.

These hit repeaterbook.com over the network, so they are disabled by default.
They query small regions and pause between requests to stay gentle on the API.

Enable with:

  REPEATERBOOK_LIVE=1 REPEATERBOOK=<rbuapp_token> uv run pytest -q -m integration
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import pycountry
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path as StdPath

from anyio import Path
from yarl import URL

from repeaterbook.exceptions import RepeaterBookAPIError
from repeaterbook.models import ExportQuery, Mode
from repeaterbook.services import RepeaterBookAPI, json_to_model

_NA_SAMPLE_SIZE = 200
_COOLDOWN_SECONDS = 2
_SMALL_NA_STATE_ID = "44"
_SMALL_ROW_COUNTRY = "Luxembourg"


def _live_enabled() -> bool:
    return os.environ.get("REPEATERBOOK_LIVE", "").lower() in {"1", "true", "yes"}


pytestmark = pytest.mark.skipif(
    not _live_enabled(), reason="Set REPEATERBOOK_LIVE=1 to run live integration tests"
)


@pytest.fixture(autouse=True)
def _cooldown() -> Iterator[None]:
    """Pause after each live test to be gentle on the API."""
    yield
    if os.environ.get("REPEATERBOOK"):
        time.sleep(_COOLDOWN_SECONDS)


@pytest.fixture
def live_token() -> str:
    """Return the RepeaterBook API token, or skip when it is not configured."""
    token = os.environ.get("REPEATERBOOK")
    if not token:
        pytest.skip("Set REPEATERBOOK=<token> to run live integration tests")
    return token


@pytest.fixture
def live_api(live_token: str, tmp_path: StdPath) -> RepeaterBookAPI:
    """Authenticated client using the library's default (approved) identity."""
    return RepeaterBookAPI(app_token=live_token, working_dir=Path(tmp_path))


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_north_america_parses(live_api: RepeaterBookAPI) -> None:
    """A small North-America export authenticates, downloads, and parses."""
    url = URL("https://repeaterbook.com/api/export.php") % {
        "state_id": _SMALL_NA_STATE_ID,
        "country": "United States",
    }

    payload = await live_api.export_json(url)
    assert payload["count"] == len(payload["results"])
    assert payload["count"] > 0

    for row in payload["results"][:_NA_SAMPLE_SIZE]:
        rep = json_to_model(row)
        assert rep.country in {"United States", "USA", "United States of America"}


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_row_parses(live_api: RepeaterBookAPI) -> None:
    """A small rest-of-world export authenticates, downloads, and parses."""
    country = pycountry.countries.lookup(_SMALL_ROW_COUNTRY)
    reps = await live_api.download(ExportQuery(countries=frozenset({country})))

    assert all(r.country for r in reps)


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_auth_accepts_different_app_version(
    live_token: str,
    tmp_path: StdPath,
) -> None:
    """Probe whether the token authenticates under a different app version.

    The token is expected to be locked to the app name/pattern (version
    flexible), but that is not guaranteed, so a rejection is reported via skip
    rather than failing the suite.
    """
    api = RepeaterBookAPI(
        app_token=live_token,
        app_version="0.0.0-version-probe",
        working_dir=Path(tmp_path),
    )
    url = URL("https://repeaterbook.com/api/export.php") % {
        "state_id": _SMALL_NA_STATE_ID,
        "country": "United States",
    }

    try:
        payload = await api.export_json(url)
    except RepeaterBookAPIError as e:
        pytest.skip(f"Token rejected a different app_version: {e}")

    assert payload["count"] == len(payload["results"])


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_na_only_via_state_id(live_api: RepeaterBookAPI) -> None:
    """A small state_id query routes only to the NA endpoint and downloads."""
    query = ExportQuery(state_ids=frozenset({_SMALL_NA_STATE_ID}))
    urls = live_api.urls_export(query)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "export.php" in url_str
    assert "exportROW" not in url_str
    assert f"state_id={_SMALL_NA_STATE_ID}" in url_str

    reps = await live_api.download(query)
    assert all(r.state_id == _SMALL_NA_STATE_ID for r in reps)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_row_only_via_region(live_api: RepeaterBookAPI) -> None:
    """A region query routes only to the ROW endpoint.

    Regions cover whole continents, so this asserts routing only and skips the
    (large) live download.
    """
    query = ExportQuery(regions=frozenset({"South America"}))
    urls = live_api.urls_export(query)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "exportROW.php" in url_str
    assert "export.php?" not in url_str
    assert "South+America" in url_str


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_na_country_only(live_api: RepeaterBookAPI) -> None:
    """A NA country query routes only to the NA endpoint."""
    us = pycountry.countries.lookup("United States")
    query = ExportQuery(
        countries=frozenset({us}),
        state_ids=frozenset({_SMALL_NA_STATE_ID}),
    )
    urls = live_api.urls_export(query)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "export.php" in url_str
    assert "exportROW" not in url_str


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_row_country_only(live_api: RepeaterBookAPI) -> None:
    """A ROW country query routes only to the ROW endpoint."""
    country = pycountry.countries.lookup(_SMALL_ROW_COUNTRY)
    query = ExportQuery(countries=frozenset({country}))
    urls = live_api.urls_export(query)

    assert len(urls) == 1
    url_str = str(next(iter(urls)))
    assert "exportROW.php" in url_str


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_mixed_countries_both_endpoints(
    live_api: RepeaterBookAPI,
) -> None:
    """A mixed NA and ROW country query routes to both endpoints."""
    us = pycountry.countries.lookup("United States")
    country = pycountry.countries.lookup(_SMALL_ROW_COUNTRY)
    query = ExportQuery(countries=frozenset({us, country}))
    urls = live_api.urls_export(query)

    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert any("export.php" in u and "exportROW" not in u for u in url_strs)
    assert any("exportROW.php" in u for u in url_strs)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_empty_query_both_endpoints(
    live_api: RepeaterBookAPI,
) -> None:
    """An empty query routes to both endpoints."""
    urls = live_api.urls_export(ExportQuery())

    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert any("export.php" in u and "exportROW" not in u for u in url_strs)
    assert any("exportROW.php" in u for u in url_strs)


@pytest.mark.integration
@pytest.mark.anyio
async def test_smart_routing_mode_filter_both_endpoints(
    live_api: RepeaterBookAPI,
) -> None:
    """A mode-only query (common filter) routes to both endpoints."""
    urls = live_api.urls_export(ExportQuery(modes=frozenset({Mode.DMR})))

    assert len(urls) == 2
    url_strs = [str(url) for url in urls]
    assert all("DMR" in u for u in url_strs)
