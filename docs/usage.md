# Usage Guide

This comprehensive guide covers all the features and capabilities of the **RepeaterBook Python Client**.

## Authentication

As of RepeaterBook's [2026-03-03 API policy](https://www.repeaterbook.com/wiki/doku.php?id=api), the export endpoints require an approved per-user API token (an `rbuapp_...` token), sent via the `X-RB-App-Token` header.

### Getting a token

**You do not need to register an application.** This library is already registered with RepeaterBook, so all you need is a free RepeaterBook account and a token issued against that existing registration:

| Field | Value |
|---|---|
| Application | **RepeaterBook Python Client** |
| Application ID | **App #114** |

1. Create a free [RepeaterBook](https://www.repeaterbook.com/) account, or log in to an existing one.
2. Go to [API Applications](https://www.repeaterbook.com/user/api_apps.php).
3. Find **RepeaterBook Python Client** (**App #114**) in the application list.
4. Generate a token for it. You'll get a string starting with `rbuapp_`.

The token is yours personally — it is tied to your account, not to the application — so keep it out of source control. The usual approach is an environment variable:

```bash
export REPEATERBOOK="rbuapp_your_token_here"
```

```python
import os

from repeaterbook.services import RepeaterBookAPI

api = RepeaterBookAPI(
    app_token=os.environ["REPEATERBOOK"],
)
```

That's all. The default `User-Agent` already matches App #114, so the token works out of the box.

!!! warning "Never share or distribute a token"
    This library is a *distributed* client: each user must generate and use their own `rbuapp_...` token. Do not embed a shared `app_...` token in source code, installers, or public repositories.

### Leave the User-Agent alone

The `app_name`, `app_version`, and `app_contact` arguments form the `User-Agent`:

```
RepeaterBook Python Client/0.6.0 (+micael@jarniac.dev)
```

That string is what RepeaterBook approved for App #114, and the API matches it literally. Changing any of the three — including setting `app_contact` to your own address — makes the request no longer match the registered application and returns `403 ua_mismatch`, even with a valid token. The defaults are correct for the token you generated above; don't override them.

### Using your own registered application

Override the identity only if you registered a *separate* application with RepeaterBook and hold a token for it. In that case all three values must match your registration byte for byte:

```python
api = RepeaterBookAPI(
    app_token=os.environ["REPEATERBOOK"],
    app_name="my-app",
    app_version="1.0.0",
    app_contact="you@example.org",
)
```

### Authentication errors

| Symptom | Cause | Fix |
|---|---|---|
| `401 auth_missing` | No token sent | Pass `app_token` |
| `401 auth_invalid` | Token wrong, revoked, or expired | Regenerate it on [API Applications](https://www.repeaterbook.com/user/api_apps.php) |
| `403 ua_mismatch` | `User-Agent` doesn't match the application the token was issued for | Drop your `app_name`/`app_version`/`app_contact` overrides and use the defaults |

## API Client

### RepeaterBookAPI

The `RepeaterBookAPI` class provides access to the RepeaterBook.com API.

#### Basic Usage

```python
import os
from repeaterbook.services import RepeaterBookAPI
from datetime import timedelta

# Create an API client with default settings
api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])

# Custom configuration
api = RepeaterBookAPI(
    app_token=os.environ["REPEATERBOOK"],
    max_cache_age=timedelta(hours=2),  # Cache responses for 2 hours
    max_count=5000,  # Expected max results (default: 3500)
)
```

Every example below assumes a token — see [Authentication](#authentication).

#### Downloading Repeater Data

The `download()` method fetches repeater data from the API:

```python
import asyncio
import os
from repeaterbook.models import ExportQuery
import pycountry

async def download_example():
    api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])

    # Download by country
    germany = pycountry.countries.get(name="Germany")
    repeaters = await api.download(
        query=ExportQuery(countries={germany})
    )

    # Download by multiple countries
    countries = {
        pycountry.countries.get(name="France"),
        pycountry.countries.get(name="Belgium"),
    }
    repeaters = await api.download(
        query=ExportQuery(countries=countries)
    )

    # Download by state (USA) - use FIPS codes
    usa = pycountry.countries.get(alpha_2="US")
    repeaters = await api.download(
        query=ExportQuery(
            countries={usa},
            state_ids={"06", "41", "53"}  # CA, OR, WA
        )
    )

    return repeaters

repeaters = asyncio.run(download_example())
```

#### Caching

The API client automatically caches responses to reduce load on RepeaterBook.com's servers and improve performance:

- Default cache directory: `.repeaterbook_cache/`, relative to `working_dir`
- Default cache TTL: 3600 seconds (1 hour)
- Cache is keyed on a hash of the full request URL, one entry per URL. A query
  that fans out to both the North America and Rest-of-World endpoints therefore
  produces two entries.

```python
# First call downloads from API (slow)
repeaters1 = await api.download(query=ExportQuery(countries={brazil}))

# Second call uses cache (fast)
repeaters2 = await api.download(query=ExportQuery(countries={brazil}))

# Different query downloads from API
repeaters3 = await api.download(query=ExportQuery(countries={argentina}))
```

#### Progress Bars

Long downloads automatically display progress bars using `tqdm`:

```python
# The bar measures bytes downloaded, not repeater records:
# 4.51MB [00:05, 892kB/s]
repeaters = await api.download(query=ExportQuery(countries={usa}))
```

### Export Queries

The frozen `ExportQuery` class specifies what data to download:

```python
from repeaterbook.models import ExportQuery
import pycountry

# By country
query = ExportQuery(
    countries={pycountry.countries.get(name="Japan")}
)

# By country and state (use FIPS codes)
query = ExportQuery(
    countries={pycountry.countries.get(alpha_2="US")},
    state_ids={"48", "40", "35"}  # TX, OK, NM
)

# Multiple countries
query = ExportQuery(
    countries={
        pycountry.countries.get(name="Australia"),
        pycountry.countries.get(name="New Zealand"),
    }
)
```

## Database Operations

### RepeaterBook Class

The `RepeaterBook` class manages a local SQLite database of repeaters:

```python
from repeaterbook import RepeaterBook
from anyio import Path

# Default database file (./repeaterbook.db)
rb = RepeaterBook()

# Custom database file name
rb = RepeaterBook(database="my_repeaters.db")

# Custom working directory
rb = RepeaterBook(working_dir=Path("/tmp"), database="repeaters.db")
```

### Populating the Database

Use `populate()` to add repeaters to the database:

```python
# Add repeaters (merges, doesn't duplicate)
rb.populate(repeaters)

# Populate from API directly
import os
from repeaterbook.services import RepeaterBookAPI
import pycountry

api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])
italy = pycountry.countries.get(name="Italy")
repeaters = await api.download(query=ExportQuery(countries={italy}))
rb.populate(repeaters)
```

The `populate()` method intelligently merges data:
- Detects duplicates by the composite primary key, `state_id` + `repeater_id`
- Updates existing records if they've changed
- Adds new records

### Querying Repeaters

The `query()` method accepts SQLAlchemy filter expressions:

```python
from repeaterbook import Repeater
from repeaterbook.models import Status, Use

# Simple queries
operational = rb.query(Repeater.operational_status == Status.ON_AIR)
open_repeaters = rb.query(Repeater.use_membership == Use.OPEN)

# Multiple conditions (AND)
results = rb.query(
    Repeater.operational_status == Status.ON_AIR,
    Repeater.use_membership == Use.OPEN,
    Repeater.dmr_capable == True
)

# OR conditions
digital = rb.query(
    (Repeater.dmr_capable | Repeater.apco_p_25_capable | Repeater.nxdn_capable)
)

# Complex queries
from sqlmodel import or_, and_

results = rb.query(
    and_(
        Repeater.operational_status == Status.ON_AIR,
        or_(
            Repeater.dmr_capable == True,
            Repeater.apco_p_25_capable == True
        )
    )
)
```

## Geographic Queries

### Defining Locations

Use the provided utility types for geographic data:

```python
from repeaterbook.utils import LatLon, Radius

# Define a point
location = LatLon(lat=51.5074, lon=-0.1278)  # London

# Define a search radius
radius = Radius(
    origin=LatLon(lat=51.5074, lon=-0.1278),
    distance=50  # kilometers
)
```

### Square Bounding Box

The `square()` function creates a bounding box query:

```python
from repeaterbook.queries import square
from repeaterbook.utils import LatLon, Radius

# Define search area
radius = Radius(
    origin=LatLon(lat=51.5074, lon=-0.1278),
    distance=50
)

# Get repeaters in bounding box
repeaters = rb.query(square(radius))
```

This is very fast as it uses simple latitude/longitude comparisons.

### Distance Filtering

For precise distance calculations, use `filter_radius()`:

```python
from repeaterbook.queries import filter_radius

# Get repeaters in bounding box
candidates = rb.query(square(radius))

# Filter by actual distance (uses Haversine formula)
# filter_radius returns repeaters sorted by distance from origin
nearby = filter_radius(candidates, radius)

# Results are already sorted by distance
# If you need the distance value for display, calculate it:
from haversine import haversine
for rep in nearby[:10]:
    distance = haversine(radius.origin, (rep.latitude, rep.longitude), unit=radius.unit)
    print(f"{distance:.1f}km - {rep.callsign}")
```

### Distance Units

The `haversine` library supports multiple units:

```python
from haversine import Unit

# Kilometers (default)
radius = Radius(origin=location, distance=50)

# Miles
radius = Radius(origin=location, distance=30, unit=Unit.MILES)

# Nautical miles
radius = Radius(origin=location, distance=25, unit=Unit.NAUTICAL_MILES)
```

## Frequency and Band Queries

### Band Filtering

The `Bands` enum defines common amateur radio bands:

```python
from repeaterbook.queries import Bands, band

# Available bands
# Bands.M_10   # 10 meters (28-29.7 MHz)
# Bands.M_6    # 6 meters (50-54 MHz)
# Bands.M_4    # 4 meters (70-72 MHz)
# Bands.M_2    # 2 meters (144-148 MHz)
# Bands.CM_70  # 70 centimeters (420-450 MHz)
# Bands.CM_33  # 33 centimeters (902-928 MHz)
# Bands.CM_23  # 23 centimeters (1240-1300 MHz)
# Bands.CM_13  # 13 centimeters (2300-2450 MHz)
# Bands.CM_3   # 3 centimeters (10000-10500 MHz)

# Query single band
vhf_repeaters = rb.query(band(Bands.M_2))

# Query multiple bands
vhf_uhf = rb.query(band(Bands.M_2, Bands.CM_70))
```

### Frequency Range Queries

For custom frequency ranges:

```python
# Repeaters between 145.0 and 146.0 MHz
results = rb.query(
    Repeater.frequency >= 145.0,
    Repeater.frequency <= 146.0
)

# Sort by frequency
sorted_results = sorted(results, key=lambda r: r.frequency)
```

## Digital Mode Queries

### Capability Flags

The `Repeater` model includes capability flags for different digital modes:

```python
# DMR repeaters
dmr = rb.query(Repeater.dmr_capable == True)

# P25 repeaters
p25 = rb.query(Repeater.apco_p_25_capable == True)

# NXDN repeaters
nxdn = rb.query(Repeater.nxdn_capable == True)

# Analog repeaters
analog = rb.query(Repeater.analog_capable == True)

# Any digital mode
digital = rb.query(
    (Repeater.dmr_capable | Repeater.apco_p_25_capable | Repeater.nxdn_capable)
)

# Dual mode (analog + digital)
dual_mode = rb.query(
    Repeater.analog_capable == True,
    (Repeater.dmr_capable | Repeater.apco_p_25_capable | Repeater.nxdn_capable)
)
```

### DMR Specific Data

DMR-capable repeaters include additional fields:

```python
dmr_repeaters = rb.query(Repeater.dmr_capable == True)

for rep in dmr_repeaters:
    print(f"{rep.callsign}:")
    print(f"  DMR ID: {rep.dmr_id}")
    print(f"  Color Code: {rep.dmr_color_code}")
```

### P25 Specific Data

```python
p25_repeaters = rb.query(Repeater.apco_p_25_capable == True)

for rep in p25_repeaters:
    print(f"{rep.callsign}:")
    print(f"  NAC: {rep.p_25_nac}")
```

## Filtering by Access

### Membership Types

```python
from repeaterbook.models import Use

# Open repeaters (no membership required)
open_repeaters = rb.query(Repeater.use_membership == Use.OPEN)

# Private repeaters (membership required)
private = rb.query(Repeater.use_membership == Use.PRIVATE)

# Closed repeaters (restricted access)
closed = rb.query(Repeater.use_membership == Use.CLOSED)
```

### CTCSS Tones

Filter by required access tones:

```python
# The tone fields are strings, not numbers: RepeaterBook packs both CTCSS
# frequencies ("110.9") and DCS codes ("D023") into the same column. Compare
# against strings, and match the exact spelling stored.

# Repeaters with a tone
with_tone = rb.query(Repeater.pl_ctcss_uplink.is_not(None))

# Specific CTCSS tone
tone_110_9 = rb.query(Repeater.pl_ctcss_uplink == "110.9")

# No tone required
no_tone = rb.query(Repeater.pl_ctcss_uplink.is_(None))
```

## Status Filtering

### Operational Status

```python
from repeaterbook.models import Status

# On-air repeaters
on_air = rb.query(Repeater.operational_status == Status.ON_AIR)

# Off-air repeaters
off_air = rb.query(Repeater.operational_status == Status.OFF_AIR)

# Unknown status
unknown = rb.query(Repeater.operational_status == Status.UNKNOWN)
```

### Emergency Services

These four columns are strings, and the North America export sets them to
`"Yes"` **or `"No"`** — not to null when a service is unsupported. So a null
check matches every row, and `== True` matches none: compare to `"Yes"`.

```python
# Repeaters with ARES support
ares = rb.query(Repeater.ares == "Yes")

# Repeaters with RACES support
races = rb.query(Repeater.races == "Yes")

# Repeaters with SKYWARN support
skywarn = rb.query(Repeater.skywarn == "Yes")

# Repeaters with CANWARN support
canwarn = rb.query(Repeater.canwarn == "Yes")

# Any emergency services
emergency = rb.query(
    (Repeater.ares == "Yes") |
    (Repeater.races == "Yes") |
    (Repeater.skywarn == "Yes") |
    (Repeater.canwarn == "Yes")
)
```

!!! note "Rest-of-world exports omit these fields"
    `exportROW.php` does not send `ARES`/`RACES`/`SKYWARN`/`CANWARN` at all, so
    for non-NA repeaters they are `None` rather than `"No"`. Treat `None` as
    "unknown", not as "unsupported".

## Combining Queries

### Complex Search Example

Find the best repeaters for a specific use case:

```python
from repeaterbook.queries import square, filter_radius, band, Bands
from repeaterbook.utils import LatLon, Radius
from repeaterbook.models import Status, Use

# Location: Chicago, IL
chicago = LatLon(lat=41.8781, lon=-87.6298)
radius = Radius(origin=chicago, distance=100)  # 100 km

# Find: Nearby, open, operational, DMR-capable repeaters on 70cm
results = rb.query(
    square(radius),
    Repeater.operational_status == Status.ON_AIR,
    Repeater.use_membership == Use.OPEN,
    Repeater.dmr_capable == True,
    band(Bands.CM_70)
)

# Filter by actual distance
# filter_radius returns repeaters sorted by distance
nearby = filter_radius(results, radius)

# Display results
from haversine import haversine
for rep in nearby[:10]:
    distance = haversine(radius.origin, (rep.latitude, rep.longitude), unit=radius.unit)
    print(f"{distance:5.1f}km - {rep.frequency:.4f} MHz - {rep.callsign}")
    print(f"  Location: {rep.location_nearest_city}")
    print(f"  DMR ID: {rep.dmr_id}, CC: {rep.dmr_color_code}")
    print(f"  Tone: {rep.pl_ctcss_uplink or 'None'}")
    print()
```

## Data Export

### Export to Pandas

```python
import pandas as pd

# Query repeaters
results = rb.query(Repeater.operational_status == Status.ON_AIR)

# Convert to DataFrame
data = [r.model_dump() for r in results]
df = pd.DataFrame(data)

# Analyze
print(df.describe())
print(df.groupby('use_membership').size())

# Export to CSV
df.to_csv('repeaters.csv', index=False)
```

### Export to JSON

```python
import json

results = rb.query(band(Bands.M_2))

# Convert to JSON
data = [r.model_dump() for r in results]

with open('repeaters.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

### Export for Radio Programming

```python
# Format for Chirp or other programming software
results = rb.query(
    square(radius),
    Repeater.operational_status == Status.ON_AIR
)

nearby = filter_radius(results, radius)

# Create CSV in Chirp format
import csv

with open('chirp_import.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Location', 'Name', 'Frequency', 'Duplex', 'Offset',
                     'Tone', 'rToneFreq', 'cToneFreq', 'DtcsCode', 'Comment'])

    # filter_radius returns repeaters sorted by distance
    # Calculate distance for each repeater for display
    from haversine import haversine
    for idx, rep in enumerate(nearby, start=1):
        distance = haversine(radius.origin, (rep.latitude, rep.longitude), unit=radius.unit)
        writer.writerow([
            idx,  # Chirp's "Location" is a channel slot number
            rep.callsign or '',
            rep.frequency,
            '+' if rep.input_frequency < rep.frequency else '-',
            abs(rep.frequency - rep.input_frequency),
            'Tone' if rep.pl_ctcss_uplink else '',
            rep.pl_ctcss_uplink or '',
            rep.pl_ctcss_tsq_downlink or '',
            '',  # DCS code not available
            f"{rep.location_nearest_city} - {distance:.1f}km"
        ])
```

## Working with Repeater Objects

### Repeater Model Fields

Key fields available on `Repeater` objects:

```python
# Identification. The primary key is the (state_id, repeater_id) pair --
# there is no single `id` field.
rep.state_id        # RepeaterBook state/province ID (e.g. "06")
rep.repeater_id     # RepeaterBook repeater ID, unique within that state
rep.callsign        # Repeater callsign (may be None)
rep.location_nearest_city  # City/location description

# Frequency
rep.frequency       # Output frequency (MHz)
rep.input_frequency # Input frequency (MHz)

# Access tones. Strings, not numbers -- may hold a CTCSS frequency
# ("110.9") or a DCS code ("D023"), or be None.
rep.pl_ctcss_uplink        # Input CTCSS/PL tone
rep.pl_ctcss_tsq_downlink  # Output CTCSS/TSQ tone

# Status
rep.operational_status  # ON_AIR, OFF_AIR, UNKNOWN
rep.use_membership      # OPEN, PRIVATE, CLOSED

# Emergency Services (string fields)
# Emergency services. Strings: "Yes"/"No" on North America exports, and
# None on rest-of-world exports, which omit these fields entirely.
rep.ares            # ARES support indicator
rep.races           # RACES support indicator
rep.skywarn         # SKYWARN support indicator
rep.canwarn         # CANWARN support indicator

# Capabilities
rep.analog_capable       # Boolean
rep.dmr_capable          # Boolean
rep.apco_p_25_capable    # Boolean (P25)
rep.nxdn_capable         # Boolean
rep.tetra_capable        # Boolean

# Digital mode details
rep.dmr_id          # DMR radio ID
rep.dmr_color_code  # DMR color code (0-15)
rep.p_25_nac        # P25 NAC code

# Location
rep.latitude        # Latitude (degrees)
rep.longitude       # Longitude (degrees)
rep.precise         # Precise location flag

# Notes
rep.notes           # Additional information
```

### Checking Capabilities

```python
def describe_repeater(rep):
    """Print a detailed description of a repeater."""
    print(f"=== {rep.callsign or rep.location_nearest_city} ===")
    print(f"Frequency: {rep.frequency:.4f} MHz ({rep.input_frequency:.4f} MHz)")
    print(f"Location: {rep.location_nearest_city}")
    print(f"Coordinates: {rep.latitude:.4f}, {rep.longitude:.4f}")

    # Access. The field is a string and may be a DCS code, so don't label
    # it as Hz unconditionally.
    if rep.pl_ctcss_uplink:
        print(f"Tone: {rep.pl_ctcss_uplink}")

    # Modes
    modes = []
    if rep.analog_capable:
        modes.append("FM")
    if rep.dmr_capable:
        modes.append(f"DMR (CC{rep.dmr_color_code})")
    if rep.apco_p_25_capable:
        # `p_25_nac` is a string as published, not an int -- don't format it
        # with a numeric spec.
        modes.append(f"P25 (NAC {rep.p_25_nac})")
    if rep.nxdn_capable:
        modes.append("NXDN")

    print(f"Modes: {', '.join(modes)}")
    # `Status` and `Use` are plain enums built with `auto()`, so `.value` is an
    # integer. Use `.name` for a readable label.
    print(f"Status: {rep.operational_status.name}")
    print(f"Access: {rep.use_membership.name}")

    if rep.notes:
        print(f"Notes: {rep.notes}")

# Example usage
results = rb.query(Repeater.callsign == "W6CX")
if results:
    describe_repeater(results[0])
```

## Performance Tips

### Use Bounding Box First

Always use `square()` before `filter_radius()` to reduce the number of distance calculations:

```python
# Good: Fast
candidates = rb.query(square(radius))
nearby = filter_radius(candidates, radius)

# Bad: Slow (calculates distance for ALL repeaters)
all_repeaters = rb.query()
nearby = filter_radius(all_repeaters, radius)
```

### Limit Query Results

For large result sets, consider using additional filters to narrow down results:

```python
# Query with multiple filters to reduce result size
results = rb.query(
    Repeater.operational_status == Status.ON_AIR,
    Repeater.use_membership == Use.OPEN,
    band(Bands.M_2)
)

# Or use Python slicing on results
results = rb.query(Repeater.operational_status == Status.ON_AIR)[:100]
```

### Cache API Responses

The API client automatically caches, but you can customize:

```python
from datetime import timedelta

# Longer cache for stable data
api = RepeaterBookAPI(max_cache_age=timedelta(hours=24))

# Shorter cache for frequently changing data
api = RepeaterBookAPI(max_cache_age=timedelta(minutes=30))
```

### Reuse Database Connection

```python
# Create once
rb = RepeaterBook(database="repeaters.db")

# Reuse for multiple queries
results1 = rb.query(band(Bands.M_2))
results2 = rb.query(band(Bands.CM_70))
results3 = rb.query(Repeater.dmr_capable == True)
```

## Error Handling

The RepeaterBook Python Client provides custom exceptions for robust error handling:

```python
from repeaterbook import (
    RepeaterBookError,
    RepeaterBookAPIError,
    RepeaterBookRateLimitError,
    RepeaterBookValidationError,
)

try:
    repeaters = await api.download(query=ExportQuery(countries={brazil}))
except RepeaterBookRateLimitError as e:
    # HTTP 429 -- carries `retry_after` when the API supplies it.
    # Must precede RepeaterBookAPIError, being a subclass of it.
    print(f"Rate limited, retry after {e.retry_after}s")
except RepeaterBookAPIError as e:
    # Any other API error response
    print(f"API error: {e}")
except RepeaterBookValidationError as e:
    # Invalid response format or data
    print(f"Validation error: {e}")
except RepeaterBookError as e:
    # Catch all library errors
    print(f"RepeaterBook error: {e}")
```

### Exception Types

| Exception | Description |
|-----------|-------------|
| `RepeaterBookError` | Base exception for all library errors |
| `RepeaterBookAPIError` | Any HTTP 4xx/5xx other than 401/403/429, or a 200 response whose body reports an error |
| `RepeaterBookUnauthorizedError` | HTTP 401 — missing or invalid app token |
| `RepeaterBookForbiddenError` | HTTP 403 — User-Agent or authorization denied |
| `RepeaterBookRateLimitError` | HTTP 429 — rate limited; carries `retry_after` |
| `RepeaterBookValidationError` | Invalid data or response format |
| `RepeaterBookRowError` | A single export row could not be modelled |
| `RepeaterBookCacheError` | Reserved for cache read/write failures. Not currently raised — an unreadable or corrupt cache entry is treated as a miss and refetched |

`RepeaterBookUnauthorizedError`, `RepeaterBookForbiddenError` and
`RepeaterBookRateLimitError` are subclasses of `RepeaterBookAPIError`;
`RepeaterBookRowError` is a subclass of `RepeaterBookValidationError`. Catching
the parent catches all of them.

### Data Validation

The `Repeater` model includes built-in validation:

```python
# These will raise ValueError if invalid:
# - Latitude must be between -90 and 90
# - Longitude must be between -180 and 180
# - Frequency must be positive
```

### Malformed Rows

RepeaterBook's data is community-maintained, and individual records
occasionally fail that validation — a zero input frequency, an out-of-range
coordinate. `download()` **logs and skips** those rows rather than failing the
whole response, so one bad record cannot cost you the other few thousand.

To see exactly what was dropped, pass a list for `skipped`:

```python
from repeaterbook.exceptions import RepeaterBookRowError

skipped: list[RepeaterBookRowError] = []
repeaters = await api.download(query, skipped=skipped)

for error in skipped:
    print(f"Dropped {error.label}: {error}")  # e.g. "48:24371 (W5AW)"
    print(error.row)  # the raw payload, for reporting upstream
```

If you would rather a malformed row be an error, opt into strict mode:

```python
# Raises RepeaterBookRowError on the first row that cannot be modelled.
repeaters = await api.download(query, strict=True)
```

## Logging

The RepeaterBook Python Client uses `loguru` for logging:

```python
from loguru import logger

# Enable debug logging
logger.add("repeaterbook.log", level="DEBUG")

# Now operations will be logged
repeaters = await api.download(query=ExportQuery(countries={brazil}))
```

## Next Steps

- [Examples](examples.md) - Real-world use cases and patterns
- [Architecture](architecture.md) - Understanding the internals
- [FAQ](faq.md) - Common questions and troubleshooting
- [API Reference](api.md) - Complete API documentation
