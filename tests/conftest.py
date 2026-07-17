"""Pytest configuration for repeaterbook.

We run async tests using AnyIO but only require the asyncio backend.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pytest
from aiohttp import web
from yarl import URL

from repeaterbook.models import Repeater, Status, Use

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from aiohttp.web import Request, StreamResponse

    from tests._types import SampleRepeaterFactory

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


@pytest.fixture
def sample_repeater() -> SampleRepeaterFactory:
    """Build a Repeater with sensible defaults, overridable per test."""

    def _make(**overrides: object) -> Repeater:
        base: dict[str, object] = {
            "state_id": "QLD", "repeater_id": 42,
            "frequency": Decimal("146.700"), "input_frequency": Decimal("146.100"),
            "pl_ctcss_uplink": "91.5", "pl_ctcss_tsq_downlink": None,
            "location_nearest_city": "Brisbane", "landmark": None, "region": None,
            "country": "Australia", "county": None, "state": "Queensland",
            "latitude": Decimal("-27.47"), "longitude": Decimal("153.02"),
            "precise": True, "callsign": "VK4RBN",
            "use_membership": Use.OPEN, "operational_status": Status.ON_AIR,
            "ares": None, "races": None, "skywarn": None, "canwarn": None,
            "allstar_node": None, "echolink_node": None, "irlp_node": None,
            "wires_node": None, "dmr_capable": False, "dmr_id": None,
            "dmr_color_code": None, "d_star_capable": False, "nxdn_capable": False,
            "apco_p_25_capable": False, "p_25_nac": None, "m17_capable": False,
            "m17_can": None, "tetra_capable": False, "tetra_mcc": None,
            "tetra_mnc": None, "yaesu_system_fusion_capable": False,
            "ysf_digital_id_uplink": None, "ysf_digital_id_downlink": None,
            "ysf_dsc": None, "analog_capable": True, "fm_bandwidth": Decimal("25.0"),
            "notes": None, "last_update": date(2026, 1, 1),
        }
        base.update(overrides)
        return Repeater(**base)

    return _make
