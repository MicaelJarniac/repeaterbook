"""Pytest configuration for repeaterbook.

We run async tests using AnyIO but only require the asyncio backend.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Force AnyIO tests to run on asyncio.

    This avoids requiring trio as a test dependency.
    """
    return "asyncio"
