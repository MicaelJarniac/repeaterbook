"""Tests for the FastMCP server wiring (no live network)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from repeaterbook.mcp import server
from repeaterbook.models import ExportQuery, Mode

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.anyio


async def test_three_tools_registered() -> None:
    """Test the FastMCP instance registers exactly the three expected tools."""
    tools = await server.mcp.list_tools()
    assert {t.name for t in tools} == {
        "sync_repeaters",
        "search_repeaters",
        "get_repeater",
    }


def test_build_query_resolves_country() -> None:
    """Test _build_query resolves a country name to an ExportQuery."""
    query = server._build_query(  # noqa: SLF001
        country="Australia", state_id=None, region=None, modes=None
    )
    assert isinstance(query, ExportQuery)
    assert any(c.name == "Australia" for c in query.countries)


def test_build_query_unknown_country_raises() -> None:
    """Test _build_query raises ValueError for an unresolvable country name."""
    with pytest.raises(ValueError, match="country"):
        server._build_query(  # noqa: SLF001
            country="Nowhere", state_id=None, region=None, modes=None
        )


def test_build_query_translates_api_mode() -> None:
    """Test _build_query translates FM into the library's Mode.ANALOG."""
    query = server._build_query(  # noqa: SLF001
        country="United States", state_id=None, region=None, modes=["FM"]
    )
    assert query.modes == frozenset({Mode.ANALOG})


def test_build_query_non_api_mode_yields_empty_modes() -> None:
    """Test _build_query leaves modes empty for a mode the API can't scope."""
    query = server._build_query(  # noqa: SLF001
        country="United States", state_id=None, region=None, modes=["FUSION"]
    )
    assert query.modes == frozenset()


def test_build_query_unknown_mode_raises() -> None:
    """Test _build_query raises ValueError for an unknown mode name."""
    with pytest.raises(ValueError, match="mode"):
        server._build_query(  # noqa: SLF001
            country="United States", state_id=None, region=None, modes=["NOTAMODE"]
        )


async def test_search_without_scope_or_data_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test search_repeaters errors when no scope is given and the DB is empty."""
    monkeypatch.setenv("REPEATERBOOK_WORKING_DIR", str(tmp_path))
    monkeypatch.setenv("REPEATERBOOK_APP_CONTACT", "test@example.com")
    server._reset_context_for_tests()  # noqa: SLF001

    with pytest.raises(ValueError, match="no local data"):
        await server.search_repeaters(lat=-27.47, lon=153.02, radius_km=40.0)
