"""Contract test: the committed JSON Schema must match the live model."""

from __future__ import annotations

import json

from repeaterbook.mcp.models import RepeaterSpec, schema_path


def test_committed_schema_matches_model() -> None:
    """Verify the committed JSON Schema matches the live RepeaterSpec model."""
    committed = json.loads(schema_path().read_text(encoding="utf-8"))
    assert committed == RepeaterSpec.model_json_schema()
