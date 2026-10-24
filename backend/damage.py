"""Historical ARCOS spatial candidates, never current outage or confirmed damage IDs.

All exact identifiers and coordinates stay in private preparation. A permitted
nearest-pole hypothesis is combined with a unique pole location-label bridge and
same-type/circuit/station device proximity. Even an exact coordinate coincidence
is a spatial candidate, not a direct ARCOS identifier join. Complete reverse
customer validation belongs to the network layer and is deliberately separate.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
import io
from pathlib import Path
from typing import Literal
import xml.etree.ElementTree as ET
import zipfile

from pyproj import CRS

from .config import RAW
from .data import (CheckpointError, NodeKey, TopologyIndex, TopologyToken, layer,
                   parse_topology, records, verify_sources)
from .spatial import (MetricPoint, MetricSpatialIndex, ProximityPolicy,
                      classify_proximity, wgs84_to_metric)

DAMAGE_POLICY_VERSION = "historical-pole-device-spatial-v1"
DAMAGE_POLICY = ProximityPolicy(max_distance_m=25.0, min_runner_up_gap_m=10.0)
DAMAGE_METHOD = "same_type_circuit_station_and_nearest_pole_location_bridge"
SUPPORTED_TYPES = {
    "Transformer": ("eo_power_xfrmr_inst", "Distribution"),
    "Fuse Bank": ("eo_isolating_eqpt_inst", "Fuse"),
    "Recloser Bank": ("eo_isolating_eqpt_inst", None),
    "Switch": ("eo_isolating_eqpt_inst", "Switch"),
}


@dataclass(frozen=True)
class DamageMatch:
    """Private association evidence; not a public DTO and not an outage count."""

    source_row: int
    asset_type: str
    status: Literal["spatial_candidate", "unavailable"]
    method: str
    report_date: date | None
    device_row: int | None
    distance_m: float | None
    runner_up_distance_m: float | None
    pole_row: int | None
    pole_distance_m: float | None
    pole_runner_up_distance_m: float | None
    pole_bridge: bool
    reasons: tuple[str, ...]
    asset_key: NodeKey | None = field(repr=False)
    # Retain observed source state privately; it never declares a current outage.
    repaired: str = ""


@dataclass(frozen=True)
class NearSourceEvidence:
    target_layer: str | None
    search_radius: str | None
    method: str | None
    verified_metadata: bool
    fid_is_asset_identifier: bool = False
    distance_is_meters: bool = False


@dataclass(frozen=True)
class DamageAudit:
    matches: tuple[DamageMatch, ...] = field(repr=False)
    near_source: NearSourceEvidence
    policy: ProximityPolicy
    policy_version: str = DAMAGE_POLICY_VERSION

    def for_row(self, source_row: int) -> DamageMatch:
        if source_row < 1 or source_row > len(self.matches):
            raise CheckpointError("unknown_damage_record", "Historical damage record is outside the prepared snapshot.")
        result = self.matches[source_row - 1]
        if result.source_row != source_row:
            raise CheckpointError("damage_record_order", "Prepared damage row order is inconsistent.")
        return result

    def safe_summary(self) -> dict:
        """Explicit aggregate allowlist: no row locators, keys or coordinates."""
        return {
            "policy_version": self.policy_version,
            "observations": len(self.matches),
            "candidate_observations": sum(m.status == "spatial_candidate" for m in self.matches),
            "unique_candidate_assets": len({m.asset_key for m in self.matches if m.asset_key is not None}),
            "statuses": dict(sorted(Counter(m.status for m in self.matches).items())),
            "reasons": dict(sorted(Counter(r for m in self.matches for r in m.reasons).items())),
            "max_distance_m": self.policy.max_distance_m,
            "min_runner_up_gap_m": self.policy.min_runner_up_gap_m,
            "classification": "prototype policy",
            "historical_only": True,
            "direct_identifier_join": False,
            "reverse_dependencies_validated": False,
            "near_target_layer": self.near_source.target_layer,
            "near_method": self.near_source.method,
            "near_search_radius": self.near_source.search_radius,
            "near_metadata_verified": self.near_source.verified_metadata,
        }


@dataclass(frozen=True)
class DamageObservation:
    row: int
    asset_type: str
    circuit_alias: str = field(repr=False)
    station_alias: str = field(repr=False)
    point: tuple[float, float] = field(repr=False)
    report_date: date | None = None
    repaired: str = ""


@dataclass(frozen=True)
class DamageDevice:
    row: int
    asset_type: str
    key: NodeKey = field(repr=False)
    kind: str
    location: str = field(repr=False)
    circuit_id: str = field(repr=False)
    circuit_alias: str = field(repr=False)
    station_alias: str = field(repr=False)
    point: tuple[float, float] = field(repr=False)


@dataclass(frozen=True)
class DamagePole:
    row: int
    location: str = field(repr=False)
    point: tuple[float, float] = field(repr=False)


class DamageMatcher:
    """Reusable private indexes; projection and source loading occur once."""

    def __init__(self, devices: tuple[DamageDevice, ...], poles: tuple[DamagePole, ...],
                 tokens: dict[NodeKey, TopologyToken], circuit_pairs: set[tuple[str, str]],
                 policy: ProximityPolicy = DAMAGE_POLICY):
        self.policy = policy
        self.devices = {str(i): a for i, a in enumerate(devices)}
        self.poles = {str(i): p for i, p in enumerate(poles)}
        self.tokens = tokens
        self.key_counts = Counter(a.key for a in devices)
        self.poles_by_location: dict[str, list[DamagePole]] = defaultdict(list)
        for pole in poles:
            self.poles_by_location[pole.location].append(pole)
        self.pole_index = MetricSpatialIndex(tuple(MetricPoint(k, *p.point) for k, p in self.poles.items()))
        groups: dict[tuple[str, str, str], list[MetricPoint]] = defaultdict(list)
        for k, device in self.devices.items():
            groups[(device.asset_type, device.circuit_alias, device.station_alias)].append(MetricPoint(k, *device.point))
        self.groups = {key: MetricSpatialIndex(tuple(points)) for key, points in groups.items()}
        self.empty_index = MetricSpatialIndex(())
        self.codes: dict[str, set[str]] = defaultdict(set)
        self.aliases: dict[str, set[str]] = defaultdict(set)
        for code, alias in circuit_pairs:
            self.codes[alias].add(code)
            self.aliases[code].add(alias)

    def match(self, observation: DamageObservation) -> DamageMatch:
        reasons: list[str] = []
        pole_match = classify_proximity(self.pole_index, observation.point, self.policy)
        pole_nearest = pole_match.nearest
        pole = self.poles[pole_nearest.key] if pole_nearest is not None else None
        nearest = runner_up = device = None
        bridge = False
        asset_key = None
        if observation.asset_type not in SUPPORTED_TYPES:
            reasons.append("unsupported_asset_type")
        else:
            group = self.groups.get((observation.asset_type, observation.circuit_alias, observation.station_alias), self.empty_index)
            device_match = classify_proximity(group, observation.point, self.policy)
            nearest, runner_up = device_match.nearest, device_match.runner_up
            if nearest is None:
                reasons.append("no_same_type_circuit_station_device")
            else:
                device = self.devices[nearest.key]
                if device_match.status != "spatial_proxy":
                    reasons.append("device_" + device_match.status)
                if pole_match.status != "spatial_proxy":
                    reasons.append("pole_" + pole_match.status)
                labeled_poles = self.poles_by_location.get(device.location, [])
                bridge = len(labeled_poles) == 1 and pole is not None and labeled_poles[0].row == pole.row
                if not bridge:
                    reasons.append("missing_or_conflicting_pole_location_bridge")
                elif ((device.point[0] - pole.point[0]) ** 2 + (device.point[1] - pole.point[1]) ** 2) ** .5 > self.policy.max_distance_m:
                    bridge = False
                    reasons.append("pole_location_geometry_conflict")
                if (self.codes[device.circuit_alias] != {device.circuit_id}
                        or self.aliases[device.circuit_id] != {device.circuit_alias}):
                    reasons.append("ambiguous_circuit_crosswalk")
                token = self.tokens.get(device.key)
                expected_entity, expected_kind = SUPPORTED_TYPES[observation.asset_type]
                if (self.key_counts[device.key] != 1 or token is None
                        or token.entity != expected_entity or token.kind != device.kind
                        or token.location_code != device.location
                        or (expected_kind is not None and device.kind != expected_kind)):
                    reasons.append("unresolved_typed_equipment_identity")
                if not reasons:
                    asset_key = device.key
        return DamageMatch(
            source_row=observation.row, asset_type=observation.asset_type,
            status="spatial_candidate" if asset_key is not None else "unavailable",
            method=DAMAGE_METHOD, report_date=observation.report_date,
            device_row=device.row if device else None,
            distance_m=nearest.distance_m if nearest else None,
            runner_up_distance_m=runner_up.distance_m if runner_up else None,
            pole_row=pole.row if pole else None,
            pole_distance_m=pole_nearest.distance_m if pole_nearest else None,
            pole_runner_up_distance_m=pole_match.runner_up.distance_m if pole_match.runner_up else None,
            pole_bridge=bridge, reasons=tuple(reasons), asset_key=asset_key,
            repaired=observation.repaired)


def _metric_point(reader, row: int) -> tuple[float, float]:
    points = reader.shape(row).points
    if len(points) != 1:
        raise CheckpointError("invalid_damage_geometry", "Damage matching requires a single source point.")
    return wgs84_to_metric(tuple(points[0][:2]))


def _require_wgs84(z, stem: str) -> None:
    if CRS.from_wkt(z.read(stem + ".prj").decode()).to_epsg() != 4326:
        raise CheckpointError("unexpected_damage_crs", "Re-audit historical matching before using a changed coordinate system.")


def _near_evidence(z) -> NearSourceEvidence:
    root = ET.fromstring(z.read("arcos_prod_damage_09_28_Clip.shp.xml"))
    expected = 'Near arcos_prod_damage_09_28_Clip Primary_ExportFeatures "200 Feet" NO_LOCATION NO_ANGLE PLANAR "NEAR_FID NEAR_FID #;NEAR_DIST NEAR_DIST #" # #'
    found = any(" ".join("".join(n.itertext()).split()) == expected
                for n in root.iter() if n.tag.lower() == "process")
    return NearSourceEvidence("Primary_ExportFeatures" if found else None,
                              "200 Feet" if found else None,
                              "PLANAR" if found else None, found)


def prepare_damage_audit(raw: Path = RAW, topology: TopologyIndex | None = None,
                         policy: ProximityPolicy = DAMAGE_POLICY) -> DamageAudit:
    """Prepare all 1,659 historical rows once; no extraction, network or outputs."""
    verify_sources(raw)
    if topology is None:
        with zipfile.ZipFile(raw / "matched_upstream.zip") as z:
            with z.open("matched_upstream.txt") as stream:
                topology = parse_topology(io.TextIOWrapper(stream, encoding="utf-8-sig"))
    tokens = {token.key: token for path in topology.paths.values() for token in path}
    devices: list[DamageDevice] = []
    circuit_pairs: set[tuple[str, str]] = set()
    layer_specs = (
        ("Data1.zip", "Fuse_Bank_Clip", "Fuse Bank", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Transformer_Clip", "Transformer", "eo_power_xfrmr_inst"),
        ("Data2.zip", "Recloser_Bank_Clip", "Recloser Bank", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Switch_Clip", "Switch", "eo_isolating_eqpt_inst"),
    )
    for archive, stem, asset_type, entity in layer_specs:
        with layer(raw, archive, stem, geometry=True) as (reader, z):
            _require_wgs84(z, stem)
            fields = ("id", "device_typ", "location_n", "circuit_id", "aep_circui", "aep_statio")
            for i, r in enumerate(records(reader, fields)):
                circuit_pairs.add((r["circuit_id"], r["aep_circui"]))
                devices.append(DamageDevice(i + 1, asset_type, (entity, str(r["id"])), r["device_typ"],
                    r["location_n"], r["circuit_id"], r["aep_circui"], r["aep_statio"], _metric_point(reader, i)))
    for archive, stem in (("Data1.zip", "Primary_ExportFeatures"), ("Data2.zip", "Secondary_ExportFeatures")):
        with layer(raw, archive, stem) as (reader, _):
            circuit_pairs.update((r["circuit_id"], r["aep_circui"]) for r in records(reader, ("circuit_id", "aep_circui")))
    poles = []
    with layer(raw, "Data1.zip", "Pole_Clip", geometry=True) as (reader, z):
        _require_wgs84(z, "Pole_Clip")
        for i, r in enumerate(records(reader, ("location_n",))):
            poles.append(DamagePole(i + 1, r["location_n"], _metric_point(reader, i)))
    matcher = DamageMatcher(tuple(devices), tuple(poles), tokens, circuit_pairs, policy)
    with layer(raw, "Data1.zip", "arcos_prod_damage_09_28_Clip", geometry=True) as (reader, z):
        _require_wgs84(z, "arcos_prod_damage_09_28_Clip")
        near_source = _near_evidence(z)
        matches = tuple(matcher.match(DamageObservation(i + 1, r["Asset_Type"], r["Circuit"], r["Substation"],
                        _metric_point(reader, i), r["Report_Tim"], r["Repaired"]))
                        for i, r in enumerate(records(reader, ("Asset_Type", "Circuit", "Substation", "Report_Tim", "Repaired"))))
    return DamageAudit(matches, near_source, policy)
