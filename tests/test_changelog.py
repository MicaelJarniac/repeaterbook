"""Guard the contract between docs/CHANGELOG.md and python-semantic-release.

PSR runs the changelog in ``update`` mode: it splits the existing file on the
``insertion_flag`` and writes the new release between the two halves. If the
flag is missing, the file is written back unchanged and nothing warns about it,
which is how v0.8.0 through v0.11.1 never made it into the changelog (#74).
These tests fail the build instead.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def pyproject() -> dict[str, object]:
    """The parsed pyproject.toml."""
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


@pytest.fixture(scope="module")
def changelog_config(pyproject: dict[str, object]) -> dict[str, object]:
    """The ``[tool.semantic_release.changelog]`` table."""
    tool = pyproject["tool"]
    assert isinstance(tool, dict)
    changelog = tool["semantic_release"]["changelog"]
    assert isinstance(changelog, dict)
    return changelog


@pytest.fixture(scope="module")
def changelog_text(changelog_config: dict[str, object]) -> str:
    """Contents of the changelog file PSR is configured to write."""
    templates = changelog_config["default_templates"]
    assert isinstance(templates, dict)
    changelog_file = templates["changelog_file"]
    assert isinstance(changelog_file, str)
    return (REPO_ROOT / changelog_file).read_text(encoding="utf-8")


def test_changelog_mode_is_pinned_to_update(
    changelog_config: dict[str, object],
) -> None:
    """The mode is explicit, so a future PSR default flip cannot change behavior."""
    assert changelog_config["mode"] == "update"


def test_changelog_carries_the_insertion_flag_below_the_title(
    changelog_config: dict[str, object], changelog_text: str
) -> None:
    """Update mode splices new releases in at the flag, so it must be present.

    It must also sit directly under the title: PSR emits the header, the flag,
    then the newest release, so anything between the flag and the first
    ``## v`` heading would be pushed below every future entry.
    """
    flag = changelog_config["insertion_flag"]
    assert isinstance(flag, str)

    assert changelog_text.count(flag) == 1, "exactly one insertion flag expected"
    flag_at = changelog_text.index(flag)
    first_release_at = changelog_text.index("\n## v")
    assert flag_at < first_release_at, "flag must precede the newest release"
    assert changelog_text[:flag_at].strip() == "# CHANGELOG", (
        "only the title belongs above the insertion flag"
    )
    assert changelog_text[flag_at + len(flag) : first_release_at].strip() == "", (
        "nothing belongs between the insertion flag and the newest release"
    )


def test_current_version_is_recorded(
    pyproject: dict[str, object], changelog_text: str
) -> None:
    """The released version in pyproject.toml has a changelog heading.

    PSR bumps the version and writes the changelog in the same release commit,
    so a version without a heading means the changelog step silently did
    nothing. Reading the version from pyproject.toml rather than git tags keeps
    the test meaningful in a shallow checkout.
    """
    project = pyproject["project"]
    assert isinstance(project, dict)
    version = project["version"]
    assert f"\n## v{version} (" in changelog_text, (
        f"v{version} is missing from the changelog"
    )
