"""Private, reusable source topology and complete reverse dependency evidence.

This module never infers a connection from geometry. Syntactic source membership
is retained even when GIS/customer validation fails. Only ``dependents`` and its
set-based helpers establish the bounded, source-validated dependency relation.
None of these internal dataclasses is a public serialization contract.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import io
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping
import zipfile

from pyproj import CRS, Transformer

from .config import RAW, SNAPSHOT
from .data import CheckpointError, NodeKey, TopologyIndex, layer, parse_topology, records, verify_sources


SUPPORTED_TYPES = frozenset({
    ("eo_power_xfrmr_inst", "Distribution"),
    ("eo_isolating_eqpt_inst", "Fuse"),
    ("eo_circuit", "Circuit Breaker"),
})


def public_asset_alias(key: NodeKey) -> str:
    """Opaque stable alias; never embed a source ID or row locator in public data."""
    source = json.dumps((SNAPSHOT, *key), separators=(",", ":"))
    return "asset-" + hashlib.sha256(source.encode()).hexdigest()[:20]


@dataclass(frozen=True)
class Equipment:
    key: NodeKey
    source_layer: str
    source_row: int
    kind: str
    location_code: str
    upstream_location: str
    circuit_id: str
    circuit_alias: str
    station_alias: str
    point: tuple[float, float]
    phase_specs: tuple[str, ...] = ()
    mounting: str | None = None

    @property
    def alias(self) -> str:
        return public_asset_alias(self.key)


@dataclass(frozen=True)
class Customer:
    premise: str
    source_row: int
    transformer_location: str
    circuit_id: str
    point: tuple[float, float]


@dataclass(frozen=True)
class NetworkIndex:
    """Internal source evidence, shared across requests; never dump to JSON."""

    topology: TopologyIndex
    equipment_by_key: Mapping[NodeKey, Equipment]
    equipment_hits: Mapping[NodeKey, tuple[Equipment, ...]]
    customers: tuple[Customer, ...]
    customers_by_premise: Mapping[str, tuple[Customer, ...]]
    node_reasons: Mapping[NodeKey, tuple[str, ...]]
    path_reasons: Mapping[str, tuple[str, ...]]
    asset_reasons: Mapping[NodeKey, tuple[str, ...]]
    source_hashes: tuple[tuple[str, str], ...] = ()

    def raw_membership(self, key: NodeKey) -> frozenset[str] | None:
        """All source paths containing this exact typed identity, before filters."""
        return self.topology.premises_by_asset.get(key)

    def dependents(self, key: NodeKey) -> frozenset[str] | None:
        members = self.raw_membership(key)
        if members is None or self.asset_reasons.get(key):
            return None
        return members

    def rejection_reasons(self, key: NodeKey) -> tuple[str, ...]:
        return self.asset_reasons.get(key, ("unknown_topology_asset",))

    def key_for_locator(self, source_layer: str, source_row: int) -> NodeKey | None:
        hits = [asset.key for values in self.equipment_hits.values() for asset in values
                if asset.source_layer == source_layer and asset.source_row == source_row]
        return hits[0] if len(hits) == 1 else None

    def key_for_alias(self, alias: str) -> NodeKey | None:
        hits = [key for key in self.topology.premises_by_asset if public_asset_alias(key) == alias]
        return hits[0] if len(hits) == 1 else None

    def affected_union(self, keys: Iterable[NodeKey]) -> frozenset[str] | None:
        result: set[str] = set()
        for key in frozenset(keys):
            members = self.dependents(key)
            if members is None:
                return None
            result.update(members)
        return frozenset(result)

    def release_groups(self, keys: Iterable[NodeKey]) -> Mapping[frozenset[NodeKey], frozenset[str]] | None:
        """Exact premise groups keyed by every damaged dependency on their path."""
        selected = frozenset(keys)
        affected = self.affected_union(selected)
        if affected is None:
            return None
        groups: dict[frozenset[NodeKey], set[str]] = defaultdict(set)
        for premise in affected:
            required = frozenset(t.key for t in self.topology.paths[premise]) & selected
            groups[required].add(premise)
        return MappingProxyType({key: frozenset(value) for key, value in groups.items()})

    def released_premises(self, keys: Iterable[NodeKey], completed: Iterable[NodeKey]) -> frozenset[str] | None:
        selected, done = frozenset(keys), frozenset(completed)
        if not done <= selected:
            raise CheckpointError("unknown_completed_repair", "A completed repair is outside the declared damage scope.")
        groups = self.release_groups(selected)
        if groups is None:
            return None
        return frozenset(p for required, premises in groups.items() if required and required <= done for p in premises)

    def upstream_damaged_dependencies(self, keys: Iterable[NodeKey]) -> Mapping[NodeKey, frozenset[NodeKey]] | None:
        """All declared upstream ancestors; order policy remains the caller's job."""
        selected = frozenset(keys)
        if self.affected_union(selected) is None:
            return None
        result = {}
        for key in selected:
            upstream, pending = set(), list(self.topology.parents[key])
            while pending:
                parent = pending.pop()
                if parent in upstream:
                    continue
                upstream.add(parent)
                pending.extend(self.topology.parents[parent])
            result[key] = frozenset(upstream & selected)
        return MappingProxyType(result)

    @property
    def coverage(self) -> dict:
        """Aggregate denominators only. Failure categories overlap by design."""
        nodes = {t.key: t for path in self.topology.paths.values() for t in path}
        verified = {key for key in nodes if not self.asset_reasons[key]}
        by_kind = {}
        for kind in sorted({t.kind for t in nodes.values()}):
            keys = [key for key, token in nodes.items() if token.kind == kind]
            by_kind[kind] = {
                "indexed_assets": len(keys),
                "topology_memberships": sum(len(self.topology.premises_by_asset[key]) for key in keys),
                "unique_gis_id_assets": sum(key in self.equipment_by_key for key in keys),
                "fully_verified_reverse_assets": sum(key in verified for key in keys),
                "node_failure_reasons": dict(sorted(Counter(r for key in keys for r in self.node_reasons[key]).items())),
            }
        return {
            "customer_rows": len(self.customers),
            "unique_customer_premises": len(self.customers_by_premise),
            "topology_paths": len(self.topology.paths),
            "topology_assets": len(nodes),
            "topology_edges": sum(len(p) for p in self.topology.parents.values()),
            "topology_memberships": sum(len(p) for p in self.topology.premises_by_asset.values()),
            "customer_rows_missing_paths": sum(c.premise not in self.topology.paths for c in self.customers),
            "topology_paths_missing_customers": sum(p not in self.customers_by_premise for p in self.topology.paths),
            "all_gis_ids_resolved_paths": sum(all(t.entity == "eo_circuit" or t.key in self.equipment_by_key for t in path)
                                              for path in self.topology.paths.values()),
            "fully_verified_paths": sum(not reasons for reasons in self.path_reasons.values()),
            "fully_verified_reverse_assets": len(verified),
            "path_failure_reasons": dict(sorted(Counter(r for reasons in self.path_reasons.values() for r in reasons).items())),
            "by_kind": by_kind,
        }


def build_network(topology: TopologyIndex, equipment: Iterable[Equipment], customers: Iterable[Customer], *,
                  circuit_evidence: Iterable[tuple[str, str, str]] = (),
                  source_hashes: tuple[tuple[str, str], ...] = ()) -> NetworkIndex:
    """Pure validator, also usable with synthetic fixtures and changed evidence."""
    hits: dict[NodeKey, list[Equipment]] = defaultdict(list)
    code_alias, alias_code, alias_station = defaultdict(set), defaultdict(set), defaultdict(set)
    for asset in equipment:
        hits[asset.key].append(asset)
    customer_tuple = tuple(customers)
    customer_hits: dict[str, list[Customer]] = defaultdict(list)
    for customer in customer_tuple:
        customer_hits[customer.premise].append(customer)
    for code, alias, station in (*circuit_evidence, *((a.circuit_id, a.circuit_alias, a.station_alias) for aa in hits.values() for a in aa)):
        code_alias[code].add(alias)
        alias_code[alias].add(code)
        alias_station[alias].add(station)
    nodes = {t.key: t for path in topology.paths.values() for t in path}
    node_reasons: dict[NodeKey, set[str]] = {}
    for key, token in nodes.items():
        reasons: set[str] = set()
        if len(topology.parents[key]) > 1:
            reasons.add("multiple_parents")
        if token.entity == "eo_circuit":
            if token.kind != "Circuit Breaker" or topology.parents[key]:
                reasons.add("invalid_terminal")
        elif not hits.get(key):
            reasons.add("missing_GIS_ID")
        elif len(hits[key]) != 1:
            reasons.add("ambiguous_GIS_ID")
        else:
            asset = hits[key][0]
            if asset.kind != token.kind:
                reasons.add("GIS_type_conflict")
            if asset.location_code != token.location_code:
                reasons.add("GIS_location_conflict")
            if len(code_alias[asset.circuit_id]) != 1 or len(alias_code[asset.circuit_alias]) != 1:
                reasons.add("circuit_crosswalk_conflict")
            if len(alias_station[asset.circuit_alias]) != 1:
                reasons.add("station_crosswalk_conflict")
            for parent in topology.parents[key]:
                upstream = nodes[parent]
                expected = "CIRCUIT" if upstream.entity == "eo_circuit" else upstream.location_code
                if asset.upstream_location != expected:
                    reasons.add("GIS_parent_conflict")
        node_reasons[key] = reasons

    path_reasons = {}
    for premise, path in topology.paths.items():
        reasons = set().union(*(node_reasons[t.key] for t in path))
        if any((t.entity, t.kind) not in SUPPORTED_TYPES for t in path):
            reasons.add("unsupported_type")
        if path[0].entity != "eo_power_xfrmr_inst" or path[0].kind != "Distribution":
            reasons.add("invalid_first")
        if path[-1].entity != "eo_circuit" or path[-1].kind != "Circuit Breaker":
            reasons.add("invalid_terminal")
        cc = customer_hits.get(premise, ())
        if len(cc) != 1:
            reasons.add("missing_customer" if not cc else "ambiguous_customer")
        else:
            customer = cc[0]
            if customer.transformer_location != path[0].location_code:
                reasons.add("customer_transformer_location_conflict")
            if customer.circuit_id != path[-1].location_code:
                reasons.add("customer_terminal_circuit_conflict")
            aa = [hits[t.key][0] for t in path[:-1] if len(hits.get(t.key, ())) == 1]
            if any(a.circuit_id != customer.circuit_id for a in aa):
                reasons.add("device_customer_circuit_conflict")
            if len({(a.circuit_alias, a.station_alias) for a in aa}) > 1:
                reasons.add("path_alias_station_conflict")
        path_reasons[premise] = tuple(sorted(reasons))
    asset_reasons = {key: tuple(sorted(set(node_reasons[key]).union(*(path_reasons[p] for p in premises))))
                     for key, premises in topology.premises_by_asset.items()}
    aliases = [public_asset_alias(key) for key in nodes]
    if len(set(aliases)) != len(aliases):
        raise CheckpointError("public_alias_collision", "Source asset aliases are not unique.")
    return NetworkIndex(topology,
                        MappingProxyType({key: aa[0] for key, aa in hits.items() if len(aa) == 1}),
                        MappingProxyType({key: tuple(aa) for key, aa in hits.items()}), customer_tuple,
                        MappingProxyType({key: tuple(cc) for key, cc in customer_hits.items()}),
                        MappingProxyType({key: tuple(sorted(rr)) for key, rr in node_reasons.items()}),
                        MappingProxyType(path_reasons), MappingProxyType(asset_reasons), source_hashes)


def _point_reader(reader, archive, stem: str):
    crs = CRS.from_wkt(archive.read(stem + ".prj").decode())
    horizontal = crs.sub_crs_list[0] if crs.is_compound else crs
    transform = Transformer.from_crs(horizontal, 4326, always_xy=True)
    for shape in reader.iterShapes():
        if len(shape.points) != 1:
            raise CheckpointError("invalid_geometry", "A source inventory point is not a single location.")
        point = transform.transform(*shape.points[0][:2])
        if not (all(math.isfinite(v) for v in point) and -180 <= point[0] <= 180 and -90 <= point[1] <= 90):
            raise CheckpointError("invalid_geometry", "A source inventory point cannot be transformed to WGS84.")
        yield point


@lru_cache(maxsize=2)
def prepare_network(raw: Path = RAW) -> NetworkIndex:
    """Verify pinned sources and prepare once. No raw extraction or disk cache."""
    raw = Path(raw)
    hashes = tuple(sorted(verify_sources(raw).items()))
    with zipfile.ZipFile(raw / "matched_upstream.zip") as archive:
        with archive.open("matched_upstream.txt") as file:
            topology = parse_topology(io.TextIOWrapper(file, encoding="utf-8-sig"))
    with layer(raw, "Data1.zip", "Customer_Clip", geometry=True) as (reader, archive):
        customer_rows = records(reader, ("premise_nu", "aep_xfmr_l", "circuit_id"))
        customers = tuple(Customer(r["premise_nu"], i + 1, r["aep_xfmr_l"], r["circuit_id"], point)
                          for i, (r, point) in enumerate(zip(customer_rows, _point_reader(reader, archive, "Customer_Clip"), strict=True)))
    equipment, circuit_evidence = [], set()
    layers = (
        ("Data1.zip", "Fuse_Bank_Clip", "eo_isolating_eqpt_inst"),
        ("Data1.zip", "Primary_ExportFeatures", None),
        ("Data2.zip", "Transformer_Clip", "eo_power_xfrmr_inst"),
        ("Data2.zip", "Recloser_Bank_Clip", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Switch_Clip", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Secondary_ExportFeatures", None),
    )
    for archive_name, stem, entity in layers:
        with layer(raw, archive_name, stem, geometry=entity is not None) as (reader, archive):
            fields = ("circuit_id", "aep_circui", "aep_statio")
            has_mounting = "mounting" in {field[0] for field in reader.fields[1:]}
            if entity:
                fields += ("id", "location_n", "device_typ", "upstream_l")
                if has_mounting:
                    fields += ("mounting",)
            if entity == "eo_power_xfrmr_inst":
                fields += ("a_phase_sp", "b_phase_sp", "c_phase_sp")
            point_iter = _point_reader(reader, archive, stem) if entity else None
            for i, r in enumerate(records(reader, fields)):
                circuit_evidence.add((r["circuit_id"], r["aep_circui"], r["aep_statio"]))
                if entity:
                    specs = tuple(r[f] for f in ("a_phase_sp", "b_phase_sp", "c_phase_sp")) if entity == "eo_power_xfrmr_inst" else ()
                    equipment.append(Equipment((entity, str(r["id"])), stem, i + 1, r["device_typ"],
                                               r["location_n"], r["upstream_l"], r["circuit_id"],
                                               r["aep_circui"], r["aep_statio"], next(point_iter), specs,
                                               r["mounting"] if has_mounting else None))
    return build_network(topology, equipment, customers, circuit_evidence=circuit_evidence, source_hashes=hashes)
