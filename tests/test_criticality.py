"""Real-source spatial proxies retain uncertainty and every inventory outcome."""
from collections import Counter
from unittest import TestCase

from backend.criticality import prepare_facility_proxies
from backend.data import source_hashes
from backend.network import prepare_network
from backend.spatial import ProximityPolicy


class CriticalityTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_hashes()
        cls.network = prepare_network()
        cls.proxies = prepare_facility_proxies(cls.network)

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.before:
            raise AssertionError("Facility preparation changed raw data")

    def feature(self, kind, row):
        return next(f for f in self.proxies if f.kind == kind and f.source_row == row)

    def test_full_inventory_and_explicit_outcomes(self):
        self.assertEqual(Counter(f.kind for f in self.proxies),
                         {"hospital": 5, "fire_station": 37, "ambulance": 10})
        self.assertEqual(Counter(f.status for f in self.proxies),
                         {"spatial_proxy": 21, "ambiguous": 11, "unmatched": 20})
        self.assertEqual(sum(f.path_validated is True for f in self.proxies), 4)
        self.assertTrue(all(f.verified_electrical_attachment is None for f in self.proxies))

    def test_clear_facility_proxy_and_exact_source_dependencies_remain_separate(self):
        proxy = self.feature("fire_station", 25)
        self.assertEqual(proxy.status, "spatial_proxy")
        self.assertEqual(proxy.nearest_customer_row, 82367)
        self.assertEqual(proxy.runner_up_customer_row, 33112)
        self.assertAlmostEqual(proxy.nearest_distance_m, 14.759, places=3)
        self.assertAlmostEqual(proxy.runner_up_distance_m, 50.999, places=3)
        self.assertTrue(proxy.path_validated)
        key = self.network.key_for_locator("Fuse_Bank_Clip", 2557)
        dependents = self.network.dependents(key)
        self.assertEqual(len(dependents), 1)
        self.assertIn(proxy.premise, dependents)
        self.assertIsNone(proxy.verified_electrical_attachment)
        self.assertNotIn(proxy.premise, repr(proxy))

    def test_golden_extent_facility_is_ambiguous_and_not_golden_attachment(self):
        proxy = self.feature("fire_station", 24)
        self.assertEqual(proxy.status, "ambiguous")
        self.assertEqual(proxy.nearest_customer_row, 1079)
        self.assertAlmostEqual(proxy.runner_up_gap_m, 3.303, places=3)
        self.assertIsNone(proxy.premise)
        nearest = next(c for c in self.network.customers if c.source_row == 1079)
        golden = self.network.key_for_locator("Fuse_Bank_Clip", 6096)
        self.assertNotIn(nearest.premise, self.network.dependents(golden))
        self.assertTrue(self.network.path_reasons[nearest.premise])

    def test_colocated_and_distant_sources_are_not_forced_to_match(self):
        tie = self.feature("fire_station", 36)
        self.assertEqual(tie.status, "ambiguous")
        self.assertAlmostEqual(tie.runner_up_gap_m, 0)
        self.assertIsNone(tie.premise)
        distant = self.feature("fire_station", 30)
        self.assertEqual(distant.status, "unmatched")
        self.assertGreater(distant.nearest_distance_m, 5000)
        self.assertIsNone(distant.premise)

    def test_invalid_nearest_path_is_retained_without_substituting_another_premise(self):
        invalid = self.feature("fire_station", 1)
        self.assertEqual(invalid.status, "spatial_proxy")
        self.assertFalse(invalid.path_validated)
        self.assertTrue(invalid.path_reasons)
        self.assertEqual(invalid.nearest_customer_row, 36627)

    def test_threshold_sensitivity_does_not_change_fully_validated_proxy_set(self):
        for radius, expected in ((40, 17), (75, 24)):
            proxies = prepare_facility_proxies(self.network, policy=ProximityPolicy(radius, 10))
            self.assertEqual(sum(f.status == "spatial_proxy" for f in proxies), expected)
            self.assertEqual({(f.kind, f.source_row) for f in proxies if f.path_validated},
                             {("fire_station", n) for n in (13, 18, 25, 31)})
