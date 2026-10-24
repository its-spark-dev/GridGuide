"""Private metric proximity helpers; proximity never proves electrical identity.

The point index uses only the standard library. Existing pyproj supplies CRS
conversion. Thresholds are disclosed prototype policies, not source accuracy or
AEP attachment rules. Query the complete candidate inventory before filtering
matches so a close runner-up cannot disappear behind a distance boundary.
"""
from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field
from functools import lru_cache
import math
from typing import Iterable, Literal

from pyproj import CRS, Transformer

Point = tuple[float, float]
TIE_TOLERANCE_M = 1e-6  # Numerical equality tolerance, not geolocation accuracy.


def _finite_point(point: Point) -> Point:
    if len(point) != 2 or any(isinstance(v, bool) or not math.isfinite(v) for v in point):
        raise ValueError("A spatial point must have two finite coordinates.")
    return float(point[0]), float(point[1])


@dataclass(frozen=True)
class MetricPoint:
    key: str = field(repr=False)
    x_m: float = field(repr=False)
    y_m: float = field(repr=False)

    def __post_init__(self):
        if not isinstance(self.key, str) or not self.key:
            raise ValueError("A spatial key must be a nonempty string.")
        _finite_point((self.x_m, self.y_m))


@dataclass(frozen=True)
class SpatialNeighbor:
    key: str = field(repr=False)
    distance_m: float


@dataclass(frozen=True)
class _Node:
    point: MetricPoint
    axis: int
    left: _Node | None
    right: _Node | None


class MetricSpatialIndex:
    """Balanced point tree with deterministic keys and no GIS connectivity rules."""

    def __init__(self, points: Iterable[MetricPoint]):
        inventory = tuple(points)
        if len({p.key for p in inventory}) != len(inventory):
            raise ValueError("A spatial inventory must have unique keys.")
        self.size = len(inventory)

        def build(items: list[MetricPoint], depth: int) -> _Node | None:
            if not items:
                return None
            axis = depth % 2
            items.sort(key=lambda p: ((p.x_m, p.y_m)[axis], p.key))
            middle = len(items) // 2
            return _Node(items[middle], axis, build(items[:middle], depth + 1),
                         build(items[middle + 1:], depth + 1))

        self._root = build(list(inventory), 0)

    def nearest(self, point: Point, k: int = 2) -> tuple[SpatialNeighbor, ...]:
        point = _finite_point(point)
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise ValueError("The nearest-neighbor count must be a positive integer.")
        best: list[tuple[float, str]] = []

        def visit(node: _Node | None):
            if node is None:
                return
            p = node.point
            distance_sq = (point[0] - p.x_m) ** 2 + (point[1] - p.y_m) ** 2
            insort(best, (distance_sq, p.key))
            if len(best) > k:
                best.pop()
            delta = point[node.axis] - (p.x_m, p.y_m)[node.axis]
            near, far = (node.left, node.right) if delta < 0 else (node.right, node.left)
            visit(near)
            if len(best) < k or delta * delta <= best[-1][0]:
                visit(far)

        visit(self._root)
        return tuple(SpatialNeighbor(key, math.sqrt(d)) for d, key in best)

    def within_radius(self, point: Point, radius_m: float) -> tuple[SpatialNeighbor, ...]:
        point = _finite_point(point)
        if isinstance(radius_m, bool) or not math.isfinite(radius_m) or radius_m < 0:
            raise ValueError("A spatial radius must be finite and nonnegative.")
        matches: list[tuple[float, str]] = []
        radius_sq = radius_m * radius_m

        def visit(node: _Node | None):
            if node is None:
                return
            p = node.point
            d = (point[0] - p.x_m) ** 2 + (point[1] - p.y_m) ** 2
            if d <= radius_sq:
                matches.append((d, p.key))
            delta = point[node.axis] - (p.x_m, p.y_m)[node.axis]
            if delta <= radius_m:
                visit(node.left)
            if delta >= -radius_m:
                visit(node.right)

        visit(self._root)
        return tuple(SpatialNeighbor(key, math.sqrt(d)) for d, key in sorted(matches))


@dataclass(frozen=True)
class ProximityPolicy:
    max_distance_m: float = 50.0
    min_runner_up_gap_m: float = 10.0

    def __post_init__(self):
        for value in (self.max_distance_m, self.min_runner_up_gap_m):
            if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("Spatial policy distances must be finite and nonnegative.")


@dataclass(frozen=True)
class ProximityMatch:
    status: Literal["spatial_proxy", "ambiguous", "unmatched"]
    nearest: SpatialNeighbor | None
    runner_up: SpatialNeighbor | None
    runner_up_gap_m: float | None
    policy: ProximityPolicy


def classify_proximity(index: MetricSpatialIndex, point: Point,
                       policy: ProximityPolicy = ProximityPolicy()) -> ProximityMatch:
    nearest = index.nearest(point, 2)
    first = nearest[0] if nearest else None
    second = nearest[1] if len(nearest) > 1 else None
    gap = second.distance_m - first.distance_m if first and second else None
    if first is None or first.distance_m > policy.max_distance_m:
        status = "unmatched"
    elif gap is not None and (gap <= TIE_TOLERANCE_M or gap < policy.min_runner_up_gap_m):
        status = "ambiguous"
    else:
        status = "spatial_proxy"
    return ProximityMatch(status, first, second, gap, policy)


def horizontal_crs(source_crs: CRS | str | int) -> CRS:
    crs = CRS.from_user_input(source_crs)
    return crs.sub_crs_list[0] if crs.is_compound else crs


@lru_cache(maxsize=16)
def _transformer(source_wkt: str, target_wkt: str) -> Transformer:
    return Transformer.from_crs(source_wkt, target_wkt, always_xy=True)


def project_point(point: Point, source_crs: CRS | str | int,
                  target_crs: CRS | str | int = 32617) -> Point:
    """Project horizontal coordinates to meters, with explicit x/y axis order."""
    point = _finite_point(point)
    source, target = horizontal_crs(source_crs), horizontal_crs(target_crs)
    if not target.is_projected or any(axis.unit_name != "metre" for axis in target.axis_info[:2]):
        raise ValueError("Spatial distance calculations require a projected metric CRS.")
    return _finite_point(_transformer(source.to_wkt(), target.to_wkt()).transform(*point, errcheck=True))


@lru_cache(maxsize=1)
def _wgs84_metric_transformer() -> Transformer:
    return Transformer.from_crs(4326, 32617, always_xy=True)


def wgs84_to_metric(point: Point) -> Point:
    lon, lat = _finite_point(point)
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError("A WGS84 spatial point is outside longitude/latitude bounds.")
    return _finite_point(_wgs84_metric_transformer().transform(lon, lat, errcheck=True))
