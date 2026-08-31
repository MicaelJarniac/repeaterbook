"""Tests for the FastMCP server wiring (no live network)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from repeaterbook.exceptions import RepeaterBookUnauthorizedError
from repeaterbook.mcp import server, service
from repeaterbook.models import ExportQuery, Mode
from repeaterbook.na_states import NAState, state_country
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.spec import RepeaterMode

if TYPE_CHECKING:
    from pathlib import Path

    from tests._types import McpEnvFactory, SampleRepeaterFactory

pytestmark = pytest.mark.anyio


async def test_three_tools_registered() -> None:
    """Test the FastMCP instance registers exactly the three expected tools."""
    tools = await server.mcp.list_tools()
    assert {t.name for t in tools} == {
        "sync_repeaters",
        "search_repeaters",
        "get_repeater",
    }


def test_build_query_resolves_country() -> None:
    """Test _build_query resolves a country name to an ExportQuery."""
    query = server._build_query(  # noqa: SLF001
        country="Australia", state=None, region=None, modes=None
    )
    assert isinstance(query, ExportQuery)
    assert any(c.name == "Australia" for c in query.countries)


def test_build_query_unknown_country_raises() -> None:
    """Test _build_query raises ValueError for an unresolvable country name."""
    with pytest.raises(ValueError, match="country"):
        server._build_query(  # noqa: SLF001
            country="Nowhere", state=None, region=None, modes=None
        )


def test_build_query_translates_api_mode() -> None:
    """Test _build_query translates FM into the library's Mode.ANALOG."""
    query = server._build_query(  # noqa: SLF001
        country="United States",
        state=None,
        region=None,
        modes={RepeaterMode.FM},
    )
    assert query.modes == frozenset({Mode.ANALOG})


def test_build_query_non_api_mode_yields_empty_modes() -> None:
    """Test _build_query leaves modes empty for a mode the API can't scope."""
    query = server._build_query(  # noqa: SLF001
        country="United States",
        state=None,
        region=None,
        modes={RepeaterMode.FUSION},
    )
    assert query.modes == frozenset()


def test_build_query_keeps_only_api_filterable_modes() -> None:
    """Test a mixed mode set keeps the API-filterable members and drops the rest."""
    query = server._build_query(  # noqa: SLF001
        country="United States",
        state=None,
        region=None,
        modes={RepeaterMode.FM, RepeaterMode.M17, RepeaterMode.DMR},
    )
    assert query.modes == frozenset({Mode.ANALOG, Mode.DMR})


async def test_search_without_scope_or_data_errors(
    mcp_env: McpEnvFactory,
) -> None:
    """Test search_repeaters errors when no scope is given and the DB is empty."""
    mcp_env()

    with pytest.raises(ValueError, match="no local data"):
        await server.search_repeaters(lat=-27.47, lon=153.02, radius_km=40.0)


def test_configured_token_reaches_auth_header_unmasked(
    mcp_env: McpEnvFactory,
) -> None:
    """Test a configured token reaches the X-RB-App-Token header unmasked."""
    mcp_env(token="rbuapp_s3cret")

    headers = server._get_context().api.headers  # noqa: SLF001

    assert headers["X-RB-App-Token"] == "rbuapp_s3cret"


def test_token_is_masked_in_repr(mcp_env: McpEnvFactory) -> None:
    """Test the token does not leak through the API client's repr.

    `headers` has to unwrap the secret to build the X-RB-App-Token value, but
    nothing else should: an accidental log or traceback of the client must
    not print the token.
    """
    mcp_env(token="rbuapp_s3cret")

    assert "rbuapp_s3cret" not in repr(server._get_context().api)  # noqa: SLF001


@pytest.mark.parametrize("token", ["", "   "])
def test_blank_token_is_rejected(
    mcp_env: McpEnvFactory,
    token: str,
) -> None:
    """Test a blank token is a configuration error, not a request to skip auth.

    Every export needs an approved token, so there is no unauthenticated mode
    to fall back to; an empty env var is a mistake worth naming.
    """
    mcp_env(token=token)

    with pytest.raises(ValidationError, match="app_token"):
        server.RepeaterBookSettings.model_validate({})


def test_missing_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the server refuses to start without a token.

    The live API answers an unauthenticated export with 401 auth_missing, so
    failing at startup beats failing on the first tool call.
    """
    monkeypatch.delenv("REPEATERBOOK_APP_TOKEN", raising=False)
    monkeypatch.setenv("REPEATERBOOK_APP_CONTACT", "test@example.com")
    server._get_context.cache_clear()  # noqa: SLF001

    with pytest.raises(ValidationError, match="app_token"):
        server.RepeaterBookSettings.model_validate({})


def test_missing_contact_keeps_approved_identity(mcp_env: McpEnvFactory) -> None:
    """Test an unset contact leaves the default User-Agent unchanged."""
    mcp_env()

    api = server._get_context().api  # noqa: SLF001

    assert api.app_contact == RepeaterBookAPI().app_contact
    assert api.headers["User-Agent"] == RepeaterBookAPI().headers["User-Agent"]


def test_contact_override_reaches_user_agent(mcp_env: McpEnvFactory) -> None:
    """Test an explicit contact replaces the default in the User-Agent."""
    mcp_env(REPEATERBOOK_APP_CONTACT="ops@example.org")

    headers = server._get_context().api.headers  # noqa: SLF001

    assert headers["User-Agent"].endswith("(+ops@example.org)")


def test_malformed_contact_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a non-address contact string is rejected."""
    monkeypatch.setenv("REPEATERBOOK_APP_CONTACT", "not-an-email")
    monkeypatch.setenv("REPEATERBOOK_APP_TOKEN", "rbuapp_test")

    with pytest.raises(ValidationError, match="app_contact"):
        server.RepeaterBookSettings.model_validate({})


def test_working_dir_is_created_and_tilde_expanded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the working dir is expanded and created rather than required to exist.

    The documented config uses `~/.repeaterbook`, which the shell does not
    expand inside an env var and which will not exist on a first run.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("REPEATERBOOK_WORKING_DIR", "~/.repeaterbook")
    monkeypatch.setenv("REPEATERBOOK_APP_CONTACT", "test@example.com")
    monkeypatch.setenv("REPEATERBOOK_APP_TOKEN", "rbuapp_test")
    server._get_context.cache_clear()  # noqa: SLF001

    target = tmp_path / ".repeaterbook"
    assert not target.exists()

    try:
        ctx = server._get_context()  # noqa: SLF001
        assert target.is_dir()
        assert str(ctx.db.working_dir) == str(target)
    finally:
        server._get_context.cache_clear()  # noqa: SLF001


def test_context_is_cached(mcp_env: McpEnvFactory) -> None:
    """Test the context is built once and shared across tool calls."""
    mcp_env()

    assert server._get_context() is server._get_context()  # noqa: SLF001


async def test_sync_wraps_auth_failure(
    mcp_env: McpEnvFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test an auth failure surfaces as a ValueError naming the token env var.

    The library's RepeaterBookUnauthorizedError means nothing to an agent; the
    tool should tell it which knob to turn. A token is required to start, so
    this path means the configured one was refused, not that none was set.
    """
    mcp_env(token="rbuapp_bad")

    async def _boom(*_: object, **__: object) -> int:
        msg = "auth_missing"
        raise RepeaterBookUnauthorizedError(
            msg, status_code=401, error_code="auth_missing"
        )

    monkeypatch.setattr(service, "sync", _boom)

    with pytest.raises(ValueError, match="rejected the API token"):
        await server.sync_repeaters(country="Australia")


async def test_search_syncs_a_scope_when_store_is_empty(
    mcp_env: McpEnvFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a scoped search downloads the region when there's nothing local yet."""
    mcp_env()
    calls: list[str | None] = []

    async def _fake_sync(*_: object, **__: object) -> int:
        calls.append("synced")
        return 0

    monkeypatch.setattr(service, "sync", _fake_sync)

    await server.search_repeaters(
        lat=-27.47, lon=153.02, radius_km=40.0, country="Australia"
    )

    assert calls == ["synced"]


async def test_search_does_not_resync_a_populated_store(
    mcp_env: McpEnvFactory,
    monkeypatch: pytest.MonkeyPatch,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test a scoped search reuses local data instead of re-downloading it.

    Syncing re-parses the whole regional payload and re-merges every row, so
    doing it per search would make a cheap read arbitrarily expensive.
    """
    mcp_env()
    server._get_context().db.populate([sample_repeater()])  # noqa: SLF001
    calls: list[str] = []

    async def _fake_sync(*_: object, **__: object) -> int:
        calls.append("synced")
        return 0

    monkeypatch.setattr(service, "sync", _fake_sync)

    specs = await server.search_repeaters(
        lat=-27.47, lon=153.02, radius_km=40.0, country="Australia"
    )

    assert calls == []
    assert [s.source_id for s in specs] == ["QLD:42"]


async def test_search_refresh_forces_a_resync(
    mcp_env: McpEnvFactory,
    monkeypatch: pytest.MonkeyPatch,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test refresh=True re-downloads even when the store already has data."""
    mcp_env()
    server._get_context().db.populate([sample_repeater()])  # noqa: SLF001
    calls: list[str] = []

    async def _fake_sync(*_: object, **__: object) -> int:
        calls.append("synced")
        return 0

    monkeypatch.setattr(service, "sync", _fake_sync)

    await server.search_repeaters(
        lat=-27.47,
        lon=153.02,
        radius_km=40.0,
        country="Australia",
        refresh=True,
    )

    assert calls == ["synced"]


async def test_get_repeater_reads_the_store(
    mcp_env: McpEnvFactory,
    sample_repeater: SampleRepeaterFactory,
) -> None:
    """Test get_repeater returns the stored repeater's specs."""
    mcp_env()
    server._get_context().db.populate([sample_repeater()])  # noqa: SLF001

    specs = await server.get_repeater("QLD:42")

    assert [s.source_id for s in specs] == ["QLD:42"]


def test_build_query_uses_the_states_own_identifier() -> None:
    """A state member is sent as RepeaterBook's identifier, not its name."""
    query = server._build_query(  # noqa: SLF001
        country="United States", state=NAState.US_CA, region=None, modes=None
    )
    assert query.state_ids == frozenset({"06"})


@pytest.mark.parametrize(
    ("state", "expected_id"),
    [
        (NAState.US_TX, "48"),
        (NAState.CA_AB, "CA01"),
        (NAState.MX_JAL, "MX14"),
    ],
)
def test_build_query_covers_all_three_na_countries(
    state: NAState,
    expected_id: str,
) -> None:
    """Each NA country's identifier scheme survives the round trip."""
    query = server._build_query(  # noqa: SLF001
        country=state_country(state), state=state, region=None, modes=None
    )
    assert query.state_ids == frozenset({expected_id})


def test_state_without_a_country_is_allowed() -> None:
    """A state alone is unambiguous, so it need not repeat its country."""
    query = server._build_query(  # noqa: SLF001
        country=None, state=NAState.CA_ON, region=None, modes=None
    )
    assert query.state_ids == frozenset({"CA08"})


def test_state_from_the_wrong_country_is_rejected() -> None:
    """Pairing a state with another country must fail, not return nothing.

    The API answers this combination with an empty result set, which is
    indistinguishable from a region that genuinely has no repeaters.
    """
    with pytest.raises(ValueError, match="Canada subdivision"):
        server._build_query(  # noqa: SLF001
            country="United States", state=NAState.CA_AB, region=None, modes=None
        )


def test_state_with_a_row_country_is_rejected() -> None:
    """A state is meaningless outside North America."""
    with pytest.raises(ValueError, match="United States subdivision"):
        server._build_query(  # noqa: SLF001
            country="Australia", state=NAState.US_CA, region=None, modes=None
        )


def test_state_and_region_together_are_rejected() -> None:
    """The two scope different endpoints and cannot be combined."""
    with pytest.raises(ValueError, match="cannot be combined"):
        server._build_query(  # noqa: SLF001
            country=None, state=NAState.US_CA, region="Queensland", modes=None
        )


def test_region_with_an_na_country_is_rejected() -> None:
    """Region is a rest-of-world parameter; the NA endpoint ignores it.

    This is the original trap in reverse: country='Australia', state='Queensland'
    routed to the NA endpoint and returned zero rows with no explanation.
    """
    with pytest.raises(ValueError, match="region is not supported"):
        server._build_query(  # noqa: SLF001
            country="Canada", state=None, region="Ontario", modes=None
        )


def test_region_with_a_row_country_is_accepted() -> None:
    """The legitimate rest-of-world pairing still works."""
    query = server._build_query(  # noqa: SLF001
        country="Australia", state=None, region="Queensland", modes=None
    )
    assert query.regions == frozenset({"Queensland"})


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("United States", "United States"),
        ("USA", "United States"),
        ("South Korea", "Korea, Republic of"),
        ("Russia", "Russian Federation"),
    ],
)
def test_country_aliases_resolve(given: str, expected: str) -> None:
    """Common aliases should resolve; an exact name always wins."""
    query = server._build_query(  # noqa: SLF001
        country=given, state=None, region=None, modes=None
    )
    assert {c.name for c in query.countries} == {expected}


def test_unresolvable_country_still_raises() -> None:
    """Fuzzy matching must not turn nonsense into a country."""
    with pytest.raises(ValueError, match="unknown country"):
        server._build_query(  # noqa: SLF001
            country="Nowhereistan", state=None, region=None, modes=None
        )
