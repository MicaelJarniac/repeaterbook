# FAQ

Frequently asked questions about **RepeaterBook**.

## General Questions

### What is RepeaterBook?

RepeaterBook is a Python library that provides programmatic access to the [RepeaterBook.com](https://www.repeaterbook.com/) database of amateur radio repeaters worldwide. It allows you to download, query, and analyze repeater data for various amateur radio applications.

### Do I need an API key?

No! The RepeaterBook API is public and doesn't require authentication or an API key. However, please be respectful of their servers by:

- Using the built-in caching (enabled by default)
- Not making excessive requests
- Respecting the cache TTL

### What data is available?

RepeaterBook provides comprehensive repeater data including:

- Frequencies (input/output)
- Location (lat/lon)
- Callsign and trustee
- Access tones (CTCSS/DCS)
- Digital mode capabilities (DMR, P25, NXDN, etc.)
- Network affiliations
- Status and access type
- Notes and additional information

### Is the data accurate?

The data comes directly from RepeaterBook.com, which is community-maintained. Accuracy varies by region and how recently the information was updated. Always verify critical information (especially for emergency communications) through local sources.

### Which countries are supported?

RepeaterBook covers repeaters worldwide. Major coverage includes:

- **North America**: USA, Canada, Mexico
- **Europe**: Most European countries
- **Asia**: Japan, South Korea, Taiwan, and others
- **Oceania**: Australia, New Zealand
- **South America**: Brazil, Argentina, Chile, and others
- **Africa**: South Africa and others

Use `pycountry` to find the correct country codes.

## Installation Issues

### ModuleNotFoundError: No module named 'repeaterbook'

Make sure you've installed the package:

```bash
pip install repeaterbook
# or
uv add repeaterbook
```

If using a virtual environment, ensure it's activated:

```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### ImportError with SQLModel or aiohttp

These are dependencies that should be installed automatically. Try:

```bash
pip install --upgrade repeaterbook
```

Or install dependencies explicitly:

```bash
pip install sqlmodel aiohttp
```

### SSL Certificate Errors

On some systems (especially macOS), you may encounter SSL errors. Install certificates:

```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Or install certifi
pip install --upgrade certifi
```

## Usage Issues

### asyncio.run() gives "Event loop is closed" error

This happens when running in Jupyter notebooks. Use this pattern instead:

```python
# In Jupyter/IPython
await api.download(query=ExportQuery(countries={brazil}))

# In regular Python scripts
import asyncio
asyncio.run(api.download(query=ExportQuery(countries={brazil})))
```

### Database file is locked

This occurs when multiple processes access the same database. Solutions:

1. **Use different database files** for concurrent access
2. **Close connections** properly with context managers
3. **Use a single RepeaterBook instance** per database file

```python
# Good
rb = RepeaterBook(database="repeaters.db")
results1 = rb.query(...)
results2 = rb.query(...)

# Bad (multiple instances to same file)
rb1 = RepeaterBook(database="repeaters.db")
rb2 = RepeaterBook(database="repeaters.db")  # May cause lock
```

### Queries return empty results

Check:

1. **Data exists**: Have you populated the database?

```python
# Check if database has data
all_repeaters = rb.query()
print(f"Database has {len(all_repeaters)} repeaters")
```

2. **Query conditions are correct**:

```python
# Use Status enum, not strings
from repeaterbook.models import Status
results = rb.query(Repeater.operational_status == Status.ON_AIR)
```

3. **Geographic bounds are reasonable**:

```python
# Too small distance?
radius = Radius(origin=location, distance=1)  # Only 1 km!
```

### Cache not working

The cache should work automatically. To debug:

```python
# Check cache directory
api = RepeaterBookAPI()
print(f"Cache dir: {api.cache_dir}")

# Verify cache files exist
import os
if os.path.exists(".repeaterbook_cache"):
    files = os.listdir(".repeaterbook_cache")
    print(f"Cache files: {files}")
```

To clear the cache:

```bash
rm -rf .repeaterbook_cache/
```

### Distance calculations seem wrong

Verify:

1. **Units**: Default is kilometers

```python
# Use miles instead
from haversine import Unit
radius = Radius(origin=location, distance=50, unit=Unit.MILES)
```

2. **Coordinates**: Ensure lat/lon are correct

```python
# Check repeater coordinates
for rep in results:
    print(f"{rep.callsign}: {rep.latitude}, {rep.longitude}")
```

3. **Use filter_radius() after square()**:

```python
# Correct order
candidates = rb.query(square(radius))
nearby = filter_radius(candidates, radius)
```

## Performance Issues

### Download is very slow

1. **Check internet connection**: API depends on network speed
2. **Use cache**: Subsequent requests use cached data
3. **Limit scope**: Download specific states/regions instead of entire countries

```python
# Instead of entire USA
query = ExportQuery(countries={usa})  # Slow!

# Download specific states
query = ExportQuery(countries={usa}, state_ids={"06"})  # California (FIPS code)
```

### Queries are slow

1. **Use square() before filter_radius()**:

```python
# Efficient
candidates = rb.query(square(radius))  # Fast: SQL indexed
nearby = filter_radius(candidates, radius)  # Slower: but fewer items

# Inefficient
all_reps = rb.query()  # Gets everything
nearby = filter_radius(all_reps, radius)  # Slow: calculates all distances
```

2. **Add query conditions** to limit results:

```python
# Add more filters to reduce result set
results = rb.query(
    square(radius),
    Repeater.operational_status == Status.ON_AIR,  # Filters out off-air
    band(Bands.M_2)  # Only 2m band
)
```

3. **Use LIMIT** for large result sets:

```python
from sqlmodel import select

statement = select(Repeater).limit(100)
with rb.session as session:
    results = session.exec(statement).all()
```

### Database is getting large

The SQLite database can grow with many repeaters. To optimize:

```python
# Compact database
import sqlite3
conn = sqlite3.connect('repeaterbook.db')
conn.execute('VACUUM')
conn.close()
```

Or start fresh:

```bash
rm repeaterbook.db
```

## API Questions

### What's the difference between export.php and exportROW.php?

- **export.php**: North America (USA, Canada, Mexico)
- **exportROW.php**: Rest of World (all other countries)

The library automatically selects the correct endpoint based on your query.

### How often should I refresh data?

Repeater data doesn't change frequently. Recommended refresh intervals:

- **Active development**: 1 hour (default cache TTL)
- **Production apps**: 24 hours or longer
- **Static analysis**: Download once, use indefinitely

```python
from datetime import timedelta

# Set longer cache for production
api = RepeaterBookAPI(max_cache_age=timedelta(hours=24))
```

### Can I download all repeaters worldwide?

Yes, but it's a lot of data and takes time. Consider:

```python
import pycountry

# All countries (slow, large)
all_countries = set(pycountry.countries)
# Download in batches...
```

Better approach: Download by region as needed.

### Rate limiting?

RepeaterBook doesn't publicly document rate limits, but be respectful:

- ✅ Use caching (enabled by default)
- ✅ Download once, query many times
- ✅ Download specific regions, not everything
- ❌ Don't make rapid-fire requests
- ❌ Don't abuse the API

## Data Questions

### Why are some repeaters missing expected fields?

Not all repeaters have complete information. Always check for None:

```python
if rep.dmr_id:
    print(f"DMR ID: {rep.dmr_id}")
else:
    print("DMR ID not available")

# Or use getattr with default
dmr_id = getattr(rep, 'dmr_id', 'Unknown')
```

### How do I handle unknown/missing coordinates?

Some repeaters have imprecise or missing coordinates:

```python
# Filter for precise coordinates
results = rb.query(Repeater.precise == True)

# Check before using
if rep.latitude and rep.longitude:
    # Use coordinates
    pass
```

### What does "UNKNOWN" status mean?

`Status.UNKNOWN` means the operational status hasn't been verified or reported. It doesn't necessarily mean the repeater is off-air.

For critical applications, prefer:

```python
results = rb.query(Repeater.operational_status == Status.ON_AIR)
```

### Why is DMR color code sometimes None?

Not all DMR repeaters report their color code. Note that the `dmr_color_code` field is a string, not an integer. Common defaults:

- **Color Code 1**: Most common default
- **Color Code 2**: Also common

When programming radios, try CC1 first if unknown.

### How are analog and digital flags set?

These are capability flags:

- `analog_capable=True`: Supports FM analog
- `dmr_capable=True`: Supports DMR
- `apco_p_25_capable=True`: Supports P25
- etc.

A repeater can have multiple flags (e.g., dual-mode).

## Integration Questions

### Can I use this with Flask/Django/FastAPI?

Yes! See the [Examples](examples.md) page for a Flask integration example.

Key considerations:

- **Initialize once**: Create `RepeaterBook` instance at startup
- **Async support**: FastAPI works great with async/await
- **Database per app**: Don't share database files across applications

### Can I export to CSV/JSON?

Yes:

```python
import pandas as pd
import json

results = rb.query(...)

# CSV with pandas
df = pd.DataFrame([r.model_dump() for r in results])
df.to_csv('repeaters.csv', index=False)

# JSON
data = [r.model_dump() for r in results]
with open('repeaters.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)
```

### Can I use this in a mobile app?

The library is designed for Python. For mobile apps:

1. **Python backend**: Create a REST API using Flask/FastAPI
2. **Direct integration**: Use frameworks like Kivy or BeeWare
3. **Alternative**: Use RepeaterBook API directly in your mobile code

### How do I integrate with radio programming software?

Most radio programming software accepts CSV imports. See the [codeplug example](examples.md#example-2-generate-codeplug-for-dmr-radio) for details.

## Development Questions

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Quick start:

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make changes
5. Run tests: `pytest --cov`
6. Submit a pull request

### How do I run tests?

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
pytest

# With coverage
pytest --cov --cov-report=html

# Run specific test
pytest tests/test_repeaterbook.py
```

### How do I build documentation?

```bash
cd docs/
mkdocs serve  # Live preview at http://127.0.0.1:8000

# Or using Nox
nox -s docs_serve
```

### Where do I report bugs?

Please report bugs on [GitHub Issues](https://github.com/MicaelJarniac/repeaterbook/issues).

Include:

- Python version
- Operating system
- Error message and stack trace
- Minimal code to reproduce

## Error Handling

### What exceptions does RepeaterBook raise?

RepeaterBook uses a hierarchy of custom exceptions:

| Exception | When Raised |
|-----------|------------|
| `RepeaterBookError` | Base exception for all library errors |
| `RepeaterBookAPIError` | API returned an error response (status: "error") |
| `RepeaterBookValidationError` | Invalid data or response format |
| `RepeaterBookCacheError` | Cache read/write operations failed |

### How do I handle errors properly?

```python
from repeaterbook import (
    RepeaterBookError,
    RepeaterBookAPIError,
    RepeaterBookValidationError,
)

try:
    repeaters = await api.download(query=query)
except RepeaterBookAPIError as e:
    print(f"API error: {e}")
except RepeaterBookValidationError as e:
    print(f"Invalid data: {e}")
except RepeaterBookError as e:
    print(f"Library error: {e}")
```

### Why did I get a validation error?

The `Repeater` model validates data automatically:

- **Latitude** must be between -90 and 90
- **Longitude** must be between -180 and 180
- **Frequency** must be positive

If you're seeing validation errors, the data from the API may be malformed.

## Troubleshooting

### Enable debug logging

```python
from loguru import logger
import sys

logger.add(sys.stdout, level="DEBUG")

# Now see detailed logs
repeaters = await api.download(query=ExportQuery(countries={brazil}))
```

### Check database contents

```bash
sqlite3 repeaterbook.db

# List tables
.tables

# Show schema
.schema repeater

# Query data
SELECT COUNT(*) FROM repeater;
SELECT * FROM repeater LIMIT 5;
```

### Verify API response

```python
import aiohttp
import asyncio

async def test_api():
    url = "https://www.repeaterbook.com/api/export.php?country=Brazil"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            print(f"Repeaters: {len(data['results'])}")

asyncio.run(test_api())
```

## Still Having Issues?

- Check the [Examples](examples.md) page for working code
- Review the [API Reference](api.md) for detailed documentation
- Search [GitHub Issues](https://github.com/MicaelJarniac/repeaterbook/issues)
- Ask for help on [Discord](https://discord.gg/Ye9yJtZQuN)

## Related Resources

- [RepeaterBook.com Official API Docs](https://www.repeaterbook.com/wiki/doku.php?id=api)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [pycountry Documentation](https://github.com/flyingcircusio/pycountry)
