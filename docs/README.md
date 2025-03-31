<div align="center">

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
[badge-all-contributors]: https://img.shields.io/badge/all_contributors-0-orange.svg?style=flat-square
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[contributors]: #Contributors-✨
[badge-code-of-conduct]: https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa?style=flat-square
[code-of-conduct]: CODE_OF_CONDUCT.md
<!---->

# RepeaterBook
Python utility to work with data from RepeaterBook.

[Read the Docs][docs]

Read RepeaterBook's official [API documentation](https://www.repeaterbook.com/wiki/doku.php?id=api) for more information.

## See Also
- https://github.com/afourney/hamkit/tree/main/packages/repeaterbook
- https://github.com/desertblade/OpenGD77-Repeaterbook
- https://github.com/TomHW/OpenGD77

## Installation

### PyPI
[*repeaterbook*][pypi] is available on PyPI:

```bash
# With uv
uv add repeaterbook
# With pip
pip install repeaterbook
# With Poetry
poetry add repeaterbook
```

### GitHub
You can also install the latest version of the code directly from GitHub:
```bash
# With uv
uv add git+https://github.com/MicaelJarniac/repeaterbook
# With pip
pip install git+git://github.com/MicaelJarniac/repeaterbook
# With Poetry
poetry add git+git://github.com/MicaelJarniac/repeaterbook
```

## Usage
For more examples, see the [full documentation][docs].

```python
from repeaterbook import repeaterbook
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

More details can be found in [CONTRIBUTING](CONTRIBUTING.md).

## Contributors ✨
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## License
[MIT](../LICENSE)

This project was created with the [MicaelJarniac/crustypy](https://github.com/MicaelJarniac/crustypy) template.
