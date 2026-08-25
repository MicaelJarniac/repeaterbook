"""Custom exceptions for the RepeaterBook Python Client."""

from __future__ import annotations

from typing import TypedDict, Unpack

__all__: tuple[str, ...] = (
    "RepeaterBookAPIError",
    "RepeaterBookCacheError",
    "RepeaterBookError",
    "RepeaterBookForbiddenError",
    "RepeaterBookRateLimitError",
    "RepeaterBookUnauthorizedError",
    "RepeaterBookValidationError",
)


class RepeaterBookError(Exception):
    """Base exception for the RepeaterBook Python Client.

    All RepeaterBook Python Client exceptions inherit from this class,
    making it easy to catch all library errors with a single except clause.
    """


class _APIErrorContext(TypedDict, total=False):
    """Optional structured context forwarded to an API error."""

    status_code: int | None
    error_code: str | None
    url: str | None
    body: object | None


class RepeaterBookAPIError(RepeaterBookError):
    """Error returned by the RepeaterBook API.

    Raised when the API returns an error response (status: "error").
    The error message from the API is preserved in the exception message.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        url: str | None = None,
        body: object | None = None,
    ) -> None:
        """Initialize an API error with optional structured response context."""
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.url = url
        self.body = body
        super().__init__(message)

    def __str__(self) -> str:
        """Render the message with any available structured context."""
        parts: list[str] = []
        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        prefix = " ".join(parts)
        text = f"{prefix}: {self.message}" if prefix else self.message
        return f"{text} (url={self.url})" if self.url else text


class RepeaterBookUnauthorizedError(RepeaterBookAPIError):
    """Unauthorized access to the API.

    Raised when the API returns a 401 Unauthorized status code,
    indicating that authentication is required or has failed.
    """


class RepeaterBookForbiddenError(RepeaterBookAPIError):
    """Authenticated but not authorized to access the API.

    Raised when the API returns a 403 Forbidden status code, such as when
    User-Agent policy enforcement or an authorization scope denies access.
    """


class RepeaterBookRateLimitError(RepeaterBookAPIError):
    """API request rejected because the rate limit was exceeded.

    Raised when the API returns a 429 Too Many Requests status code.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kwargs: Unpack[_APIErrorContext],
    ) -> None:
        """Initialize a rate-limit error with an optional retry delay."""
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

    def __str__(self) -> str:
        """Render the API error with an available retry delay."""
        base = super().__str__()
        return (
            f"{base} (retry_after={self.retry_after}s)"
            if self.retry_after is not None
            else base
        )


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
