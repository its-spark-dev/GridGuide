"""Aggregate source dependency and facility context; never infer facility service."""
from dataclasses import dataclass
from collections import Counter
from pyproj import CRS

from .contracts import AssetImpact, FacilityCount
from .data import layer, records, point_wgs84, CheckpointError


@dataclass(frozen=True)
class ImpactContext:
    # Only selected public aliases and counts; no customer/facility identity export.
    dependency_groups: tuple[tuple[tuple[str, ...], int], ...]
    facilities: tuple[FacilityCount, ...]
    asset_impacts: tuple[AssetImpact, ...]


def prepare_impact(raw, index, assets) -> ImpactContext:
    transformer, _, terminal = assets
    selected = {a.token.key: a.alias for a in assets if a.point is not None}
    with layer(raw, "Data1.zip", "Customer_Clip") as (reader, _):
        customers = list(records(reader, ("premise_nu", "circuit_id", "aep_xfmr_l")))
    pairs = Counter((r["premise_nu"], r["circuit_id"]) for r in customers)
    premise_counts = Counter(r["premise_nu"] for r in customers)
    customer_by_premise = {r["premise_nu"]: r for r in customers}
    dependent = set().union(*(index.premises_by_asset.get(a.token.key, frozenset()) for a in assets if a.point is not None))
    needed_transformers = {index.paths[p][0].identifier for p in dependent}
    transformers = {}
    with layer(raw, "Data2.zip", "Transformer_Clip") as (reader, _):
        for r in records(reader, ("id", "location_n", "device_typ", "circuit_id", "aep_circui", "aep_statio", "upstream_l")):
            if str(r['id']) in needed_transformers:
                transformers.setdefault(str(r['id']), []).append(r)

    def verified_premise(premise, asset):
        path = index.paths[premise]
        customer = customer_by_premise.get(premise)
        first = path[0]
        hits = transformers.get(first.identifier, [])
        if premise_counts[premise] != 1 or customer is None or len(hits) != 1:
            return False
        t = hits[0]
        return (asset.token in path and path[-1] == terminal.token
                and len(path) >= 2 and all(node in tuple(a.token for a in assets) for node in path[1:])
                and all(len(index.parents[node.key]) <= 1 for node in path)
                and first.entity == 'eo_power_xfrmr_inst' and first.kind == t['device_typ']
                and customer['aep_xfmr_l'] == first.location_code == t['location_n']
                and customer['circuit_id'] == t['circuit_id'] == transformer.circuit_id
                and (t['aep_circui'], t['aep_statio']) == (transformer.circuit_alias, transformer.station_alias)
                and t['upstream_l'] == ('CIRCUIT' if path[1].entity == 'eo_circuit' else path[1].location_code))

    impacts = []
    for asset in assets:
        if asset.point is None:
            continue
        # Start with every path containing the typed ID, before any circuit filter.
        candidates = index.premises_by_asset.get(asset.token.key)
        unresolved = sum(not verified_premise(p, asset) for p in candidates) if candidates is not None else 0
        available = candidates is not None and unresolved == 0
        impacts.append(AssetImpact(node_alias=asset.alias,
            status='verified_reverse_dependency' if available else 'unavailable',
            identity_basis='exact_typed_GIS_and_topology' if candidates is not None else 'unavailable',
            topology_path_count=None if candidates is None else len(candidates),
            dependent_customers=len(candidates) if available else None, unresolved_path_count=unresolved,
            dependency_classification='source-derived' if available else 'unavailable',
            source_refs=('matched_upstream.txt: typed entity + ID, type and location metadata',
                         'Customer_Clip: unique premise, transformer location and circuit',
                         'Transformer_Clip / Fuse_Bank_Clip: exact typed ID, location, circuit and upstream checks'),
            note='Damage is explicitly simulated on this source-verified asset; no ARCOS record is asserted to identify it. All indexed premises are checked before publishing a complete dependent count.'))
    groups = Counter()
    for (premise, circuit), count in pairs.items():
        path = index.paths.get(premise)
        if count != 1 or premise_counts[premise] != 1 or circuit != transformer.circuit_id or not path or path[-1].key != terminal.token.key:
            continue
        groups[tuple(selected[t.key] for t in path if t.key in selected)] += 1

    # This envelope is only a reproducible geographic context window, NOT an
    # electrical service polygon or outage boundary. Do not join nearby facilities.
    extent = None
    with layer(raw, "Data1.zip", "Primary_ExportFeatures", geometry=True) as (reader, z):
        if CRS.from_wkt(z.read("Primary_ExportFeatures.prj").decode()).to_epsg() != 4326:
            raise CheckpointError("unexpected_primary_crs", "Re-audit primary geometry before using a geographic extent.")
        for i, r in enumerate(records(reader, ("circuit_id", "aep_circui", "aep_statio"))):
            if (r["circuit_id"], r["aep_circui"], r["aep_statio"]) != (transformer.circuit_id, transformer.circuit_alias, transformer.station_alias):
                continue
            box = reader.shape(i).bbox
            extent = list(box) if extent is None else [min(extent[0], box[0]), min(extent[1], box[1]), max(extent[2], box[2]), max(extent[3], box[3])]
    facilities = []
    for kind, stem in (("hospital", "Hospitals_Medic_Pairwis_Clip"), ("fire_station", "Fire_Stations_E_Pairwis_Clip"), ("ambulance", "Ambulance_Servi_Pairwis_Clip")):
        with layer(raw, "Data1.zip", stem, geometry=True) as (reader, z):
            points = (point_wgs84(reader, z, stem, i) for i in range(len(reader)))
            within = None if extent is None else sum(extent[0] <= x <= extent[2] and extent[1] <= y <= extent[3] for x, y in points)
            facilities.append(FacilityCount(kind=kind, source_layer=stem, regional_features=len(reader), within_primary_extent=within))
    return ImpactContext(tuple(sorted(groups.items())), tuple(facilities), tuple(impacts))
