"""Optional MCP server exposing RepeaterBook to agents.

Requires the ``mcp`` extra: ``pip install repeaterbook[mcp]``.
"""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "RepeaterMode",
    "RepeaterSpec",
)

from repeaterbook.mcp.models import RepeaterMode, RepeaterSpec
