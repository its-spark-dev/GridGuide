"""Read-only geographic presentation. No numerical engine or connectivity inference."""
import math
from pathlib import Path

from pyproj import CRS, Transformer
import shapefile

from .config import RAW, SNAPSHOT
from .contracts import GeographicAsset, GeographicMap, MapPoint, PrimaryLineContext
from .data import (CheckpointError, PreparedContext, layer, public_point,
                   records, validate_crosswalk, verify_sources)


def generalized_line_parts(shape, transformer: Transformer) -> tuple[tuple[tuple[MapPoint, ...], ...], int]:
    """Transform every supplied vertex; preserve part boundaries and vertex order.

    Cell quantization deliberately removes precision. Never connect separate source
    records/parts or offset points to make them look separate. Omit collapsed parts.
    """
    if shape.shapeType != shapefile.POLYLINE:
        raise CheckpointError("map_geometry_invalid", "Primary context is not a supported source line.")
    paths = []
    omitted = 0
    cuts = list(shape.parts) + [len(shape.points)]
    for start, end in zip(cuts, cuts[1:]):
        points = []
        for x, y, *_ in shape.points[start:end]:
            lon, lat = transformer.transform(x, y)
            if not (math.isfinite(lon) and math.isfinite(lat) and -180 < lon < 180 and -90 < lat < 90):
                raise CheckpointError("map_geometry_invalid", "A source line has invalid transformed coordinates.")
            point = public_point((lon, lat))
            if not points or point != points[-1]:
                points.append(point)
        if len({(p.longitude, p.latitude) for p in points}) < 2:
            omitted += 1
        else:
            paths.append(tuple(points))
    return tuple(paths), omitted


def primary_context(context: PreparedContext, raw: Path) -> PrimaryLineContext:
    target = context.assets[0]
    with layer(raw, "Data1.zip", "Primary_ExportFeatures", geometry=True) as (reader, archive):
        pairs = set()
        selected = []
        for idx, record in enumerate(records(reader, ("circuit_id", "aep_circui", "aep_statio"))):
            pairs.add((record["circuit_id"], record["aep_circui"]))
            if record["circuit_id"] == target.circuit_id:
                if record["aep_circui"] != target.circuit_alias or record["aep_statio"] != target.station_alias:
                    raise CheckpointError("map_circuit_conflict", "Primary line circuit/station identity is inconsistent.")
                selected.append(idx)
        # The prepared context already validates this across device and line layers;
        # repeat the line-side bijection to fail closed on changed/ambiguous input.
        validate_crosswalk(target.circuit_id, target.circuit_alias, pairs)
        crs = CRS.from_wkt(archive.read("Primary_ExportFeatures.prj").decode())
        if crs.is_compound:
            crs = crs.sub_crs_list[0]
        transform = Transformer.from_crs(crs, 4326, always_xy=True)
        paths = []
        omitted = 0
        for idx in selected:
            parts, collapsed = generalized_line_parts(reader.shape(idx), transform)
            paths.extend(parts)
            omitted += collapsed
    return PrimaryLineContext(status="available" if paths else "unavailable", paths=tuple(paths),
        source_segment_count=len(selected), omitted_collapsed_parts=omitted,
        note="Generalized primary line context for the verified circuit; not a service route, current outage boundary or verified electrical path. Parts smaller than the privacy grid are omitted.")


def prepare_map(context: PreparedContext, raw: Path = RAW) -> GeographicMap:
    if tuple(sorted(verify_sources(raw).items())) != context.source_hashes:
        raise CheckpointError("map_source_changed", "Map sources do not match the verified analysis snapshot.")
    location = context.location
    assets = [GeographicAsset(alias=location.alias, label=location.label, kind="customer",
        position=location.map_position, geometry_status="verified_generalized" if location.map_position else "unavailable",
        source_layer="Customer_Clip", provenance="verified_customer_record")]
    kinds = {"Distribution": ("transformer", "Distribution transformer", "Transformer_Clip"),
             "Fuse": ("fuse", "Fuse", "Fuse_Bank_Clip"),
             "Circuit Breaker": ("circuit_terminal", "Circuit Breaker terminal", None)}
    for asset in location.upstream_assets:
        kind, label, source = kinds[asset.kind]
        assets.append(GeographicAsset(alias=asset.alias, label=label, kind=kind,
            position=asset.map_position, geometry_status="verified_generalized" if asset.map_position else "unavailable",
            source_layer=source, provenance="abstract_circuit_terminal" if kind == "circuit_terminal" else "verified_typed_upstream_id"))
    try:
        lines = primary_context(context, raw)
    except (CheckpointError, ValueError, shapefile.ShapefileException):
        # Do not invent a line on an ambiguous join or bad geometry. Validated points
        # still support a useful map, and the analysis remains independent.
        lines = PrimaryLineContext(status="unavailable", paths=(), source_segment_count=0, omitted_collapsed_parts=0,
            note="Primary line context is unavailable because source geometry or circuit identity could not be verified.")
    return GeographicMap(location_alias=location.alias, data_snapshot=SNAPSHOT, assets=tuple(assets), primary_lines=lines,
        disclosures=("Locations and line vertices are generalized to 0.01° cells (roughly 1 km); exact positions are not shown.",
                     "Customer and transformer share a generalized cell; this does not imply they occupy the same physical point. Do not use this view for routing or distance measurement.",
                     "Circuit Breaker terminal has no supplied geometry and appears only in the dependency schematic.",
                     "Map = source-derived geography. Schematic = verified dependency order. Neither shows live outage or switching status."))
