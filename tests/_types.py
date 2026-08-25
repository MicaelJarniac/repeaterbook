"""Shared typing aliases for the test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from repeaterbook.database import RepeaterBook
    from repeaterbook.models import Repeater


class SampleRepeaterFactory(Protocol):
    """Return type of the ``sample_repeater`` fixture: a Repeater factory."""

    def __call__(self, **overrides: object) -> Repeater:
        """Build a Repeater, overriding any field by keyword."""
        ...


class McpEnvFactory(Protocol):
    """Return type of the ``mcp_env`` fixture: an env configurator."""

    def __call__(self, token: str | None = None, **env: str) -> None:
        """Point the MCP server at a temp working dir and reset its context."""
        ...


class PopulatedDbFactory(Protocol):
    """Return type of the ``populated_db`` fixture: a seeded-DB factory."""

    def __call__(self, *repeaters: Repeater) -> RepeaterBook:
        """Build a temp-dir RepeaterBook seeded with the given repeaters."""
        ...
