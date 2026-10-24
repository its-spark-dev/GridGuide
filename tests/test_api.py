"""HTTP integration against real prepared AEP data and the unchanged engine."""
import json
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.api import AnalysisResponse, create_app
from backend.data import CheckpointError, prepare_context, source_hashes
from backend.engine import compare_access, default_scenario, evaluate


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_hashes()
        cls.context = prepare_context()
        cls.loader = Mock(return_value=cls.context)
        cls.client = TestClient(create_app(cls.loader))
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        if source_hashes() != cls.before:
            raise AssertionError("API tests modified raw source data")

    def analyze(self, access="clear", revision=1, previous=None):
        response = self.client.post("/api/evaluate", json={
            "location_alias": "demo-a", "access": access, "scenario_revision": revision, "previous": previous})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        return AnalysisResponse.model_validate(response.json())

    def test_golden_customer_endpoint_is_public_location(self):
        response = self.client.get("/api/locations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [self.context.location.model_dump(mode="json")])
        self.assertEqual(len(response.json()[0]["dependency_edges"]), 3)

    def test_every_access_output_matches_direct_engine(self):
        for access in ("clear", "restricted", "blocked"):
            with self.subTest(access=access):
                actual = self.analyze(access).result
                expected = evaluate(self.context, default_scenario(self.context, access=access))
                self.assertEqual(actual, expected)

    def test_access_counterfactual_is_monotonic_and_risk_stable(self):
        clear = self.analyze().result
        restricted = self.analyze("restricted").result
        blocked = self.analyze("blocked").result
        self.assertGreater(restricted.restoration.raw_hours.lower, clear.restoration.raw_hours.lower)
        self.assertGreater(restricted.restoration.raw_hours.upper, clear.restoration.raw_hours.upper)
        self.assertEqual(blocked.restoration.status, "pending_clearance")
        self.assertIsNone(blocked.restoration.raw_hours)
        self.assertIsNone(blocked.restoration.display_hours)
        self.assertEqual(clear.risk, restricted.risk)
        self.assertEqual(clear.risk, blocked.risk)

    def test_all_transition_comparisons_match_engine_and_revisions(self):
        for previous in ("clear", "restricted", "blocked"):
            for access in ("clear", "restricted", "blocked"):
                with self.subTest(previous=previous, access=access):
                    before = self.analyze(previous, 3).result
                    after = self.analyze(access, 7, {"access": previous, "scenario_revision": 3})
                    self.assertEqual(after.comparison, compare_access(before, after.result))
                    self.assertEqual(after.comparison.before_result_id, before.result_id)
                    self.assertEqual(after.comparison.after_result_id, after.result.result_id)
                    self.assertTrue(after.comparison.explanation)
                    ids = {f.id for f in after.result.restoration.factors}
                    self.assertTrue(all(set(c.cause_factor_ids) <= ids for c in after.comparison.changes))

    def test_repeated_requests_are_identical(self):
        self.assertEqual(self.analyze("restricted").model_dump_json(), self.analyze("restricted").model_dump_json())

    def test_invalid_request_fields_are_rejected_without_echo(self):
        for body in ({"access": "invented-private-value"}, {"scenario_revision": True}, {"scenario_revision": "2"},
                     {"scenario_revision": 0}, {"road_name": "private-road"}, {"crew_count": 2},
                     {"scenario_revision": 2, "previous": {"access": "clear", "scenario_revision": 2}}):
            with self.subTest(body=body):
                response = self.client.post("/api/evaluate", json=body)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["error"]["code"], "invalid_input")
                self.assertNotIn("private", response.text)

    def test_unknown_location_does_not_fall_back_or_echo_identifier(self):
        response = self.client.post("/api/evaluate", json={"location_alias": "private-unknown-customer"})
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("private-unknown-customer", response.text)

    def test_public_api_does_not_leak_private_source_fields_or_values(self):
        payload = {"locations": self.client.get("/api/locations").json(),
                   "analysis": self.analyze("restricted", 2, {"access": "clear", "scenario_revision": 1}).model_dump(mode="json")}
        forbidden = {"premise_nu", "road_name", "anno_strin", "critical_c", "private_premise", "private_customer_point",
                     "location_n", "aep_xfmr_l", "ADDRESS", "NAME"}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        inspect(payload)
        raw = json.dumps(payload)
        private = [self.context.private_premise, self.context.private_customer_id]
        for asset in self.context.assets:
            private += [asset.token.identifier, asset.token.location_code, asset.circuit_id, asset.circuit_alias, asset.station_alias]
        for value in filter(None, private):
            self.assertNotIn(json.dumps(value), raw)
        self.assertIsNone(payload["analysis"]["result"]["generated_explanation"])

    def test_context_is_prepared_once_and_health_is_ready(self):
        self.client.get("/api/locations")
        self.analyze()
        response = self.client.get("/api/health")
        self.assertTrue(response.json()["ready"])
        self.loader.assert_called_once_with()

    def test_source_failure_prevents_startup(self):
        loader = Mock(side_effect=CheckpointError("source_hash_mismatch", "Source pin failed"))
        with self.assertRaises(CheckpointError):
            with TestClient(create_app(loader)):
                self.fail("Invalid sources must not start an application")

    def test_unexpected_error_returns_safe_unavailable_response(self):
        with TestClient(create_app(lambda: self.context), raise_server_exceptions=False) as client:
            with patch("backend.api.evaluate", side_effect=RuntimeError("private-secret-value")):
                response = client.post("/api/evaluate", json={"access": "clear"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "analysis_unavailable")
        self.assertNotIn("private-secret-value", response.text)

    def test_openapi_preserves_typed_result_contract(self):
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/api/evaluate", schema["paths"])
        self.assertIn("/api/locations", schema["paths"])
        self.assertIn("AnalysisResponse", schema["components"]["schemas"])
        self.assertFalse(schema["components"]["schemas"]["AnalysisRequest"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
