"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from repeaterbook.exceptions import (
    RepeaterBookAPIError,
    RepeaterBookCacheError,
    RepeaterBookError,
    RepeaterBookValidationError,
)


class TestExceptionHierarchy:
    """Test that all exceptions inherit from RepeaterBookError."""

    def test_api_error_is_repeaterbook_error(self) -> None:
        """RepeaterBookAPIError should be a subclass of RepeaterBookError."""
        assert issubclass(RepeaterBookAPIError, RepeaterBookError)

    def test_cache_error_is_repeaterbook_error(self) -> None:
        """RepeaterBookCacheError should be a subclass of RepeaterBookError."""
        assert issubclass(RepeaterBookCacheError, RepeaterBookError)

    def test_validation_error_is_repeaterbook_error(self) -> None:
        """RepeaterBookValidationError should be a subclass of RepeaterBookError."""
        assert issubclass(RepeaterBookValidationError, RepeaterBookError)


class TestExceptionMessages:
    """Test that exception messages are preserved."""

    def test_api_error_preserves_message(self) -> None:
        """RepeaterBookAPIError should preserve its message."""
        msg = "API returned error"
        with pytest.raises(RepeaterBookAPIError, match=msg):
            raise RepeaterBookAPIError(msg)

    def test_validation_error_preserves_message(self) -> None:
        """RepeaterBookValidationError should preserve its message."""
        msg = "Invalid data format"
        with pytest.raises(RepeaterBookValidationError, match=msg):
            raise RepeaterBookValidationError(msg)

    def test_cache_error_preserves_message(self) -> None:
        """RepeaterBookCacheError should preserve its message."""
        msg = "Cache write failed"
        with pytest.raises(RepeaterBookCacheError, match=msg):
            raise RepeaterBookCacheError(msg)


class TestCatchAllExceptions:
    """Test that RepeaterBookError can catch all library exceptions."""

    def test_catch_api_error(self) -> None:
        """RepeaterBookError should catch RepeaterBookAPIError."""
        msg = "test"
        with pytest.raises(RepeaterBookError):
            raise RepeaterBookAPIError(msg)

    def test_catch_cache_error(self) -> None:
        """RepeaterBookError should catch RepeaterBookCacheError."""
        msg = "test"
        with pytest.raises(RepeaterBookError):
            raise RepeaterBookCacheError(msg)

    def test_catch_validation_error(self) -> None:
        """RepeaterBookError should catch RepeaterBookValidationError."""
        msg = "test"
        with pytest.raises(RepeaterBookError):
            raise RepeaterBookValidationError(msg)
