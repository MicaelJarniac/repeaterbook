# CHANGELOG

<!-- version list -->

## v0.11.3 (2026-09-04)

### Bug Fixes

- **deps**: Bump nox to >=2026.2.9 so sessions survive a second local run
  ([`07c03a4`](https://github.com/MicaelJarniac/repeaterbook/commit/07c03a43fff90caf753e51aa9681216f2b65ed94))


## v0.11.2 (2026-09-04)

### Bug Fixes

- **release**: Keep the changelog updating under PSR v10
  ([`ef3f46c`](https://github.com/MicaelJarniac/repeaterbook/commit/ef3f46c135457ac72dd5fcb04c881ff15ccc80a8))

### Chores

- **deps-dev**: Bump mkdocs-material in the uv group across 1 directory
  ([`3898d43`](https://github.com/MicaelJarniac/repeaterbook/commit/3898d43f7a5a7194a96ae4219560ebe79d0083b9))

- **wordlist**: Update
  ([`e4c018d`](https://github.com/MicaelJarniac/repeaterbook/commit/e4c018db268dc857139a44d17e535facb406e60d))

### Testing

- Reach 100% line and branch coverage, and enforce it
  ([`d9c792e`](https://github.com/MicaelJarniac/repeaterbook/commit/d9c792ef6c8bd170358e85573bf8b191015fb7cc))


## v0.11.1 (2026-09-02)

### Bug Fixes

- **ci**: Stop a failed asset upload from skipping the PyPI publish
  ([`16b5be3`](https://github.com/MicaelJarniac/repeaterbook/commit/16b5be3cf61873f7c4dd55e74a22858cafcb0b0c))


## v0.11.0 (2026-09-02)

### Bug Fixes

- **models**: Type ARES/RACES/SKYWARN/CANWARN as tri-state booleans
  ([`33aef9f`](https://github.com/MicaelJarniac/repeaterbook/commit/33aef9f8115292774b75cf4fe62090ce208bf7a1))

### Features

- **database**: Rebuild the local database when its schema drifts
  ([`5aa339a`](https://github.com/MicaelJarniac/repeaterbook/commit/5aa339ab65af579d7482a81602d87db9c0aa6ce7))

### Breaking Changes

- **models**: Repeater.ares, .races, .skywarn and .canwarn are now `bool | None` instead of `str |
  None`. Replace `== "Yes"` with `== True`, and note that a null check no longer means "supported":
  None is a third state meaning the export did not report it. An existing database is discarded and
  rebuilt on first use, since its columns hold the old text.


## v0.10.2 (2026-09-01)

### Bug Fixes

- Raise RepeaterBookCacheError on cache write failure
  ([`7e891bf`](https://github.com/MicaelJarniac/repeaterbook/commit/7e891bf9db8479066327eb1f5ef4c565f508f943))


## v0.10.1 (2026-09-01)

### Bug Fixes

- **mcp**: Validate settings at startup
  ([`e1c40e4`](https://github.com/MicaelJarniac/repeaterbook/commit/e1c40e48c6753dee9f7581f7bdc3e5d3aea079f0))

### Chores

- **deps**: Bump tornado from 6.5.7 to 6.5.8
  ([`6e79bfd`](https://github.com/MicaelJarniac/repeaterbook/commit/6e79bfd156107ed0b7b72d8958ec554d5b929a32))

### Documentation

- Compare emcomm fields to "Yes", not to null
  ([`50f2c8b`](https://github.com/MicaelJarniac/repeaterbook/commit/50f2c8ba6b35e0e6e67df32f069ed67001fe5b76))

- Correct broken and inaccurate code examples
  ([`fd8a49c`](https://github.com/MicaelJarniac/repeaterbook/commit/fd8a49cfda9e8a830a94cb07f728db97a7a6b48c))

- Cover all submodules in the API reference and fix dead links
  ([`7330f34`](https://github.com/MicaelJarniac/repeaterbook/commit/7330f341c0441c15823d12685e9af9554de86f88))

- Document the MCP subpackage in the API reference
  ([`1b26a26`](https://github.com/MicaelJarniac/repeaterbook/commit/1b26a26cef3827f8c40bc99f952ad4de489347aa))

- Explain how to get an API token via App #114
  ([`b465f99`](https://github.com/MicaelJarniac/repeaterbook/commit/b465f994c5c51328958afd27ad1284a0d5587ce9))

- Rewrite architecture for the current codebase
  ([`45023ee`](https://github.com/MicaelJarniac/repeaterbook/commit/45023eeba82ee5ba2d1dfb8d67e92a2521ba8a8d))


## v0.10.0 (2026-08-31)

### Documentation

- Update .all-contributorsrc [skip ci]
  ([`5971b17`](https://github.com/MicaelJarniac/repeaterbook/commit/5971b17ca14c605cb3cc492f4356acdd08006419))

- Update docs/README.md [skip ci]
  ([`1a0e155`](https://github.com/MicaelJarniac/repeaterbook/commit/1a0e155c09a2ca8cd6f77d4158ca0d305d69f455))

### Features

- **mcp**: Declare the server in the MCP Registry
  ([`5c07d1b`](https://github.com/MicaelJarniac/repeaterbook/commit/5c07d1b08cb1516e40ef0454e5fd22a303b1e998))


## v0.9.1 (2026-08-31)

### Bug Fixes

- **mcp**: Stop overriding the approved User-Agent contact
  ([`44fb0b9`](https://github.com/MicaelJarniac/repeaterbook/commit/44fb0b90f7b1f36dda4b9e019aa31bef79cf397f))

### Documentation

- Replace the User-Agent override example in usage.md
  ([`fab0e98`](https://github.com/MicaelJarniac/repeaterbook/commit/fab0e98c00925f42b6cdd40da5bafc6cd8914e0f))


## v0.9.0 (2026-08-27)

### Features

- **spec**: Expose linking node fields on RepeaterSpec
  ([`571ca47`](https://github.com/MicaelJarniac/repeaterbook/commit/571ca47142d1648ec4027d0a127e55ddd8c7e38a))


## v0.8.4 (2026-08-27)

### Bug Fixes

- **spec**: Make last_update timezone-aware for RFC 3339 output
  ([`e2eed21`](https://github.com/MicaelJarniac/repeaterbook/commit/e2eed210e236e2d6742a3a506673e9cc0fcb9789))

### Documentation

- Update .all-contributorsrc [skip ci]
  ([`c9edcbe`](https://github.com/MicaelJarniac/repeaterbook/commit/c9edcbee7c988f5ce07f0e9cf77faadc62c5f232))

- Update docs/README.md [skip ci]
  ([`5767376`](https://github.com/MicaelJarniac/repeaterbook/commit/5767376ec851373d17caaadee0807e12fd0acbf6))


## v0.8.3 (2026-08-26)

### Bug Fixes

- **meta**: Surface the MCP server in project metadata and correct stale claims
  ([`dfb82f3`](https://github.com/MicaelJarniac/repeaterbook/commit/dfb82f37593d32c843cee12b8666e876863845d0))

### Documentation

- Update .all-contributorsrc [skip ci]
  ([`639ee6e`](https://github.com/MicaelJarniac/repeaterbook/commit/639ee6edd80483cab884e39a8a688433fb24da93))

- Update .all-contributorsrc [skip ci]
  ([`9e0919f`](https://github.com/MicaelJarniac/repeaterbook/commit/9e0919f8d04b8ca6e28164de590f59241396ccc0))

- Update docs/README.md [skip ci]
  ([`b8a78e7`](https://github.com/MicaelJarniac/repeaterbook/commit/b8a78e7264d86b4b3e15223dadedd588fc472646))

- Update docs/README.md [skip ci]
  ([`7d8c8a5`](https://github.com/MicaelJarniac/repeaterbook/commit/7d8c8a5b70de3769870432d3a207b168fba37406))


## v0.8.2 (2026-08-26)

### Bug Fixes

- **services**: Skip unmodellable export rows instead of failing the batch
  ([`a79abc3`](https://github.com/MicaelJarniac/repeaterbook/commit/a79abc326ffa4de020e2ce96aa437df9a14f3f21))


## v0.8.1 (2026-08-26)

### Bug Fixes

- **ci**: Run the GitHub publish step from the locked environment too
  ([`06d0f1f`](https://github.com/MicaelJarniac/repeaterbook/commit/06d0f1fdc994c6e986f5a7a9729024ef1be3d37d))


## v0.8.0 (2026-08-26)

### Bug Fixes

- **ci**: Run semantic-release from the locked environment
  ([`4f008ff`](https://github.com/MicaelJarniac/repeaterbook/commit/4f008ff9693e7d79acda25f0956373036073a126))

- **ci**: Upgrade semantic-release to v10 and pin 0.x versioning
  ([`ad12bcd`](https://github.com/MicaelJarniac/repeaterbook/commit/ad12bcd254af014bf67109af27999bda29167cc9))

### Chores

- **deps**: Bump aiohttp from 3.14.1 to 3.14.3
  ([`dcb5fc1`](https://github.com/MicaelJarniac/repeaterbook/commit/dcb5fc1b65092b8c2f60c0332a75751a03dd22b0))

- **deps**: Bump gitpython from 3.1.54 to 3.1.57
  ([`a97e581`](https://github.com/MicaelJarniac/repeaterbook/commit/a97e581c4fb0837bac145e69e4c730c937a1caa5))

- **deps**: Bump gitpython from 3.1.57 to 3.1.58
  ([`8c566dd`](https://github.com/MicaelJarniac/repeaterbook/commit/8c566dd4aa61e6cab22fbfb469eed809f0ce24e3))

- **deps**: Bump pymdown-extensions from 11.0 to 11.0.1
  ([`fc6cc18`](https://github.com/MicaelJarniac/repeaterbook/commit/fc6cc18c8c5e39548cf51d240966443bc796dd5c))

### Features

- **mcp**: Add an MCP server and promote the repeater-spec contract into core
  ([`ad1021a`](https://github.com/MicaelJarniac/repeaterbook/commit/ad1021a618d902fe971a0f8176990147cb209832))


## v0.7.0 (2026-07-28)

### Bug Fixes

- **auth**: Pin app_version to keep the approved User-Agent stable
  ([`892ec14`](https://github.com/MicaelJarniac/repeaterbook/commit/892ec14b3a6a4e7046c5bc783c3bc49572244fd5))

RepeaterBook approves tokens against a specific User-Agent (including the version). Deriving
  app_version from the package __version__ changed the UA on every release and could break
  already-approved tokens, so pin it to the approved value and bump it deliberately in lockstep with
  the registered User-Agent.

- **auth**: Use X-RB-App-Token header
  ([`7c09d2d`](https://github.com/MicaelJarniac/repeaterbook/commit/7c09d2d503b7be84066656a478938537b141dfd9))

RepeaterBook's 2026-03-03 API policy requires an approved per-user token sent via the preferred
  X-RB-App-Token header. The live API rejects Authorization: Bearer <token> with HTTP 401
  auth_missing even for valid tokens, so the client could never authenticate.

Send the raw token in X-RB-App-Token when app_token is set, mark app_token repr=False so the
  credential never leaks via attrs __repr__, add unit coverage for the 401/500 error paths, switch
  the live integration tests to an authenticated fixture (reads REPEATERBOOK), and correct the
  docs/FAQ that wrongly stated no auth was required.

Fixes #31

### Chores

- Align default User-Agent app_name with the client name
  ([`cce19bc`](https://github.com/MicaelJarniac/repeaterbook/commit/cce19bca921b877b6f709ced812edd4b0d538ed9))

Change RepeaterBookAPI.app_name default from "RepeaterBook Python SDK" to "RepeaterBook Python
  Client" so the User-Agent sent to RepeaterBook.com matches the project's unofficial-client
  identity. Also rewords the class docstring and updates the playground example to match.

- Sync .cruft.json template context with the new client identity
  ([`a3274dd`](https://github.com/MicaelJarniac/repeaterbook/commit/a3274dd0398e2c916f4cc11430506810bb42bd11))

Update the cruft/cookiecutter context so project_name and project_short_description match the
  repositioned identity ("RepeaterBook Python Client" / unofficial third-party client). This keeps a
  future cruft update from reverting the new naming. project_slug and project_distribution_name are
  unchanged, so the package/import name stays "repeaterbook".

- **deps**: Bump aiohttp from 3.13.4 to 3.14.1
  ([`10b9719`](https://github.com/MicaelJarniac/repeaterbook/commit/10b9719cfc83d3b345d603ba06fcf75821544af9))

--- updated-dependencies: - dependency-name: aiohttp dependency-version: 3.14.1

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump gitpython from 3.1.46 to 3.1.50
  ([`8fa4e1f`](https://github.com/MicaelJarniac/repeaterbook/commit/8fa4e1f726591fa4065984a96d71ac3fcc003cdf))

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.46 to 3.1.50. -
  [Release notes](https://github.com/gitpython-developers/GitPython/releases) -
  [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES) -
  [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.46...3.1.50)

--- updated-dependencies: - dependency-name: gitpython dependency-version: 3.1.50

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump gitpython from 3.1.50 to 3.1.52
  ([`70f849b`](https://github.com/MicaelJarniac/repeaterbook/commit/70f849b363accfa9a4ca34cdc54621572887ae49))

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.50 to 3.1.52. -
  [Release notes](https://github.com/gitpython-developers/GitPython/releases) -
  [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES) -
  [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.50...3.1.52)

--- updated-dependencies: - dependency-name: gitpython dependency-version: 3.1.52

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump gitpython from 3.1.52 to 3.1.54
  ([`bfcb2b1`](https://github.com/MicaelJarniac/repeaterbook/commit/bfcb2b1f0759642a735143aea7f358e6cb662f30))

Bumps [gitpython](https://github.com/gitpython-developers/GitPython) from 3.1.52 to 3.1.54. -
  [Release notes](https://github.com/gitpython-developers/GitPython/releases) -
  [Changelog](https://github.com/gitpython-developers/GitPython/blob/main/CHANGES) -
  [Commits](https://github.com/gitpython-developers/GitPython/compare/3.1.52...3.1.54)

--- updated-dependencies: - dependency-name: gitpython dependency-version: 3.1.54

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump idna from 3.11 to 3.15
  ([`d41169f`](https://github.com/MicaelJarniac/repeaterbook/commit/d41169f3657d5586e8ac51d76c428cb9bd410855))

Bumps [idna](https://github.com/kjd/idna) from 3.11 to 3.15. - [Release
  notes](https://github.com/kjd/idna/releases) -
  [Changelog](https://github.com/kjd/idna/blob/master/HISTORY.md) -
  [Commits](https://github.com/kjd/idna/compare/v3.11...v3.15)

--- updated-dependencies: - dependency-name: idna dependency-version: '3.15'

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump pygments from 2.19.2 to 2.20.0
  ([`8247f18`](https://github.com/MicaelJarniac/repeaterbook/commit/8247f18453a79c926fb2629a47c87739f64954d6))

Bumps [pygments](https://github.com/pygments/pygments) from 2.19.2 to 2.20.0. - [Release
  notes](https://github.com/pygments/pygments/releases) -
  [Changelog](https://github.com/pygments/pygments/blob/master/CHANGES) -
  [Commits](https://github.com/pygments/pygments/compare/2.19.2...2.20.0)

--- updated-dependencies: - dependency-name: pygments dependency-version: 2.20.0

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump pymdown-extensions from 10.20.1 to 10.21.3
  ([`b28e151`](https://github.com/MicaelJarniac/repeaterbook/commit/b28e15125c54740382f43703ba03124232ddf475))

Bumps [pymdown-extensions](https://github.com/facelessuser/pymdown-extensions) from 10.20.1 to
  10.21.3. - [Release notes](https://github.com/facelessuser/pymdown-extensions/releases) -
  [Commits](https://github.com/facelessuser/pymdown-extensions/commits/10.21.3)

--- updated-dependencies: - dependency-name: pymdown-extensions dependency-version: 10.21.3

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump pymdown-extensions from 10.21.3 to 11.0
  ([`9a8ac8f`](https://github.com/MicaelJarniac/repeaterbook/commit/9a8ac8fbb74b68bae21fd41c0d01ba6ced675def))

Bumps [pymdown-extensions](https://github.com/facelessuser/pymdown-extensions) from 10.21.3 to 11.0.
  - [Release notes](https://github.com/facelessuser/pymdown-extensions/releases) -
  [Commits](https://github.com/facelessuser/pymdown-extensions/compare/10.21.3...11.0)

--- updated-dependencies: - dependency-name: pymdown-extensions dependency-version: '11.0'

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump pytest from 9.0.2 to 9.0.3
  ([`54b34e1`](https://github.com/MicaelJarniac/repeaterbook/commit/54b34e18aa2ece0ffd58a6bb6fa3af99ce30363b))

Bumps [pytest](https://github.com/pytest-dev/pytest) from 9.0.2 to 9.0.3. - [Release
  notes](https://github.com/pytest-dev/pytest/releases) -
  [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst) -
  [Commits](https://github.com/pytest-dev/pytest/compare/9.0.2...9.0.3)

--- updated-dependencies: - dependency-name: pytest dependency-version: 9.0.3

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump tornado from 6.5.5 to 6.5.7
  ([`1f76792`](https://github.com/MicaelJarniac/repeaterbook/commit/1f767923b502f7345415e2e6a8101cb962850ca2))

Bumps [tornado](https://github.com/tornadoweb/tornado) from 6.5.5 to 6.5.7. -
  [Changelog](https://github.com/tornadoweb/tornado/blob/master/docs/releases.rst) -
  [Commits](https://github.com/tornadoweb/tornado/compare/v6.5.5...v6.5.7)

--- updated-dependencies: - dependency-name: tornado dependency-version: 6.5.7

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump urllib3 from 2.6.3 to 2.7.0
  ([`6da49fe`](https://github.com/MicaelJarniac/repeaterbook/commit/6da49fedd7da123fbf1d5446ad12fc18f906e8bc))

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.6.3 to 2.7.0. - [Release
  notes](https://github.com/urllib3/urllib3/releases) -
  [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst) -
  [Commits](https://github.com/urllib3/urllib3/compare/2.6.3...2.7.0)

--- updated-dependencies: - dependency-name: urllib3 dependency-version: 2.7.0

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump uv from 0.9.28 to 0.11.15
  ([`045fa3a`](https://github.com/MicaelJarniac/repeaterbook/commit/045fa3a93277e507175f3df67b0604d82714a2e0))

Bumps [uv](https://github.com/astral-sh/uv) from 0.9.28 to 0.11.15. - [Release
  notes](https://github.com/astral-sh/uv/releases) -
  [Changelog](https://github.com/astral-sh/uv/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/astral-sh/uv/compare/0.9.28...0.11.15)

--- updated-dependencies: - dependency-name: uv dependency-version: 0.11.15

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

### Documentation

- Remove www
  ([`f7b40c9`](https://github.com/MicaelJarniac/repeaterbook/commit/f7b40c9c594d40c5e226f3f5895c8e1843bf9f90))

- Reposition as unofficial third-party RepeaterBook.com client
  ([`2796627`](https://github.com/MicaelJarniac/repeaterbook/commit/279662760f51d412640cc0b538296753a52ded47))

Reword documentation, package metadata, and public docstrings so the project presents as
  "RepeaterBook Python Client" -- an unofficial, third-party client for the RepeaterBook.com API --
  rather than as RepeaterBook itself.

- Add "unofficial / not affiliated with, endorsed by, or officially supported by RepeaterBook.com"
  notices: README banner, a new docs FAQ entry, the pyproject/site description, and a new root
  NOTICE (trademark acknowledgement). - Reserve the bare name "RepeaterBook"/"RepeaterBook.com" for
  the upstream service; refer to this library as the "RepeaterBook Python Client". - No public API
  symbols renamed and no behavior change.

- **auth**: Show required API token in quick-start examples
  ([`18aeea7`](https://github.com/MicaelJarniac/repeaterbook/commit/18aeea716391b37596bd3d8030ac2a3f3d9e8ed2))

Update the README quick example, the getting-started tutorial, and the examples page to reflect that
  a per-user token is now required: load it from the REPEATERBOOK environment variable and pass it
  via app_token. Adds token notes that point to the Authentication guide.

### Features

- **exceptions**: Surface API error_code/message and add 403/429 types
  ([`92d77a9`](https://github.com/MicaelJarniac/repeaterbook/commit/92d77a985530c22989a0abf41ec3ff13e16e12f9))

Read the API error body and raise structured exceptions carrying status_code, error_code, the server
  message, and the request url. fetch_json now inspects the response instead of using
  raise_for_status, so the JSON error envelope ({"ok":false,"error_code":...,"message":...}) is no
  longer discarded.

Adds RepeaterBookForbiddenError (403) and RepeaterBookRateLimitError (429, with retry_after);
  export_json handles both the ok:false and legacy status:error envelopes. Request headers and the
  token are never included in exception output.

### Testing

- **auth**: Harden live integration tests and cover User-Agent
  ([`cbf2c05`](https://github.com/MicaelJarniac/repeaterbook/commit/cbf2c05cd178a3e66c3bece7fa3b2893f382fe66))

Switch the live tests to the token's approved default identity, shrink queries to small regions
  (Rhode Island and a small ROW country), and add a 2s cooldown between live calls. Add an offline
  test that a mismatched User-Agent is rejected, and a live probe that reports (via skip) whether
  the token accepts a different app version.


## v0.6.0 (2026-04-07)

### Chores

- **deps**: Bump aiohttp from 3.13.3 to 3.13.4
  ([`24b513c`](https://github.com/MicaelJarniac/repeaterbook/commit/24b513c2b7893b43a18ec374758abc7e03fa5e23))

--- updated-dependencies: - dependency-name: aiohttp dependency-version: 3.13.4

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

- **deps**: Bump requests from 2.32.5 to 2.33.0
  ([`0e47556`](https://github.com/MicaelJarniac/repeaterbook/commit/0e47556f129ae47c5398f8bcefb0bee8a2bcdbdb))

Bumps [requests](https://github.com/psf/requests) from 2.32.5 to 2.33.0. - [Release
  notes](https://github.com/psf/requests/releases) -
  [Changelog](https://github.com/psf/requests/blob/main/HISTORY.md) -
  [Commits](https://github.com/psf/requests/compare/v2.32.5...v2.33.0)

--- updated-dependencies: - dependency-name: requests dependency-version: 2.33.0

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

### Features

- Truncate
  ([`f1d70f6`](https://github.com/MicaelJarniac/repeaterbook/commit/f1d70f6356e0d7f37d5480a494905480f1ce8400))


## v0.5.1 (2026-04-06)

### Bug Fixes

- Remove Py 3.10, add 3.14
  ([`51b5cb9`](https://github.com/MicaelJarniac/repeaterbook/commit/51b5cb93f0e02c12821bdec61c3a74b46acd4b4f))


## v0.5.0 (2026-04-06)

### Chores

- **deps**: Bump tornado from 6.5.4 to 6.5.5
  ([`49e0d7b`](https://github.com/MicaelJarniac/repeaterbook/commit/49e0d7b98382ceeeba2be96e4fc77c517440e899))

Bumps [tornado](https://github.com/tornadoweb/tornado) from 6.5.4 to 6.5.5. -
  [Changelog](https://github.com/tornadoweb/tornado/blob/master/docs/releases.rst) -
  [Commits](https://github.com/tornadoweb/tornado/compare/v6.5.4...v6.5.5)

--- updated-dependencies: - dependency-name: tornado dependency-version: 6.5.5

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

### Documentation

- Add AGENTS.md project knowledge base
  ([`d1a63e4`](https://github.com/MicaelJarniac/repeaterbook/commit/d1a63e41b528c4a52a2b20dd94c4cbfeb3dd9044))

### Features

- Import from CSV export
  ([`4e569a2`](https://github.com/MicaelJarniac/repeaterbook/commit/4e569a2d2f7b01548bedd0e5fea478255b1d9e2d))


## v0.4.2 (2026-03-04)

### Bug Fixes

- Support auth
  ([`fbdcf71`](https://github.com/MicaelJarniac/repeaterbook/commit/fbdcf715e6a32ba91d9c4c8db36ba0963acc6f48))

### Chores

- Format
  ([`9e71ff4`](https://github.com/MicaelJarniac/repeaterbook/commit/9e71ff44e570e491c67760ca0d7208a42d699f85))


## v0.4.1 (2026-03-04)

### Bug Fixes

- Handle API errors
  ([`e676c5b`](https://github.com/MicaelJarniac/repeaterbook/commit/e676c5bb1cf0ae232d62a2d34cd8d85abc644aeb))

### Documentation

- Add comprehensive documentation ([#12](https://github.com/MicaelJarniac/repeaterbook/pull/12),
  [`457a003`](https://github.com/MicaelJarniac/repeaterbook/commit/457a00322ed0816a39219817b8fa4c8b38dda8f8))

* docs: add comprehensive documentation

Add extensive documentation covering all aspects of the RepeaterBook library:

- getting-started.md: Complete tutorial for beginners with quick start examples - usage.md:
  Comprehensive usage guide covering API client, database operations, geographic queries, frequency
  filtering, digital modes, and data export - architecture.md: Technical architecture documentation
  with diagrams, data flow explanations, design decisions, and extensibility guide - examples.md:
  Real-world examples including web apps, codeplug generation, coverage maps, statistics dashboards,
  travel planning, and network analysis - faq.md: Extensive FAQ covering installation, usage,
  performance, troubleshooting, and integration questions - README.md: Enhanced with better
  introduction, features list, quick example, and clear navigation to all documentation sections -
  mkdocs.yml: Updated navigation structure to include all new documentation pages

This significantly improves the developer experience by providing clear, comprehensive documentation
  with practical examples for common use cases.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

* fix: regenerate corrupted uv.lock file

The uv.lock file had a corruption with typing-extensions dependency missing source field.
  Regenerated the lock file to resolve the issue.

* fix: correct all field names and API usage in documentation examples

Fixed all code examples across documentation to use correct field names and proper API patterns:

- Changed LatLon(latitude=, longitude=) to LatLon(lat=, lon=) - Updated field names to match actual
  model: - location → location_nearest_city - input_ctcss → pl_ctcss_uplink - output_ctcss →
  pl_ctcss_tsq_downlink - p25_capable → apco_p_25_capable - p25_nac → p_25_nac - Fixed distance
  handling: filter_radius() returns sorted repeaters but doesn't add distance attribute, must
  calculate manually with haversine - Changed states= to state_ids= in ExportQuery - Removed
  references to non-existent fields (input_dcs, output_dcs, nxdn_ran, trustee) - Fixed emergency
  services to use actual fields (ares, races, skywarn, canwarn) instead of non-existent
  Emergency.YES/NO enum - Removed incorrect rb.session usage

All examples now work correctly with the actual codebase.

* fix: infinite CI

* chore: update cruft

* build(CI): fix pre-commit

* chore: cruft update

* docs: update documentation for v0.4.0 features

- Updated API configuration to use max_cache_age (timedelta) instead of cache_ttl - Added
  documentation for custom exceptions: - RepeaterBookError (base) - RepeaterBookAPIError -
  RepeaterBookValidationError - RepeaterBookCacheError - Documented model validation (latitude,
  longitude, frequency) - Added error handling examples to usage guide and FAQ - Added timedelta,
  haversine, frozenset to wordlist

- Changed LatLon(latitude=, longitude=) to LatLon(lat=, lon=) - Removed non-existent .distance
  attribute access - Added inline haversine calculation for distance display - filter_radius()
  returns sorted repeaters without distance attribute

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

* fix: remove non-existent field references and update API patterns

- Remove rep.network references (field doesn't exist in Repeater model) - Update cache_ttl to
  max_cache_age (timedelta) in examples - Fix filter_radius documentation to not set
  repeater.distance - Fix square_bounds call signature - Rename Example 7 from network analysis to
  DMR analysis

* fix: use FIPS codes for state_ids instead of state names

The state_ids parameter requires numeric FIPS codes (e.g., "06" for California, "48" for Texas), not
  state names. Updated all documentation examples to use correct FIPS codes.

Examples: - California: "06" - Nevada: "32" - Oregon: "41" - Washington: "53" - Texas: "48" -
  Oklahoma: "40" - New Mexico: "35" - Florida: "12" - Arizona: "04" - Utah: "49"

* fix: use keyword argument for RepeaterBook database parameter

RepeaterBook's first positional arg is working_dir, not database. Fixed all examples to use
  database= keyword argument.

Also removed incorrect :memory: example - the current implementation doesn't support in-memory
  databases as it always constructs a file path.

* chore: mkdocs cfg place

---------

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>


## v0.4.0 (2026-02-04)

### Features

- Comprehensive codebase improvements ([#8](https://github.com/MicaelJarniac/repeaterbook/pull/8),
  [`c893c4b`](https://github.com/MicaelJarniac/repeaterbook/commit/c893c4b39125d4f843d11cb06f633122b809b769))

* feat: comprehensive codebase improvements

- Add custom exception classes (RepeaterBookError, RepeaterBookAPIError, RepeaterBookCacheError,
  RepeaterBookValidationError) - Enable North America endpoint in urls_export() - Fix cache race
  conditions with atomic write pattern - Add model validation for latitude, longitude, and frequency
  fields - Replace MD5 with SHA256 for cache key generation - Make configuration injectable
  (max_cache_age, max_count) - Remove commented-out operating_mode field - Improve type safety with
  explanatory comments for casts - Optimize cache stat calls (single stat instead of exists + stat)

Test suite expansion: - Add test_exceptions.py for exception hierarchy - Add test_services.py for
  services module - Add test_models.py for model validation - Add test_queries.py for query builders
  - Add test_database.py for database operations - Add test_utils.py for utility functions - Expand
  test_repeaterbook.py for public API

Total: 108 tests passing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

* feat: add smart routing for NA/ROW endpoints

Implement intelligent endpoint routing in urls_export(): - NA-specific fields (state_id, county,
  emcomm, stype) route to NA only - ROW-specific fields (region) route to ROW only - NA countries
  (US, Canada, Mexico) route to NA only - ROW countries route to ROW only - Mixed or common-only
  queries route to both

This prevents redundant API calls and avoids unfiltered queries that could return thousands of
  irrelevant results.

Added tests for all routing scenarios.

* test: add comprehensive smart routing integration tests

Add live API integration tests to verify smart routing behavior: - NA-only queries (state_id) route
  to export.php only - ROW-only queries (region) route to exportROW.php only - NA country queries
  route to NA endpoint - ROW country queries route to ROW endpoint - Mixed country queries route to
  both endpoints - Empty queries route to both endpoints - Mode-only queries route to both endpoints

Also fix linting warnings (use next(iter()) instead of list()[0]).

---------

Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>


## v0.3.0 (2026-02-03)

### Chores

- **deps**: Bump aiohttp from 3.11.14 to 3.13.3
  ([#6](https://github.com/MicaelJarniac/repeaterbook/pull/6),
  [`5ac6362`](https://github.com/MicaelJarniac/repeaterbook/commit/5ac63626172f12e422fc4025d1eb3fbfcfe87d5f))

--- updated-dependencies: - dependency-name: aiohttp dependency-version: 3.13.3

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump filelock from 3.18.0 to 3.20.3
  ([#4](https://github.com/MicaelJarniac/repeaterbook/pull/4),
  [`00e7717`](https://github.com/MicaelJarniac/repeaterbook/commit/00e7717186b77a8510ee6e0580bd1f13a4d495d6))

Bumps [filelock](https://github.com/tox-dev/py-filelock) from 3.18.0 to 3.20.3. - [Release
  notes](https://github.com/tox-dev/py-filelock/releases) -
  [Changelog](https://github.com/tox-dev/filelock/blob/main/docs/changelog.rst) -
  [Commits](https://github.com/tox-dev/py-filelock/compare/3.18.0...3.20.3)

--- updated-dependencies: - dependency-name: filelock dependency-version: 3.20.3

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump urllib3 from 2.3.0 to 2.6.3
  ([#5](https://github.com/MicaelJarniac/repeaterbook/pull/5),
  [`6870e08`](https://github.com/MicaelJarniac/repeaterbook/commit/6870e0894ef62164124096a7eba2a65d0da7637f))

Bumps [urllib3](https://github.com/urllib3/urllib3) from 2.3.0 to 2.6.3. - [Release
  notes](https://github.com/urllib3/urllib3/releases) -
  [Changelog](https://github.com/urllib3/urllib3/blob/main/CHANGES.rst) -
  [Commits](https://github.com/urllib3/urllib3/compare/2.3.0...2.6.3)

--- updated-dependencies: - dependency-name: urllib3 dependency-version: 2.6.3

dependency-type: indirect ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

- **deps**: Bump virtualenv from 20.29.3 to 20.36.1
  ([#3](https://github.com/MicaelJarniac/repeaterbook/pull/3),
  [`89b2aa3`](https://github.com/MicaelJarniac/repeaterbook/commit/89b2aa32f1c18b988dac0e1894456fd4576930b7))

Bumps [virtualenv](https://github.com/pypa/virtualenv) from 20.29.3 to 20.36.1. - [Release
  notes](https://github.com/pypa/virtualenv/releases) -
  [Changelog](https://github.com/pypa/virtualenv/blob/main/docs/changelog.rst) -
  [Commits](https://github.com/pypa/virtualenv/compare/20.29.3...20.36.1)

--- updated-dependencies: - dependency-name: virtualenv dependency-version: 20.36.1

dependency-type: direct:production ...

Signed-off-by: dependabot[bot] <support@github.com>

Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>

### Features

- Update Cruft ([#11](https://github.com/MicaelJarniac/repeaterbook/pull/11),
  [`0c7c471`](https://github.com/MicaelJarniac/repeaterbook/commit/0c7c471d559a8814018a645767bd34dbe381b58f))

* feat: update Cruft

* chore: update Cruft

### Testing

- Add cache tests + opt-in live API integration
  ([#7](https://github.com/MicaelJarniac/repeaterbook/pull/7),
  [`804cedd`](https://github.com/MicaelJarniac/repeaterbook/commit/804cedd0a0abd51d6ea31653f893db9cecef454f))

* test: add offline cache tests and opt-in live API integration tests

* refactor: fix linting and type checking issues in tests

- Add missing __init__.py to tests/integration/ package - Replace Any with proper StdPath type
  annotations for tmp_path - Add missing docstring to test function - Fix line length violations (88
  char limit) - Use more specific type:ignore[union-attr] for mypy - Extract magic number to named
  constant - Move pathlib imports to TYPE_CHECKING block

All linting (ruff) and type checking (mypy) now pass.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

* refactor(tests): extract local server fixture and clean up test code

- Add local_server fixture in conftest.py to reduce test duplication - Simplify _live_enabled() with
  case-insensitive comparison - Move pycountry import to module level in test_live_api.py - Extract
  _NA_SAMPLE_SIZE constant for magic number 200 - Fix import organization (blank lines after
  TYPE_CHECKING blocks)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

---------

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>


## v0.2.2 (2026-01-31)

### Bug Fixes

- Tolerate RepeaterBook API drift ([#2](https://github.com/MicaelJarniac/repeaterbook/pull/2),
  [`665d78e`](https://github.com/MicaelJarniac/repeaterbook/commit/665d78ee38ca856a242b8f5f6289c441f00193a2))

* fix: tolerate RepeaterBook API drift (sponsor, NA fields, empty Use)

* refactor: simplify Region parsing (use .get)

* refactor: add b() helper for Yes/No + 1/0 fields


## v0.2.1 (2025-04-09)

### Chores

- Links
  ([`1d93cdb`](https://github.com/MicaelJarniac/repeaterbook/commit/1d93cdb5ae7dff17a6cb9943e66b2111f39617b5))


## v0.2.0 (2025-04-08)

### Bug Fixes

- Use `and_` for `square` query
  ([`9c09b5e`](https://github.com/MicaelJarniac/repeaterbook/commit/9c09b5eff8a2a4cef3dda91d5fa4d44001b0f241))

### Features

- Queries
  ([`78972e5`](https://github.com/MicaelJarniac/repeaterbook/commit/78972e5cbdcd150dd9e6435d5dd5c759bb22f96b))


## v0.1.1 (2025-04-03)

### Bug Fixes

- Merge instead of add to local DB
  ([`f6dfcbf`](https://github.com/MicaelJarniac/repeaterbook/commit/f6dfcbf242c9af07578d5a2e8e19047ee2db96b9))

### Chores

- Dunder all as tuples
  ([`2dfb808`](https://github.com/MicaelJarniac/repeaterbook/commit/2dfb8089fee6db5fc26b9d3ea986fe8f9ce86cd3))

- Simpler working dir default
  ([`fecdd43`](https://github.com/MicaelJarniac/repeaterbook/commit/fecdd4353fb37f46d42de3b6da69d7d402b76742))


## v0.1.0 (2025-03-31)

### Features

- Initial release
  ([`2a257dd`](https://github.com/MicaelJarniac/repeaterbook/commit/2a257ddaada98ffa6871e607a868aabf6556bae1))


## v0.0.0 (2025-03-21)
