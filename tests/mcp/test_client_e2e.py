"""End-to-end MCP tests through an in-memory FastMCP client (no subprocess)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from fastmcp import Client

from repeaterbook.mcp import server
from repeaterbook.queries import BandName
from repeaterbook.spec import RepeaterMode, RepeaterStatus, RepeaterUse

if TYPE_CHECKING:
    from tests._types import McpEnvFactory

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
    mcp_env: McpEnvFactory,
) -> None:
    """get_repeater round-trips over the protocol and returns [] for a missing id."""
    mcp_env()

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_repeater", {"source_id": "CA:999999"})

    assert result.data == []


def _enum_values(schema: dict[str, Any], name: str) -> set[str]:
    """Return the allowed values a tool advertises for a set-valued parameter.

    The parameter is an optional set, so its schema is an `anyOf` of an array
    branch and a null branch; FastMCP inlines the member enum rather than
    emitting a `$ref`.
    """
    prop = schema["properties"][name]
    for branch in prop.get("anyOf", [prop]):
        items = branch.get("items")
        if items is not None and "enum" in items:
            return set(cast("list[str]", items["enum"]))
    msg = f"parameter {name!r} advertises no enum: {prop!r}"
    raise AssertionError(msg)


@pytest.mark.parametrize(
    ("param", "expected"),
    [
        ("bands", {b.value for b in BandName}),
        ("modes", {m.value for m in RepeaterMode}),
        ("status", {s.value for s in RepeaterStatus}),
        ("use", {u.value for u in RepeaterUse}),
    ],
)
async def test_search_filters_advertise_their_vocabulary(
    param: str,
    expected: set[str],
) -> None:
    """Each filter must publish its allowed values in the tool schema.

    A bare `list[str]` gives the model nothing to go on and invites guessed
    values; the enum makes the tool self-documenting over the wire.
    """
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "search_repeaters")

    assert _enum_values(tool.inputSchema, param) == expected


async def test_search_rejects_a_value_outside_the_vocabulary(
    mcp_env: McpEnvFactory,
) -> None:
    """An unknown filter value is rejected by the protocol, not by hand-rolled code."""
    mcp_env()

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "search_repeaters",
            {"lat": -27.47, "lon": 153.02, "radius_km": 40.0, "modes": ["NOTAMODE"]},
            raise_on_error=False,
        )

    assert result.is_error
