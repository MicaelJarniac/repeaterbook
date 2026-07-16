# Promote the neutral repeater-spec contract into core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the neutral `RepeaterSpec` contract out of `repeaterbook.mcp` into the core library as a discriminated union that carries per-mode parameters, and expose it as derived accessors on `Repeater`.

**Scope:** This plan covers **only the `repeaterbook` (producer) side**. The FTM-150 consumer changes (adopting `params`, deriving channel narrow/wide from `params.bandwidth_khz`) are handed off as a separate work item — see the cross-repo note below. FTM-150's schema is independent of this work, so the two do not need to land in lockstep; only the `params` **shape** is a shared contract.

**Architecture:** `RepeaterSpec` becomes a `mode`-discriminated union of thin per-mode subclasses, each pairing `mode: Literal[...]` with a typed, `extra="forbid"` `params` object. `Repeater`'s flat indexed columns are untouched; it gains read-only `@property` accessors that return the same param models. The mapper is rebuilt on those accessors.

**Tech Stack:** Python ≥3.11, pydantic v2 (via sqlmodel), SQLModel, hatchling.

**Design doc:** `docs/superpowers/specs/2026-07-14-promote-repeater-spec-to-core-design.md`

**FTM-150 handoff:** `FTM-150_format/docs/superpowers/plans/2026-07-15-repeater-spec-params-handoff.md` (in the FTM-150 repo).

## Global Constraints

- Python floor is `>=3.11` (`pyproject.toml:21`). `StrEnum` and `X | None` unions are available; use them.
- The MCP subpackage is **unreleased** (0.6.0 predates it). **No back-compat shims** — delete `repeaterbook/mcp/models.py` and `repeaterbook/mcp/mapper.py` outright.
- `Repeater`'s columns and indexes must **not** change. No Alembic/DDL migration. Accessors are `@property` only.
- The contract's **wire JSON must not change** for existing fields: `operational_status` stays the string `"ON_AIR"` (not an int), `use` stays `"OPEN"`, decimals stay strings. This is why status/use are typed as `Literal[...name...]`, **not** as the `Status`/`Use` enums (pydantic would serialize those by their integer `auto()` value).
- `extra="forbid"` on every param model is **mandatory**, not stylistic — it is the only thing that makes a mode/params mismatch fail validation and makes the generated schema emit `additionalProperties: false`. A test asserts this; do not remove it to make a test pass.
- Run tests with the venv binaries: `.venv/bin/pytest`. `uv` is not installed.
- Commit after every task.

## Circular-import rule (read before Task 1)

The dependency direction is one-way: **`models.py` imports param models from `spec.py`; `spec.py` never imports `models.py` at module load time.**

- `spec.py` may reference `Repeater` **only** under `if TYPE_CHECKING:`.
- `spec.py`'s `freq_to_band` needs `Bands` from `queries.py`, and `queries.py` imports `models.py`. To avoid pulling `models.py` in while it is mid-import, **import `Bands` lazily inside `freq_to_band`**, not at module top.
- Status/use are `Literal` string aliases in `spec.py`, so `spec.py` needs no runtime import of the `Status`/`Use` enums.

This exact two-module graph was prototyped and verified to import cleanly in both orders.

## File map (repeaterbook, producer)

- Create: `src/repeaterbook/spec.py` — the whole contract + mapper.
- Create: `src/repeaterbook/schemas/repeater_spec.schema.json` — moved + regenerated.
- Modify: `src/repeaterbook/models.py` — add accessors + `modes` property on `Repeater`.
- Modify: `src/repeaterbook/mcp/__init__.py`, `mcp/server.py`, `mcp/service.py` — imports.
- Delete: `src/repeaterbook/mcp/models.py`, `src/repeaterbook/mcp/mapper.py`, `src/repeaterbook/mcp/schemas/`.
- Modify: `pyproject.toml:53` — console-script target.
- Create/move tests: `tests/test_spec.py` (from `tests/mcp/test_models.py`, `test_mapper.py`, `test_schema_contract.py`), `tests/test_entry_points.py` (from `tests/mcp/`).

---

### Task 1: The contract module `spec.py`

**Files:**
- Create: `src/repeaterbook/spec.py`
- Create: `src/repeaterbook/schemas/repeater_spec.schema.json` (generated in Step 7)
- Test: `tests/test_spec.py`
- Delete at end: none yet (mcp/models.py deleted in Task 4)

**Interfaces:**
- Produces: `RepeaterMode(StrEnum)`; param models `FmParams, DmrParams, DStarParams, FusionParams, P25Params, NxdnParams, TetraParams, M17Params` (all pydantic `BaseModel`, `extra="forbid"`); `StatusName`/`UseName` Literal aliases; per-mode specs `FmSpec…M17Spec`; `RepeaterSpec` (Annotated discriminated-union TypeAlias); `repeater_spec_json_schema() -> dict`; `write_schema() -> None`; `schema_path() -> Path`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_spec.py`:

```python
"""Tests for the core RepeaterSpec contract."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import get_args

import jsonschema
import pytest
from pydantic import ValidationError

from repeaterbook.models import Status, Use
from repeaterbook.spec import (
    DmrParams,
    DmrSpec,
    FmParams,
    FmSpec,
    RepeaterMode,
    StatusName,
    UseName,
    repeater_spec_json_schema,
    schema_path,
)


def test_repeater_mode_members() -> None:
    assert {m.value for m in RepeaterMode} == {
        "FM", "DMR", "DSTAR", "FUSION", "P25", "NXDN", "TETRA", "M17",
    }


def test_status_use_literals_match_enums() -> None:
    # The wire uses the enum *names*; guard against drift.
    assert set(get_args(StatusName)) == {s.name for s in Status}
    assert set(get_args(UseName)) == {u.name for u in Use}


def test_fm_spec_defaults_and_wire_shape() -> None:
    spec = FmSpec(
        name="VK4RBN",
        callsign="VK4RBN",
        rx_frequency_mhz=Decimal("146.700"),
        tx_frequency_mhz=Decimal("146.100"),
        ctcss_tx_hz=Decimal("91.5"),
        ctcss_rx_hz=None,
        dcs_code=None,
        latitude=Decimal("-27.47"),
        longitude=Decimal("153.02"),
        distance_km=12.3,
        operational_status="ON_AIR",
        use="OPEN",
        band="M_2",
        notes=None,
        last_update="2026-01-01",
        source_id="QLD:42",
        params=FmParams(bandwidth_khz=Decimal("25.0")),
    )
    payload = json.loads(spec.model_dump_json())
    assert payload["mode"] == "FM"
    assert payload["source"] == "repeaterbook"
    assert payload["operational_status"] == "ON_AIR"  # name, NOT an int
    assert payload["params"] == {"bandwidth_khz": "25.0"}


def test_dmr_spec_carries_color_code() -> None:
    spec = DmrSpec(
        name="VK4RDM",
        callsign="VK4RDM",
        rx_frequency_mhz=Decimal("439.000"),
        tx_frequency_mhz=Decimal("434.000"),
        ctcss_tx_hz=None,
        ctcss_rx_hz=None,
        dcs_code=None,
        latitude=Decimal("-27.5"),
        longitude=Decimal("153.0"),
        distance_km=None,
        operational_status="ON_AIR",
        use="OPEN",
        band="CM_70",
        notes=None,
        last_update="2026-01-01",
        source_id="QLD:99",
        params=DmrParams(dmr_id="5051", color_code="1"),
    )
    assert spec.params.color_code == "1"


def test_extra_key_on_params_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FmParams(color_code="1")  # type: ignore[call-arg]


def test_schema_rejects_mode_params_mismatch() -> None:
    schema = repeater_spec_json_schema()
    bad = {
        "name": "x", "callsign": None,
        "rx_frequency_mhz": "146.7", "tx_frequency_mhz": "146.1",
        "ctcss_tx_hz": None, "ctcss_rx_hz": None, "dcs_code": None,
        "latitude": "-27.4", "longitude": "153.0", "distance_km": None,
        "operational_status": "ON_AIR", "use": "OPEN", "band": "M_2",
        "notes": None, "last_update": "2026-01-01", "source_id": "QLD:1",
        "mode": "FM", "params": {"color_code": "1"},  # FM can't have a color code
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_committed_schema_matches_model() -> None:
    committed = json.loads(schema_path().read_text(encoding="utf-8"))
    assert committed == repeater_spec_json_schema()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_spec.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'repeaterbook.spec'`.

- [ ] **Step 3: Write `src/repeaterbook/spec.py`**

```python
"""Neutral, source-agnostic repeater-spec contract and its mapper.

One RepeaterSpec is one programmable radio channel. A multi-mode repeater
expands to one spec per mode. `mode` discriminates a union whose `params`
object carries exactly that mode's parameters; `extra="forbid"` on each
params model is what makes a mode/params mismatch illegal by construction.
"""

from __future__ import annotations

__all__: tuple[str, ...] = (
    "DmrParams",
    "DmrSpec",
    "DStarParams",
    "DStarSpec",
    "FmParams",
    "FmSpec",
    "FusionParams",
    "FusionSpec",
    "M17Params",
    "M17Spec",
    "NxdnParams",
    "NxdnSpec",
    "P25Params",
    "P25Spec",
    "RepeaterMode",
    "RepeaterSpec",
    "StatusName",
    "TetraParams",
    "TetraSpec",
    "UseName",
    "freq_to_band",
    "parse_tone",
    "repeater_spec_json_schema",
    "repeater_to_specs",
    "schema_path",
    "write_schema",
)

import json
from datetime import date  # noqa: TC003
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

if TYPE_CHECKING:
    from repeaterbook.models import Repeater


class RepeaterMode(StrEnum):
    """A single radio operating mode for one programmable channel."""

    FM = "FM"
    DMR = "DMR"
    DSTAR = "DSTAR"
    FUSION = "FUSION"
    P25 = "P25"
    NXDN = "NXDN"
    TETRA = "TETRA"
    M17 = "M17"


# Wire uses the *names* of the core Status/Use enums (e.g. "ON_AIR", "OPEN").
# Typing these as the enums themselves would serialize their integer auto()
# values instead; test_status_use_literals_match_enums guards against drift.
StatusName: TypeAlias = Literal["OFF_AIR", "ON_AIR", "UNKNOWN"]
UseName: TypeAlias = Literal["OPEN", "PRIVATE", "CLOSED"]


class _Params(BaseModel):
    """Base for per-mode parameter blocks. Forbids unknown keys."""

    model_config = ConfigDict(extra="forbid")


class FmParams(_Params):
    bandwidth_khz: Decimal | None = None


class DmrParams(_Params):
    dmr_id: str | None = None
    color_code: str | None = None


class DStarParams(_Params):
    """RepeaterBook carries no D-STAR parameters; intentionally empty."""


class FusionParams(_Params):
    digital_id_uplink: str | None = None
    digital_id_downlink: str | None = None
    dsc: str | None = None


class P25Params(_Params):
    nac: str | None = None


class NxdnParams(_Params):
    """RepeaterBook carries no NXDN parameters; intentionally empty."""


class TetraParams(_Params):
    mcc: str | None = None
    mnc: str | None = None


class M17Params(_Params):
    can: str | None = None


class _BaseSpec(BaseModel):
    """Fields common to every mode."""

    name: str
    callsign: str | None
    rx_frequency_mhz: Decimal
    tx_frequency_mhz: Decimal
    ctcss_tx_hz: Decimal | None
    ctcss_rx_hz: Decimal | None
    dcs_code: str | None
    latitude: Decimal
    longitude: Decimal
    distance_km: float | None
    operational_status: StatusName
    use: UseName
    band: str | None
    notes: str | None
    last_update: date
    source: str = "repeaterbook"
    source_id: str


class FmSpec(_BaseSpec):
    mode: Literal[RepeaterMode.FM] = RepeaterMode.FM
    params: FmParams = FmParams()


class DmrSpec(_BaseSpec):
    mode: Literal[RepeaterMode.DMR] = RepeaterMode.DMR
    params: DmrParams = DmrParams()


class DStarSpec(_BaseSpec):
    mode: Literal[RepeaterMode.DSTAR] = RepeaterMode.DSTAR
    params: DStarParams = DStarParams()


class FusionSpec(_BaseSpec):
    mode: Literal[RepeaterMode.FUSION] = RepeaterMode.FUSION
    params: FusionParams = FusionParams()


class P25Spec(_BaseSpec):
    mode: Literal[RepeaterMode.P25] = RepeaterMode.P25
    params: P25Params = P25Params()


class NxdnSpec(_BaseSpec):
    mode: Literal[RepeaterMode.NXDN] = RepeaterMode.NXDN
    params: NxdnParams = NxdnParams()


class TetraSpec(_BaseSpec):
    mode: Literal[RepeaterMode.TETRA] = RepeaterMode.TETRA
    params: TetraParams = TetraParams()


class M17Spec(_BaseSpec):
    mode: Literal[RepeaterMode.M17] = RepeaterMode.M17
    params: M17Params = M17Params()


RepeaterSpec: TypeAlias = Annotated[
    FmSpec
    | DmrSpec
    | DStarSpec
    | FusionSpec
    | P25Spec
    | NxdnSpec
    | TetraSpec
    | M17Spec,
    Field(discriminator="mode"),
]

_ADAPTER: TypeAdapter[RepeaterSpec] = TypeAdapter(RepeaterSpec)


def repeater_spec_json_schema() -> dict[str, object]:
    """Return the JSON Schema for the RepeaterSpec union."""
    return _ADAPTER.json_schema()


def schema_path() -> Path:
    """Return the path to the published repeater-spec JSON Schema."""
    return Path(__file__).parent / "schemas" / "repeater_spec.schema.json"


def write_schema() -> None:
    """Regenerate the published JSON Schema from the model."""
    path = schema_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(repeater_spec_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )


def parse_tone(raw: str | None) -> tuple[Decimal | None, str | None]:
    """Split a RepeaterBook tone string into (ctcss_hz, dcs_code).

    RepeaterBook mixes CTCSS frequencies and DCS codes in one string field.
    Rule: "." -> CTCSS Decimal; "D"/"d" prefix -> DCS (letter stripped+uppercased);
    all-digits -> DCS; else (None, None).
    """
    if raw is None or not (value := raw.strip()):
        return (None, None)
    if "." in value:
        try:
            return (Decimal(value), None)
        except InvalidOperation:
            return (None, None)
    if value[0] in {"D", "d"}:
        return (None, value[1:].upper())
    if value.isdigit():
        return (None, value)
    return (None, None)


def freq_to_band(freq: Decimal) -> str | None:
    """Return the amateur band name for a frequency, or None if unknown."""
    from repeaterbook.queries import Bands  # lazy: breaks a models<->spec cycle

    for b in Bands:
        if b.low <= freq <= b.high:
            return b.name
    return None


# Maps a mode to (Spec subclass, Repeater accessor attribute).
_MODE_DISPATCH: dict[RepeaterMode, tuple[type[_BaseSpec], str]] = {
    RepeaterMode.FM: (FmSpec, "fm"),
    RepeaterMode.DMR: (DmrSpec, "dmr"),
    RepeaterMode.DSTAR: (DStarSpec, "dstar"),
    RepeaterMode.FUSION: (FusionSpec, "fusion"),
    RepeaterMode.P25: (P25Spec, "p25"),
    RepeaterMode.NXDN: (NxdnSpec, "nxdn"),
    RepeaterMode.TETRA: (TetraSpec, "tetra"),
    RepeaterMode.M17: (M17Spec, "m17"),
}


def repeater_to_specs(
    rep: Repeater,
    distance_km: float | None = None,
) -> list[RepeaterSpec]:
    """Expand one repeater into one spec per supported mode."""
    ctcss_tx, dcs_tx = parse_tone(rep.pl_ctcss_uplink)
    ctcss_rx, dcs_rx = parse_tone(rep.pl_ctcss_tsq_downlink)
    common: dict[str, object] = {
        "name": rep.callsign or rep.location_nearest_city,
        "callsign": rep.callsign,
        "rx_frequency_mhz": rep.frequency,
        "tx_frequency_mhz": rep.input_frequency,
        "ctcss_tx_hz": ctcss_tx,
        "ctcss_rx_hz": ctcss_rx,
        "dcs_code": dcs_tx or dcs_rx,
        "latitude": rep.latitude,
        "longitude": rep.longitude,
        "distance_km": distance_km,
        "operational_status": rep.operational_status.name,
        "use": rep.use_membership.name,
        "band": freq_to_band(rep.frequency),
        "notes": rep.notes,
        "last_update": rep.last_update,
        "source_id": f"{rep.state_id}:{rep.repeater_id}",
    }
    modes = list(rep.modes) or [RepeaterMode.FM]
    specs: list[RepeaterSpec] = []
    for mode in modes:
        spec_cls, accessor = _MODE_DISPATCH[mode]
        params = getattr(rep, accessor) or spec_cls.model_fields["params"].default
        specs.append(spec_cls(**common, params=params))
    return specs
```

- [ ] **Step 4: Run non-schema tests to verify they pass**

Run: `.venv/bin/pytest tests/test_spec.py -q -k "not committed_schema"`
Expected: PASS for the mode/params/literal/mismatch tests. (`test_committed_schema_matches_model` still fails — schema not written yet.)

- [ ] **Step 5: Move the schema file and regenerate it**

```bash
git mv src/repeaterbook/mcp/schemas/repeater_spec.schema.json src/repeaterbook/schemas/repeater_spec.schema.json
.venv/bin/python -c "from repeaterbook.spec import write_schema; write_schema()"
```

- [ ] **Step 6: Run the full spec test file**

Run: `.venv/bin/pytest tests/test_spec.py -q`
Expected: PASS (all, including `test_committed_schema_matches_model`).
Sanity-check the regenerated file contains a discriminated union:
Run: `.venv/bin/python -c "import json; s=json.load(open('src/repeaterbook/schemas/repeater_spec.schema.json')); print('oneOf' in s, s.get('discriminator',{}).get('propertyName'))"`
Expected: `True mode`

- [ ] **Step 7: Commit**

```bash
git add src/repeaterbook/spec.py src/repeaterbook/schemas/repeater_spec.schema.json tests/test_spec.py
git commit -m "feat(spec): core RepeaterSpec discriminated-union contract with per-mode params"
```

---

### Task 2: Derived accessors on `Repeater`

**Files:**
- Modify: `src/repeaterbook/models.py` (add imports + accessors on `Repeater`, after the frequency validator ~line 159)
- Test: `tests/test_models.py` (append)

**Interfaces:**
- Consumes: param models + `RepeaterMode` from `repeaterbook.spec` (Task 1).
- Produces: `Repeater.fm/dmr/dstar/fusion/p25/nxdn/tetra/m17 -> <ModeParams> | None`; `Repeater.modes -> frozenset[RepeaterMode]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_models.py`:

```python
def test_repeater_dmr_accessor_returns_none_when_incapable(sample_repeater):
    rep = sample_repeater(dmr_capable=False, dmr_color_code="1")
    assert rep.dmr is None


def test_repeater_dmr_accessor_populates_params(sample_repeater):
    from repeaterbook.spec import DmrParams

    rep = sample_repeater(dmr_capable=True, dmr_id="5051", dmr_color_code="1")
    assert rep.dmr == DmrParams(dmr_id="5051", color_code="1")


def test_repeater_fm_accessor_carries_bandwidth(sample_repeater):
    from decimal import Decimal
    from repeaterbook.spec import FmParams

    rep = sample_repeater(analog_capable=True, fm_bandwidth=Decimal("12.5"))
    assert rep.fm == FmParams(bandwidth_khz=Decimal("12.5"))


def test_repeater_modes_reflects_capabilities(sample_repeater):
    from repeaterbook.spec import RepeaterMode

    rep = sample_repeater(analog_capable=True, yaesu_system_fusion_capable=True)
    assert rep.modes == frozenset({RepeaterMode.FM, RepeaterMode.FUSION})


def test_accessors_do_not_change_persistence_surface(sample_repeater):
    # The accessors must be invisible to SQL/pydantic: no new column, no new field.
    from repeaterbook.models import Repeater

    columns = {c.name for c in Repeater.__table__.columns}
    assert "dmr" not in columns and "fm" not in columns and "modes" not in columns
    assert "dmr" not in Repeater.model_fields
    rep = sample_repeater(dmr_capable=True, dmr_id="5051")
    assert "dmr" not in rep.model_dump()
```

If `tests/test_models.py` has no `sample_repeater` fixture, add this factory at the top of the file (mirrors the base dict from the old `tests/mcp/test_mapper.py`):

```python
import pytest
from datetime import date
from decimal import Decimal
from repeaterbook.models import Repeater, Status, Use


@pytest.fixture
def sample_repeater():
    def _make(**overrides: object) -> Repeater:
        base: dict[str, object] = {
            "state_id": "QLD", "repeater_id": 42,
            "frequency": Decimal("146.700"), "input_frequency": Decimal("146.100"),
            "pl_ctcss_uplink": "91.5", "pl_ctcss_tsq_downlink": None,
            "location_nearest_city": "Brisbane", "landmark": None, "region": None,
            "country": "Australia", "county": None, "state": "Queensland",
            "latitude": Decimal("-27.47"), "longitude": Decimal("153.02"),
            "precise": True, "callsign": "VK4RBN",
            "use_membership": Use.OPEN, "operational_status": Status.ON_AIR,
            "ares": None, "races": None, "skywarn": None, "canwarn": None,
            "allstar_node": None, "echolink_node": None, "irlp_node": None,
            "wires_node": None, "dmr_capable": False, "dmr_id": None,
            "dmr_color_code": None, "d_star_capable": False, "nxdn_capable": False,
            "apco_p_25_capable": False, "p_25_nac": None, "m17_capable": False,
            "m17_can": None, "tetra_capable": False, "tetra_mcc": None,
            "tetra_mnc": None, "yaesu_system_fusion_capable": False,
            "ysf_digital_id_uplink": None, "ysf_digital_id_downlink": None,
            "ysf_dsc": None, "analog_capable": True, "fm_bandwidth": Decimal("25.0"),
            "notes": None, "last_update": date(2026, 1, 1),
        }
        base.update(overrides)
        return Repeater(**base)

    return _make
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_models.py -q -k "accessor or modes or persistence"`
Expected: FAIL — `AttributeError: 'Repeater' object has no attribute 'dmr'`.

- [ ] **Step 3: Add accessors to `Repeater`**

Add to `src/repeaterbook/models.py`. At the top, alongside the other imports (these are runtime imports; `spec.py` does not import `models.py` at load time, so this is safe):

```python
from repeaterbook.spec import (
    DmrParams,
    DStarParams,
    FmParams,
    FusionParams,
    M17Params,
    NxdnParams,
    P25Params,
    RepeaterMode,
    TetraParams,
)
```

Add these methods to the `Repeater` class, after `validate_frequency` (~line 159):

```python
    @property
    def fm(self) -> FmParams | None:
        """FM parameters, or None if not FM-capable."""
        if not self.analog_capable:
            return None
        return FmParams(bandwidth_khz=self.fm_bandwidth)

    @property
    def dmr(self) -> DmrParams | None:
        if not self.dmr_capable:
            return None
        return DmrParams(dmr_id=self.dmr_id, color_code=self.dmr_color_code)

    @property
    def dstar(self) -> DStarParams | None:
        return DStarParams() if self.d_star_capable else None

    @property
    def fusion(self) -> FusionParams | None:
        if not self.yaesu_system_fusion_capable:
            return None
        return FusionParams(
            digital_id_uplink=self.ysf_digital_id_uplink,
            digital_id_downlink=self.ysf_digital_id_downlink,
            dsc=self.ysf_dsc,
        )

    @property
    def p25(self) -> P25Params | None:
        return P25Params(nac=self.p_25_nac) if self.apco_p_25_capable else None

    @property
    def nxdn(self) -> NxdnParams | None:
        return NxdnParams() if self.nxdn_capable else None

    @property
    def tetra(self) -> TetraParams | None:
        if not self.tetra_capable:
            return None
        return TetraParams(mcc=self.tetra_mcc, mnc=self.tetra_mnc)

    @property
    def m17(self) -> M17Params | None:
        return M17Params(can=self.m17_can) if self.m17_capable else None

    @property
    def modes(self) -> frozenset[RepeaterMode]:
        """The set of modes this repeater supports."""
        pairs = (
            (self.analog_capable, RepeaterMode.FM),
            (self.dmr_capable, RepeaterMode.DMR),
            (self.d_star_capable, RepeaterMode.DSTAR),
            (self.yaesu_system_fusion_capable, RepeaterMode.FUSION),
            (self.apco_p_25_capable, RepeaterMode.P25),
            (self.nxdn_capable, RepeaterMode.NXDN),
            (self.tetra_capable, RepeaterMode.TETRA),
            (self.m17_capable, RepeaterMode.M17),
        )
        return frozenset(mode for capable, mode in pairs if capable)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_models.py -q`
Expected: PASS (new accessor tests + all pre-existing model tests still green).

- [ ] **Step 5: Confirm no import cycle and no DDL change**

Run: `.venv/bin/python -c "import repeaterbook.models, repeaterbook.spec; print('import ok')"`
Run: `.venv/bin/python -c "import repeaterbook.spec, repeaterbook.models; print('reverse import ok')"`
Expected: both print `... ok` (no `ImportError`).

- [ ] **Step 6: Commit**

```bash
git add src/repeaterbook/models.py tests/test_models.py
git commit -m "feat(models): derived per-mode param accessors on Repeater"
```

---

### Task 3: Migrate mapper tests onto the core mapper

**Files:**
- Modify: `tests/test_spec.py` (append the migrated mapper tests)
- Delete: `tests/mcp/test_mapper.py`, `tests/mcp/test_models.py`
- Test: `tests/test_spec.py`

**Interfaces:**
- Consumes: `repeater_to_specs`, `parse_tone`, `freq_to_band` from `repeaterbook.spec`; `sample_repeater` factory.

- [ ] **Step 1: Add the migrated mapper tests**

Append to `tests/test_spec.py` (reuse the `sample_repeater` fixture — move it to `tests/conftest.py` if both test files need it; otherwise duplicate the factory shown in Task 2 Step 1):

```python
from decimal import Decimal
import pytest
from repeaterbook.spec import (
    RepeaterMode, freq_to_band, parse_tone, repeater_to_specs,
)


def test_freq_to_band() -> None:
    assert freq_to_band(Decimal("146.700")) == "M_2"
    assert freq_to_band(Decimal("438.000")) == "CM_70"
    assert freq_to_band(Decimal("27.000")) is None


def test_single_mode_expansion(sample_repeater) -> None:
    specs = repeater_to_specs(sample_repeater(), distance_km=5.0)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.mode is RepeaterMode.FM
    assert spec.name == "VK4RBN"
    assert spec.rx_frequency_mhz == Decimal("146.700")
    assert spec.tx_frequency_mhz == Decimal("146.100")
    assert spec.ctcss_tx_hz == Decimal("91.5")
    assert spec.band == "M_2"
    assert spec.distance_km == 5.0
    assert spec.source_id == "QLD:42"
    assert spec.operational_status == "ON_AIR"
    assert spec.use == "OPEN"
    assert spec.params.bandwidth_khz == Decimal("25.0")


def test_multi_mode_expansion_carries_per_mode_params(sample_repeater) -> None:
    specs = repeater_to_specs(sample_repeater(
        analog_capable=True, dmr_capable=True,
        dmr_id="5051", dmr_color_code="1",
    ))
    by_mode = {s.mode: s for s in specs}
    assert set(by_mode) == {RepeaterMode.FM, RepeaterMode.DMR}
    assert by_mode[RepeaterMode.DMR].params.color_code == "1"
    assert by_mode[RepeaterMode.FM].params.bandwidth_khz == Decimal("25.0")


def test_no_capability_defaults_to_fm(sample_repeater) -> None:
    specs = repeater_to_specs(sample_repeater(analog_capable=False))
    assert [s.mode for s in specs] == [RepeaterMode.FM]


def test_name_falls_back_to_city(sample_repeater) -> None:
    specs = repeater_to_specs(sample_repeater(callsign=None))
    assert specs[0].name == "Brisbane"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("91.5", (Decimal("91.5"), None)),
        ("100.0", (Decimal("100.0"), None)),
        ("D023", (None, "023")),
        ("023", (None, "023")),
        ("D023N", (None, "023N")),
        ("", (None, None)),
        (None, (None, None)),
        ("garbage", (None, None)),
    ],
)
def test_parse_tone(raw, expected) -> None:
    assert parse_tone(raw) == expected
```

Move the `sample_repeater` fixture from Task 2 into `tests/conftest.py` so both `test_models.py` and `test_spec.py` share it (delete the inline copy in `test_models.py` if you moved it).

- [ ] **Step 2: Delete the superseded mcp tests**

```bash
git rm tests/mcp/test_mapper.py tests/mcp/test_models.py
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_spec.py tests/test_models.py -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_spec.py tests/conftest.py tests/test_models.py
git commit -m "test(spec): migrate mapper/model tests, assert per-mode params flow"
```

---

### Task 4: Rewire MCP consumers, delete old modules, repoint console script

**Files:**
- Modify: `src/repeaterbook/mcp/__init__.py`, `src/repeaterbook/mcp/server.py`, `src/repeaterbook/mcp/service.py`
- Delete: `src/repeaterbook/mcp/models.py`, `src/repeaterbook/mcp/mapper.py`, `src/repeaterbook/mcp/schemas/`
- Modify: `pyproject.toml:53`
- Move: `tests/mcp/test_schema_contract.py` -> `tests/test_spec.py` coverage (already added in Task 1); `tests/mcp/test_entry_points.py` -> `tests/test_entry_points.py`

**Interfaces:**
- Consumes: `repeaterbook.spec` public API.

- [ ] **Step 1: Update the three import sites**

In `src/repeaterbook/mcp/__init__.py`, replace the import line:

```python
from repeaterbook.spec import RepeaterMode, RepeaterSpec
```

In `src/repeaterbook/mcp/service.py`, replace lines 12–13:

```python
from repeaterbook.spec import RepeaterMode, repeater_to_specs
```

and in its `TYPE_CHECKING` block replace `from repeaterbook.mcp.models import RepeaterSpec` with:

```python
    from repeaterbook.spec import RepeaterSpec
```

In `src/repeaterbook/mcp/server.py`, replace lines 24–27:

```python
from repeaterbook.spec import RepeaterMode, RepeaterSpec
```

- [ ] **Step 2: Delete the old modules**

```bash
git rm src/repeaterbook/mcp/models.py src/repeaterbook/mcp/mapper.py
git rm -r src/repeaterbook/mcp/schemas
```

- [ ] **Step 3: Repoint the console script**

In `pyproject.toml`, change line 53 from
`repeaterbook-write-schema = "repeaterbook.mcp.models:write_schema"` to:

```toml
repeaterbook-write-schema = "repeaterbook.spec:write_schema"
```

Then reinstall so the entry point re-registers:

Run: `.venv/bin/pip install -e . --no-deps -q`

- [ ] **Step 4: Move and update the entry-point test**

```bash
git rm tests/mcp/test_schema_contract.py
git mv tests/mcp/test_entry_points.py tests/test_entry_points.py
```

(The schema-contract assertion now lives in `tests/test_spec.py::test_committed_schema_matches_model`, so the old file is removed.)

Edit `tests/test_entry_points.py` to point at the new target:

```python
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
```

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS. If `tests/mcp/` MCP server/service/e2e tests import RepeaterSpec/RepeaterMode, they resolve via the rewired `mcp` package. Confirm no `ModuleNotFoundError: repeaterbook.mcp.models`.

- [ ] **Step 6: Grep for stragglers**

Run: `grep -rn "mcp.models\|mcp.mapper\|mcp import models\|mcp import mapper" src tests`
Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor(mcp): consume repeaterbook.spec; drop mcp.models/mapper; repoint write-schema"
```

---

## FTM-150 consumer work (handed off — out of scope for this plan)

The FTM-150 side is tracked separately in the FTM-150 repo:
`FTM-150_format/docs/superpowers/plans/2026-07-15-repeater-spec-params-handoff.md`.

That work adopts an optional `params` object in FTM-150's (independent, hand-written)
schema and derives channel narrow/wide from `params.bandwidth_khz`, replacing a hardcoded
wide-FM default. **Do not implement it from this repo.** The only shared obligation is the
`params` **shape** produced by Task 1's mapper — the per-mode keys below. If a key name
changes here, update the handoff doc so both sides stay in agreement:

| mode | params keys |
|---|---|
| FM | `bandwidth_khz` |
| DMR | `dmr_id`, `color_code` |
| DSTAR | *(empty)* |
| FUSION | `digital_id_uplink`, `digital_id_downlink`, `dsc` |
| P25 | `nac` |
| NXDN | *(empty)* |
| TETRA | `mcc`, `mnc` |
| M17 | `can` |

## Self-review notes (deviations from the spec, with rationale)

- **status/use typed as `Literal[...names...]`, not the `Status`/`Use` enums.** The spec said "type them as `Status`/`Use`". Pydantic serializes an `Enum` by `.value`, and those enums use integer `auto()`, which would turn `"ON_AIR"` into `1` and break both the "JSON unchanged" guarantee and the FTM-150 string consumer. The `Literal` of member names delivers the spec's *intent* (schema enum-constraint + unchanged wire string) and is drift-guarded by `test_status_use_literals_match_enums`. Verified empirically.
- **`freq_to_band` imports `Bands` lazily.** Required to break a `models <-> spec` import cycle (see the "Circular-import rule" section). Verified by importing both modules in both orders.
- **FTM-150 consumer work removed from this plan.** The design's §5 (re-vendor schema, carry `params`, derive narrow from bandwidth) is handed to a separate FTM-150 work item so that project's maintainer can independently decide why its schema is hand-written and looser than the generated one. Only the `params` **shape** produced by Task 1 is a shared obligation; it is restated in the "FTM-150 consumer work" section above.

## Spec coverage check

| Spec section | Task |
|---|---|
| §1 Placement (spec.py, delete mcp.models/mapper, move schema, repoint script) | 1, 4 |
| §2 Discriminated union + `params` + `extra="forbid"` + empty DSTAR/NXDN | 1 |
| §2 status/use constrained, `distance_km` retained | 1 |
| §3 `Repeater` accessors + `modes`, no migration, regression guard | 2 |
| §3 `repeater_to_specs` rebuilt on accessors | 1 (mapper), 3 (tests) |
| §4 `Mode`/`RepeaterMode` stay separate | untouched (no task needed) |
| §5 FTM-150 re-vendor + fixtures + narrow from bandwidth | handed off (out of scope) |
| §6 producer drift test moves to core; no version field | 1, 4 |
