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
from yarl import URL

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


@pytest.mark.anyio
async def test_fetch_json_defaults_cache_dir_to_cwd(
    tmp_path: StdPath,
    monkeypatch: pytest.MonkeyPatch,
    local_server: Any,  # noqa: ANN401
) -> None:
    """With no cache_dir, the entry lands in the working directory.

    `RepeaterBookAPI` always supplies one, so this default only matters for a
    caller using `fetch_json` directly. chdir into tmp_path so the file the
    test writes does not land in the repository.
    """
    monkeypatch.chdir(tmp_path)

    async def handler(_: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with local_server(handler) as url:
        result = await fetch_json(url)

    assert result == {"ok": True}
    assert len(list(tmp_path.glob("api_cache_*.json"))) == 1


class TestCacheDir:
    """`RepeaterBookAPI.cache_dir()` creates the directory once, then reuses it."""

    @pytest.mark.anyio
    async def test_existing_cache_dir_is_reused(self, tmp_path: StdPath) -> None:
        """A second call finds the directory and leaves its contents alone.

        Every fetch goes through `cache_dir()`, so this is the steady-state
        path: recreating the directory or rewriting the `.gitignore` on each
        call would be needless I/O at best and clobber a user's edits at worst.
        """
        api = RepeaterBookAPI(working_dir=Path(tmp_path))
        first = await api.cache_dir()
        gitignore = tmp_path / ".repeaterbook_cache" / ".gitignore"
        gitignore.write_text("*\n!keep-me\n", encoding="utf-8")

        second = await api.cache_dir()

        assert second == first
        assert gitignore.read_text(encoding="utf-8") == "*\n!keep-me\n"

    @pytest.mark.anyio
    async def test_gitignore_already_present_is_not_rewritten(
        self,
        tmp_path: StdPath,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A `.gitignore` that appears with the directory is kept as-is.

        Not reachable through the filesystem alone -- a directory that did not
        exist cannot already hold a file -- but it is the branch that protects
        the file once `mkdir` succeeds, so pin it by having `mkdir` plant one.
        """
        original_mkdir = Path.mkdir

        async def mkdir_with_gitignore(self: Path, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
            await original_mkdir(self, *args, **kwargs)
            await (self / ".gitignore").write_text("custom\n", encoding="utf-8")

        monkeypatch.setattr(Path, "mkdir", mkdir_with_gitignore)

        api = RepeaterBookAPI(working_dir=Path(tmp_path))
        cache = await api.cache_dir()

        assert await (cache / ".gitignore").read_text(encoding="utf-8") == "custom\n"


class TestClearCache:
    """`RepeaterBookAPI.clear_cache()` empties the response cache, and only that."""

    @pytest.mark.anyio
    async def test_next_fetch_hits_the_network_again(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """Clearing makes a fresh entry stale: the fetch after it is a real request.

        This is the property the MCP wipe tool depends on. Without it, a
        response younger than `max_cache_age` would be served again and a
        "cleared" store would silently refill with the same data.
        """
        state: dict[str, int] = {"calls": 0}

        async def handler(_: web.Request) -> web.Response:
            state["calls"] += 1
            return web.json_response({"count": 0, "results": []})

        async with local_server(handler, path="/api/exportROW.php") as url:
            base = URL.build(scheme=url.scheme, host=url.host, port=url.port)
            api = RepeaterBookAPI(base_url=base, working_dir=Path(tmp_path))

            await api.export_json(url)
            await api.export_json(url)
            assert state["calls"] == 1, "sanity: the second call was cached"

            removed = await api.clear_cache()
            await api.export_json(url)

        assert removed == 1
        assert state["calls"] == 2

    @pytest.mark.anyio
    async def test_removes_every_entry_and_counts_them(self, tmp_path: StdPath) -> None:
        """Each `api_cache_*.json` is one response; the count says how many went."""
        cache = tmp_path / ".repeaterbook_cache"
        cache.mkdir()
        for i in range(3):
            (cache / f"api_cache_{i:064x}.json").write_text("{}", encoding="utf-8")

        removed = await RepeaterBookAPI(working_dir=Path(tmp_path)).clear_cache()

        assert removed == 3
        assert list(cache.glob("api_cache_*")) == []

    @pytest.mark.anyio
    async def test_sweeps_stray_temp_files_without_counting_them(
        self, tmp_path: StdPath
    ) -> None:
        """A `.tmp` orphaned by a crash is removed, but it was never a response."""
        cache = tmp_path / ".repeaterbook_cache"
        cache.mkdir()
        (cache / f"api_cache_{0:064x}.json").write_text("{}", encoding="utf-8")
        (cache / f"api_cache_{1:064x}.tmp").write_bytes(b"partial")

        removed = await RepeaterBookAPI(working_dir=Path(tmp_path)).clear_cache()

        assert removed == 1
        assert list(cache.iterdir()) == []

    @pytest.mark.anyio
    async def test_leaves_the_directory_and_foreign_files_alone(
        self, tmp_path: StdPath
    ) -> None:
        """Only what `fetch_json` wrote is fair game.

        The `.gitignore` is the library's courtesy to the user's repo, and
        anything else in there is the user's. `rm -rf` semantics would take
        both.
        """
        api = RepeaterBookAPI(working_dir=Path(tmp_path))
        cache = await api.cache_dir()
        gitignore = tmp_path / ".repeaterbook_cache" / ".gitignore"
        gitignore.write_text("*\n!keep-me\n", encoding="utf-8")
        (tmp_path / ".repeaterbook_cache" / "keep-me").write_text("mine")
        (tmp_path / ".repeaterbook_cache" / f"api_cache_{7:064x}.json").write_text(
            "{}", encoding="utf-8"
        )

        removed = await api.clear_cache()

        assert removed == 1
        assert await cache.is_dir()
        assert gitignore.read_text(encoding="utf-8") == "*\n!keep-me\n"
        assert (tmp_path / ".repeaterbook_cache" / "keep-me").read_text() == "mine"

    @pytest.mark.anyio
    async def test_missing_cache_dir_is_a_zero_no_op(self, tmp_path: StdPath) -> None:
        """Clearing before anything was ever fetched neither fails nor creates."""
        removed = await RepeaterBookAPI(working_dir=Path(tmp_path)).clear_cache()

        assert removed == 0
        assert not (tmp_path / ".repeaterbook_cache").exists()

    @pytest.mark.anyio
    async def test_undeletable_entry_raises_cache_error(
        self,
        tmp_path: StdPath,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A removal the filesystem refuses is a `RepeaterBookCacheError`.

        The public exception hierarchy promises every cache failure under one
        name; a bare `OSError` here would be the odd one out.
        """
        cache = tmp_path / ".repeaterbook_cache"
        cache.mkdir()
        (cache / f"api_cache_{0:064x}.json").write_text("{}", encoding="utf-8")

        async def boom(*_args: object, **_kwargs: object) -> None:
            msg = "Permission denied"
            raise OSError(msg)

        monkeypatch.setattr(Path, "unlink", boom)

        with pytest.raises(RepeaterBookCacheError, match="Failed to remove"):
            await RepeaterBookAPI(working_dir=Path(tmp_path)).clear_cache()


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
