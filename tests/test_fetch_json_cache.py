"""Tests for fetch_json caching and streaming behavior.

These tests are *offline*: they spin up a local aiohttp server.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

import pytest
from aiohttp import web

if TYPE_CHECKING:
    from pathlib import Path as StdPath

from anyio import Path

from repeaterbook.services import fetch_json


@pytest.mark.anyio
async def test_fetch_json_uses_cache_when_fresh(
    tmp_path: StdPath,
    local_server: Any,  # noqa: ANN401
) -> None:
    """Second call should hit cache even if server would return different data."""
    state: dict[str, int] = {"calls": 0}

    async def handler(_: web.Request) -> web.Response:
        state["calls"] += 1
        return web.json_response({"calls": state["calls"]})

    async with local_server(handler) as url:
        cache_dir = Path(tmp_path) / "cache"
        await cache_dir.mkdir(parents=True, exist_ok=True)

        first = await fetch_json(url, cache_dir=cache_dir)
        second = await fetch_json(url, cache_dir=cache_dir)

        assert first == {"calls": 1}
        assert second == {"calls": 1}
        assert state["calls"] == 1


@pytest.mark.anyio
async def test_fetch_json_refreshes_cache_when_stale(
    tmp_path: StdPath,
    local_server: Any,  # noqa: ANN401
) -> None:
    """If cache is stale, a new request should be made."""
    state: dict[str, int] = {"calls": 0}

    async def handler(_: web.Request) -> web.Response:
        state["calls"] += 1
        return web.json_response({"calls": state["calls"]})

    async with local_server(handler) as url:
        cache_dir = Path(tmp_path) / "cache"
        await cache_dir.mkdir(parents=True, exist_ok=True)

        first = await fetch_json(url, cache_dir=cache_dir)

        # Force staleness by setting max_cache_age=0.
        second = await fetch_json(
            url, cache_dir=cache_dir, max_cache_age=timedelta(seconds=0)
        )

        expected_refreshed_count = 2
        assert first == {"calls": 1}
        assert second == {"calls": expected_refreshed_count}
        assert state["calls"] == expected_refreshed_count
