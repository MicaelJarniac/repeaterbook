# Getting Started

This guide will walk you through the basics of using **RepeaterBook** to access and work with amateur radio repeater data.

## What is RepeaterBook?

**RepeaterBook** is a Python library that provides a convenient interface to [RepeaterBook.com](https://www.repeaterbook.com/), a comprehensive database of amateur radio repeaters worldwide. It allows you to:

- Download repeater data from the RepeaterBook API
- Store repeater information in a local SQLite database
- Query repeaters by location, frequency, capabilities, and more
- Filter repeaters based on distance from a point
- Work with different digital modes (DMR, P25, NXDN, etc.)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip, uv, or Poetry for package management

### Install from PyPI

=== "uv (Recommended)"
    ```bash
    uv add repeaterbook
    ```

=== "pip"
    ```bash
    pip install repeaterbook
    ```

=== "Poetry"
    ```bash
    poetry add repeaterbook
    ```

### Install from Source

To install the latest development version:

=== "uv"
    ```bash
    uv add git+https://github.com/MicaelJarniac/repeaterbook
    ```

=== "pip"
    ```bash
    pip install git+https://github.com/MicaelJarniac/repeaterbook
    ```

## Quick Start

### 1. Download Repeater Data

First, let's download repeater data for a specific region. RepeaterBook provides data for different countries and states.

```python
import asyncio
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery
import pycountry

async def download_repeaters():
    # Create an API client
    api = RepeaterBookAPI()

    # Download repeaters for Brazil
    brazil = pycountry.countries.get(name="Brazil")
    repeaters = await api.download(
        query=ExportQuery(countries={brazil})
    )

    print(f"Downloaded {len(repeaters)} repeaters")
    return repeaters

# Run the async function
repeaters = asyncio.run(download_repeaters())
```

### 2. Store in Local Database

Now let's store the downloaded data in a local SQLite database for easier querying:

```python
from repeaterbook import RepeaterBook

# Create a database connection (defaults to repeaterbook.db)
rb = RepeaterBook()

# Populate the database with our repeaters
rb.populate(repeaters)

print(f"Database populated with {len(repeaters)} repeaters")
```

### 3. Query Repeaters

With data in the database, you can perform various queries:

```python
from repeaterbook import Repeater
from repeaterbook.models import Status, Use

# Find all operational open repeaters
results = rb.query(
    Repeater.operational_status == Status.ON_AIR,
    Repeater.use_membership == Use.OPEN
)

print(f"Found {len(results)} open repeaters")

# Print first 5 repeaters
for repeater in results[:5]:
    print(f"{repeater.frequency:.4f} MHz - {repeater.callsign} - {repeater.location_nearest_city}")
```

### 4. Geographic Queries

Find repeaters near a specific location:

```python
from repeaterbook.utils import LatLon, Radius
from repeaterbook.queries import filter_radius, square

# Define a search area (São Paulo, Brazil)
sao_paulo = LatLon(lat=-23.5505, lon=-46.6333)
radius = Radius(
    origin=sao_paulo,
    distance=50  # kilometers
)

# Find repeaters within the square bounding box
nearby = rb.query(square(radius))

# Filter by actual distance from origin
nearby_exact = filter_radius(nearby, radius)

print(f"Found {len(nearby_exact)} repeaters within 50km of São Paulo")

# Print repeaters with distances
# filter_radius returns repeaters sorted by distance, but doesn't add distance attribute
from haversine import haversine
for repeater in nearby_exact[:5]:
    distance = haversine(sao_paulo, (repeater.latitude, repeater.longitude))
    print(f"{distance:.1f}km - {repeater.frequency:.4f} MHz - {repeater.callsign}")
```

### 5. Filter by Capabilities

Find repeaters with specific digital modes:

```python
from repeaterbook.queries import Bands, band

# Find DMR-capable repeaters on 2m or 70cm bands
dmr_repeaters = rb.query(
    Repeater.dmr_capable == True,
    band(Bands.M_2, Bands.CM_70),
    Repeater.operational_status == Status.ON_AIR
)

print(f"Found {len(dmr_repeaters)} DMR repeaters")

for repeater in dmr_repeaters[:5]:
    modes = []
    if repeater.dmr_capable:
        modes.append("DMR")
    if repeater.apco_p_25_capable:
        modes.append("P25")
    if repeater.nxdn_capable:
        modes.append("NXDN")

    print(f"{repeater.callsign} - {repeater.frequency:.4f} MHz - {', '.join(modes)}")
```

## Complete Example

Here's a complete example that ties everything together:

```python
import asyncio
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status, Use
from repeaterbook.utils import LatLon, Radius
from repeaterbook.queries import filter_radius, square, band, Bands
import pycountry

async def main():
    # 1. Download repeater data
    api = RepeaterBookAPI()
    brazil = pycountry.countries.get(name="Brazil")

    print("Downloading repeaters...")
    repeaters = await api.download(
        query=ExportQuery(countries={brazil})
    )
    print(f"Downloaded {len(repeaters)} repeaters")

    # 2. Store in database
    rb = RepeaterBook("my_repeaters.db")
    rb.populate(repeaters)

    # 3. Find DMR repeaters near São Paulo
    sao_paulo = LatLon(lat=-23.5505, lon=-46.6333)
    radius = Radius(origin=sao_paulo, distance=50)

    nearby = rb.query(
        square(radius),
        Repeater.dmr_capable == True,
        Repeater.operational_status == Status.ON_AIR,
        Repeater.use_membership == Use.OPEN,
        band(Bands.CM_70)  # 70cm band
    )

    nearby_filtered = filter_radius(nearby, radius)

    print(f"\nFound {len(nearby_filtered)} DMR repeaters within 50km:")
    # filter_radius returns repeaters sorted by distance
    # Calculate distances for display
    from haversine import haversine
    for rep in nearby_filtered[:10]:
        distance = haversine(radius.origin, (rep.latitude, rep.longitude), unit=radius.unit)
        print(f"  {distance:5.1f}km - {rep.frequency:.4f} MHz - {rep.callsign:8s} - {rep.location_nearest_city}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

Now that you understand the basics, explore:

- [Usage Guide](usage.md) - Detailed usage examples and patterns
- [Architecture](architecture.md) - Understanding how RepeaterBook works
- [Examples](examples.md) - Real-world use cases
- [API Reference](api.md) - Complete API documentation
- [FAQ](faq.md) - Common questions and troubleshooting

## Tips

- **Caching**: The API client automatically caches responses to avoid unnecessary downloads
- **Database Updates**: Use `rb.populate()` to merge new data without duplicates
- **Async/Await**: Most API operations are asynchronous for better performance
- **Units**: Distance calculations use kilometers by default (configurable with `haversine` units)
- **Filtering**: Combine multiple query conditions using standard SQLAlchemy expressions

## Common Patterns

### Search by State (USA)

```python
from repeaterbook.models import ExportQuery
import pycountry

usa = pycountry.countries.get(alpha_2="US")
query = ExportQuery(countries={usa}, state_ids={"California", "Nevada"})
repeaters = await api.download(query=query)
```

### Find All Digital Modes

```python
digital_repeaters = rb.query(
    (Repeater.dmr_capable | Repeater.apco_p_25_capable | Repeater.nxdn_capable),
    Repeater.operational_status == Status.ON_AIR
)
```

### Export to DataFrame

```python
import pandas as pd

results = rb.query(Repeater.operational_status == Status.ON_AIR)
df = pd.DataFrame([r.model_dump() for r in results])
print(df.head())
```
