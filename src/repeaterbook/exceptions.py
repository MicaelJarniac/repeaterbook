"""Custom exceptions for RepeaterBook library."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "RepeaterBookAPIError",
    "RepeaterBookCacheError",
    "RepeaterBookError",
    "RepeaterBookValidationError",
)


class RepeaterBookError(Exception):
    """Base exception for RepeaterBook library.

    All RepeaterBook-specific exceptions inherit from this class,
    making it easy to catch all library errors with a single except clause.
    """


class RepeaterBookAPIError(RepeaterBookError):
    """Error returned by the RepeaterBook API.

    Raised when the API returns an error response (status: "error").
    The error message from the API is preserved in the exception message.
    """


class RepeaterBookCacheError(RepeaterBookError):
    """Error during cache operations.

    Raised when reading from or writing to the cache fails,
    such as file permission issues or disk full errors.
    """


class RepeaterBookValidationError(RepeaterBookError):
    """Invalid data or response format.

    Raised when:
    - API response is not in expected format (not a dict)
    - Required fields are missing from the response
    - Data values fail validation (e.g., invalid coordinates)
    """
