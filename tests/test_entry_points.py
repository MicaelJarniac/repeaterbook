"""Guard the console-script entry points declared in pyproject.toml."""

from __future__ import annotations

import importlib.metadata as md

from repeaterbook.spec import write_schema


def test_write_schema_console_script_registered() -> None:
    """`repeaterbook-write-schema` resolves to spec.write_schema."""
    eps = md.entry_points(group="console_scripts")
    ep = next((e for e in eps if e.name == "repeaterbook-write-schema"), None)
    assert ep is not None, "repeaterbook-write-schema entry point not registered"
    assert ep.value == "repeaterbook.spec:write_schema"
    assert ep.load() is write_schema
