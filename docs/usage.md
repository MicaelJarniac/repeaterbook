# Usage Guide

This comprehensive guide covers all the features and capabilities of **RepeaterBook**.

## API Client

### RepeaterBookAPI

The `RepeaterBookAPI` class provides access to the RepeaterBook.com API.

#### Basic Usage

```python
from repeaterbook.services import RepeaterBookAPI

# Create an API client with default settings
api = RepeaterBookAPI()

# Custom cache directory and TTL
api = RepeaterBookAPI(
    cache_dir=".my_cache",
    cache_ttl=7200  # 2 hours in seconds
)
```

#### Downloading Repeater Data

The `download()` method fetches repeater data from the API:

```python
import asyncio
from repeaterbook.models import ExportQuery
import pycountry

async def download_example():
    api = RepeaterBookAPI()

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

    # Download by state (USA)
    usa = pycountry.countries.get(alpha_2="US")
    repeaters = await api.download(
        query=ExportQuery(
            countries={usa},
            states={"California", "Oregon", "Washington"}
        )
    )

    return repeaters

repeaters = asyncio.run(download_example())
```

#### Caching

The API client automatically caches responses to reduce load on the RepeaterBook servers and improve performance:

- Default cache directory: `.repeaterbook_cache/`
- Default cache TTL: 3600 seconds (1 hour)
- Cache is based on the query parameters

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
# Progress bar shows automatically for large downloads
# Downloading repeaters: 100%|████████████| 1234/1234 [00:05<00:00, 245.67it/s]
repeaters = await api.download(query=ExportQuery(countries={usa}))
```

### Export Queries

The `ExportQuery` dataclass specifies what data to download:

```python
from repeaterbook.models import ExportQuery
import pycountry

# By country
query = ExportQuery(
    countries={pycountry.countries.get(name="Japan")}
)

# By country and state
query = ExportQuery(
    countries={pycountry.countries.get(alpha_2="US")},
    states={"Texas", "Oklahoma", "New Mexico"}
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

# Default database file (repeaterbook.db)
rb = RepeaterBook()

# Custom database file
rb = RepeaterBook("my_repeaters.db")

# In-memory database (for temporary use)
rb = RepeaterBook(":memory:")
```

### Populating the Database

Use `populate()` to add repeaters to the database:

```python
# Add repeaters (merges, doesn't duplicate)
rb.populate(repeaters)

# Populate from API directly
from repeaterbook.services import RepeaterBookAPI
import pycountry

api = RepeaterBookAPI()
italy = pycountry.countries.get(name="Italy")
repeaters = await api.download(query=ExportQuery(countries={italy}))
rb.populate(repeaters)
```

The `populate()` method intelligently merges data:
- Uses the `id` field to detect duplicates
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
    (Repeater.dmr_capable | Repeater.p25_capable | Repeater.nxdn_capable)
)

# Complex queries
from sqlmodel import or_, and_

results = rb.query(
    and_(
        Repeater.operational_status == Status.ON_AIR,
        or_(
            Repeater.dmr_capable == True,
            Repeater.p25_capable == True
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
location = LatLon(latitude=51.5074, longitude=-0.1278)  # London

# Define a search radius
radius = Radius(
    origin=LatLon(latitude=51.5074, longitude=-0.1278),
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
    origin=LatLon(latitude=51.5074, longitude=-0.1278),
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
nearby = filter_radius(candidates, radius)

# Sort by distance
sorted_repeaters = sorted(nearby, key=lambda r: r.distance)
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
# Bands.M_4    # 4 meters (70-70.5 MHz)
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
p25 = rb.query(Repeater.p25_capable == True)

# NXDN repeaters
nxdn = rb.query(Repeater.nxdn_capable == True)

# Analog repeaters
analog = rb.query(Repeater.analog_capable == True)

# Any digital mode
digital = rb.query(
    (Repeater.dmr_capable | Repeater.p25_capable | Repeater.nxdn_capable)
)

# Dual mode (analog + digital)
dual_mode = rb.query(
    Repeater.analog_capable == True,
    (Repeater.dmr_capable | Repeater.p25_capable | Repeater.nxdn_capable)
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
    print(f"  Network: {rep.network}")
```

### P25 Specific Data

```python
p25_repeaters = rb.query(Repeater.p25_capable == True)

for rep in p25_repeaters:
    print(f"{rep.callsign}:")
    print(f"  NAC: {rep.p25_nac}")
```

### NXDN Specific Data

```python
nxdn_repeaters = rb.query(Repeater.nxdn_capable == True)

for rep in nxdn_repeaters:
    print(f"{rep.callsign}:")
    print(f"  RAN: {rep.nxdn_ran}")
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

### CTCSS/DCS Tones

Filter by required access tones:

```python
# Repeaters with CTCSS tone
with_tone = rb.query(Repeater.input_ctcss != None)

# Specific CTCSS tone
tone_110_9 = rb.query(Repeater.input_ctcss == 110.9)

# No tone required
no_tone = rb.query(
    Repeater.input_ctcss == None,
    Repeater.input_dcs == None
)
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

```python
from repeaterbook.models import Emergency

# Repeaters with emergency services
emergency = rb.query(Repeater.emergency == Emergency.YES)

# Repeaters without emergency services
no_emergency = rb.query(Repeater.emergency == Emergency.NO)
```

## Combining Queries

### Complex Search Example

Find the best repeaters for a specific use case:

```python
from repeaterbook.queries import square, filter_radius, band, Bands
from repeaterbook.utils import LatLon, Radius
from repeaterbook.models import Status, Use

# Location: Chicago, IL
chicago = LatLon(latitude=41.8781, longitude=-87.6298)
radius = Radius(origin=chicago, distance=100)  # 100 km

# Find: Nearby, open, operational, DMR-capable repeaters on 70cm
results = rb.query(
    square(radius),
    Repeater.operational_status == Status.ON_AIR,
    Repeater.use_membership == Use.OPEN,
    Repeater.dmr_capable == True,
    band(Bands.CM_70)
)

# Filter by actual distance and sort
nearby = filter_radius(results, radius)
sorted_results = sorted(nearby, key=lambda r: r.distance)

# Display results
for rep in sorted_results[:10]:
    print(f"{rep.distance:5.1f}km - {rep.frequency:.4f} MHz - {rep.callsign}")
    print(f"  Location: {rep.location}")
    print(f"  DMR ID: {rep.dmr_id}, CC: {rep.dmr_color_code}")
    print(f"  Tone: {rep.input_ctcss or 'None'}")
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

    for rep in sorted(nearby, key=lambda r: r.distance):
        writer.writerow([
            rep.id,
            rep.callsign,
            rep.frequency,
            '+' if rep.input_frequency < rep.frequency else '-',
            abs(rep.frequency - rep.input_frequency),
            'Tone' if rep.input_ctcss else '',
            rep.input_ctcss or '',
            rep.output_ctcss or '',
            rep.input_dcs or '',
            f"{rep.location} - {rep.distance:.1f}km"
        ])
```

## Working with Repeater Objects

### Repeater Model Fields

Key fields available on `Repeater` objects:

```python
# Identification
rep.id              # Unique RepeaterBook ID
rep.callsign        # Repeater callsign
rep.location        # City/location description
rep.trustee         # Trustee/sponsor name

# Frequency
rep.frequency       # Output frequency (MHz)
rep.input_frequency # Input frequency (MHz)

# Access
rep.input_ctcss     # Input CTCSS tone (Hz)
rep.output_ctcss    # Output CTCSS tone (Hz)
rep.input_dcs       # Input DCS code
rep.output_dcs      # Output DCS code

# Status
rep.operational_status  # ON_AIR, OFF_AIR, UNKNOWN
rep.use_membership      # OPEN, PRIVATE, CLOSED
rep.emergency           # YES, NO, UNKNOWN

# Capabilities
rep.analog_capable  # Boolean
rep.dmr_capable     # Boolean
rep.p25_capable     # Boolean
rep.nxdn_capable    # Boolean
rep.tetra_capable   # Boolean

# Digital mode details
rep.dmr_id          # DMR radio ID
rep.dmr_color_code  # DMR color code (0-15)
rep.p25_nac         # P25 NAC code
rep.nxdn_ran        # NXDN RAN code

# Location
rep.latitude        # Latitude (degrees)
rep.longitude       # Longitude (degrees)
rep.precise         # Precise location flag

# Network
rep.network         # Network name (Brandmeister, DMR-MARC, etc.)

# Notes
rep.notes           # Additional information
```

### Checking Capabilities

```python
def describe_repeater(rep):
    """Print a detailed description of a repeater."""
    print(f"=== {rep.callsign} ===")
    print(f"Frequency: {rep.frequency:.4f} MHz ({rep.input_frequency:.4f} MHz)")
    print(f"Location: {rep.location}")
    print(f"Coordinates: {rep.latitude:.4f}, {rep.longitude:.4f}")

    # Access
    if rep.input_ctcss:
        print(f"CTCSS: {rep.input_ctcss} Hz")
    if rep.input_dcs:
        print(f"DCS: {rep.input_dcs}")

    # Modes
    modes = []
    if rep.analog_capable:
        modes.append("FM")
    if rep.dmr_capable:
        modes.append(f"DMR (CC{rep.dmr_color_code})")
    if rep.p25_capable:
        modes.append(f"P25 (NAC ${rep.p25_nac:03X})")
    if rep.nxdn_capable:
        modes.append("NXDN")

    print(f"Modes: {', '.join(modes)}")
    print(f"Status: {rep.operational_status.value}")
    print(f"Access: {rep.use_membership.value}")

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

Use SQL LIMIT for large result sets:

```python
from sqlmodel import select

# Get first 100 results
statement = select(Repeater).where(
    Repeater.operational_status == Status.ON_AIR
).limit(100)

with rb.session as session:
    results = session.exec(statement).all()
```

### Cache API Responses

The API client automatically caches, but you can customize:

```python
# Longer cache for stable data
api = RepeaterBookAPI(cache_ttl=86400)  # 24 hours

# Shorter cache for frequently changing data
api = RepeaterBookAPI(cache_ttl=1800)  # 30 minutes
```

### Reuse Database Connection

```python
# Create once
rb = RepeaterBook("repeaters.db")

# Reuse for multiple queries
results1 = rb.query(band(Bands.M_2))
results2 = rb.query(band(Bands.CM_70))
results3 = rb.query(Repeater.dmr_capable == True)
```

## Logging

RepeaterBook uses `loguru` for logging:

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
