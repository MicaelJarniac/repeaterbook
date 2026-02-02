"""Tests for repeaterbook public API."""

from __future__ import annotations

import repeaterbook


class TestPublicAPI:
    """Test that the public API is correctly exported."""

    def test_repeater_exported(self) -> None:
        """Repeater model should be exported."""
        assert hasattr(repeaterbook, "Repeater")

    def test_repeaterbook_exported(self) -> None:
        """RepeaterBook database wrapper should be exported."""
        assert hasattr(repeaterbook, "RepeaterBook")

    def test_exceptions_exported(self) -> None:
        """All custom exceptions should be exported."""
        assert hasattr(repeaterbook, "RepeaterBookError")
        assert hasattr(repeaterbook, "RepeaterBookAPIError")
        assert hasattr(repeaterbook, "RepeaterBookCacheError")
        assert hasattr(repeaterbook, "RepeaterBookValidationError")

    def test_all_exports_match(self) -> None:
        """__all__ should match actual exports."""
        for name in repeaterbook.__all__:
            assert hasattr(repeaterbook, name), f"{name} in __all__ but not exported"
