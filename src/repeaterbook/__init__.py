"""Python utility to work with data from RepeaterBook."""

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
