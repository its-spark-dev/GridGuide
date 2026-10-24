"""Pole replacement labor and the pole-to-mounted-device bridge (AEP data guide §3).

Standalone module: it reuses data/spatial/damage helpers and changes none of them.

* Labor: workbook pole size groups (Labor time material related!A11:D14) and the
  crossarm row (A1:B3) are label-checked, then loaded as Recipe objects. Rates are
  source-derived; one pole and one crossarm per damaged pole are scenario assumptions
  (the guide: "assume the pole and associated hardware must be removed and replaced").
* Size: Pole_Clip ``height`` ("40 Feet") is mapped to the workbook's labeled ranges
  only. Unknown heights and heights outside every labeled range (for example 17 ft or
  36-39 ft) stay unavailable; no nearest size is substituted.
* Damage: ARCOS ``Asset_Type == "Pole"`` observations use the same nearest/runner-up
  proximity policy as backend.damage (the guide permits a nearest-pole assumption).
  A match is a disclosed spatial candidate, never a direct ARCOS identifier.
* Impact bridge: poles are absent from matched_upstream.txt. A pole links to customer
  dependencies only through devices whose exact ``location_n`` equals the pole's
  unique ``location_n`` and whose typed ID/type/location resolves in the topology.
  Complete reverse-dependency validation remains the network layer's responsibility.
  A pole with no such device has unavailable customer impact, never zero.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
import io
from pathlib import Path
import re
from typing import Literal
import zipfile

import openpyxl

from .config import RAW
from .data import (CheckpointError, NodeKey, Recipe, TopologyIndex, TopologyToken,
                   labor_decimal, layer, parse_topology, records, verify_sources)
from .damage import DAMAGE_POLICY, _metric_point, _require_wgs84
from .spatial import MetricPoint, MetricSpatialIndex, ProximityPolicy, classify_proximity

POLE_POLICY_VERSION = "pole-size-and-mounted-device-bridge-v1"
PoleSize = Literal["Small", "Medium", "Large"]
SIZE_ROWS: dict[PoleSize, int] = {"Small": 12, "Medium": 13, "Large": 14}
# Inclusive feet ranges, transcribed from the label-checked workbook text in column B.
SIZE_RANGES_FT: dict[PoleSize, tuple[int, int | None]] = {"Small": (25, 35), "Medium": (40, 55), "Large": (60, None)}
WORKBOOK_LABELS = {
    "A1": "Crossarm CU Average Hours", "A2": "Avg Install Hours", "B2": "Avg Removal Hours",
    "A10": "Pole CU Average Hours by Size", "A11": "Size Group", "B11": "Height Range",
    "C11": "Avg Install Hours", "D11": "Avg Removal Hours",
    "A12": "Small", "B12": "25–35 ft", "A13": "Medium", "B13": "40–55 ft", "A14": "Large", "B14": "60 ft and above",
}
MOUNTED_DEVICE_LAYERS = (  # (archive, stem, topology entity)
    ("Data2.zip", "Transformer_Clip", "eo_power_xfrmr_inst"),
    ("Data1.zip", "Fuse_Bank_Clip", "eo_isolating_eqpt_inst"),
    ("Data2.zip", "Recloser_Bank_Clip", "eo_isolating_eqpt_inst"),
    ("Data2.zip", "Switch_Clip", "eo_isolating_eqpt_inst"),
)
_HEIGHT = re.compile(r"^\s*(\d{1,3})\s+Feet\s*$")


# ---------------- labor (source-derived rates) ----------------
def read_pole_recipes(workbook: Path) -> tuple[Recipe, ...]:
    """Label-checked pole and crossarm recipes; install + remove = replacement."""
    with workbook.open("rb") as f:
        wb = openpyxl.load_workbook(f, data_only=False, read_only=True)
        try:
            sheet = wb["Labor time material related"]
            if any(sheet[cell].value != label for cell, label in WORKBOOK_LABELS.items()):
                raise CheckpointError("labor_schema_mismatch", "Pole/crossarm labor cells no longer have the documented labels.")
            ref = lambda cell: f"Labor time material related!{cell}"
            recipes = [Recipe(f"pole-{size.lower()}-replace", "Pole", labor_decimal(sheet[f"C{row}"].value),
                              labor_decimal(sheet[f"D{row}"].value), (ref(f"C{row}"), ref(f"D{row}")))
                       for size, row in SIZE_ROWS.items()]
            recipes.append(Recipe("crossarm-replace", "Crossarm", labor_decimal(sheet["A3"].value),
                                  labor_decimal(sheet["B3"].value), (ref("A3"), ref("B3"))))
            return tuple(recipes)
        finally:
            wb.close()


def parse_height_ft(value) -> int | None:
    """'40 Feet' -> 40. 'Unknown', blanks and other formats -> None."""
    match = _HEIGHT.match(value) if isinstance(value, str) else None
    return int(match.group(1)) if match else None


def size_group(height_ft: int | None) -> PoleSize | None:
    if height_ft is None:
        return None
    for size, (low, high) in SIZE_RANGES_FT.items():
        if height_ft >= low and (high is None or height_ft <= high):
            return size
    return None


@dataclass(frozen=True)
class PoleLabor:
    size: PoleSize
    recipe_ids: tuple[str, ...]
    install_hours: Decimal
    remove_hours: Decimal
    direct_hours: Decimal
    person_hours: Decimal
    source_refs: tuple[str, ...]
    rate_classification: Literal["source-derived"] = "source-derived"
    scope_classification: Literal["scenario assumption"] = "scenario assumption"


def pole_replacement_labor(recipes: tuple[Recipe, ...], size: PoleSize, indirect_multiplier: Decimal,
                           include_crossarm: bool = True) -> PoleLabor:
    """One pole (+ one crossarm) removed and replaced; x multiplier once -> person-hours."""
    by_id = {r.id: r for r in recipes}
    ids = (f"pole-{size.lower()}-replace",) + (("crossarm-replace",) if include_crossarm else ())
    if any(i not in by_id for i in ids):
        raise CheckpointError("unsupported_recipe", "A required pole recipe is missing.")
    if indirect_multiplier <= 0:
        raise CheckpointError("invalid_labor_rate", "Indirect labor multiplier must be positive.")
    install = sum((by_id[i].install_hours for i in ids), Decimal(0))
    remove = sum((by_id[i].remove_hours for i in ids), Decimal(0))
    direct = install + remove
    return PoleLabor(size, ids, install, remove, direct, direct * indirect_multiplier,
                     tuple(ref for i in ids for ref in by_id[i].source_refs))


# ---------------- private inventory ----------------
@dataclass(frozen=True)
class PoleRecord:
    row: int
    location: str = field(repr=False)
    point: tuple[float, float] = field(repr=False)
    height_ft: int | None = None
    size: PoleSize | None = None
    usage: str = ""


@dataclass(frozen=True)
class MountedDevice:
    row: int
    layer: str
    key: NodeKey = field(repr=False)
    kind: str = ""
    location: str = field(repr=False, default="")


@dataclass(frozen=True)
class PoleDamageMatch:
    """Private association evidence; not a public DTO and not an outage count."""

    source_row: int
    status: Literal["spatial_candidate", "unavailable"]
    pole_row: int | None
    distance_m: float | None
    runner_up_distance_m: float | None
    size: PoleSize | None
    labor_available: bool
    impact_basis: Literal["mounted_device_bridge", "unavailable"]
    device_keys: tuple[NodeKey, ...] = field(repr=False)
    reasons: tuple[str, ...]


class PoleMatcher:
    """Pure matching core so it can be tested without the pinned archives."""

    def __init__(self, poles: tuple[PoleRecord, ...], devices: tuple[MountedDevice, ...],
                 tokens: dict[NodeKey, TopologyToken], policy: ProximityPolicy = DAMAGE_POLICY):
        self.policy = policy
        self.poles = {str(i): p for i, p in enumerate(poles)}
        self.index = MetricSpatialIndex(tuple(MetricPoint(k, *p.point) for k, p in self.poles.items()))
        self.label_counts = Counter(p.location for p in poles)
        self.key_counts = Counter(d.key for d in devices)
        self.tokens = tokens
        self.devices_by_location: dict[str, list[MountedDevice]] = defaultdict(list)
        for device in devices:
            self.devices_by_location[device.location].append(device)

    def resolved_devices(self, pole: PoleRecord) -> tuple[tuple[NodeKey, ...], tuple[str, ...]]:
        """Devices sharing this pole's unique label whose typed identity resolves in topology."""
        reasons: list[str] = []
        if self.label_counts[pole.location] != 1:
            return (), ("pole_location_label_not_unique",)
        mounted = self.devices_by_location.get(pole.location, [])
        if not mounted:
            return (), ("no_mounted_device_on_pole",)
        keys = []
        for device in mounted:
            token = self.tokens.get(device.key)
            if (self.key_counts[device.key] != 1 or token is None or token.kind != device.kind
                    or token.location_code != device.location):
                reasons.append("unresolved_mounted_device_identity")
            else:
                keys.append(device.key)
        # Any unresolved device on the pole withholds the bridge: impact would be partial.
        return (() if reasons else tuple(sorted(set(keys)))), tuple(sorted(set(reasons)))

    def match(self, source_row: int, point: tuple[float, float]) -> PoleDamageMatch:
        proximity = classify_proximity(self.index, point, self.policy)
        nearest = proximity.nearest
        if proximity.status != "spatial_proxy":
            return PoleDamageMatch(source_row, "unavailable", None,
                                   nearest.distance_m if nearest else None,
                                   proximity.runner_up.distance_m if proximity.runner_up else None,
                                   None, False, "unavailable", (), ("pole_" + proximity.status,))
        pole = self.poles[nearest.key]
        reasons = [] if pole.size else ["pole_size_unavailable"]
        keys, bridge_reasons = self.resolved_devices(pole)
        reasons += bridge_reasons
        return PoleDamageMatch(source_row, "spatial_candidate", pole.row, nearest.distance_m,
                               proximity.runner_up.distance_m if proximity.runner_up else None,
                               pole.size, pole.size is not None,
                               "mounted_device_bridge" if keys else "unavailable", keys, tuple(reasons))


# ---------------- preparation from the pinned sources ----------------
@dataclass(frozen=True)
class PoleAudit:
    recipes: tuple[Recipe, ...]
    matches: tuple[PoleDamageMatch, ...] = field(repr=False)
    pole_count: int
    size_counts: tuple[tuple[str, int], ...]
    policy: ProximityPolicy
    policy_version: str = POLE_POLICY_VERSION

    def safe_summary(self) -> dict:
        """Aggregate allowlist: no row locators, keys or coordinates."""
        m = self.matches
        return {
            "policy_version": self.policy_version,
            "pole_inventory": self.pole_count,
            "pole_size_groups": dict(self.size_counts),
            "arcos_pole_observations": len(m),
            "spatial_candidates": sum(x.status == "spatial_candidate" for x in m),
            "candidates_with_labor": sum(x.labor_available for x in m),
            "candidates_with_device_bridge": sum(x.impact_basis == "mounted_device_bridge" for x in m),
            "reasons": dict(sorted(Counter(r for x in m for r in x.reasons).items())),
            "max_distance_m": self.policy.max_distance_m,
            "min_runner_up_gap_m": self.policy.min_runner_up_gap_m,
            "classification": "prototype policy",
            "historical_only": True,
            "direct_identifier_join": False,
            "reverse_dependencies_validated": False,
        }


def prepare_pole_audit(raw: Path = RAW, topology: TopologyIndex | None = None,
                       policy: ProximityPolicy = DAMAGE_POLICY) -> PoleAudit:
    verify_sources(raw)
    if topology is None:
        with zipfile.ZipFile(raw / "matched_upstream.zip") as z:
            with z.open("matched_upstream.txt") as stream:
                topology = parse_topology(io.TextIOWrapper(stream, encoding="utf-8-sig"))
    tokens = {t.key: t for path in topology.paths.values() for t in path}
    recipes = read_pole_recipes(raw / "Install_Labor_HackOHIO.xlsx")

    poles = []
    with layer(raw, "Data1.zip", "Pole_Clip", geometry=True) as (reader, z):
        _require_wgs84(z, "Pole_Clip")
        for i, r in enumerate(records(reader, ("location_n", "height", "usage"))):
            height = parse_height_ft(r["height"])
            poles.append(PoleRecord(i + 1, r["location_n"], _metric_point(reader, i), height, size_group(height), r["usage"]))

    devices = []
    for archive, stem, entity in MOUNTED_DEVICE_LAYERS:
        with layer(raw, archive, stem) as (reader, _):
            for i, r in enumerate(records(reader, ("id", "device_typ", "location_n"))):
                devices.append(MountedDevice(i + 1, stem, (entity, str(r["id"])), r["device_typ"], r["location_n"]))

    matcher = PoleMatcher(tuple(poles), tuple(devices), tokens, policy)
    matches = []
    with layer(raw, "Data1.zip", "arcos_prod_damage_09_28_Clip", geometry=True) as (reader, z):
        _require_wgs84(z, "arcos_prod_damage_09_28_Clip")
        for i, r in enumerate(records(reader, ("Asset_Type",))):
            if r["Asset_Type"] == "Pole":
                matches.append(matcher.match(i + 1, _metric_point(reader, i)))
    sizes = Counter(p.size or "unavailable" for p in poles)
    return PoleAudit(recipes, tuple(matches), len(poles), tuple(sorted(sizes.items())), policy)


if __name__ == "__main__":
    import json
    from .data import read_labor
    audit = prepare_pole_audit()
    ilm = read_labor(RAW).indirect_multiplier
    print(json.dumps(audit.safe_summary(), indent=2))
    for size in SIZE_ROWS:
        labor = pole_replacement_labor(audit.recipes, size, ilm)
        print(f"{size:<6} pole + crossarm: {labor.direct_hours.normalize()} direct h x {ilm.normalize()} "
              f"= {labor.person_hours.quantize(Decimal('0.001'))} person-hours  [{', '.join(labor.source_refs)}]")