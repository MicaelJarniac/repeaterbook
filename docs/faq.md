# FAQ

Frequently asked questions about the **RepeaterBook Python Client**.

## General Questions

### Is this an official RepeaterBook.com project?

No. RepeaterBook Python Client is an independent, community-maintained library that provides programmatic access to RepeaterBook.com's public API. It is not affiliated with, endorsed by, or officially supported by RepeaterBook.com.

### What is the RepeaterBook Python Client?

The RepeaterBook Python Client is an unofficial, third-party Python library that provides programmatic access to the [RepeaterBook.com](https://repeaterbook.com/) database of amateur radio repeaters worldwide. It allows you to download, query, and analyze repeater data for various amateur radio applications.

### Do I need an API key?

Yes. As of RepeaterBook's [2026-03-03 API policy](https://www.repeaterbook.com/wiki/doku.php?id=api), the export endpoints require an approved per-user API token (an `rbuapp_...` token), sent via the `X-RB-App-Token` header.

Getting one takes about a minute, and **you do not need to register an application** — this library is already registered as **RepeaterBook Python Client** (**App #114**):

1. Create a free [RepeaterBook](https://www.repeaterbook.com/) account, or log in to an existing one.
2. Go to [API Applications](https://www.repeaterbook.com/user/api_apps.php).
3. Find **RepeaterBook Python Client** (**App #114**) and generate a token for it.
4. Pass the resulting `rbuapp_...` token to `RepeaterBookAPI`, ideally from an environment variable:

```python
import os

from repeaterbook.services import RepeaterBookAPI

api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])
```

The default `User-Agent` already matches App #114, so the token works as-is — don't override `app_name`, `app_version`, or `app_contact`. See the [Authentication guide](usage.md#authentication) for details.

**Never share or distribute a token.** This library is a *distributed* client: each user generates their **own** token against App #114. RepeaterBook's policy prohibits embedding a shared `app_...` token in source code, installers, or public repositories.

Please also be respectful of their servers by:

- Using the built-in caching (enabled by default)
- Not making excessive requests
- Respecting the cache TTL

### What data is available?

RepeaterBook.com provides comprehensive repeater data including:

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

`ExportQuery.countries` takes `pycountry` country objects, and the query sends
each country's **name** — so the lookup has to succeed before the query can.
`pycountry.countries.get(name=...)` matches the official name exactly and
returns `None` otherwise, which is easy to trip over:

```python
import pycountry

pycountry.countries.get(name="South Korea")        # -> None
pycountry.countries.search_fuzzy("South Korea")[0] # -> Korea, Republic of
```

Prefer `get(alpha_2="KR")` when you know the code, and fall back to
`search_fuzzy()` for free-form names.

## Installation Issues

### ModuleNotFoundError: No module named 'repeaterbook'

Make sure you've installed the package:

=== "uv (Recommended)"
    ```bash
    uv add repeaterbook
    ```

=== "pip"
    ```bash
    pip install repeaterbook
    ```

If using a virtual environment, ensure it's activated:

```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### ImportError with SQLModel or aiohttp

These are dependencies that should be installed automatically. Try:

=== "uv (Recommended)"
    ```bash
    uv add --upgrade repeaterbook
    ```

=== "pip"
    ```bash
    pip install --upgrade repeaterbook
    ```

Or install dependencies explicitly:

=== "uv (Recommended)"
    ```bash
    uv add sqlmodel aiohttp
    ```

=== "pip"
    ```bash
    pip install sqlmodel aiohttp
    ```

### SSL Certificate Errors

On some systems (especially macOS), you may encounter SSL errors. Install certificates:

```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command
```

Or upgrade certifi:

=== "uv (Recommended)"
    ```bash
    uv add --upgrade certifi
    ```

=== "pip"
    ```bash
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
import asyncio
import os

from repeaterbook.services import RepeaterBookAPI

async def inspect_cache():
    api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])

    # `cache_dir()` is an async method -- it creates the directory on first
    # call -- not a plain attribute.
    cache = await api.cache_dir()
    print(f"Cache dir: {cache}")

    # Entries are named `api_cache_<sha256-of-url>.json`, one per request URL.
    # A query that fans out to both the NA and ROW endpoints yields two.
    print(f"Cache files: {[p.name async for p in cache.iterdir()]}")

asyncio.run(inspect_cache())
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
from sqlmodel import Session, select

# `RepeaterBook` opens a session per call internally and exposes the engine,
# so build your own `Session` when you need a statement it can't express.
statement = select(Repeater).limit(100)
with Session(rb.engine) as session:
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

### Why am I getting 401 or 403 from the API?

| Error | Cause | Fix |
|---|---|---|
| `401 auth_missing` | No token was sent | Pass `app_token=os.environ["REPEATERBOOK"]` |
| `401 auth_invalid` | Token wrong, revoked, or expired | Regenerate it on [API Applications](https://www.repeaterbook.com/user/api_apps.php) |
| `403 ua_mismatch` | `User-Agent` doesn't match the application the token was issued for | Remove your `app_name` / `app_version` / `app_contact` overrides |

`ua_mismatch` is the common one. A token generated against **RepeaterBook Python Client** (**App #114**) is only valid alongside that application's registered `User-Agent`, which this library sends by default. Overriding any part of it — even just `app_contact`, to your own address — breaks the match. See the [Authentication guide](usage.md#authentication).

### Do I need to register my own application with RepeaterBook?

No. This library ships registered as **RepeaterBook Python Client** (**App #114**); generate a token against it from [API Applications](https://www.repeaterbook.com/user/api_apps.php) and use the library's default `User-Agent`.

Register your own only if you're building a separate product with its own identity. Then override `app_name`, `app_version`, and `app_contact` to match your registration exactly, and use a token issued for it.

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
# Install dev dependencies. Dev tooling lives in dependency *groups*; the
# `mcp` extra is separate, so ask for both.
uv sync --all-extras --all-groups

# Run tests
pytest

# With coverage
pytest --cov --cov-report=html

# Run specific test
pytest tests/test_repeaterbook.py
```

### How do I build documentation?

```bash
# Run from the repository root -- `mkdocs.yml` lives there, not in `docs/`.
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

### What exceptions does the RepeaterBook Python Client raise?

The RepeaterBook Python Client uses a hierarchy of custom exceptions:

| Exception | When Raised |
|-----------|------------|
| `RepeaterBookError` | Base exception for all library errors |
| `RepeaterBookAPIError` | Any HTTP 4xx/5xx other than 401/403/429, or a 200 response whose body reports an error |
| `RepeaterBookUnauthorizedError` | HTTP 401 — missing or invalid app token |
| `RepeaterBookForbiddenError` | HTTP 403 — User-Agent or authorization denied |
| `RepeaterBookRateLimitError` | HTTP 429 — rate limited; carries `retry_after` |
| `RepeaterBookValidationError` | Invalid data or response format |
| `RepeaterBookRowError` | A single export row could not be modelled |
| `RepeaterBookCacheError` | The response could not be cached — a full disk or an unwritable working directory. A cache entry that is merely missing or corrupt is *not* an error: it is treated as a miss and refetched |

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

A single row that fails these checks does **not** fail a download. The data is
community-maintained and bad rows do occur, so `download()` logs and skips them
and returns everything else. You'll see a warning like:

```text
Skipping unmodellable repeater 48:24371 (W5AW): Frequency must be positive, got 0.00000
Skipped 1 unmodellable of 1669 repeaters: 48:24371 (W5AW)
```

### How do I find out which rows were skipped?

Pass a list for `skipped` and inspect it afterwards:

```python
from repeaterbook.exceptions import RepeaterBookRowError

skipped: list[RepeaterBookRowError] = []
repeaters = await api.download(query, skipped=skipped)

print(f"{len(repeaters)} usable, {len(skipped)} dropped")
for error in skipped:
    print(error.label, "->", error)
```

Each entry keeps the offending payload on `error.row`, which is what you'd
attach when reporting the record to RepeaterBook.

### Can I make malformed rows an error instead?

Yes — pass `strict=True` and the first unmodellable row raises
`RepeaterBookRowError` instead of being skipped:

```python
repeaters = await api.download(query, strict=True)
```

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

The API rejects unauthenticated requests, so a raw check has to send the same
identity the library does — both the approved `User-Agent` and the token.
Reuse `api.headers` rather than hand-rolling them, so the `User-Agent` keeps
matching the application your token was issued for:

```python
import aiohttp
import asyncio
import os

from repeaterbook.services import RepeaterBookAPI

async def test_api():
    api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])
    url = "https://repeaterbook.com/api/export.php?country=Brazil"
    async with aiohttp.ClientSession(headers=dict(api.headers)) as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            # An error payload carries `status`/`message` instead of `results`.
            if "results" not in data:
                print(f"API error: {data}")
                return
            print(f"Repeaters: {len(data['results'])}")

asyncio.run(test_api())
```

## Still Having Issues?

- Check the [Examples](examples.md) page for working code
- Review the [API Reference](api.md) for detailed documentation
- Search [GitHub Issues](https://github.com/MicaelJarniac/repeaterbook/issues)
- Ask for help on [Discord](https://discord.gg/Ye9yJtZQuN)

## Related Resources

- [RepeaterBook.com Official API Docs](https://repeaterbook.com/wiki/doku.php?id=api)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [pycountry Documentation](https://github.com/flyingcircusio/pycountry)
