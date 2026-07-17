"""End-to-end MCP tests through an in-memory FastMCP client (no subprocess)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastmcp import Client

from repeaterbook.mcp import server

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.anyio


async def test_client_lists_three_tools() -> None:
    """The MCP protocol lists exactly the three repeater tools."""
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == {
        "sync_repeaters",
        "search_repeaters",
        "get_repeater",
    }


async def test_client_get_repeater_empty_db_returns_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_repeater round-trips over the protocol and returns [] for a missing id."""
    monkeypatch.setenv("REPEATERBOOK_WORKING_DIR", str(tmp_path))
    monkeypatch.setenv("REPEATERBOOK_APP_CONTACT", "test@example.com")
    server._reset_context_for_tests()  # noqa: SLF001

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_repeater", {"source_id": "CA:999999"})

    assert result.data == []
