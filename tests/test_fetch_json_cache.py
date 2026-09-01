"""Tests for fetch_json caching and streaming behavior.

These tests are *offline*: they spin up a local aiohttp server.
"""

from __future__ import annotations

import os
import stat as stat_module
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import aiohttp
import pytest
from aiohttp import web

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path as StdPath

from anyio import Path

from repeaterbook.exceptions import RepeaterBookCacheError
from repeaterbook.services import RepeaterBookAPI, _cache_errors, fetch_json


@pytest.fixture
def read_only_dir(tmp_path: StdPath) -> Iterator[Path]:
    """A directory that cannot be written to, restored afterwards.

    Skips when running as root, for whom the mode bits are advisory.
    """
    if os.geteuid() == 0:
        pytest.skip("root bypasses directory permissions")

    target = tmp_path / "read_only"
    target.mkdir()
    original = stat_module.S_IMODE(target.stat().st_mode)
    target.chmod(0o500)  # r-x own
    try:
        yield Path(target)
    finally:
        # Restore so pytest's tmp_path cleanup can remove it.
        target.chmod(original)


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


class TestCacheErrors:
    """A failing cache *write* is a library error, not a silent miss."""

    @pytest.mark.anyio
    async def test_unwritable_cache_dir_raises_cache_error(
        self,
        read_only_dir: Path,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A read-only cache dir surfaces as RepeaterBookCacheError, not OSError."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"ok": True})

        async with local_server(handler) as url:
            with pytest.raises(RepeaterBookCacheError, match="Failed to write"):
                await fetch_json(url, cache_dir=read_only_dir)

    @pytest.mark.anyio
    async def test_cache_error_chains_original_oserror(
        self,
        read_only_dir: Path,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """The underlying OSError is preserved as __cause__ for diagnosis."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"ok": True})

        async with local_server(handler) as url:
            with pytest.raises(RepeaterBookCacheError) as exc_info:
                await fetch_json(url, cache_dir=read_only_dir)

        assert isinstance(exc_info.value.__cause__, OSError)

    @pytest.mark.anyio
    async def test_failed_commit_raises_cache_error(
        self,
        tmp_path: StdPath,
        monkeypatch: pytest.MonkeyPatch,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """An OSError from the atomic rename surfaces as a cache error."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"ok": True})

        async def boom(*_args: object, **_kwargs: object) -> None:
            msg = "No space left on device"
            raise OSError(msg)

        monkeypatch.setattr(Path, "rename", boom)

        async with local_server(handler) as url:
            cache_dir = Path(tmp_path) / "cache"
            await cache_dir.mkdir(parents=True, exist_ok=True)

            with pytest.raises(RepeaterBookCacheError, match="Failed to commit"):
                await fetch_json(url, cache_dir=cache_dir)

    @pytest.mark.anyio
    async def test_no_temp_file_left_behind_on_failure(
        self,
        tmp_path: StdPath,
        monkeypatch: pytest.MonkeyPatch,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A failed write must not leave an orphaned .tmp in the cache dir."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"ok": True})

        async def boom(*_args: object, **_kwargs: object) -> None:
            msg = "No space left on device"
            raise OSError(msg)

        monkeypatch.setattr(Path, "rename", boom)

        async with local_server(handler) as url:
            cache_dir = Path(tmp_path) / "cache"
            await cache_dir.mkdir(parents=True, exist_ok=True)

            with pytest.raises(RepeaterBookCacheError):
                await fetch_json(url, cache_dir=cache_dir)

            leftovers = [path async for path in cache_dir.glob("*.tmp")]
            assert leftovers == []

    @pytest.mark.anyio
    async def test_unwritable_working_dir_raises_cache_error(
        self,
        read_only_dir: Path,
    ) -> None:
        """cache_dir() cannot create its directory under a read-only parent."""
        api = RepeaterBookAPI(working_dir=read_only_dir)

        with pytest.raises(RepeaterBookCacheError, match="Failed to create"):
            await api.cache_dir()

    @pytest.mark.anyio
    async def test_gitignore_failure_does_not_fail_cache_dir(
        self,
        tmp_path: StdPath,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The .gitignore is a courtesy; failing to write it must not raise."""

        async def boom(*_args: object, **_kwargs: object) -> None:
            msg = "Permission denied"
            raise OSError(msg)

        monkeypatch.setattr(Path, "write_text", boom)

        api = RepeaterBookAPI(working_dir=Path(tmp_path))
        cache = await api.cache_dir()

        assert await cache.is_dir()

    def test_client_os_error_is_not_a_cache_error(self) -> None:
        """aiohttp.ClientOSError subclasses OSError but is a transport failure.

        Misreporting a dropped connection as a cache failure would send a
        caller looking at their disk for a network problem.
        """
        with (
            pytest.raises(aiohttp.ClientOSError),
            _cache_errors("write", Path("/tmp/x")),  # noqa: S108
        ):
            raise aiohttp.ClientOSError
