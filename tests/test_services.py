"""Tests for services module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar, cast

import pycountry
import pytest
from aiohttp import web
from loguru import logger
from yarl import URL

from repeaterbook.exceptions import (
    RepeaterBookAPIError,
    RepeaterBookForbiddenError,
    RepeaterBookRateLimitError,
    RepeaterBookRowError,
    RepeaterBookUnauthorizedError,
    RepeaterBookValidationError,
)
from repeaterbook.models import (
    ExportQuery,
    Mode,
    Status,
    Use,
)
from repeaterbook.services import (
    BOOL_MAP,
    STATUS_MAP,
    USE_MAP,
    RepeaterBookAPI,
    json_to_model,
    json_to_models,
    parse_date,
    row_label,
)

if TYPE_CHECKING:
    from pathlib import Path as StdPath

    from pycountry.db import Country

from anyio import Path


class TestBoolMap:
    """Tests for BOOL_MAP constant."""

    def test_yes_is_true(self) -> None:
        """'Yes' should map to True."""
        assert BOOL_MAP["Yes"] is True

    def test_no_is_false(self) -> None:
        """'No' should map to False."""
        assert BOOL_MAP["No"] is False

    def test_one_is_true(self) -> None:
        """1 should map to True."""
        assert BOOL_MAP[1] is True

    def test_zero_is_false(self) -> None:
        """0 should map to False."""
        assert BOOL_MAP[0] is False


class TestUseMap:
    """Tests for USE_MAP constant."""

    def test_open(self) -> None:
        """'OPEN' should map to Use.OPEN."""
        assert USE_MAP["OPEN"] == Use.OPEN

    def test_private(self) -> None:
        """'PRIVATE' should map to Use.PRIVATE."""
        assert USE_MAP["PRIVATE"] == Use.PRIVATE

    def test_closed(self) -> None:
        """'CLOSED' should map to Use.CLOSED."""
        assert USE_MAP["CLOSED"] == Use.CLOSED

    def test_empty_defaults_to_open(self) -> None:
        """Empty string should default to Use.OPEN."""
        assert USE_MAP[""] == Use.OPEN


class TestStatusMap:
    """Tests for STATUS_MAP constant."""

    def test_off_air(self) -> None:
        """'Off-air' should map to Status.OFF_AIR."""
        assert STATUS_MAP["Off-air"] == Status.OFF_AIR

    def test_on_air(self) -> None:
        """'On-air' should map to Status.ON_AIR."""
        assert STATUS_MAP["On-air"] == Status.ON_AIR

    def test_unknown(self) -> None:
        """'Unknown' should map to Status.UNKNOWN."""
        assert STATUS_MAP["Unknown"] == Status.UNKNOWN


class TestParseDate:
    """Tests for parse_date function."""

    def test_valid_date(self) -> None:
        """Valid ISO date should be parsed correctly."""
        result = parse_date("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_invalid_date_returns_min(self) -> None:
        """Invalid date should return date.min."""
        result = parse_date("not-a-date")
        assert result == date.min

    def test_empty_string_returns_min(self) -> None:
        """Empty string should return date.min."""
        result = parse_date("")
        assert result == date.min


class TestJsonToModel:
    """Tests for json_to_model function."""

    @pytest.fixture
    def minimal_payload(self) -> dict[str, Any]:
        """Minimal valid payload."""
        return {
            "State ID": "CA",
            "Rptr ID": 123,
            "Frequency": "146.940000",
            "Input Freq": "146.340000",
            "PL": "",
            "TSQ": "",
            "Nearest City": "Los Angeles",
            "Landmark": "",
            "Country": "United States",
            "Lat": "34.0522",
            "Long": "-118.2437",
            "Precise": 1,
            "Callsign": "W6ABC",
            "Use": "OPEN",
            "Operational Status": "On-air",
            "AllStar Node": "",
            "EchoLink Node": "",
            "IRLP Node": "",
            "Wires Node": "",
            "FM Analog": "Yes",
            "FM Bandwidth": "",
            "DMR": "No",
            "DMR Color Code": "",
            "DMR ID": "",
            "D-Star": "No",
            "NXDN": "No",
            "APCO P-25": "No",
            "P-25 NAC": "",
            "M17": "No",
            "M17 CAN": "",
            "Tetra": "No",
            "Tetra MCC": "",
            "Tetra MNC": "",
            "System Fusion": "No",
            "Notes": "",
            "Last Update": "2024-01-15",
        }

    def test_basic_fields(self, minimal_payload: dict[str, Any]) -> None:
        """Basic fields should be parsed correctly."""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.state_id == "CA"
        assert rep.repeater_id == 123
        assert rep.frequency == Decimal("146.940000")
        assert rep.callsign == "W6ABC"

    def test_coordinates(self, minimal_payload: dict[str, Any]) -> None:
        """Coordinates should be parsed as Decimal."""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.latitude == Decimal("34.0522")
        assert rep.longitude == Decimal("-118.2437")

    def test_boolean_fields_yes_no(self, minimal_payload: dict[str, Any]) -> None:
        """Yes/No boolean fields should be parsed correctly."""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.analog_capable is True
        assert rep.dmr_capable is False

    def test_boolean_fields_zero_one(self, minimal_payload: dict[str, Any]) -> None:
        """0/1 boolean fields should be parsed correctly."""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.precise is True

        minimal_payload["Precise"] = 0
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.precise is False

    def test_empty_use_defaults_to_open(self, minimal_payload: dict[str, Any]) -> None:
        """Empty Use field should default to OPEN."""
        minimal_payload["Use"] = ""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.use_membership == Use.OPEN

    def test_missing_region(self, minimal_payload: dict[str, Any]) -> None:
        """Missing Region field should be None."""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.region is None

    def test_null_region(self, minimal_payload: dict[str, Any]) -> None:
        """Null Region field should be None."""
        minimal_payload["Region"] = None
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.region is None

    def test_fm_bandwidth_strips_khz(self, minimal_payload: dict[str, Any]) -> None:
        """FM Bandwidth should strip ' kHz' suffix."""
        minimal_payload["FM Bandwidth"] = "25 kHz"
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.fm_bandwidth == Decimal(25)

    def test_extra_keys_ignored(self, minimal_payload: dict[str, Any]) -> None:
        """Extra keys (like 'sponsor') should be ignored."""
        minimal_payload["sponsor"] = "Someone"
        minimal_payload["unknown_field"] = "value"
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.state_id == "CA"

    def test_empty_operational_status_defaults_to_unknown(
        self, minimal_payload: dict[str, Any]
    ) -> None:
        """Empty Operational Status should default to UNKNOWN."""
        minimal_payload["Operational Status"] = ""
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.operational_status == Status.UNKNOWN

    def test_echolink_node_as_int(self, minimal_payload: dict[str, Any]) -> None:
        """EchoLink Node can be an int in some payloads."""
        minimal_payload["EchoLink Node"] = 12345
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.echolink_node == "12345"

    def test_unknown_precise_value_defaults_to_false(
        self, minimal_payload: dict[str, Any]
    ) -> None:
        """An unrecognised Precise value should default rather than raise KeyError."""
        minimal_payload["Precise"] = "maybe"
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.precise is False

    def test_missing_precise_defaults_to_false(
        self, minimal_payload: dict[str, Any]
    ) -> None:
        """An absent Precise key should default to False."""
        del minimal_payload["Precise"]
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.precise is False

    def test_unknown_operational_status_defaults_to_unknown(
        self, minimal_payload: dict[str, Any]
    ) -> None:
        """An unrecognised status should default rather than raise KeyError."""
        minimal_payload["Operational Status"] = "Sporadic"
        rep = json_to_model(minimal_payload)  # type: ignore[arg-type]
        assert rep.operational_status == Status.UNKNOWN


class TestRowLabel:
    """Tests for row_label function."""

    def test_full_label(self) -> None:
        """State, id and callsign should all appear."""
        row = {"State ID": "48", "Rptr ID": 24371, "Callsign": "W5AW"}
        assert row_label(row) == "48:24371 (W5AW)"  # type: ignore[arg-type]

    def test_label_without_callsign(self) -> None:
        """A row with no callsign should still identify by state and id."""
        assert row_label({"State ID": "48", "Rptr ID": 24371}) == "48:24371"  # type: ignore[arg-type]

    def test_label_with_only_callsign(self) -> None:
        """A row identified only by callsign should render just the callsign."""
        assert row_label({"Callsign": "W5AW"}) == "(W5AW)"  # type: ignore[arg-type]

    def test_label_skips_empty_parts(self) -> None:
        """Empty identifier fields should be omitted, not rendered as blanks."""
        assert row_label({"State ID": "", "Rptr ID": 7}) == "7"  # type: ignore[arg-type]

    def test_unidentifiable_row(self) -> None:
        """A row with no identifying fields should get a placeholder label."""
        assert row_label({}) == "<unidentified>"  # type: ignore[arg-type]


class TestJsonToModels:
    """Tests for the lenient batch converter."""

    @pytest.fixture
    def good_row(self) -> dict[str, Any]:
        """A row that converts cleanly."""
        return {
            "State ID": "06",
            "Rptr ID": 1,
            "Frequency": "146.940000",
            "Input Freq": "146.340000",
            "Nearest City": "Los Angeles",
            "Lat": "34.0522",
            "Long": "-118.2437",
            "Precise": 1,
            "Callsign": "W6ABC",
            "Use": "OPEN",
            "Operational Status": "On-air",
            "FM Analog": "Yes",
            "Last Update": "2024-01-15",
        }

    def test_all_good_rows_are_converted(self, good_row: dict[str, Any]) -> None:
        """A clean batch should convert entirely, in input order."""
        rows = [good_row, {**good_row, "Rptr ID": 2}, {**good_row, "Rptr ID": 3}]
        repeaters = json_to_models(rows)  # type: ignore[arg-type]
        assert [rep.repeater_id for rep in repeaters] == [1, 2, 3]

    def test_empty_batch(self) -> None:
        """An empty batch should produce no repeaters and no error."""
        assert json_to_models([]) == []

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("Input Freq", "0.00000"),  # zero frequency
            ("Frequency", "-1.0"),  # negative frequency
            ("Lat", "not-a-number"),  # InvalidOperation
            ("Lat", "91.0"),  # out-of-range latitude
            ("Long", "181.0"),  # out-of-range longitude
            ("Frequency", None),  # missing required decimal
            ("FM Analog", []),  # TypeError from a bad boolean type
        ],
    )
    def test_unmodellable_rows_are_skipped(
        self,
        good_row: dict[str, Any],
        field: str,
        value: object,
    ) -> None:
        """Each flavour of bad row should cost only itself."""
        bad = {**good_row, "Rptr ID": 99, field: value}
        repeaters = json_to_models([good_row, bad])  # type: ignore[list-item]
        assert [rep.repeater_id for rep in repeaters] == [1]

    def test_strict_raises_row_error(self, good_row: dict[str, Any]) -> None:
        """Strict mode should raise, carrying the row and its cause."""
        bad = {**good_row, "Rptr ID": 99, "Input Freq": "0.00000"}
        with pytest.raises(RepeaterBookRowError) as exc:
            json_to_models([good_row, bad], strict=True)  # type: ignore[list-item]

        assert exc.value.label == "06:99 (W6ABC)"
        assert exc.value.row == bad
        assert exc.value.__cause__ is not None

    def test_row_error_is_a_validation_error(self, good_row: dict[str, Any]) -> None:
        """Row errors should be catchable as the existing validation error."""
        bad = {**good_row, "Input Freq": "0.00000"}
        with pytest.raises(RepeaterBookValidationError):
            json_to_models([bad], strict=True)  # type: ignore[list-item]

    def test_skips_are_logged_with_the_offender(
        self,
        good_row: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A skipped row must be named in the logs, not dropped silently."""
        bad = {**good_row, "Rptr ID": 99, "Input Freq": "0.00000"}

        handler_id = logger.add(caplog.handler, level="WARNING", format="{message}")
        try:
            json_to_models([good_row, bad])  # type: ignore[list-item]
        finally:
            logger.remove(handler_id)

        assert "06:99 (W6ABC)" in caplog.text
        assert "Skipped 1 unmodellable of 2" in caplog.text

    def test_bugs_in_our_own_mapping_still_propagate(
        self,
        good_row: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Leniency must not swallow library bugs, only bad data."""
        msg = "bug in mapping code"

        def _boom(_: Any) -> Any:  # noqa: ANN401
            raise RuntimeError(msg)

        monkeypatch.setattr("repeaterbook.services.json_to_model", _boom)

        with pytest.raises(RuntimeError, match="bug in mapping code"):
            json_to_models([good_row])  # type: ignore[list-item]


class TestRepeaterBookAPIUrls:
    """Tests for RepeaterBookAPI URL generation."""

    def test_url_api(self) -> None:
        """url_api should return correct API base URL."""
        api = RepeaterBookAPI()
        assert api.url_api == URL("https://repeaterbook.com/api")

    def test_url_export_north_america(self) -> None:
        """url_export_north_america should return correct URL."""
        api = RepeaterBookAPI()
        assert api.url_export_north_america == URL(
            "https://repeaterbook.com/api/export.php"
        )

    def test_url_export_rest_of_world(self) -> None:
        """url_export_rest_of_world should return correct URL."""
        api = RepeaterBookAPI()
        assert api.url_export_rest_of_world == URL(
            "https://repeaterbook.com/api/exportROW.php"
        )

    def test_urls_export_empty_query(self) -> None:
        """Empty query should return both NA and ROW URLs."""
        api = RepeaterBookAPI()
        query = ExportQuery()
        urls = api.urls_export(query)
        # Both NA and ROW endpoints are returned
        assert len(urls) == 2
        url_strs = [str(url) for url in urls]
        assert any("export.php" in url for url in url_strs)  # NA
        assert any("exportROW.php" in url for url in url_strs)  # ROW

    def test_urls_export_na_country_routes_to_na_only(self) -> None:
        """Query with NA country (US) should only query NA endpoint."""
        api = RepeaterBookAPI()
        us = cast("Country", pycountry.countries.lookup("United States"))
        query = ExportQuery(countries=frozenset({us}))
        urls = api.urls_export(query)
        assert len(urls) == 1
        url_str = str(next(iter(urls)))
        assert "export.php" in url_str
        assert "exportROW" not in url_str
        assert "United+States" in url_str

    def test_urls_export_row_country_routes_to_row_only(self) -> None:
        """Query with ROW country (Brazil) should only query ROW endpoint."""
        api = RepeaterBookAPI()
        brazil = cast("Country", pycountry.countries.lookup("Brazil"))
        query = ExportQuery(countries=frozenset({brazil}))
        urls = api.urls_export(query)
        assert len(urls) == 1
        url_str = str(next(iter(urls)))
        assert "exportROW.php" in url_str
        assert "Brazil" in url_str

    def test_urls_export_mixed_countries_routes_to_both(self) -> None:
        """Query with both NA and ROW countries should query both endpoints."""
        api = RepeaterBookAPI()
        us = cast("Country", pycountry.countries.lookup("United States"))
        brazil = cast("Country", pycountry.countries.lookup("Brazil"))
        query = ExportQuery(countries=frozenset({us, brazil}))
        urls = api.urls_export(query)
        assert len(urls) == 2

    def test_urls_export_state_id_routes_to_na_only(self) -> None:
        """Query with state_id (NA-specific) should only query NA endpoint."""
        api = RepeaterBookAPI()
        query = ExportQuery(state_ids=frozenset({"06"}))
        urls = api.urls_export(query)
        assert len(urls) == 1
        url_str = str(next(iter(urls)))
        assert "export.php" in url_str
        assert "exportROW" not in url_str
        assert "state_id=06" in url_str

    def test_urls_export_region_routes_to_row_only(self) -> None:
        """Query with region (ROW-specific) should only query ROW endpoint."""
        api = RepeaterBookAPI()
        query = ExportQuery(regions=frozenset({"South America"}))
        urls = api.urls_export(query)
        assert len(urls) == 1
        url_str = str(next(iter(urls)))
        assert "exportROW.php" in url_str
        assert "South+America" in url_str

    def test_urls_export_with_mode(self) -> None:
        """Query with mode only should query both endpoints."""
        api = RepeaterBookAPI()
        query = ExportQuery(modes=frozenset({Mode.DMR}))
        urls = api.urls_export(query)
        # Mode is a common field, so both endpoints are queried
        assert len(urls) == 2
        url_strs = [str(url) for url in urls]
        assert all("DMR" in url for url in url_strs)

    def test_custom_base_url(self) -> None:
        """Custom base_url should be used."""
        api = RepeaterBookAPI(base_url=URL("https://example.com"))
        assert api.url_api == URL("https://example.com/api")


class TestRepeaterBookAPIExport:
    """Tests for RepeaterBookAPI export methods."""

    @pytest.mark.anyio
    async def test_export_json_raises_on_non_dict_response(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookValidationError on non-dict response."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(["not", "a", "dict"])

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookValidationError, match="Expected dict"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_raises_on_api_error(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookAPIError on API error response."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"status": "error", "message": "Rate limited"})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="Rate limited"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_raises_on_modern_api_error(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should preserve modern API error envelope details."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(
                {
                    "ok": False,
                    "error_code": "bad_query",
                    "message": "Invalid query.",
                }
            )

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="Invalid query") as exc:
                await api.export_json(url)

        assert exc.value.error_code == "bad_query"
        assert exc.value.status_code == 200

    @pytest.mark.anyio
    async def test_export_json_error_code_alone_is_api_error(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """An error code alone should identify a 200 response as an API error."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"error_code": "bad_query"})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="Unknown API error"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_raises_on_missing_count(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookValidationError on missing count."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"results": []})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookValidationError, match="missing required"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_raises_on_missing_results(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookValidationError on missing results."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": 0})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookValidationError, match="missing required"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_success(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should return data on valid response."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": 1, "results": [{"test": "data"}]})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            result = await api.export_json(url)
            assert result["count"] == 1
            assert len(result["results"]) == 1


class TestRepeaterBookAPIDownload:
    """Tests for RepeaterBookAPI.download row tolerance."""

    _GOOD: ClassVar[dict[str, Any]] = {
        "State ID": "48",
        "Rptr ID": 1,
        "Frequency": "146.940000",
        "Input Freq": "146.340000",
        "Nearest City": "Austin",
        "Lat": "30.2672",
        "Long": "-97.7431",
        "Precise": 1,
        "Callsign": "W5GOOD",
        "Use": "OPEN",
        "Operational Status": "On-air",
        "FM Analog": "Yes",
        "Last Update": "2025-01-01",
    }
    # The Texas row that made the whole state undownloadable.
    _BAD: ClassVar[dict[str, Any]] = {
        **_GOOD,
        "Rptr ID": 24371,
        "Callsign": "W5AW",
        "Frequency": "1253.30000",
        "Input Freq": "0.00000",
    }

    @staticmethod
    def _api(url: URL, tmp_path: StdPath) -> RepeaterBookAPI:
        """Point a client at the local test server."""
        return RepeaterBookAPI(base_url=url.origin(), working_dir=Path(tmp_path))

    @pytest.mark.anyio
    async def test_download_skips_malformed_row(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """One unmodellable row must not discard the good rows beside it."""
        rows = [self._GOOD, self._BAD, {**self._GOOD, "Rptr ID": 2}]

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": len(rows), "results": rows})

        async with local_server(handler, path="/api/export.php") as url:
            api = self._api(url, tmp_path)
            repeaters = await api.download(ExportQuery(state_ids=frozenset({"48"})))

        assert [rep.repeater_id for rep in repeaters] == [1, 2]

    @pytest.mark.anyio
    async def test_download_strict_raises_on_malformed_row(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """Opting into strict mode should surface the offending row."""
        rows = [self._GOOD, self._BAD]

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": len(rows), "results": rows})

        async with local_server(handler, path="/api/export.php") as url:
            api = self._api(url, tmp_path)
            with pytest.raises(RepeaterBookRowError) as exc:
                await api.download(
                    ExportQuery(state_ids=frozenset({"48"})),
                    strict=True,
                )

        assert exc.value.label == "48:24371 (W5AW)"

    @pytest.mark.anyio
    async def test_download_returns_all_good_rows(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A clean response should convert in full."""
        rows = [{**self._GOOD, "Rptr ID": i} for i in range(3)]

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": len(rows), "results": rows})

        async with local_server(handler, path="/api/export.php") as url:
            api = self._api(url, tmp_path)
            repeaters = await api.download(ExportQuery(state_ids=frozenset({"48"})))

        assert len(repeaters) == 3


class TestRepeaterBookAPIAuth:
    """Tests for RepeaterBookAPI authentication headers."""

    def test_headers_without_token_omit_auth(self) -> None:
        """Without a token, no authentication header is sent."""
        headers = dict(RepeaterBookAPI().headers)
        assert "User-Agent" in headers
        assert "X-RB-App-Token" not in headers
        assert "Authorization" not in headers

    def test_headers_with_token_use_x_rb_app_token(self) -> None:
        """With a token, the raw token is sent via the X-RB-App-Token header."""
        headers = dict(RepeaterBookAPI(app_token="rbuapp_test").headers)
        assert headers["X-RB-App-Token"] == "rbuapp_test"
        assert "Authorization" not in headers

    @pytest.mark.anyio
    async def test_auth_header_reaches_server(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """The X-RB-App-Token header should reach the server with the raw token."""
        captured: dict[str, str | None] = {}

        async def handler(request: web.Request) -> web.Response:
            captured["X-RB-App-Token"] = request.headers.get("X-RB-App-Token")
            captured["Authorization"] = request.headers.get("Authorization")
            return web.json_response({"count": 0, "results": []})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(app_token="rbuapp_test", working_dir=Path(tmp_path))
            await api.export_json(url)

        assert captured["X-RB-App-Token"] == "rbuapp_test"
        assert captured["Authorization"] is None

    @pytest.mark.anyio
    async def test_export_json_raises_unauthorized_on_401(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookUnauthorizedError on HTTP 401."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(
                {
                    "ok": False,
                    "error_code": "auth_invalid",
                    "message": "Invalid user app token format.",
                },
                status=401,
            )

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookUnauthorizedError) as exc:
                await api.export_json(url)

        assert exc.value.error_code == "auth_invalid"
        assert exc.value.status_code == 401
        assert "Invalid user app token format." in str(exc.value)

    @pytest.mark.anyio
    async def test_export_json_raises_api_error_on_500(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookAPIError on other HTTP errors."""

        async def handler(_: web.Request) -> web.Response:
            return web.Response(status=500)

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="HTTP 500"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_non_dict_http_error_body_is_preserved(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A non-dict JSON HTTP error body should be preserved as text."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(["server error"], status=500)

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="server error"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_user_agent_mismatch_is_rejected(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A server gating on the app name rejects a mismatched User-Agent."""
        approved = "RepeaterBook Python Client"

        async def handler(request: web.Request) -> web.Response:
            if not request.headers.get("User-Agent", "").startswith(approved):
                return web.json_response(
                    {
                        "ok": False,
                        "error_code": "ua_mismatch",
                        "message": "Application User-Agent policy check failed.",
                    },
                    status=403,
                )
            return web.json_response({"count": 0, "results": []})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(
                app_token="rbuapp_test",
                app_name="not-the-approved-app",
                working_dir=Path(tmp_path),
            )
            with pytest.raises(RepeaterBookForbiddenError) as exc:
                await api.export_json(url)

        assert exc.value.error_code == "ua_mismatch"
        assert exc.value.status_code == 403
        assert "Application User-Agent" in str(exc.value)

    @pytest.mark.anyio
    async def test_rate_limit_error_has_retry_after(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A 429 response should expose its numeric Retry-After delay."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(
                {
                    "ok": False,
                    "error_code": "rate_limited",
                    "message": "Too many requests.",
                },
                status=429,
                headers={"Retry-After": "30"},
            )

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookRateLimitError) as exc:
                await api.export_json(url)

        assert exc.value.retry_after == 30.0
        assert exc.value.error_code == "rate_limited"

    @pytest.mark.anyio
    async def test_rate_limit_http_date_is_parsed(
        self,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """A past Retry-After HTTP-date should produce a zero-second delay."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response(
                {"ok": False, "message": "Too many requests."},
                status=429,
                headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"},
            )

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookRateLimitError) as exc:
                await api.export_json(url)

        assert exc.value.retry_after == 0.0

    @pytest.mark.parametrize("retry_after", [None, "not-a-date"])
    @pytest.mark.anyio
    async def test_unavailable_retry_after_is_none(
        self,
        retry_after: str | None,
        tmp_path: StdPath,
        local_server: Any,  # noqa: ANN401
    ) -> None:
        """An absent or invalid Retry-After header should produce no delay."""

        async def handler(_: web.Request) -> web.Response:
            headers = {} if retry_after is None else {"Retry-After": retry_after}
            return web.json_response(
                {"ok": False, "message": "Too many requests."},
                status=429,
                headers=headers,
            )

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookRateLimitError) as exc:
                await api.export_json(url)

        assert exc.value.retry_after is None
        assert "retry_after" not in str(exc.value)

    def test_api_error_does_not_leak_secret(self) -> None:
        """Structured API error text should not expose authentication secrets."""
        token = f"rbuapp_{RepeaterBookAPIError.__name__}"
        exc = RepeaterBookAPIError(
            "Invalid token",
            status_code=401,
            error_code="auth_invalid",
            url="https://example.com/api/export.php",
            body={
                "X-RB-App-Token": token,
                "Authorization": f"Bearer {token}",
            },
        )

        text = str(exc)
        assert token not in text
        assert "X-RB-App-Token" not in text
        assert "Authorization" not in text
