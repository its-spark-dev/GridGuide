"""Read-only source verification and minimal, in-memory preparation for Demo A.

Private IDs/precise coordinates remain in PreparedContext. Only its public
Location and SourceFacts cross the presentation boundary. No source extraction,
disk cache, nearest-neighbor identity matching, or synthetic fallback path.
"""
from __future__ import annotations
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import io
import math
from pathlib import Path
from typing import Iterable, TYPE_CHECKING
import zipfile

import openpyxl
from pyproj import CRS, Geod, Transformer
import shapefile

from .config import GOLDEN_ALIAS, GOLDEN_CUSTOMER_RECORD, RAW, SNAPSHOT_DATE, SOURCE_SHA256
from .contracts import DependencyEdge, Issue, Location, MapPoint, PublicAsset, SourceFacts

NodeKey = tuple[str, str]
if TYPE_CHECKING:
    from .impact import ImpactContext


class CheckpointError(ValueError):
    """Code and message are safe for public errors; never include raw record values."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class TopologyToken:
    entity: str
    identifier: str
    kind: str
    location_code: str

    @property
    def key(self) -> NodeKey:
        return self.entity, self.identifier


@dataclass
class TopologyIndex:
    paths: dict[str, tuple[TopologyToken, ...]]
    parents: dict[NodeKey, set[NodeKey]]
    # Private, deterministic reverse lookup across ALL supplied premise paths.
    premises_by_asset: dict[NodeKey, frozenset[str]]


@dataclass(frozen=True)
class ResolvedAsset:
    token: TopologyToken
    alias: str
    point: tuple[float, float] | None
    circuit_id: str
    circuit_alias: str
    station_alias: str
    upstream_location: str | None
    mounting: str | None
    phase_specs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Recipe:
    id: str
    asset_kind: str
    install_hours: Decimal
    remove_hours: Decimal
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class LaborReference:
    recipes: tuple[Recipe, ...]
    restricted_access_hours: Decimal
    indirect_multiplier: Decimal
    access_source: str = "Labor only work!D2"
    multiplier_source: str = "Indirect Labor Multiplier!B1"


@dataclass(frozen=True)
class PreparedContext:
    """Internal only. Do not serialize this object for a client or LLM."""

    location: Location
    facts: SourceFacts
    assets: tuple[ResolvedAsset, ...]
    labor: LaborReference
    source_hashes: tuple[tuple[str, str], ...]
    private_premise: str
    private_customer_id: str
    private_customer_point: tuple[float, float]
    transformer_fuse_distance_m: float
    impact: ImpactContext


def source_hashes(raw: Path = RAW) -> dict[str, str]:
    result = {}
    for name in SOURCE_SHA256:
        try:
            with (raw / name).open("rb") as f:
                result[name] = hashlib.file_digest(f, "sha256").hexdigest()
        except FileNotFoundError as e:
            raise CheckpointError("missing_source", f"Required raw source is missing: {name}") from e
    return result


def verify_sources(raw: Path = RAW) -> dict[str, str]:
    actual = source_hashes(raw)
    for name, expected in SOURCE_SHA256.items():
        if actual[name] != expected:
            raise CheckpointError("source_hash_mismatch", f"Source changed: {name}. Re-audit before using the golden locator.")
    return actual


def parse_topology(lines: Iterable[str]) -> TopologyIndex:
    paths: dict[str, tuple[TopologyToken, ...]] = {}
    parents: dict[NodeKey, set[NodeKey]] = defaultdict(set)
    metadata: dict[NodeKey, TopologyToken] = {}
    reverse: dict[NodeKey, set[str]] = defaultdict(set)
    for line in lines:
        if not line.strip():
            continue
        pieces = line.rstrip("\r\n").split("\t")
        fields = [p.split("*") for p in pieces[1:]]
        if len(pieces) < 2 or not pieces[0] or any(len(f) != 4 or not all(f) for f in fields):
            raise CheckpointError("malformed_topology", "An upstream record has an invalid token structure.")
        premise = pieces[0]  # No integer conversion or zero-padding.
        if premise in paths:
            raise CheckpointError("duplicate_premise", "A premise has duplicate or conflicting upstream records.")
        path = tuple(TopologyToken(*f) for f in fields)
        if len({t.key for t in path}) != len(path):
            raise CheckpointError("topology_cycle", "An upstream path repeats an equipment node.")
        for token in path:
            if token.key in metadata and metadata[token.key] != token:
                raise CheckpointError("conflicting_node_metadata", "One equipment key has conflicting source descriptions.")
            metadata[token.key] = token
            reverse[token.key].add(premise)
            parents.setdefault(token.key, set())
        for child, parent in zip(path, path[1:]):
            parents[child.key].add(parent.key)
        paths[premise] = path

    indegree = {k: 0 for k in metadata}
    for pp in parents.values():
        for parent in pp:
            indegree[parent] += 1
    queue = deque(k for k, n in indegree.items() if n == 0)
    visited = 0
    while queue:
        key = queue.popleft()
        visited += 1
        for parent in parents[key]:
            indegree[parent] -= 1
            if indegree[parent] == 0:
                queue.append(parent)
    if visited != len(metadata):
        raise CheckpointError("topology_cycle", "The union of source paths contains a cycle.")
    return TopologyIndex(paths, dict(parents), {key: frozenset(values) for key, values in reverse.items()})


def select_path(index: TopologyIndex, premise: str) -> tuple[TopologyToken, ...]:
    if premise not in index.paths:
        raise CheckpointError("missing_topology", "The selected customer has no upstream record; no fallback path was created.")
    path = index.paths[premise]
    if path[0].entity != "eo_power_xfrmr_inst" or path[-1].entity != "eo_circuit":
        raise CheckpointError("unsupported_path", "The selected path lacks a supported transformer-to-circuit trace.")
    if any(len(index.parents[t.key]) > 1 for t in path):
        raise CheckpointError("ambiguous_parent", "A selected upstream node has conflicting parents across source paths.")
    if index.parents[path[-1].key]:
        raise CheckpointError("invalid_terminal", "The selected circuit is not a terminal node.")
    return path


def validate_crosswalk(code: str, alias: str, pairs: set[tuple[str, str]]) -> None:
    aliases = {a for c, a in pairs if c == code}
    codes = {c for c, a in pairs if a == alias}
    if aliases != {alias} or codes != {code}:
        raise CheckpointError("ambiguous_circuit", "Circuit code/alias mapping is missing or inconsistent across GIS layers.")


@contextmanager
def layer(raw: Path, archive: str, stem: str, *, geometry: bool = False):
    with zipfile.ZipFile(raw / archive) as z:
        parts = {"dbf": io.BytesIO(z.read(stem + ".dbf"))}
        if geometry:
            parts.update({ext: io.BytesIO(z.read(stem + "." + ext)) for ext in ("shp", "shx")})
        with shapefile.Reader(**parts, encoding="utf-8") as reader:
            yield reader, z


def records(reader, fields: tuple[str, ...]):
    if not set(fields) <= {f[0] for f in reader.fields[1:]}:
        raise CheckpointError("source_schema_mismatch", "A GIS layer lacks a required field.")
    return reader.iterRecords(fields=list(fields))


def point_wgs84(reader, z, stem: str, row_index: int) -> tuple[float, float]:
    shp = reader.shape(row_index)
    if len(shp.points) != 1:
        raise CheckpointError("invalid_geometry", "Expected a single source point for the selected asset.")
    crs = CRS.from_wkt(z.read(stem + ".prj").decode())
    if crs.is_compound:
        crs = crs.sub_crs_list[0]
    lon, lat = Transformer.from_crs(crs, 4326, always_xy=True).transform(*shp.points[0][:2])
    if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
        raise CheckpointError("invalid_geometry", "Source geometry cannot be transformed to a valid location.")
    return lon, lat


def public_point(point: tuple[float, float]) -> MapPoint:
    # Deterministic 0.01-degree cell center, not an exact customer/asset coordinate.
    lon, lat = (round((math.floor(v * 100) + 0.5) / 100, 3) for v in point)
    return MapPoint(longitude=lon, latitude=lat)


def validate_resolved_path(customer: dict, path: tuple[TopologyToken, ...], assets: tuple[ResolvedAsset, ...]) -> None:
    if tuple(a.token for a in assets) != path:
        raise CheckpointError("unresolved_equipment", "Not every source path node resolved uniquely.")
    first = assets[0]
    if customer["aep_xfmr_l"] != first.token.location_code:
        raise CheckpointError("transformer_location_conflict", "Customer and source path disagree about the transformer location.")
    if any(a.circuit_id != customer["circuit_id"] for a in assets):
        raise CheckpointError("circuit_conflict", "Customer, assets and circuit terminal do not agree.")
    if len({a.circuit_alias for a in assets[:-1]}) != 1 or len({a.station_alias for a in assets[:-1]}) != 1:
        raise CheckpointError("circuit_conflict", "Selected device circuit/station aliases do not agree.")
    for child, parent in zip(assets, assets[1:]):
        expected = "CIRCUIT" if parent.token.entity == "eo_circuit" else parent.token.location_code
        if child.upstream_location != expected:
            raise CheckpointError("upstream_conflict", "GIS upstream location disagrees with the selected source path.")


def labor_decimal(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise CheckpointError("invalid_labor_rate", "A required labor reference is missing, nonnumeric, negative or nonfinite.")
    # Remove Excel binary representation noise before outward display rounding.
    return Decimal(str(value)).quantize(Decimal("0.000000000001"))


def read_labor(raw: Path) -> LaborReference:
    with (raw / "Install_Labor_HackOHIO.xlsx").open("rb") as f:
        wb = openpyxl.load_workbook(f, data_only=False, read_only=True)
        try:
            material = wb["Labor time material related"]
            expected = {"A18": "Size (kVA)", "C18": "Avg Install Hours", "D18": "Avg Removal Hours",
                        "A25": 100, "A88": "Fuse Cutout Average Hours", "A89": "Avg Install Hours", "B89": "Avg Removal Hours"}
            if any(material[cell].value != value for cell, value in expected.items()):
                raise CheckpointError("labor_schema_mismatch", "Labor cells no longer have the documented component/size labels.")
            access = wb["Labor only work"]
            if access["B2"].value != "Restricted Access Work" or access["D1"].value != "INSTALL_HOURS":
                raise CheckpointError("labor_schema_mismatch", "Restricted-access rate context changed.")
            recipes = tuple(Recipe(name, kind, labor_decimal(material[install].value), labor_decimal(material[remove].value),
                                   (f"Labor time material related!{install}", f"Labor time material related!{remove}"))
                            for name, kind, install, remove in (
                                ("fuse-cutout-replace", "Fuse", "A90", "B90"),
                                ("transformer-100kva-replace", "Distribution", "C25", "D25")))
            multiplier = labor_decimal(wb["Indirect Labor Multiplier"]["B1"].value)
            if multiplier <= 0:
                raise CheckpointError("invalid_labor_rate", "Indirect labor multiplier must be positive.")
            return LaborReference(recipes, labor_decimal(access["D2"].value), multiplier)
        finally:
            wb.close()


def prepare_context(raw: Path = RAW, location_alias: str = GOLDEN_ALIAS) -> PreparedContext:
    """Verify and load once, then reuse the context for responsive scenario changes."""
    if location_alias != GOLDEN_ALIAS:
        raise CheckpointError("unsupported_location", "Only the audited demo-a location is supported by this checkpoint.")
    hashes = verify_sources(raw)
    with layer(raw, "Data1.zip", "Customer_Clip", geometry=True) as (reader, z):
        row = GOLDEN_CUSTOMER_RECORD - 1
        required = ("id", "premise_nu", "aep_xfmr_l", "circuit_id")
        records(reader, required)  # Verify schema even before indexed access.
        customer = {field: reader.record(row)[field] for field in required}
        if sum(r["premise_nu"] == customer["premise_nu"] for r in records(reader, ("premise_nu",))) != 1:
            raise CheckpointError("ambiguous_customer", "Golden customer identifier is not unique.")
        customer_point = point_wgs84(reader, z, "Customer_Clip", row)

    with zipfile.ZipFile(raw / "matched_upstream.zip") as z:
        with z.open("matched_upstream.txt") as f:
            index = parse_topology(io.TextIOWrapper(f, encoding="utf-8-sig"))
    path = select_path(index, customer["premise_nu"])
    supported = {("eo_power_xfrmr_inst", "Distribution"), ("eo_isolating_eqpt_inst", "Fuse"), ("eo_circuit", "Circuit Breaker")}
    if any((t.entity, t.kind) not in supported for t in path):
        raise CheckpointError("unsupported_path", "Selected path includes equipment outside the checkpoint's verified scope.")

    pairs: set[tuple[str, str]] = set()
    hits: dict[NodeKey, list[ResolvedAsset]] = defaultdict(list)
    layers = (
        ("Data1.zip", "Fuse_Bank_Clip", "eo_isolating_eqpt_inst"),
        ("Data1.zip", "Primary_ExportFeatures", None),
        ("Data2.zip", "Transformer_Clip", "eo_power_xfrmr_inst"),
        ("Data2.zip", "Recloser_Bank_Clip", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Switch_Clip", "eo_isolating_eqpt_inst"),
        ("Data2.zip", "Secondary_ExportFeatures", None),
    )
    wanted = {t.key: t for t in path}
    for archive, stem, entity in layers:
        with layer(raw, archive, stem, geometry=entity is not None) as (reader, z):
            fields = ("circuit_id", "aep_circui") + (("id",) if entity else ())
            for row_idx, record in enumerate(records(reader, fields)):
                pairs.add((record["circuit_id"], record["aep_circui"]))
                if not entity or (entity, str(record["id"])) not in wanted:
                    continue
                token = wanted[(entity, str(record["id"]))]
                rec = reader.record(row_idx)
                if rec["location_n"] != token.location_code or rec["device_typ"] != token.kind:
                    raise CheckpointError("equipment_identity_conflict", "An equipment ID matches but its location or type does not.")
                alias = ("transformer" if token.kind == "Distribution" else "protective") + "-a"
                specs = tuple(rec[f] for f in ("a_phase_sp", "b_phase_sp", "c_phase_sp")) if entity == "eo_power_xfrmr_inst" else ()
                hits[token.key].append(ResolvedAsset(token, alias, point_wgs84(reader, z, stem, row_idx),
                    rec["circuit_id"], rec["aep_circui"], rec["aep_statio"], rec["upstream_l"],
                    rec["mounting"] if "mounting" in {f[0] for f in reader.fields[1:]} else None, specs))

    assets = []
    for token in path:
        if token.entity == "eo_circuit":
            assets.append(ResolvedAsset(token, "circuit-a", None, token.location_code, "", "", None, None))
        elif len(hits[token.key]) != 1:
            raise CheckpointError("unresolved_equipment", "A required upstream ID has zero or multiple GIS matches.")
        else:
            assets.append(hits[token.key][0])
    resolved = tuple(assets)
    validate_resolved_path(customer, path, resolved)
    if len({a.alias for a in resolved}) != len(resolved) or tuple(a.token.kind for a in resolved) != ("Distribution", "Fuse", "Circuit Breaker"):
        raise CheckpointError("unsupported_path", "Golden source path differs from its audited scope; re-audit instead of substituting a path.")
    transformer, fuse, _ = resolved
    validate_crosswalk(customer["circuit_id"], transformer.circuit_alias, pairs)
    if not any(spec == "100 kVA XFR PL" for spec in transformer.phase_specs):
        raise CheckpointError("unsupported_transformer_recipe", "The selected transformer has no verified 100-kVA specification.")

    history_count = 0
    with layer(raw, "Data1.zip", "arcos_prod_damage_09_28_Clip") as (reader, _):
        for r in records(reader, ("Circuit", "Substation", "Report_Tim")):
            if r["Circuit"] == transformer.circuit_alias:
                if r["Substation"] != transformer.station_alias or r["Report_Tim"] is None:
                    raise CheckpointError("historical_context_conflict", "Historical circuit evidence has inconsistent station/date context.")
                history_count += r["Report_Tim"] <= SNAPSHOT_DATE

    public_assets = tuple(PublicAsset(alias=a.alias, kind=a.token.kind,
        resolution="abstract_circuit_terminal" if a.point is None else "exact_typed_id",
        map_position=public_point(a.point) if a.point else None) for a in resolved)
    aliases = (GOLDEN_ALIAS,) + tuple(a.alias for a in resolved)
    location = Location(alias=GOLDEN_ALIAS, label="Demo location A", map_position=public_point(customer_point),
        upstream_assets=public_assets,
        dependency_edges=tuple(DependencyEdge(downstream_alias=a, upstream_alias=b) for a, b in zip(aliases, aliases[1:])),
        topology_warnings=(Issue(code="abstract_supply_terminal", message="Circuit terminal has no supplied geometry; current supply availability is simulated."),))
    facts = SourceFacts(snapshot_date=SNAPSHOT_DATE.isoformat(), path_types=tuple(t.kind for t in path),
        transformer_mounting=transformer.mounting or "Unknown", historical_circuit_evidence=history_count > 0,
        historical_damage_record_count=history_count)
    from .impact import prepare_impact
    return PreparedContext(location, facts, resolved, read_labor(raw), tuple(sorted(hashes.items())),
        customer["premise_nu"], str(customer["id"]), customer_point,
        Geod(ellps="WGS84").inv(*transformer.point, *fuse.point)[2], prepare_impact(raw, index, resolved))
