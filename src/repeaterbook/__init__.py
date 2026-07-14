"""Unofficial third-party Python client for the RepeaterBook.com API."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "Repeater",
    "RepeaterBook",
    "RepeaterBookAPIError",
    "RepeaterBookCacheError",
    "RepeaterBookError",
    "RepeaterBookUnauthorizedError",
    "RepeaterBookValidationError",
    "__version__",
)

from importlib.metadata import version

from repeaterbook.database import RepeaterBook
from repeaterbook.exceptions import (
    RepeaterBookAPIError,
    RepeaterBookCacheError,
    RepeaterBookError,
    RepeaterBookUnauthorizedError,
    RepeaterBookValidationError,
)
from repeaterbook.models import Repeater

__version__ = version("repeaterbook")
