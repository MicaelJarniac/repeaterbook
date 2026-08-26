<div align="center" markdown="1">

  [![Discord][badge-chat]][chat]
  <br>
  <br>

  | | ![Badges][label-badges] |
  |:-|:-|
  | ![Build][label-build] | [![Nox][badge-actions]][actions] [![semantic-release][badge-semantic-release]][semantic-release] [![PyPI][badge-pypi]][pypi] [![Read the Docs][badge-docs]][docs] |
  | ![Tests][label-tests] | [![coverage][badge-coverage]][coverage] [![pre-commit][badge-pre-commit]][pre-commit] [![asv][badge-asv]][asv] |
  | ![Standards][label-standards] | [![SemVer 2.0.0][badge-semver]][semver] [![Conventional Commits][badge-conventional-commits]][conventional-commits] |
  | ![Code][label-code] | [![uv][badge-uv]][uv] [![Ruff][badge-ruff]][ruff] [![Nox][badge-nox]][nox] [![Checked with mypy][badge-mypy]][mypy] |
  | ![Repo][label-repo] | [![GitHub issues][badge-issues]][issues] [![GitHub stars][badge-stars]][stars] [![GitHub license][badge-license]][license] [![All Contributors][badge-all-contributors]][contributors] [![Contributor Covenant][badge-code-of-conduct]][code-of-conduct] |
</div>

<!-- Badges -->
[badge-chat]: https://img.shields.io/badge/dynamic/json?color=green&label=chat&query=%24.approximate_presence_count&suffix=%20online&logo=discord&style=flat-square&url=https%3A%2F%2Fdiscord.com%2Fapi%2Fv10%2Finvites%2FYe9yJtZQuN%3Fwith_counts%3Dtrue
[chat]: https://discord.gg/Ye9yJtZQuN

<!-- Labels -->
[label-badges]: https://img.shields.io/badge/%F0%9F%94%96-badges-purple?style=for-the-badge
[label-build]: https://img.shields.io/badge/%F0%9F%94%A7-build-darkblue?style=flat-square
[label-tests]: https://img.shields.io/badge/%F0%9F%A7%AA-tests-darkblue?style=flat-square
[label-standards]: https://img.shields.io/badge/%F0%9F%93%91-standards-darkblue?style=flat-square
[label-code]: https://img.shields.io/badge/%F0%9F%92%BB-code-darkblue?style=flat-square
[label-repo]: https://img.shields.io/badge/%F0%9F%93%81-repo-darkblue?style=flat-square

<!-- Build -->
[badge-actions]: https://img.shields.io/github/actions/workflow/status/MicaelJarniac/repeaterbook/ci.yml?branch=main&style=flat-square
[actions]: https://github.com/MicaelJarniac/repeaterbook/actions
[badge-semantic-release]: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079?style=flat-square
[semantic-release]: https://github.com/semantic-release/semantic-release
[badge-pypi]: https://img.shields.io/pypi/v/repeaterbook?style=flat-square
[pypi]: https://pypi.org/project/repeaterbook
[badge-docs]: https://img.shields.io/readthedocs/repeaterbook?style=flat-square
[docs]: https://repeaterbook.readthedocs.io

<!-- Tests -->
[badge-coverage]: https://img.shields.io/codecov/c/gh/MicaelJarniac/repeaterbook?logo=codecov&style=flat-square
[coverage]: https://codecov.io/gh/MicaelJarniac/repeaterbook
[badge-pre-commit]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat-square&logo=pre-commit&logoColor=white
[pre-commit]: https://github.com/pre-commit/pre-commit
[badge-asv]: https://img.shields.io/badge/benchmarked%20by-asv-blue?style=flat-square
[asv]: https://github.com/airspeed-velocity/asv

<!-- Standards -->
[badge-semver]: https://img.shields.io/badge/SemVer-2.0.0-blue?style=flat-square&logo=semver
[semver]: https://semver.org/spec/v2.0.0.html
[badge-conventional-commits]: https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow?style=flat-square
[conventional-commits]: https://conventionalcommits.org

<!-- Code -->
[badge-uv]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square
[uv]: https://github.com/astral-sh/uv
[badge-ruff]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square
[ruff]: https://github.com/astral-sh/ruff
[badge-nox]: https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg?style=flat-square
[nox]: https://github.com/wntrblm/nox
[badge-mypy]: https://img.shields.io/badge/mypy-checked-2A6DB2?style=flat-square
[mypy]: http://mypy-lang.org

<!-- Repo -->
[badge-issues]: https://img.shields.io/github/issues/MicaelJarniac/repeaterbook?style=flat-square
[issues]: https://github.com/MicaelJarniac/repeaterbook/issues
[badge-stars]: https://img.shields.io/github/stars/MicaelJarniac/repeaterbook?style=flat-square
[stars]: https://github.com/MicaelJarniac/repeaterbook/stargazers
[badge-license]: https://img.shields.io/github/license/MicaelJarniac/repeaterbook?style=flat-square
[license]: https://github.com/MicaelJarniac/repeaterbook/blob/main/LICENSE
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[badge-all-contributors]: https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[contributors]: #Contributors-✨
[badge-code-of-conduct]: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa?style=flat-square
[code-of-conduct]: CODE_OF_CONDUCT.md
<!---->

# RepeaterBook Python Client

> **Unofficial project.** RepeaterBook Python Client is an independent, community-maintained library and MCP server, and is **not affiliated with, endorsed by, or officially supported by RepeaterBook.com**. "RepeaterBook" is a trademark of its respective owner. For the official website and API, visit <https://repeaterbook.com/>.

Welcome to the **RepeaterBook Python Client** documentation!

**RepeaterBook Python Client** is an unofficial, third-party Python library **and [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server** that provides a powerful and convenient interface to the [RepeaterBook.com](https://repeaterbook.com/) API — the world's largest database of amateur radio repeaters. Use it as a library to programmatically download, query, and analyze repeater data, or run the bundled MCP server to give AI agents and LLM tools the same repeater lookup capabilities.

## Features

- **Easy API Access**: Download repeater data from RepeaterBook.com with a simple async interface
- **Unofficial MCP Server**: Ship repeater sync, geographic search, and lookup to any MCP client as three typed tools — see the [MCP Server guide](mcp.md)
- **Local Database**: Store repeater information in a local SQLite database for fast queries
- **Geographic Queries**: Find repeaters near a location using distance-based filtering
- **Band Filtering**: Query repeaters by frequency band (2m, 70cm, etc.)
- **Digital Mode Support**: Filter by DMR, P25, NXDN, and other digital modes
- **Smart Caching**: Automatic caching of API responses to reduce load and improve performance
- **Type Safe**: Fully typed with mypy for excellent IDE support
- **Async/Await**: Non-blocking I/O for efficient API operations

## Quick Example

> This library requires a per-user RepeaterBook API token. [Request access](https://repeaterbook.com/wiki/doku.php?id=api), generate your token, and expose it as the `REPEATERBOOK` environment variable (for example `export REPEATERBOOK="rbuapp_..."`).

```python
import asyncio
import os
from repeaterbook import RepeaterBook, Repeater
from repeaterbook.services import RepeaterBookAPI
from repeaterbook.models import ExportQuery, Status
from repeaterbook.utils import LatLon, Radius
from repeaterbook.queries import filter_radius, square, band, Bands
import pycountry

async def find_nearby_repeaters():
    # Download repeater data
    api = RepeaterBookAPI(app_token=os.environ["REPEATERBOOK"])
    brazil = pycountry.countries.get(name="Brazil")
    repeaters = await api.download(query=ExportQuery(countries={brazil}))

    # Store in local database
    rb = RepeaterBook()
    rb.populate(repeaters)

    # Find DMR repeaters within 50km of São Paulo
    sao_paulo = LatLon(lat=-23.5505, lon=-46.6333)
    radius = Radius(origin=sao_paulo, distance=50)

    nearby = rb.query(
        square(radius),
        Repeater.dmr_capable == True,
        Repeater.operational_status == Status.ON_AIR,
        band(Bands.CM_70)  # 70cm band
    )

    filtered = filter_radius(nearby, radius)

    # Display results (filter_radius returns repeaters sorted by distance)
    from haversine import haversine
    for rep in filtered[:5]:
        distance = haversine(radius.origin, (rep.latitude, rep.longitude), unit=radius.unit)
        print(f"{distance:.1f}km - {rep.frequency:.4f} MHz - {rep.callsign}")

asyncio.run(find_nearby_repeaters())
```

## Quick Example (MCP)

Prefer to drive RepeaterBook from an AI agent? The unofficial MCP server ships as
the `repeaterbook-mcp` console script behind the `mcp` extra. Point your MCP
client at `uvx` and nothing needs installing up front:

```json
{
  "mcpServers": {
    "repeaterbook": {
      "command": "uvx",
      "args": ["--from", "repeaterbook[mcp]", "repeaterbook-mcp"],
      "env": {
        "REPEATERBOOK_WORKING_DIR": "~/.repeaterbook",
        "REPEATERBOOK_APP_CONTACT": "you@example.com",
        "REPEATERBOOK_APP_TOKEN": "rbuapp_..."
      }
    }
  }
}
```

That exposes three tools — `sync_repeaters`, `search_repeaters`, and
`get_repeater` — returning a stable, source-agnostic repeater spec. See the
**[MCP Server guide](mcp.md)** for the full tool reference, filter vocabulary,
and configuration options.

## Documentation

- **[Getting Started](getting-started.md)** - Tutorial for beginners
- **[Usage Guide](usage.md)** - Comprehensive usage examples
- **[MCP Server](mcp.md)** - Run the unofficial MCP server for AI agents
- **[Examples](examples.md)** - Real-world use cases
- **[Architecture](architecture.md)** - Understanding the internals
- **[API Reference](api.md)** - Complete API documentation
- **[FAQ](faq.md)** - Common questions and troubleshooting

[Read the full documentation][docs]

Read RepeaterBook.com's official [API documentation](https://repeaterbook.com/wiki/doku.php?id=api) for more information about the upstream API.

## Use Cases

- **AI Agents & Assistants**: Let an LLM look up repeaters conversationally over MCP
- **Trip Planning**: Find repeaters along travel routes
- **Emergency Communications**: Identify emergency-capable repeaters
- **Radio Programming**: Generate codeplugs for DMR and other digital radios
- **Coverage Analysis**: Create coverage maps and statistics
- **Network Analysis**: Analyze repeater networks and infrastructure
- **Mobile Apps**: Build repeater directory applications
- **Research**: Analyze amateur radio repeater trends and distributions

## Related Projects

- [MicaelJarniac/opengd77](https://github.com/MicaelJarniac/opengd77) - OpenGD77 radio programming
- [MicaelJarniac/ogdrb](https://github.com/MicaelJarniac/ogdrb) - OpenGD77 RepeaterBook integration

## See Also

- [afourney/hamkit](https://github.com/afourney/hamkit/tree/main/packages/repeaterbook) - Ham radio toolkit
- [desertblade/OpenGD77-Repeaterbook](https://github.com/desertblade/OpenGD77-Repeaterbook) - OpenGD77 integration
- [TomHW/OpenGD77](https://github.com/TomHW/OpenGD77) - OpenGD77 firmware

## Installation

### PyPI

[*repeaterbook*][pypi] is available on PyPI:

```bash
# With uv (recommended)
uv add repeaterbook

# With pip
pip install repeaterbook

# With Poetry
poetry add repeaterbook
```

### MCP server

The MCP server lives behind the `mcp` extra. Most MCP clients should invoke it
via `uvx`, with no install step at all:

```bash
# Run on demand, no install (what MCP clients should use)
uvx --from "repeaterbook[mcp]" repeaterbook-mcp

# Or install it persistently
uv tool install "repeaterbook[mcp]"

# Or add it as a project dependency
uv add "repeaterbook[mcp]"
pip install "repeaterbook[mcp]"
```

### GitHub

You can also install the latest version of the code directly from GitHub:

```bash
# With uv
uv add git+https://github.com/MicaelJarniac/repeaterbook

# With pip
pip install git+https://github.com/MicaelJarniac/repeaterbook

# With Poetry
poetry add git+https://github.com/MicaelJarniac/repeaterbook
```

## Requirements

- Python 3.11 or higher
- Dependencies are automatically installed:
  - aiohttp - Async HTTP client
  - anyio - Async compatibility layer
  - attrs - Immutable config classes
  - haversine - Distance calculations
  - loguru - Structured logging
  - pycountry - Country/region codes
  - pydantic - Data validation
  - sqlmodel - SQL ORM with type safety
  - tqdm - Progress bars
  - yarl - URL handling
- The optional `mcp` extra additionally installs `fastmcp` and `pydantic-settings`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

More details can be found in [CONTRIBUTING](CONTRIBUTING.md).

## Contributors ✨
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/MicaelJarniac"><img src="https://avatars.githubusercontent.com/u/19514231?v=4?s=100" width="100px;" alt="Micael Jarniac"/><br /><sub><b>Micael Jarniac</b></sub></a><br /><a href="https://github.com/MicaelJarniac/repeaterbook/issues?q=author%3AMicaelJarniac" title="Bug reports">🐛</a> <a href="https://github.com/MicaelJarniac/repeaterbook/commits?author=MicaelJarniac" title="Code">💻</a> <a href="#content-MicaelJarniac" title="Content">🖋</a> <a href="#data-MicaelJarniac" title="Data">🔣</a> <a href="https://github.com/MicaelJarniac/repeaterbook/commits?author=MicaelJarniac" title="Documentation">📖</a> <a href="#example-MicaelJarniac" title="Examples">💡</a> <a href="#ideas-MicaelJarniac" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-MicaelJarniac" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-MicaelJarniac" title="Maintenance">🚧</a> <a href="#projectManagement-MicaelJarniac" title="Project Management">📆</a> <a href="#question-MicaelJarniac" title="Answering Questions">💬</a> <a href="#research-MicaelJarniac" title="Research">🔬</a> <a href="https://github.com/MicaelJarniac/repeaterbook/pulls?q=is%3Apr+reviewed-by%3AMicaelJarniac" title="Reviewed Pull Requests">👀</a> <a href="#tool-MicaelJarniac" title="Tools">🔧</a> <a href="https://github.com/MicaelJarniac/repeaterbook/commits?author=MicaelJarniac" title="Tests">⚠️</a> <a href="#userTesting-MicaelJarniac" title="User Testing">📓</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/adamancini"><img src="https://avatars.githubusercontent.com/u/292598?v=4?s=100" width="100px;" alt="ada mancini"/><br /><sub><b>ada mancini</b></sub></a><br /><a href="https://github.com/MicaelJarniac/repeaterbook/issues?q=author%3Aadamancini" title="Bug reports">🐛</a> <a href="#ideas-adamancini" title="Ideas, Planning, & Feedback">🤔</a> <a href="#userTesting-adamancini" title="User Testing">📓</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## License
[MIT](../LICENSE)

This project was created with the [MicaelJarniac/crustypy](https://github.com/MicaelJarniac/crustypy) template.
