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
from typing import Any, ClassVar, Final, cast

import aiohttp
import attrs
from anyio import Path
from loguru import logger
from tqdm import tqdm
from yarl import URL

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
) -> Any:  # noqa: ANN401
    """Fetches JSON data from the specified URL using a streaming response.

    - If a cached copy exists and is recent (not older than max_cache_age seconds) and
      not forced, it loads and returns the cached data.
    - Otherwise, it streams the data in chunks while displaying a progress bar, caches
      it, and returns the parsed JSON data.
    """
    # Create a unique filename for caching based on the URL hash.
    if cache_dir is None:
        cache_dir = Path()
    hashed_url = hashlib.md5(str(url).encode("utf-8")).hexdigest()  # noqa: S324
    cache_file = cache_dir / f"api_cache_{hashed_url}.json"

    # Check if fresh cached data exists.
    if await cache_file.exists():
        file_age = time.time() - (await cache_file.stat()).st_mtime
        if file_age < max_cache_age.total_seconds():
            logger.info("Using cached data.")
            return json.loads(await cache_file.read_text(encoding="utf-8"))

    await cache_file.unlink(missing_ok=True)

    logger.info("Fetching new data from API...")
    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers) as response,
    ):
        response.raise_for_status()
        # Open file for writing in binary mode and stream content into it.
        async with await cache_file.open("wb") as f:
            with tqdm(
                total=response.content_length,
                unit="B",
                unit_scale=True,
            ) as progress:
                async for chunk in response.content.iter_chunked(chunk_size):
                    await f.write(chunk)
                    progress.update(len(chunk))

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
    """Converts a JSON object to a Repeater model."""
    return Repeater.model_validate(
        Repeater(
            state_id=j["State ID"],
            repeater_id=j["Rptr ID"],
            frequency=j["Frequency"],
            input_frequency=j["Input Freq"],
            pl_ctcss_uplink=j["PL"] or None,
            pl_ctcss_tsq_downlink=j["TSQ"] or None,
            location_nearest_city=j["Nearest City"],
            landmark=j["Landmark"] or None,
            region=j["Region"],
            state=j["State"],
            country=j["Country"],
            latitude=j["Lat"],
            longitude=j["Long"],
            precise=BOOL_MAP[j["Precise"]],
            callsign=j["Callsign"],
            use_membership=USE_MAP[j["Use"]],
            operational_status=STATUS_MAP[j["Operational Status"]],
            allstar_node=j["AllStar Node"],
            echolink_node=str(j["EchoLink Node"]) or None,
            irlp_node=j["IRLP Node"] or None,
            wires_node=j["Wires Node"] or None,
            analog_capable=BOOL_MAP[j["FM Analog"]],
            fm_bandwidth=j["FM Bandwidth"].replace(" kHz", "") or None,
            dmr_capable=BOOL_MAP[j["DMR"]],
            dmr_color_code=j["DMR Color Code"] or None,
            dmr_id=str(j["DMR ID"]) or None,
            d_star_capable=BOOL_MAP[j["D-Star"]],
            nxdn_capable=BOOL_MAP[j["NXDN"]],
            apco_p_25_capable=BOOL_MAP[j["APCO P-25"]],
            p_25_nac=j["P-25 NAC"] or None,
            m17_capable=BOOL_MAP[j["M17"]],
            m17_can=j["M17 CAN"] or None,
            tetra_capable=BOOL_MAP[j["Tetra"]],
            tetra_mcc=j["Tetra MCC"] or None,
            tetra_mnc=j["Tetra MNC"] or None,
            yaesu_system_fusion_capable=BOOL_MAP[j["System Fusion"]],
            notes=j["Notes"] or None,
            last_update=parse_date(j["Last Update"]),
        )
    )


@attrs.frozen
class RepeaterBookAPI:
    """RepeaterBook API client."""

    base_url: URL = attrs.Factory(lambda: URL("https://repeaterbook.com"))
    app_name: str = "RepeaterBook Python SDK"
    app_email: str = "micael@jarniac.dev"

    working_dir: Path = attrs.Factory(Path)

    MAX_COUNT: ClassVar[int] = 3500

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

    def urls_export(
        self,
        query: ExportQuery,
    ) -> set[URL]:
        """Generate export URLs for given query."""
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
        query_world = cast(
            "ExportWorldQuery", {k: v for k, v in query_world.items() if v}
        )

        return {
            #' self.url_export_north_america % cast("dict[str, str]", query_na),
            self.url_export_rest_of_world % cast("dict[str, str]", query_world),
        }

    async def export_json(self, url: URL) -> ExportJSON:
        """Export data for given URL."""
        data: ExportJSON | ExportErrorJSON = await fetch_json(
            url,
            headers={"User-Agent": f"{self.app_name} <{self.app_email}>"},
            cache_dir=await self.cache_dir(),
        )

        if not isinstance(data, dict):
            raise TypeError

        if data.get("status") == "error":
            raise ValueError(data.get("message"))

        if "count" not in data or "results" not in data:
            raise ValueError

        data = cast("ExportJSON", data)

        if data["count"] >= self.MAX_COUNT:
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
