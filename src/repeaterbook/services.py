"""Services."""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "BOOL_MAP",
    "STATUS_MAP",
    "USE_MAP",
    "RepeaterBookAPI",
    "fetch_json",
    "json_to_model",
)

import asyncio
import hashlib
import json
import time
from datetime import date, timedelta
from typing import Any, Final, cast

import aiohttp
import attrs
from anyio import Path
from loguru import logger
from tqdm import tqdm
from yarl import URL

from repeaterbook.exceptions import (
    RepeaterBookAPIError,
    RepeaterBookValidationError,
)
from repeaterbook.models import (
    Emergency,
    EmergencyJSON,
    ExportErrorJSON,
    ExportJSON,
    ExportNorthAmericaQuery,
    ExportQuery,
    ExportWorldQuery,
    Mode,
    ModeJSON,
    Repeater,
    RepeaterJSON,
    ServiceType,
    ServiceTypeJSON,
    Status,
    Use,
)


async def fetch_json(
    url: URL,
    *,
    headers: dict[str, str] | None = None,
    cache_dir: Path | None = None,
    max_cache_age: timedelta = timedelta(seconds=3600),
    chunk_size: int = 1024,
) -> Any:  # noqa: ANN401 - json.loads() returns Any; validation done by callers
    """Fetches JSON data from the specified URL using a streaming response.

    - If a cached copy exists and is recent (not older than max_cache_age seconds) and
      not forced, it loads and returns the cached data.
    - Otherwise, it streams the data in chunks while displaying a progress bar, caches
      it, and returns the parsed JSON data.
    """
    # Create a unique filename for caching based on the URL hash.
    if cache_dir is None:
        cache_dir = Path()
    hashed_url = hashlib.sha256(str(url).encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"api_cache_{hashed_url}.json"
    temp_file = cache_dir / f"api_cache_{hashed_url}.tmp"

    # Check if fresh cached data exists using a single stat call.
    try:
        stat = await cache_file.stat()
        file_age = time.time() - stat.st_mtime
        if file_age < max_cache_age.total_seconds():
            logger.info("Using cached data.")
            return json.loads(await cache_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pass  # Cache doesn't exist, continue to fetch

    logger.info("Fetching new data from API...")
    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers) as response,
    ):
        response.raise_for_status()
        # Write to temp file first for atomic cache updates.
        async with await temp_file.open("wb") as f:
            with tqdm(
                total=response.content_length,
                unit="B",
                unit_scale=True,
            ) as progress:
                async for chunk in response.content.iter_chunked(chunk_size):
                    await f.write(chunk)
                    progress.update(len(chunk))

    # Atomic rename from temp file to cache file.
    # This prevents race conditions where concurrent requests might read
    # a partially written cache file.
    await temp_file.rename(cache_file)

    # After saving the file, load and parse the JSON data.
    return json.loads(await cache_file.read_text(encoding="utf-8"))


BOOL_MAP: Final = {
    "Yes": True,
    "No": False,
    1: True,
    0: False,
}


USE_MAP: Final = {
    "OPEN": Use.OPEN,
    "PRIVATE": Use.PRIVATE,
    "CLOSED": Use.CLOSED,
    "": Use.OPEN,  # Some export payloads include empty Use; treat as OPEN.
}

STATUS_MAP: Final = {
    "Off-air": Status.OFF_AIR,
    "On-air": Status.ON_AIR,
    "Unknown": Status.UNKNOWN,
}


def parse_date(date_str: str) -> date:
    """Parses a date string in the format YYYY-MM-DD."""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return date.min


def json_to_model(j: RepeaterJSON, /) -> Repeater:
    """Converts a JSON object to a Repeater model.

    RepeaterBook export payloads vary slightly between endpoints.

    - `exportROW.php` may include extra keys like `sponsor`.
    - `export.php` (North America) includes keys like `County`/`ARES`/… and may omit
      `Region`.

    This function should be resilient to those differences.
    """

    def s(key: str) -> str:
        v = j.get(key, "")
        if v is None:
            return ""
        return str(v)

    def b(key: str, *, default: bool = False) -> bool:
        """Parse RepeaterBook boolean-ish fields.

        RepeaterBook uses a mix of "Yes"/"No" strings and 1/0 ints.
        Missing/unknown values fall back to `default`.
        """
        return BOOL_MAP.get(j.get(key), default)

    return Repeater.model_validate(
        Repeater(
            state_id=s("State ID"),
            repeater_id=int(j.get("Rptr ID", 0) or 0),
            frequency=s("Frequency"),
            input_frequency=s("Input Freq"),
            pl_ctcss_uplink=s("PL") or None,
            pl_ctcss_tsq_downlink=s("TSQ") or None,
            location_nearest_city=s("Nearest City"),
            landmark=s("Landmark") or None,
            region=j.get("Region"),
            country=s("Country") or None,
            county=s("County") or None,
            state=s("State") or None,
            latitude=s("Lat"),
            longitude=s("Long"),
            precise=BOOL_MAP[j.get("Precise", 0)],
            callsign=s("Callsign") or None,
            use_membership=USE_MAP.get(s("Use"), Use.OPEN),
            operational_status=(
                STATUS_MAP[s("Operational Status")]
                if s("Operational Status")
                else Status.UNKNOWN
            ),
            ares=s("ARES") or None,
            races=s("RACES") or None,
            skywarn=s("SKYWARN") or None,
            canwarn=s("CANWARN") or None,
            allstar_node=s("AllStar Node") or None,
            echolink_node=s("EchoLink Node") or None,
            irlp_node=s("IRLP Node") or None,
            wires_node=s("Wires Node") or None,
            analog_capable=b("FM Analog", default=False),
            fm_bandwidth=s("FM Bandwidth").replace(" kHz", "") or None,
            dmr_capable=b("DMR", default=False),
            dmr_color_code=s("DMR Color Code") or None,
            dmr_id=s("DMR ID") or None,
            d_star_capable=b("D-Star", default=False),
            nxdn_capable=b("NXDN", default=False),
            apco_p_25_capable=b("APCO P-25", default=False),
            p_25_nac=s("P-25 NAC") or None,
            m17_capable=b("M17", default=False),
            m17_can=s("M17 CAN") or None,
            tetra_capable=b("Tetra", default=False),
            tetra_mcc=s("Tetra MCC") or None,
            tetra_mnc=s("Tetra MNC") or None,
            yaesu_system_fusion_capable=b("System Fusion", default=False),
            notes=s("Notes") or None,
            last_update=parse_date(s("Last Update")),
        )
    )


@attrs.frozen
class RepeaterBookAPI:
    """RepeaterBook API client.

    Must read https://www.repeaterbook.com/wiki/doku.php?id=api before using.

    Attributes:
        base_url: The RepeaterBook API base URL.
        app_name: Application name for User-Agent header.
        app_email: Contact email for User-Agent header.
        working_dir: Directory for cache and database files.
        max_cache_age: Maximum age of cached API responses before refresh.
            Defaults to 1 hour.
        max_count: Maximum expected results per API request. Used to warn
            when response may have been trimmed. Defaults to 3500.
    """

    base_url: URL = attrs.Factory(lambda: URL("https://repeaterbook.com"))
    app_name: str = "RepeaterBook Python SDK"
    app_email: str = "micael@jarniac.dev"

    working_dir: Path = attrs.Factory(Path)

    max_cache_age: timedelta = timedelta(hours=1)
    max_count: int = 3500

    async def cache_dir(self) -> Path:
        """Cache directory for API responses."""
        cache = self.working_dir / ".repeaterbook_cache"
        if not await cache.exists():
            logger.info("Creating cache directory.")
            await cache.mkdir(parents=True, exist_ok=True)
            gitignore = cache / ".gitignore"
            if not await gitignore.exists():
                logger.info("Creating .gitignore file.")
                await gitignore.write_text("*\n", encoding="utf-8")
        return cache

    @property
    def url_api(self) -> URL:
        """RepeaterBook API base URL."""
        return self.base_url / "api"

    @property
    def url_export_north_america(self) -> URL:
        """North-america export URL."""
        return self.url_api / "export.php"

    @property
    def url_export_rest_of_world(self) -> URL:
        """Rest of world (not north-america) export URL."""
        return self.url_api / "exportROW.php"

    # North America countries served by export.php endpoint
    NA_COUNTRIES: frozenset[str] = frozenset({
        "United States",
        "Canada",
        "Mexico",
    })

    def urls_export(
        self,
        query: ExportQuery,
    ) -> set[URL]:
        """Generate export URLs for given query.

        Smart routing logic:
        - If NA-specific fields are used (state_id, county, emcomm, stype),
          only query the NA endpoint
        - If ROW-specific fields are used (region), only query the ROW endpoint
        - If countries are specified, route based on whether they're NA or ROW
        - If no routing hints, query both endpoints
        """
        mode_map: dict[Mode, ModeJSON] = {
            Mode.ANALOG: "analog",
            Mode.DMR: "DMR",
            Mode.NXDN: "NXDN",
            Mode.P25: "P25",
            Mode.TETRA: "tetra",
        }
        emergency_map: dict[Emergency, EmergencyJSON] = {
            Emergency.ARES: "ARES",
            Emergency.RACES: "RACES",
            Emergency.SKYWARN: "SKYWARN",
            Emergency.CANWARN: "CANWARN",
        }
        type_map: dict[ServiceType, ServiceTypeJSON] = {
            ServiceType.GMRS: "GMRS",
        }

        # Determine which endpoints to query based on the query parameters
        has_na_specific = bool(
            query.state_ids or query.counties or
            query.emergency_services or query.service_types
        )
        has_row_specific = bool(query.regions)

        # Check if countries are specified and categorize them
        query_countries = {country.name for country in query.countries}
        has_na_countries = bool(query_countries & self.NA_COUNTRIES)
        has_row_countries = bool(query_countries - self.NA_COUNTRIES)

        # Determine which endpoints to query
        query_na_endpoint = True
        query_row_endpoint = True

        if has_na_specific and not has_row_specific:
            # NA-specific fields used, only query NA
            query_row_endpoint = False
        elif has_row_specific and not has_na_specific:
            # ROW-specific fields used, only query ROW
            query_na_endpoint = False
        elif query_countries:
            # Countries specified - route based on country location
            query_na_endpoint = has_na_countries
            query_row_endpoint = has_row_countries

        query_na = ExportNorthAmericaQuery(
            callsign=list(query.callsigns),
            city=list(query.cities),
            landmark=list(query.landmarks),
            country=[country.name for country in query.countries],
            frequency=[str(frequency) for frequency in query.frequencies],
            mode=[mode_map[mode] for mode in query.modes],
            state_id=list(query.state_ids),
            county=list(query.counties),
            emcomm=[emergency_map[emergency] for emergency in query.emergency_services],
            stype=[type_map[service_type] for service_type in query.service_types],
        )
        # Safe cast: dict comprehension preserves TypedDict structure, only removes
        # empty values (which are optional in ExportNorthAmericaQuery).
        query_na = cast(
            "ExportNorthAmericaQuery", {k: v for k, v in query_na.items() if v}
        )

        query_world = ExportWorldQuery(
            callsign=list(query.callsigns),
            city=list(query.cities),
            landmark=list(query.landmarks),
            country=[country.name for country in query.countries],
            frequency=[str(frequency) for frequency in query.frequencies],
            mode=[mode_map[mode] for mode in query.modes],
            region=list(query.regions),
        )
        # Safe cast: dict comprehension preserves TypedDict structure, only removes
        # empty values (which are optional in ExportWorldQuery).
        query_world = cast(
            "ExportWorldQuery", {k: v for k, v in query_world.items() if v}
        )

        # Safe casts: URL % operator expects dict[str, str], and TypedDict values
        # are all list[str] which serialize correctly for query parameters.
        urls: set[URL] = set()
        if query_na_endpoint:
            na_params = cast("dict[str, str]", query_na)
            urls.add(self.url_export_north_america % na_params)
        if query_row_endpoint:
            row_params = cast("dict[str, str]", query_world)
            urls.add(self.url_export_rest_of_world % row_params)
        return urls

    async def export_json(self, url: URL) -> ExportJSON:
        """Export data for given URL."""
        data: ExportJSON | ExportErrorJSON = await fetch_json(
            url,
            headers={"User-Agent": f"{self.app_name} <{self.app_email}>"},
            cache_dir=await self.cache_dir(),
            max_cache_age=self.max_cache_age,
        )

        if not isinstance(data, dict):
            msg = f"Expected dict response from API, got {type(data).__name__}"
            raise RepeaterBookValidationError(msg)

        if data.get("status") == "error":
            raise RepeaterBookAPIError(data.get("message", "Unknown API error"))

        if "count" not in data or "results" not in data:
            msg = "API response missing required 'count' or 'results' field"
            raise RepeaterBookValidationError(msg)

        data = cast("ExportJSON", data)

        if data["count"] >= self.max_count:
            logger.warning(
                "Reached max count for API response. Response may have been trimmed."
            )

        if data["count"] != len(data["results"]):
            logger.warning("Mismatched count and length of results.")

        return data

    async def export_multi_json(self, urls: set[URL]) -> list[ExportJSON]:
        """Export data for given URLs."""
        tasks = [self.export_json(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def download(self, query: ExportQuery) -> list[Repeater]:
        """Download repeaters."""
        data = await self.export_multi_json(self.urls_export(query))

        results: list[RepeaterJSON] = []
        for export in data:
            results.extend(export["results"])

        repeaters = [json_to_model(result) for result in results]

        logger.info(f"Downloaded {len(repeaters)} repeaters.")
        return repeaters
