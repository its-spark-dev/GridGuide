"""Private facility proximity hypotheses, separate from electrical attachment.

Every supplied hospital/fire/ambulance feature receives an outcome. The nearest
premise is selected from the entire customer inventory, before topology checks;
an unresolved nearest path is never replaced by a more convenient premise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .config import RAW
from .data import layer
from .spatial import (MetricPoint, MetricSpatialIndex, ProximityMatch, ProximityPolicy,
                      classify_proximity, horizontal_crs, project_point, wgs84_to_metric)

if TYPE_CHECKING:
    from .network import NetworkIndex


FACILITY_POLICY = ProximityPolicy(max_distance_m=50.0, min_runner_up_gap_m=10.0)
FACILITY_POLICY_VERSION = "facility-proximity-50m-gap10m-v1"
FACILITY_LAYERS = (
    ("hospital", "Hospitals_Medic_Pairwis_Clip"),
    ("fire_station", "Fire_Stations_E_Pairwis_Clip"),
    ("ambulance", "Ambulance_Servi_Pairwis_Clip"),
)


@dataclass(frozen=True)
class FacilityProxy:
    """Internal provenance only; build an explicit public allowlist separately."""
    kind: str
    source_layer: str
    source_row: int = field(repr=False)
    status: Literal["spatial_proxy", "ambiguous", "unmatched"]
    premise: str | None = field(repr=False)
    nearest_customer_row: int | None = field(repr=False)
    runner_up_customer_row: int | None = field(repr=False)
    nearest_distance_m: float | None
    runner_up_distance_m: float | None
    runner_up_gap_m: float | None
    path_validated: bool | None
    path_reasons: tuple[str, ...]
    policy: ProximityPolicy
    # No source here establishes the facility's actual electrical attachment.
    verified_electrical_attachment: None = field(default=None, init=False)


def _proxy(kind: str, stem: str, row: int, match: ProximityMatch,
           customers_by_row: dict, network: NetworkIndex) -> FacilityProxy:
    nearest = customers_by_row[match.nearest.key] if match.nearest else None
    runner_up = customers_by_row[match.runner_up.key] if match.runner_up else None
    premise = nearest.premise if nearest and match.status == "spatial_proxy" else None
    reasons: tuple[str, ...] = ()
    path_validated = None
    if premise is not None:
        reasons = network.path_reasons.get(premise, ("missing_topology",))
        path_validated = not reasons
    return FacilityProxy(kind, stem, row, match.status, premise,
                         nearest.source_row if nearest else None,
                         runner_up.source_row if runner_up else None,
                         match.nearest.distance_m if match.nearest else None,
                         match.runner_up.distance_m if match.runner_up else None,
                         match.runner_up_gap_m, path_validated, reasons, match.policy)


def prepare_facility_proxies(network: NetworkIndex, raw: Path = RAW,
                             policy: ProximityPolicy = FACILITY_POLICY) -> tuple[FacilityProxy, ...]:
    """Return every source feature, including ambiguous/unmatched hypotheses.

50 meters and a 10-meter runner-up gap are prototype choices. AEP supplies no
matching radius or positional-accuracy guarantee. Even an accepted proximity
hypothesis with a valid premise path has unknown facility electrical attachment.
"""
    customers_by_row = {str(c.source_row): c for c in network.customers}
    if len(customers_by_row) != len(network.customers):
        raise ValueError("Customer source row locators must be unique.")
    points = (MetricPoint(key, *wgs84_to_metric(customer.point))
              for key, customer in customers_by_row.items())
    index = MetricSpatialIndex(points)
    proxies = []
    for kind, stem in FACILITY_LAYERS:
        with layer(raw, "Data1.zip", stem, geometry=True) as (reader, archive):
            crs = horizontal_crs(archive.read(stem + ".prj").decode())
            if crs.to_epsg() != 3857:
                raise ValueError("Facility source CRS changed; re-audit before proximity matching.")
            for row, shape in enumerate(reader.iterShapes(), 1):
                if len(shape.points) != 1:
                    raise ValueError("Facility proximity requires one source point per feature.")
                point = project_point(tuple(shape.points[0][:2]), crs)
                match = classify_proximity(index, point, policy)
                proxies.append(_proxy(kind, stem, row, match, customers_by_row, network))
    return tuple(proxies)
