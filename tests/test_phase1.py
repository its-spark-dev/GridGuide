"""G1: fictional evidence integrity, mode isolation and publication boundaries."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import zipfile

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.contracts import SyntheticCatalog, SyntheticScenario
from backend.runtime import create_runtime_app
from backend.scenarios import CATALOG_PATH, CATALOG_SHA256, SyntheticCatalogError, prepare_synthetic
from backend.synthetic_api import create_synthetic_app
from research.datasets import DATASETS, DECISIONS, SourceFile, register
from scripts.check_phase1_artifact import ALLOWLIST, MANIFEST, build_artifact, inspect_artifact
from scripts.generate_synthetic import catalog_bytes, definitions

ROOT = Path(__file__).resolve().parents[1]


class SyntheticDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.raw = definitions()["scenarios"][0]

    def reject(self, mutate):
        candidate = deepcopy(self.raw)
        mutate(candidate)
        with self.assertRaises(ValidationError):
            SyntheticScenario.model_validate(candidate)

    def test_generator_reproduces_pinned_fiction_without_raw_inputs(self):
        self.assertEqual(CATALOG_PATH.read_bytes(), catalog_bytes())
        self.assertEqual(hashlib.sha256(catalog_bytes()).hexdigest(), CATALOG_SHA256)
        catalog = SyntheticCatalog.model_validate_json(catalog_bytes())
        self.assertEqual(len(catalog.scenarios), 6)
        self.assertEqual(len({s.id for s in catalog.scenarios}), 6)
        self.assertTrue(all(s.origin == "independently_authored_fiction" for s in catalog.scenarios))

    def test_modes_and_evidence_cannot_be_relabelled_observed(self):
        for field, value in (("mode", "challenge-local"), ("origin", "observed"),
                             ("observed_outages", 1), ("observed_restoration_hours", 2.0)):
            self.reject(lambda s: s.update({field: value}))
        self.reject(lambda s: s["evidence"][0].update(classification="source-derived"))
        self.reject(lambda s: s["evidence"][0].update(classification="AEP-specified"))
        self.reject(lambda s: s["evidence"][0].update(classification=["scenario assumption", "prototype policy"]))
        self.reject(lambda s: s["evidence"].pop(0))
        self.reject(lambda s: s["evidence"].append(deepcopy(s["evidence"][0])))

    def test_identifiers_are_typed_fictional_strings_and_unique(self):
        self.reject(lambda s: s["assets"][0].update(id=123))
        self.reject(lambda s: s["assets"][0].update(id="0000000123"))
        self.reject(lambda s: s["assets"].append(deepcopy(s["assets"][0])))
        self.reject(lambda s: s["customer_paths"].append(deepcopy(s["customer_paths"][0])))
        self.reject(lambda s: s["repairs"][0].update(id=s["assets"][0]["id"]))

    def test_undefined_ambiguous_and_cyclic_topology_is_rejected(self):
        self.reject(lambda s: s["links"][0].update(upstream_id="syn-missing-asset"))
        self.reject(lambda s: s["links"].append(deepcopy(s["links"][0])))
        self.reject(lambda s: s["links"][0].update(upstream_id=s["links"][1]["downstream_id"]))
        self.reject(lambda s: s["links"][0].update(downstream_id=s["assets"][0]["id"]))

    def test_paths_must_resolve_explicit_links_and_abstract_terminal(self):
        self.reject(lambda s: s["customer_paths"][0].update(asset_ids=["syn-undefined"]))
        self.reject(lambda s: s["customer_paths"][0]["asset_ids"].pop())
        self.reject(lambda s: s["customer_paths"][0]["asset_ids"].pop(1))
        self.reject(lambda s: s["customer_paths"][0]["asset_ids"].insert(0, s["customer_paths"][0]["asset_ids"][0]))

    def test_repair_scope_and_precedence_are_validated_separately(self):
        self.reject(lambda s: s["repairs"][0].update(asset_id="syn-undefined"))
        self.reject(lambda s: s["repairs"][0].update(asset_id=s["assets"][0]["id"]))
        self.reject(lambda s: s["repairs"][0].update(prerequisite_ids=[s["repairs"][0]["id"]]))
        self.reject(lambda s: s["repairs"][0].update(prerequisite_ids=[s["repairs"][1]["id"]]))
        self.reject(lambda s: s["repairs"][0].update(prerequisite_ids=["syn-undefined"]))
        self.reject(lambda s: s["repairs"][1].update(asset_id=s["repairs"][0]["asset_id"]))
        self.reject(lambda s: s["repairs"][1].update(precedence_evidence_ref="ev-topology"))

    def test_person_hours_are_positive_finite_and_explicitly_missing(self):
        for value in (-1.0, 0.0, float("nan"), float("inf"), True, "5", None):
            self.reject(lambda s: s["repairs"][0].update(repair_person_hours=value))
        self.reject(lambda s: s["repairs"][0].update(elapsed_hours=1.0))

    def test_crews_people_and_unknown_efficiency_remain_distinct(self):
        for field, value in (("count", 0), ("count", 5), ("count", True), ("people_per_crew", 1),
                             ("people_per_crew", 9), ("actual_efficiency", .5), ("available_at_hours", [-1.0]),
                             ("available_at_hours", [0.0, 0.0])):
            self.reject(lambda s: s["crews"].update({field: value}))

    def test_private_fields_and_real_geometry_are_not_in_schema(self):
        for key in ("road_name", "premise_nu", "critical_c", "latitude", "longitude", "declared_needs", "source_row"):
            self.reject(lambda s: s.update({key: "private"}))
            self.reject(lambda s: s["assets"][0].update({key: "private"}))

    def test_unresolved_fixture_does_not_acquire_complete_coverage(self):
        context = prepare_synthetic()
        result = context.definition("syn-missing")
        self.assertIsNone(result.complete_dependency_customer_count)
        self.assertIsNone(result.restoration_hours)
        self.assertIsNone(result.outage_probability)
        self.assertIn("complete_dependency_evidence", result.missing_inputs)
        self.assertIn("repair_effort", result.missing_inputs)
        data = result.definition.model_dump(mode="json")
        data["topology_status"] = "valid_by_construction"
        with self.assertRaises(ValidationError):
            SyntheticScenario.model_validate(data)
        data = result.definition.model_dump(mode="json")
        data["links"][0]["status"] = "defined_in_fixture"
        with self.assertRaises(ValidationError):
            SyntheticScenario.model_validate(data)

    def test_blocked_access_never_acquires_a_clearance_duration(self):
        result = prepare_synthetic().definition("syn-blocked")
        self.assertIn("access_clearance_time", result.missing_inputs)
        self.assertIsNone(result.restoration_hours)
        self.assertFalse(result.numerical_evaluation_available)

    def test_overlap_is_unique_customers_not_sum_of_asset_memberships(self):
        result = prepare_synthetic().definition("syn-overlap")
        self.assertEqual(result.complete_dependency_customer_count, 3)
        paths = result.definition.customer_paths
        total_memberships = sum(sum(r.asset_id in p.asset_ids for p in paths) for r in result.definition.repairs)
        self.assertEqual(total_memberships, 5)

    def test_critical_service_is_explicit_fiction_not_proximity(self):
        raw = prepare_synthetic().definition("syn-critical").definition.model_dump(mode="json")
        self.assertEqual(raw["critical_services"][0]["relationship"], "explicit_fictional_dependency")
        raw["critical_services"][0]["customer_id"] = "syn-unknown"
        with self.assertRaises(ValidationError):
            SyntheticScenario.model_validate(raw)

    def test_frozen_context_and_stable_bound_fingerprints(self):
        first, second = prepare_synthetic(), prepare_synthetic()
        self.assertEqual(first.catalog().model_dump_json(), second.catalog().model_dump_json())
        with self.assertRaises(TypeError):
            first.scenarios["syn-simple"] = None
        with self.assertRaises(ValidationError):
            first.scenarios["syn-simple"].revision = 2
        for field, value in (("revision", 2), ("label", "Revised fictional label")):
            raw = definitions()
            raw["scenarios"][0][field] = value
            payload = json.dumps(raw).encode()
            with TemporaryDirectory() as d:
                p = Path(d) / "catalog.json"
                p.write_bytes(payload)
                with patch("backend.scenarios.CATALOG_SHA256", hashlib.sha256(payload).hexdigest()):
                    changed = prepare_synthetic(p)
            self.assertNotEqual(first.metadata["syn-simple"].input_fingerprint, changed.metadata["syn-simple"].input_fingerprint)

    def test_missing_tampered_symlinked_or_invalid_catalog_fails_closed(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "catalog.json"
            with self.assertRaises(SyntheticCatalogError):
                prepare_synthetic(p)
            p.write_text("private invalid text")
            with self.assertRaisesRegex(SyntheticCatalogError, "startup is withheld"):
                prepare_synthetic(p)
            link = Path(d) / "link.json"
            link.symlink_to(CATALOG_PATH)
            with self.assertRaises(SyntheticCatalogError):
                prepare_synthetic(link)
            p.write_text('{"scenarios":[]}')
            with patch("backend.scenarios.CATALOG_SHA256", hashlib.sha256(p.read_bytes()).hexdigest()):
                with self.assertRaises(SyntheticCatalogError):
                    prepare_synthetic(p)


class SyntheticApiTests(unittest.TestCase):
    def test_default_mode_explicit_mode_and_invalid_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with TestClient(create_runtime_app()) as client:
                health = client.get("/api/health").json()
                self.assertEqual(health["mode"], "synthetic-demo")
                self.assertFalse(health["external_ai_enabled"])
                self.assertNotIn("data_snapshot", health)
                self.assertFalse(health["numerical_evaluation_available"])
        with self.assertRaises(ValueError):
            create_runtime_app("private-invalid-value")
        with patch("backend.api.create_app", return_value="challenge") as legacy:
            self.assertEqual(create_runtime_app("challenge-local"), "challenge")
            legacy.assert_called_once_with()

    def test_catalog_prepares_once_and_all_definitions_are_bound(self):
        context = prepare_synthetic()
        loader = Mock(return_value=context)
        with TestClient(create_synthetic_app(loader)) as client:
            listing = client.get("/api/v2/scenarios")
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.headers["cache-control"], "no-store")
            for summary in listing.json()["scenarios"]:
                response = client.get("/api/v2/scenarios/" + summary["metadata"]["scenario_id"])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["metadata"], summary["metadata"])
            self.assertEqual(client.get("/api/v2/health").json()["mode"], "synthetic-demo")
        loader.assert_called_once_with()

    def test_legacy_and_future_numerical_routes_are_absent(self):
        with TestClient(create_synthetic_app()) as client:
            for path in ("/api/evaluate", "/api/restoration-plan", "/api/explain", "/api/v2/evaluate", "/api/v2/plans/compare", "/api/v2/simulations", "/api/v2/review-export"):
                self.assertEqual(client.post(path, json={}).status_code, 404)
            self.assertEqual(client.get("/api/map").status_code, 404)
            self.assertEqual(client.post("/api/v2/scenarios", json={}).status_code, 405)

    def test_unknown_scenario_and_runtime_errors_never_echo_input(self):
        with TestClient(create_synthetic_app(), raise_server_exceptions=False) as client:
            response = client.get("/api/v2/scenarios/private-unknown-value")
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("private-unknown-value", response.text)
            with patch("backend.scenarios.SyntheticContext.catalog", side_effect=RuntimeError("private-secret")):
                response = client.get("/api/v2/scenarios")
                self.assertEqual(response.status_code, 500)
                self.assertNotIn("private-secret", response.text)

    def test_failed_catalog_does_not_fall_back(self):
        with self.assertRaises(SyntheticCatalogError):
            with TestClient(create_synthetic_app(Mock(side_effect=SyntheticCatalogError("unavailable")))):
                self.fail("Invalid catalog must not start")

    def test_openapi_is_strict_and_never_claims_source_resolution(self):
        schema = create_synthetic_app().openapi()
        models = schema["components"]["schemas"]
        self.assertFalse(models["SyntheticScenario"]["additionalProperties"])
        self.assertNotIn("SourceFacts", models)
        self.assertNotIn("RestorationPlan", models)
        self.assertNotIn("exact_typed_id", json.dumps(schema))
        self.assertEqual(models["ScenarioDefinitionResponse"]["properties"]["outage_probability"]["type"], "null")


class PublicationArtifactTests(unittest.TestCase):
    def test_archive_reproducible_and_only_allowlisted_files(self):
        with TemporaryDirectory() as d:
            a, b = Path(d) / "a.zip", Path(d) / "b.zip"
            build_artifact(a)
            build_artifact(b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertTrue(inspect_artifact(a)["passed"])
            with zipfile.ZipFile(a) as z:
                self.assertEqual(set(z.namelist()), set(ALLOWLIST) | {MANIFEST})
                self.assertFalse(any("data/raw/" in n or "data/processed/" in n or ".git/" in n or n.endswith(".env") for n in z.namelist()))
                self.assertNotIn("backend/config.py", z.namelist())
                self.assertNotIn("backend/ai_provider.py", z.namelist())
            with self.assertRaises(FileExistsError):
                build_artifact(a)

    def test_archive_rejects_added_private_file_and_modified_allowed_content(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "artifact.zip"
            build_artifact(p)
            with zipfile.ZipFile(p, "a") as z:
                z.writestr("data/raw/private.json", "private")
            with self.assertRaises(ValueError):
                inspect_artifact(p)
            q = Path(d) / "modified.zip"
            build_artifact(q)
            with zipfile.ZipFile(q) as z:
                files = {name: z.read(name) for name in z.namelist()}
            files["backend/risk_rules.py"] += b"\n# unreviewed change\n"
            with zipfile.ZipFile(q, "w") as z:
                for name, value in files.items():
                    z.writestr(name, value)
            with self.assertRaises(ValueError):
                inspect_artifact(q)

    def test_archive_refuses_symlinked_inputs_and_source_output(self):
        with self.assertRaises(ValueError):
            build_artifact(ROOT / "data/raw/forbidden-output.zip")
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "backend").symlink_to(ROOT / "backend", target_is_directory=True)
            with self.assertRaises(ValueError):
                build_artifact(root / "artifacts/a.zip", root)

    def test_extracted_artifact_runs_without_raw_data_or_provider_imports(self):
        with TemporaryDirectory() as d:
            archive = Path(d) / "catalog.zip"
            build_artifact(archive)
            extracted = Path(d) / "isolated"
            with zipfile.ZipFile(archive) as z:
                z.extractall(extracted)
            code = r'''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
os.environ["GRIDGUIDE_MODE"] = "synthetic-demo"
os.environ["GRIDGUIDE_AI_PROVIDER"] = "gemini"
os.environ["GEMINI_API_KEY"] = "test-only-not-a-real-key"
def audit(event, args):
    if event == "socket.connect":
        raise AssertionError("External network must not be used")
    if event == "open" and isinstance(args[0], str) and ("/data/raw/" in args[0] or "/data/processed/" in args[0]):
        raise AssertionError("Challenge data must not be read")
sys.addaudithook(audit)
from fastapi.testclient import TestClient
from backend.runtime import app, create_runtime_app
with TestClient(app) as client:
    assert client.get("/api/health").json()["mode"] == "synthetic-demo"
    assert len(client.get("/api/v2/scenarios").json()["scenarios"]) == 6
    assert client.get("/api/v2/scenarios/syn-missing").json()["complete_dependency_customer_count"] is None
assert not any(m in sys.modules for m in ("backend.data", "backend.config", "backend.ai_provider", "backend.planning", "backend.api"))
assert not (Path(sys.argv[1]) / "data/raw").exists()
try:
    create_runtime_app("challenge-local")
except ModuleNotFoundError:
    pass
else:
    raise AssertionError("Artifact must not silently supply challenge mode")
print("isolated catalog passed")
'''
            result = subprocess.run([sys.executable, "-I", "-c", code, str(extracted)], cwd=extracted,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("isolated catalog passed", result.stdout)


class EvidenceRegisterTests(unittest.TestCase):
    def test_every_target_has_an_explicit_scoped_feasibility_decision(self):
        by_target = {d.target: d for d in DECISIONS}
        self.assertEqual(len(by_target), 6)
        for decision in DECISIONS:
            for field in ("unit", "horizon_and_origin", "observation_process", "inclusion_rule",
                          "licensing_gate", "coverage_gate"):
                self.assertTrue(getattr(decision, field))
            self.assertTrue(set(decision.evidence).issubset({d.id for d in DATASETS}))
            if decision.decision != "go_synthetic_only":
                self.assertTrue(decision.missing_prerequisites)
        for target in ("premise_outage_risk", "repair_task_duration", "customer_restoration_time"):
            self.assertEqual(by_target[target].decision, "no_go_current_data")
        self.assertEqual(by_target["county_reported_outage_risk"].decision, "conditional_not_cleared")

    def test_checked_in_register_reproduces(self):
        path = ROOT / "docs/research/phase1/dataset_register.json"
        self.assertEqual(json.loads(path.read_text()), json.loads(json.dumps(register())))

    def test_all_sources_separate_license_coverage_and_data_use(self):
        for record in DATASETS:
            self.assertTrue(record.license_status)
            self.assertTrue(record.coverage)
            self.assertTrue(record.data_use_feasibility)
            self.assertTrue(record.prohibited_claims)
            self.assertEqual(record.included_in_public_artifact, record.id == "synthetic-fixtures")
            if record.availability != "local_pinned":
                self.assertTrue(all(f.sha256 is None for f in record.files))
                self.assertTrue(record.unresolved_requirements)

    def test_missing_downloads_never_acquire_a_checksum(self):
        with self.assertRaises(ValueError):
            SourceFile("missing", "a" * 64, "not_acquired")
        with self.assertRaises(ValueError):
            SourceFile("missing", None, "pinned_local_bytes")


if __name__ == "__main__":
    unittest.main()
