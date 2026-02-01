"""Pytest configuration for repeaterbook.

We run async tests using AnyIO but only require the asyncio backend.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import pytest
from aiohttp import web
from yarl import URL

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from aiohttp.web import Request, StreamResponse

# Type alias for aiohttp route handlers.
_Handler = Callable[["Request"], Awaitable["StreamResponse"]]


@pytest.fixture
def anyio_backend() -> str:
    """Force AnyIO tests to run on asyncio.

    This avoids requiring trio as a test dependency.
    """
    return "asyncio"


@pytest.fixture
def local_server() -> Any:  # noqa: ANN401
    """Provide an async context manager for spinning up a local aiohttp test server.

    Usage:
        async with local_server(my_handler) as url:
            response = await fetch_json(url, ...)

    The server binds to an ephemeral port on 127.0.0.1 and returns the base URL.
    """

    @asynccontextmanager
    async def _create_server(
        handler: _Handler,
        path: str = "/data",
    ) -> AsyncIterator[URL]:
        app = web.Application()
        app.router.add_get(path, handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()

        try:
            # Get ephemeral port from the bound socket.
            port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]  # noqa: SLF001
            yield URL.build(scheme="http", host="127.0.0.1", port=port, path=path)
        finally:
            await runner.cleanup()

    return _create_server
