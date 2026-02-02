"""Tests for services module."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pycountry
import pytest
from aiohttp import web
from yarl import URL

from repeaterbook.exceptions import (
    RepeaterBookAPIError,
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
    parse_date,
)

if TYPE_CHECKING:
    from pathlib import Path as StdPath

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

    def test_urls_export_with_country(self) -> None:
        """Query with country should include country in URL."""
        api = RepeaterBookAPI()
        brazil = pycountry.countries.lookup("Brazil")
        query = ExportQuery(countries=frozenset({brazil}))
        urls = api.urls_export(query)
        # Check that at least one URL contains the country
        url_strs = [str(url) for url in urls]
        assert any("Brazil" in url for url in url_strs)

    def test_urls_export_with_mode(self) -> None:
        """Query with mode should include mode in URL."""
        api = RepeaterBookAPI()
        query = ExportQuery(modes=frozenset({Mode.DMR}))
        urls = api.urls_export(query)
        url_strs = [str(url) for url in urls]
        assert any("DMR" in url for url in url_strs)

    def test_custom_base_url(self) -> None:
        """Custom base_url should be used."""
        api = RepeaterBookAPI(base_url=URL("https://example.com"))
        assert api.url_api == URL("https://example.com/api")


class TestRepeaterBookAPIExport:
    """Tests for RepeaterBookAPI export methods."""

    @pytest.mark.anyio
    async def test_export_json_raises_on_non_dict_response(
        self, tmp_path: StdPath, local_server: Any  # noqa: ANN401
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
        self, tmp_path: StdPath, local_server: Any  # noqa: ANN401
    ) -> None:
        """export_json should raise RepeaterBookAPIError on API error response."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"status": "error", "message": "Rate limited"})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            with pytest.raises(RepeaterBookAPIError, match="Rate limited"):
                await api.export_json(url)

    @pytest.mark.anyio
    async def test_export_json_raises_on_missing_count(
        self, tmp_path: StdPath, local_server: Any  # noqa: ANN401
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
        self, tmp_path: StdPath, local_server: Any  # noqa: ANN401
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
        self, tmp_path: StdPath, local_server: Any  # noqa: ANN401
    ) -> None:
        """export_json should return data on valid response."""

        async def handler(_: web.Request) -> web.Response:
            return web.json_response({"count": 1, "results": [{"test": "data"}]})

        async with local_server(handler) as url:
            api = RepeaterBookAPI(working_dir=Path(tmp_path))
            result = await api.export_json(url)
            assert result["count"] == 1
            assert len(result["results"]) == 1
