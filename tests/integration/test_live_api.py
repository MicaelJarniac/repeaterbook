"""Live API integration tests.

These hit repeaterbook.com over the network, so they are disabled by default.

Enable with:

  REPEATERBOOK_LIVE=1 uv run pytest -q -m integration
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from anyio import Path
from yarl import URL

from repeaterbook.models import ExportQuery
from repeaterbook.services import RepeaterBookAPI, json_to_model


def _live_enabled() -> bool:
    return os.environ.get("REPEATERBOOK_LIVE") in {"1", "true", "TRUE", "yes", "YES"}


pytestmark = pytest.mark.skipif(
    not _live_enabled(), reason="Set REPEATERBOOK_LIVE=1 to run live integration tests"
)


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_row_brazil_downloads_and_parses(tmp_path: Any) -> None:
    api = RepeaterBookAPI(
        app_name="repeaterbook-live-test",
        app_email="micael@jarniac.dev",
        working_dir=Path(tmp_path),
    )

    # Brazil is served by ROW endpoint.
    import pycountry

    q = ExportQuery(countries=frozenset({pycountry.countries.lookup("Brazil")}))
    reps = await api.download(q)

    assert len(reps) > 0
    assert all(r.country for r in reps)


@pytest.mark.integration
@pytest.mark.anyio
async def test_live_export_north_america_payload_parses_first_rows(tmp_path: Any) -> None:
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
    for row in payload["results"][:200]:
        rep = json_to_model(row)
        assert rep.country in {"United States", "USA", "United States of America"}
