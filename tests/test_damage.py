"""Historical spatial assignment gates and independent raw-source fixtures."""
from dataclasses import replace
from datetime import date
import json
import socket
import unittest
from unittest.mock import patch

from backend.damage import (DAMAGE_POLICY, DamageDevice, DamageMatcher,
                            DamageObservation, DamagePole, prepare_damage_audit)
from backend.data import TopologyToken, source_hashes


class DamagePolicyTests(unittest.TestCase):
    def setUp(self):
        self.device = DamageDevice(1, "Fuse Bank", ("eo_isolating_eqpt_inst", "synthetic-fuse"),
            "Fuse", "synthetic-pole", "synthetic-code", "synthetic-alias", "synthetic-station", (0., 0.))
        self.poles = (DamagePole(1, "synthetic-pole", (0., 3.)), DamagePole(2, "other-pole", (0., 40.)))
        self.token = TopologyToken(*self.device.key, "Fuse", "synthetic-pole")
        self.observation = DamageObservation(1, "Fuse Bank", "synthetic-alias", "synthetic-station", (0., 0.), date(2025, 1, 1), "Yes")

    def match(self, devices=None, poles=None, tokens=None, pairs=None, observation=None):
        return DamageMatcher(devices or (self.device,), self.poles if poles is None else poles,
            {self.token.key: self.token} if tokens is None else tokens,
            {("synthetic-code", "synthetic-alias")} if pairs is None else pairs).match(observation or self.observation)

    def test_unique_exact_geometry_retains_spatial_hypothesis(self):
        match = self.match()
        self.assertEqual(match.status, "spatial_candidate")
        self.assertEqual(match.asset_key, self.device.key)
        self.assertEqual(match.distance_m, 0)
        self.assertTrue(match.pole_bridge)
        self.assertNotIn("synthetic-fuse", repr(match))
        self.assertIn("nearest_pole", match.method)

    def test_nearby_runner_up_outside_max_distance_is_still_ambiguous(self):
        # Distances24/26m: runner-up must not disappear outside25m radius.
        first = replace(self.device, point=(24., 0.))
        second = replace(self.device, row=2, key=("eo_isolating_eqpt_inst", "second"), point=(26., 0.))
        result = self.match(devices=(first, second), poles=(DamagePole(1, "synthetic-pole", (24., 0.)),))
        self.assertIsNone(result.asset_key)
        self.assertIn("device_ambiguous", result.reasons)
        self.assertEqual(result.runner_up_distance_m, 26)

    def test_coincident_devices_are_not_resolved_by_first_match(self):
        second = replace(self.device, row=2, key=("eo_isolating_eqpt_inst", "second"))
        result = self.match(devices=(self.device, second))
        self.assertIsNone(result.asset_key)
        self.assertIn("device_ambiguous", result.reasons)

    def test_nearest_pole_label_conflict_is_unavailable(self):
        result = self.match(poles=(DamagePole(1, "other-label", (0., 2.)), DamagePole(2, "synthetic-pole", (0., 50.))))
        self.assertIsNone(result.asset_key)
        self.assertFalse(result.pole_bridge)
        self.assertIn("missing_or_conflicting_pole_location_bridge", result.reasons)

    def test_duplicate_pole_labels_and_close_poles_are_unavailable(self):
        result = self.match(poles=(DamagePole(1, "synthetic-pole", (0., 2.)), DamagePole(2, "synthetic-pole", (0., 3.))))
        self.assertIsNone(result.asset_key)
        self.assertIn("pole_ambiguous", result.reasons)
        self.assertIn("missing_or_conflicting_pole_location_bridge", result.reasons)

    def test_missing_or_mismatched_typed_id_never_exports_candidate_key(self):
        for tokens in ({}, {self.token.key: replace(self.token, location_code="other-location")},
                       {self.token.key: replace(self.token, kind="Switch")}):
            with self.subTest(tokens_present=bool(tokens)):
                result = self.match(tokens=tokens)
                self.assertIsNone(result.asset_key)
                self.assertIn("unresolved_typed_equipment_identity", result.reasons)

    def test_ambiguous_circuit_and_different_station_fail_closed(self):
        result = self.match(pairs={("synthetic-code", "synthetic-alias"), ("other-code", "synthetic-alias")})
        self.assertIsNone(result.asset_key)
        self.assertIn("ambiguous_circuit_crosswalk", result.reasons)
        result = self.match(observation=replace(self.observation, station_alias="other-station"))
        self.assertIsNone(result.asset_key)
        self.assertIn("no_same_type_circuit_station_device", result.reasons)

    def test_pole_observation_is_not_a_complete_electrical_dependency(self):
        result = self.match(observation=replace(self.observation, asset_type="Pole"))
        self.assertIsNone(result.asset_key)
        self.assertIn("unsupported_asset_type", result.reasons)
        self.assertIsNotNone(result.pole_distance_m)


class RealDamageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes_before = source_hashes()
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network use")):
            cls.audit = prepare_damage_audit()

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.hashes_before:
            raise AssertionError("Damage audit modified raw sources")

    def test_observed_fuse_fixture_uses_documented_spatial_bridge(self):
        match = self.audit.for_row(933)
        self.assertEqual(match.status, "spatial_candidate")
        self.assertEqual(match.device_row, 6271)
        self.assertEqual(match.pole_row, 69624)
        self.assertAlmostEqual(match.distance_m, 0., places=6)
        self.assertAlmostEqual(match.runner_up_distance_m, 53.640, places=3)
        self.assertAlmostEqual(match.pole_distance_m, 5.765, places=3)
        self.assertAlmostEqual(match.pole_runner_up_distance_m, 31.378, places=3)
        self.assertTrue(match.pole_bridge)
        self.assertEqual(match.report_date, date(2025, 2, 13))
        self.assertIsNotNone(match.asset_key)

    def test_no_historical_assignment_is_fabricated_for_golden_or_proxy_assets(self):
        self.assertFalse(any(m.status == "spatial_candidate" and m.asset_type == "Fuse Bank" and m.device_row in (6096, 2557) for m in self.audit.matches))
        self.assertFalse(any(m.status == "spatial_candidate" and m.asset_type == "Transformer" and m.device_row == 24215 for m in self.audit.matches))

    def test_primary_near_metadata_cannot_be_mistaken_for_meter_asset_identity(self):
        evidence = self.audit.near_source
        self.assertTrue(evidence.verified_metadata)
        self.assertEqual((evidence.target_layer, evidence.search_radius, evidence.method), ("Primary_ExportFeatures", "200 Feet", "PLANAR"))
        self.assertFalse(evidence.fid_is_asset_identifier)
        self.assertFalse(evidence.distance_is_meters)

    def test_aggregate_allowlist_and_all_record_coverage(self):
        summary = self.audit.safe_summary()
        self.assertEqual(summary["observations"], 1659)
        self.assertGreater(summary["candidate_observations"], 0)
        self.assertEqual(summary["max_distance_m"], DAMAGE_POLICY.max_distance_m)
        serialized = json.dumps(summary)
        for forbidden in ("asset_key", "source_row", "device_row", "pole_row", "longitude", "latitude", "premise", "road_name"):
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(summary["historical_only"])
        self.assertFalse(summary["direct_identifier_join"])
        self.assertFalse(summary["reverse_dependencies_validated"])


if __name__ == "__main__":
    unittest.main()
