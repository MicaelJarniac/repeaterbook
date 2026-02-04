# Architecture

This document explains the internal architecture of **RepeaterBook** and how the different components work together.

## Overview

RepeaterBook is structured into several key modules:

```
repeaterbook/
├── models.py      # Data models and type definitions
├── services.py    # API client and data fetching
├── database.py    # SQLite database interface
├── queries.py     # Query building utilities
└── utils.py       # Geographic and utility functions
```

## Architecture Diagram

```
┌─────────────┐
│   User Code │
└──────┬──────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│ API Client  │    │  RepeaterBook│
│ (services)  │    │  (database)  │
└──────┬──────┘    └──────┬───────┘
       │                  │
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│ RepeaterBook│    │   SQLite DB  │
│     API     │    │   (SQLModel) │
└──────┬──────┘    └──────┬───────┘
       │                  │
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│  JSON Data  │    │   Repeater   │
│             │───>│    Models    │
└─────────────┘    └──────────────┘
                          │
                          │
                          ▼
                   ┌──────────────┐
                   │   Queries    │
                   │   (queries)  │
                   └──────────────┘
```

## Core Components

### 1. Models (`models.py`)

The models module defines the data structures used throughout the library.

#### Repeater Model

The `Repeater` class is a SQLModel that represents a radio repeater:

```python
from sqlmodel import SQLModel, Field

class Repeater(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    callsign: str
    frequency: float
    # ... 50+ fields
```

**Key Features:**

- **SQLModel Base**: Combines Pydantic validation with SQLAlchemy ORM
- **Type Safety**: All fields are strictly typed
- **Validation**: Automatic validation on creation
- **Table Mapping**: Direct mapping to SQLite tables

#### Enums

Several enums define categorical data:

```python
from enum import Enum

class Status(str, Enum):
    """Operational status of a repeater."""
    ON_AIR = "On-air"
    OFF_AIR = "Off-air"
    UNKNOWN = "Unknown"

class Use(str, Enum):
    """Membership/use requirements."""
    OPEN = "OPEN"
    PRIVATE = "PRIVATE"
    CLOSED = "CLOSED"

class Mode(str, Enum):
    """Supported digital modes."""
    ANALOG = "FM"
    DMR = "DMR"
    P25 = "P25"
    NXDN = "NXDN"
    TETRA = "TETRA"
```

#### TypedDicts

TypedDicts define the API payload structures:

```python
class RepeaterJSON(TypedDict, total=False):
    """JSON structure returned by RepeaterBook API."""
    State_ID: str
    Rptr_ID: str
    Frequency: str
    # ... matching API field names
```

**Why TypedDicts?**

- **API Compatibility**: Field names match the API exactly
- **Flexible Parsing**: Can handle optional/missing fields
- **Type Checking**: Static type checking for API responses

### 2. Services (`services.py`)

The services module handles API communication and data transformation.

#### RepeaterBookAPI

The main API client class:

```python
from datetime import timedelta

class RepeaterBookAPI:
    """Client for RepeaterBook API."""

    def __init__(
        self,
        working_dir: Path = Path(),
        max_cache_age: timedelta = timedelta(hours=1),
    ):
        self.working_dir = working_dir
        self.max_cache_age = max_cache_age
```

**Features:**

- **Async/Await**: Uses `aiohttp` for non-blocking I/O
- **Automatic Caching**: File-based cache with TTL
- **Progress Bars**: Visual feedback for long downloads
- **Error Handling**: Graceful handling of API errors
- **Multiple Endpoints**: Supports both North America and Rest-of-World APIs

#### Download Flow

```
download() called
     │
     ├─> Check cache
     │   ├─> Cache hit? Return cached data
     │   └─> Cache miss? Continue
     │
     ├─> Build API URL
     │   ├─> North America endpoint (US/Canada)
     │   └─> Rest-of-World endpoint (other countries)
     │
     ├─> Fetch data (async HTTP request)
     │   └─> Show progress bar
     │
     ├─> Parse JSON response
     │   └─> Convert to RepeaterJSON TypedDict
     │
     ├─> Convert to Repeater models
     │   └─> json_to_model() transformation
     │
     ├─> Cache results
     │   └─> Write to cache file
     │
     └─> Return list of Repeater objects
```

#### Data Transformation

The `json_to_model()` function converts API JSON to `Repeater` objects:

```python
def json_to_model(data: RepeaterJSON) -> Repeater:
    """Convert JSON payload to Repeater model."""
    return Repeater(
        id=int(data["Rptr_ID"]),
        callsign=data["Callsign"],
        frequency=float(data["Frequency"]),
        # ... field mappings with type conversion
    )
```

**Handles:**

- **Type Conversion**: String → Float, Int, Bool, Date
- **Missing Fields**: Provides sensible defaults
- **Variations**: Different API formats (NA vs RoW)
- **Boolean Normalization**: "Yes"/"No", "1"/"0" → True/False

### 3. Database (`database.py`)

The database module provides the SQLite interface.

#### RepeaterBook Class

```python
class RepeaterBook:
    """Local database of repeaters."""

    def __init__(self, db_path: str = "repeaterbook.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)
```

**Features:**

- **SQLModel ORM**: Type-safe database operations
- **Auto-Migration**: Tables created automatically
- **Session Management**: Context manager for safe transactions

#### Database Operations

**Initialize:**

```python
# Creates tables if they don't exist
rb = RepeaterBook(database="repeaters.db")
```

**Populate:**

```python
# Merges repeaters (no duplicates)
rb.populate(repeaters)

# Behind the scenes:
# 1. Start transaction
# 2. For each repeater:
#    - Check if exists (by id)
#    - Insert if new
#    - Update if changed
# 3. Commit transaction
```

**Query:**

```python
# Returns list of Repeater objects
results = rb.query(Repeater.dmr_capable == True)

# Behind the scenes:
# 1. Build SQLAlchemy SELECT statement
# 2. Execute query
# 3. Fetch all results
# 4. Convert to Repeater objects
```

### 4. Queries (`queries.py`)

The queries module provides helper functions for common query patterns.

#### Geographic Queries

**Square Bounding Box:**

```python
def square(radius: Radius) -> BinaryExpression:
    """Create bounding box query around a point."""
    bounds = square_bounds(radius)  # Takes the full Radius object

    return and_(
        Repeater.latitude >= bounds.south,
        Repeater.latitude <= bounds.north,
        Repeater.longitude >= bounds.west,
        Repeater.longitude <= bounds.east,
    )
```

**How it works:**

1. Calculate bounding box from center point and radius
2. Create SQL conditions for lat/lon ranges
3. Return SQLAlchemy expression

**Radius Filtering:**

```python
def filter_radius(repeaters: Iterable[Repeater], radius: Radius) -> list[Repeater]:
    """Filter repeaters by actual distance from origin, sorted by distance."""
    rep_dists = []

    for repeater in repeaters:
        # Calculate great-circle distance
        distance = haversine(
            radius.origin,  # LatLon is tuple-compatible (lat, lon)
            (repeater.latitude, repeater.longitude),
            unit=radius.unit,
        )

        if distance <= radius.distance:
            rep_dists.append((repeater, distance))

    # Sort by distance
    rep_dists.sort(key=lambda x: x[1])

    # Return just the repeaters (sorted by distance)
    return [rep for rep, _ in rep_dists]
```

**How it works:**

1. Iterate through repeaters
2. Calculate Haversine distance for each
3. Keep only those within radius
4. Attach distance as attribute

#### Band Queries

```python
class Bands(Enum):
    """Amateur radio frequency bands."""
    M_2 = (144.0, 148.0)   # 2 meters
    CM_70 = (420.0, 450.0)  # 70 centimeters

def band(*bands: Bands) -> BinaryExpression:
    """Create frequency range query for bands."""
    conditions = []

    for b in bands:
        min_freq, max_freq = b.value
        conditions.append(
            and_(
                Repeater.frequency >= min_freq,
                Repeater.frequency <= max_freq,
            )
        )

    return or_(*conditions)
```

### 5. Utils (`utils.py`)

Utility functions and type definitions.

#### Geographic Types

```python
from typing import NamedTuple

class LatLon(NamedTuple):
    """Geographic coordinate."""
    latitude: float
    longitude: float

class Radius(NamedTuple):
    """Search radius around a point."""
    origin: LatLon
    distance: float
    unit: Unit = Unit.KILOMETERS

class SquareBounds(NamedTuple):
    """Bounding box coordinates."""
    north: float
    south: float
    east: float
    west: float
```

#### Square Bounds Calculation

```python
def square_bounds(origin: LatLon, distance: float) -> SquareBounds:
    """Calculate bounding box for a square area."""
    # Earth's radius in kilometers
    R = 6371.0

    # Calculate offsets in degrees
    lat_offset = (distance / R) * (180 / pi)
    lon_offset = (distance / R) * (180 / pi) / cos(origin.latitude * pi / 180)

    return SquareBounds(
        north=origin.latitude + lat_offset,
        south=origin.latitude - lat_offset,
        east=origin.longitude + lon_offset,
        west=origin.longitude - lon_offset,
    )
```

## Data Flow

### Complete Data Flow Example

```
1. User calls api.download()
   ↓
2. RepeaterBookAPI.download()
   ↓
3. Check file cache
   ↓
4. HTTP request to repeaterbook.com
   ↓
5. JSON response
   ↓
6. Parse to RepeaterJSON TypedDict
   ↓
7. Convert to Repeater objects
   ↓
8. Cache to file
   ↓
9. Return to user
   ↓
10. User calls rb.populate()
   ↓
11. RepeaterBook.populate()
   ↓
12. SQLModel merge operation
   ↓
13. SQLite database updated
   ↓
14. User calls rb.query()
   ↓
15. Build SQL query
   ↓
16. Execute on SQLite
   ↓
17. Convert rows to Repeater objects
   ↓
18. Return to user
```

## Design Decisions

### Why SQLModel?

**SQLModel** combines Pydantic and SQLAlchemy:

- ✅ Type safety (Pydantic validation)
- ✅ ORM functionality (SQLAlchemy)
- ✅ Single model definition
- ✅ Automatic migrations
- ✅ IDE autocomplete

### Why File-Based Caching?

**Simple and effective:**

- ✅ No external dependencies (Redis, Memcached)
- ✅ Survives application restarts
- ✅ Easy to inspect and debug
- ✅ TTL-based expiration

### Why Two Query Stages?

**square() + filter_radius():**

1. **square()**: Fast SQL query using indexed lat/lon
2. **filter_radius()**: Precise distance calculation on smaller set

This is much faster than calculating distance for every repeater:

```
All repeaters (10,000)
     │ square() - SQL indexed lookup
     ↓
Candidates (100)
     │ filter_radius() - Haversine calculation
     ↓
Results (50)
```

### Why TypedDict for API?

**Flexibility with type safety:**

- ✅ Handles optional/missing fields
- ✅ Field names match API exactly
- ✅ No inheritance complexity
- ✅ Type checking without runtime overhead

## Performance Characteristics

### API Client

- **First download**: Slow (network-bound)
- **Cached download**: Fast (< 1ms)
- **Large downloads**: Chunked with progress bars

### Database Operations

- **Initial populate**: ~1000 repeaters/second
- **Merge populate**: ~500 repeaters/second (duplicate checking)
- **Query (indexed)**: < 10ms for typical queries
- **Query (unindexed)**: 100-500ms for full scans

### Geographic Queries

- **square()**: < 5ms (uses indexes)
- **filter_radius()**: ~1ms per 100 repeaters

## Extensibility

### Custom Queries

Add your own query functions:

```python
from sqlmodel import and_
from repeaterbook import Repeater

def my_custom_query(callsign_prefix: str):
    """Find repeaters by callsign prefix."""
    return Repeater.callsign.startswith(callsign_prefix)

# Usage
results = rb.query(my_custom_query("W6"))
```

### Custom Models

Extend the Repeater model:

```python
class ExtendedRepeater(Repeater, table=True):
    """Add custom fields."""
    favorite: bool = False
    last_used: datetime | None = None
```

### Custom API Endpoints

Subclass RepeaterBookAPI:

```python
class CustomAPI(RepeaterBookAPI):
    """Add custom API functionality."""

    async def download_favorites(self):
        """Download from a custom endpoint."""
        # Custom implementation
        pass
```

## Testing

### Test Structure

```
tests/
├── test_repeaterbook.py      # Basic integration tests
├── test_api_format.py         # API format validation
├── test_fetch_json_cache.py   # Caching tests
└── integration/
    └── test_live_api.py       # Live API tests
```

### Testing Approach

- **Unit Tests**: Individual functions and classes
- **Integration Tests**: End-to-end workflows
- **API Format Tests**: Handle API variations
- **Live Tests**: Optional real API calls (marked with `@pytest.mark.integration`)

### Test Coverage

Target: **100% code coverage**

```bash
pytest --cov=repeaterbook --cov-report=html
```

## Logging and Debugging

### Enable Logging

```python
from loguru import logger

# Log to file
logger.add("repeaterbook.log", level="DEBUG")

# Log to console
logger.add(sys.stdout, level="INFO")
```

### Debug API Calls

```python
import logging

# Enable aiohttp debug logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Cache

```bash
# Cache files are stored with query hash as filename
ls .repeaterbook_cache/

# View cached data
cat .repeaterbook_cache/<hash>.json
```

### Database Schema

```bash
# Inspect database with sqlite3
sqlite3 repeaterbook.db ".schema"

# Query directly
sqlite3 repeaterbook.db "SELECT * FROM repeater LIMIT 10"
```

## Future Enhancements

Potential improvements for future versions:

1. **Async Database**: AsyncIO-compatible database operations
2. **Connection Pooling**: Better performance for concurrent queries
3. **Indexes**: Additional database indexes for common queries
4. **Bulk Operations**: Optimized bulk insert/update
5. **Streaming**: Stream large result sets
6. **GraphQL API**: Alternative query interface
7. **Web UI**: Browser-based query interface
8. **Mobile Support**: iOS/Android apps using the library
9. **Real-time Updates**: WebSocket support for live data
10. **Advanced Caching**: Redis/Memcached backend options

## Related Documentation

- [Getting Started](getting-started.md) - Tutorial for beginners
- [Usage Guide](usage.md) - Comprehensive usage examples
- [Examples](examples.md) - Real-world use cases
- [API Reference](api.md) - Complete API documentation
