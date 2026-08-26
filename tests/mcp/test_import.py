"""Import smoke test for the mcp subpackage."""

from __future__ import annotations


def test_mcp_subpackage_imports() -> None:
    """The mcp subpackage imports and has a docstring."""
    # Import inside the function so an import failure surfaces as a test failure.
    import repeaterbook.mcp  # noqa: PLC0415

    assert repeaterbook.mcp.__doc__ is not None
