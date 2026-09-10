"""End-to-end MCP tests through an in-memory FastMCP client (no subprocess)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest
from fastmcp import Client

from repeaterbook.mcp import server
from repeaterbook.na_states import NAState
from repeaterbook.queries import BandName
from repeaterbook.spec import RepeaterMode, RepeaterStatus, RepeaterUse

if TYPE_CHECKING:
    from tests._types import McpEnvFactory, SampleRepeaterFactory

pytestmark = pytest.mark.anyio


async def test_client_lists_four_tools() -> None:
    """The MCP protocol lists exactly the four repeater tools."""
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == {
        "sync_repeaters",
        "search_repeaters",
        "get_repeater",
        "clear_local_data",
    }


async def test_client_get_repeater_empty_db_returns_empty(
    mcp_env: McpEnvFactory,
) -> None:
    """get_repeater round-trips over the protocol and returns [] for a missing id."""
    mcp_env()

    async with Client(server.mcp) as client:
        result = await client.call_tool("get_repeater", {"source_id": "CA:999999"})

    assert result.data == []


async def test_client_clear_local_data_round_trips(
    mcp_env: McpEnvFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """clear_local_data takes no arguments and reports both counts over the wire.

    The structured result is what an agent reads back to tell the user what
    happened, so pin the field names and not just the Python return type.
    """
    mcp_env()
    server._get_context().db.populate([sample_repeater()])  # noqa: SLF001

    async with Client(server.mcp) as client:
        result = await client.call_tool("clear_local_data", {})
        after = await client.call_tool("get_repeater", {"source_id": "QLD:42"})

    assert result.structured_content == {"repeaters": 1, "cached_responses": 0}
    assert after.data == []


async def test_clear_local_data_advertises_its_hints_over_the_wire() -> None:
    """The destructive/idempotent hints survive serialization to the client.

    They are advisory, but a client can only honour what it receives; a hint
    set on the server object and lost on the wire protects nobody.
    """
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "clear_local_data")

    assert tool.annotations is not None
    assert tool.annotations.destructiveHint is True
    assert tool.annotations.idempotentHint is True
    assert tool.inputSchema.get("properties", {}) == {}


def _enum_values(schema: dict[str, Any], name: str) -> set[str]:
    """Return the allowed values a tool advertises for a parameter.

    Optional parameters are an `anyOf` over the real branch and a null one.
    The enum sits on the branch itself for a scalar, or on its `items` for a
    set; FastMCP inlines it either way rather than emitting a `$ref`.
    """
    prop = schema["properties"][name]
    for branch in prop.get("anyOf", [prop]):
        for candidate in (branch.get("items"), branch):
            if isinstance(candidate, dict) and "enum" in candidate:
                return set(cast("list[str]", candidate["enum"]))
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


async def test_state_advertises_repeaterbook_identifiers() -> None:
    """The state filter must publish RepeaterBook's own identifiers.

    These are not ISO 3166-2 and cannot be derived from it, so the schema is
    the only place a caller can learn them.
    """
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "sync_repeaters")

    values = _enum_values(tool.inputSchema, "state")
    assert {"06", "CA01", "MX14"} <= values
    assert len(values) == len(NAState)


async def test_state_description_warns_about_truncation() -> None:
    """The state parameter should explain why it matters."""
    async with Client(server.mcp) as client:
        tools = await client.list_tools()
    tool = next(t for t in tools if t.name == "sync_repeaters")

    description = tool.inputSchema["properties"]["state"]["description"]
    assert "3500" in description


async def test_wrong_country_state_pairing_errors_over_the_wire(
    mcp_env: McpEnvFactory,
) -> None:
    """A mismatched scope must surface as an error, not an empty result."""
    mcp_env()

    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "sync_repeaters",
            {"country": "United States", "state": "CA01"},
            raise_on_error=False,
        )

    assert result.is_error
    assert "Canada subdivision" in result.content[0].text
