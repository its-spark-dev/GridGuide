"""Independent distance checks, ambiguity and CRS regression cases."""
from random import Random
from unittest import TestCase

from pyproj import Geod, Transformer

from backend.spatial import (MetricPoint, MetricSpatialIndex, ProximityPolicy,
                             classify_proximity, project_point, wgs84_to_metric)


class SpatialTests(TestCase):
    def test_index_matches_exhaustive_distances_and_is_order_independent(self):
        random = Random(71)
        points = [MetricPoint(str(i), random.uniform(-100, 100), random.uniform(-100, 100))
                  for i in range(301)]
        index = MetricSpatialIndex(points)
        reverse = MetricSpatialIndex(reversed(points))
        for point in ((0.0, 0.0), (50.0, 20.0), (-110.0, 99.0)):
            expected = sorted((((p.x_m-point[0])**2+(p.y_m-point[1])**2)**0.5, p.key)
                              for p in points)
            for count in (1, 2, 9):
                actual = index.nearest(point, count)
                self.assertEqual([n.key for n in actual], [key for _, key in expected[:count]])
                for n, (distance, _) in zip(actual, expected):
                    self.assertAlmostEqual(n.distance_m, distance)
                self.assertEqual(actual, reverse.nearest(point, count))
            actual = index.within_radius(point, 20)
            self.assertEqual([n.key for n in actual], [key for distance, key in expected if distance <= 20])

    def test_ties_and_colocated_premises_remain_ambiguous(self):
        points = [MetricPoint("b", 3, 4), MetricPoint("a", 3, 4), MetricPoint("c", 30, 40)]
        for inventory in (points, list(reversed(points))):
            match = classify_proximity(MetricSpatialIndex(inventory), (0, 0))
            self.assertEqual(match.status, "ambiguous")
            self.assertEqual(match.runner_up_gap_m, 0)
            self.assertEqual((match.nearest.key, match.runner_up.key), ("a", "b"))
        self.assertEqual(classify_proximity(MetricSpatialIndex(points), (0, 0),
                                          ProximityPolicy(50, 0)).status, "ambiguous")

    def test_runner_up_outside_radius_is_still_considered(self):
        index = MetricSpatialIndex([MetricPoint("closest", 49, 0), MetricPoint("other", 51, 0)])
        result = classify_proximity(index, (0, 0))
        self.assertEqual(result.status, "ambiguous")
        self.assertEqual(result.runner_up.distance_m, 51)
        self.assertEqual(result.runner_up_gap_m, 2)

    def test_threshold_boundaries_and_missing_candidates(self):
        index = MetricSpatialIndex([MetricPoint("first", 50, 0), MetricPoint("second", 60, 0)])
        result = classify_proximity(index, (0, 0))
        self.assertEqual(result.status, "spatial_proxy")
        self.assertEqual(result.runner_up_gap_m, 10)
        self.assertEqual(classify_proximity(index, (-0.001, 0)).status, "unmatched")
        self.assertEqual(classify_proximity(MetricSpatialIndex([]), (0, 0)).status, "unmatched")
        single = classify_proximity(MetricSpatialIndex([MetricPoint("only", 0, 0)]), (0, 0))
        self.assertEqual(single.status, "spatial_proxy")
        self.assertIsNone(single.runner_up)
        self.assertIsNone(single.runner_up_gap_m)

    def test_metric_conversion_uses_xy_and_removes_mercator_distortion(self):
        start, end = (-80.1, 37.1), (-80.099, 37.1)
        metric = [wgs84_to_metric(p) for p in (start, end)]
        actual = ((metric[1][0]-metric[0][0])**2 + (metric[1][1]-metric[0][1])**2)**0.5
        distance = Geod(ellps="WGS84").inv(*start, *end)[2]
        self.assertLess(abs(actual-distance), 0.1)
        mercator = Transformer.from_crs(4326, 3857, always_xy=True).transform(*start)
        projected = project_point(mercator, 3857)
        self.assertAlmostEqual(projected[0], metric[0][0], places=6)
        self.assertAlmostEqual(projected[1], metric[0][1], places=6)
        with self.assertRaises(ValueError):
            project_point(start, 4326, 4326)

    def test_invalid_inputs_and_private_repr(self):
        with self.assertRaises(ValueError):
            MetricSpatialIndex([MetricPoint("same", 0, 0), MetricPoint("same", 1, 1)])
        with self.assertRaises(ValueError):
            MetricPoint("private", float("nan"), 0)
        with self.assertRaises(ValueError):
            ProximityPolicy(float("inf"), 10)
        with self.assertRaises(ValueError):
            MetricSpatialIndex([]).within_radius((0, 0), -1)
        with self.assertRaises(ValueError):
            MetricSpatialIndex([]).nearest((0, 0), True)
        with self.assertRaises(ValueError):
            wgs84_to_metric((37, -100))
        point = MetricPoint("private-identifier", 123.456, 789.123)
        self.assertNotIn("private-identifier", repr(point))
        self.assertNotIn("123.456", repr(point))
        self.assertNotIn("private-identifier", repr(MetricSpatialIndex([point]).nearest((0, 0))))
