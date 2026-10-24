"""The golden integration reads actual archives/workbook, not a canned result.

Tiny synthetic topology and altered in-memory inputs are used only to exercise
rejection paths and invariants, never as evidence of real AEP connectivity.
"""
from dataclasses import replace
from decimal import Decimal
import io
import json
import math
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import openpyxl
from pydantic import ValidationError
import shapefile

from backend.config import ASSUMPTIONS, RAW, ROOT, SOURCE_SHA256, Assumptions
from backend.contracts import Bounds, Evaluation, Scenario, WorkItem
from backend.data import (CheckpointError, labor_decimal, parse_topology, prepare_context, select_path,
                          source_hashes, validate_crosswalk, validate_resolved_path, verify_sources)
from backend.engine import calculate_risk, compare_access, default_scenario, evaluate


class RealPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes_before = source_hashes()
        # An outbound connection is a failure: this entire checkpoint must work offline.
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Unexpected network use")):
            cls.context = prepare_context()
        cls.base = default_scenario(cls.context)
        cls.clear = evaluate(cls.context, cls.base)
        cls.restricted = evaluate(cls.context, default_scenario(cls.context, access="restricted", scenario_revision=2))
        cls.blocked = evaluate(cls.context, default_scenario(cls.context, access="blocked", scenario_revision=3))

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.hashes_before:
            raise AssertionError("Checkpoint tests modified raw data")

    def test_golden_customer_and_path_reconcile_independently_to_source(self):
        with zipfile.ZipFile(RAW / "Data1.zip") as z:
            with shapefile.Reader(dbf=io.BytesIO(z.read("Customer_Clip.dbf"))) as reader:
                customer = reader.record(1076).as_dict()
        self.assertEqual(self.context.private_premise, customer["premise_nu"])
        self.assertEqual(self.context.private_customer_id, str(customer["id"]))
        with zipfile.ZipFile(RAW / "matched_upstream.zip") as z:
            lines = z.read("matched_upstream.txt").decode().splitlines()
        matching = [line.split("\t") for line in lines if line.split("\t")[0] == customer["premise_nu"]]
        self.assertEqual(len(matching), 1)
        original = [token.split("*") for token in matching[0][1:]]
        self.assertEqual([(a.token.entity, a.token.identifier, a.token.kind, a.token.location_code) for a in self.context.assets],
                         [tuple(t) for t in original])
        self.assertEqual([a.kind for a in self.clear.location.upstream_assets], ["Distribution", "Fuse", "Circuit Breaker"])
        self.assertEqual(len(self.clear.location.dependency_edges), 3)
        self.assertEqual(self.clear.location.unresolved_links, ())
        self.assertEqual(self.context.assets[0].token.location_code, customer["aep_xfmr_l"])
        self.assertTrue(all(a.circuit_id == customer["circuit_id"] for a in self.context.assets))

    def test_history_and_worksites_are_real_source_context(self):
        self.assertEqual(self.context.facts.historical_damage_record_count, 140)
        self.assertAlmostEqual(self.context.transformer_fuse_distance_m, 140.2660031303659, places=5)
        self.assertEqual(self.restricted.restoration.worksite_count, 2)
        self.assertEqual(self.context.assets[0].upstream_location, self.context.assets[1].token.location_code)
        self.assertEqual(self.context.assets[1].upstream_location, "CIRCUIT")

    def test_risk_is_explainable_and_not_probability(self):
        risk = self.clear.risk
        self.assertEqual((risk.score, risk.band, risk.predictive_confidence), (4, "HIGH", "LOW"))
        self.assertIsNone(risk.probability)
        self.assertEqual(sum(f.contribution_points for f in risk.factors), risk.score)
        self.assertTrue(all(f.label and f.provenance for f in risk.factors))
        self.assertTrue(risk.limitations)

    def test_risk_truth_table_and_monotonicity(self):
        # Expected published band definitions, including every feature combination.
        expected = {0: "LOW", 1: "MODERATE", 2: "MODERATE", 3: "HIGH", 4: "HIGH", 5: "SEVERE"}
        for mounting in ("Overhead", "Underground"):
            for history in (True, False):
                facts = self.context.facts.model_copy(update={"transformer_mounting": mounting, "historical_circuit_evidence": history})
                scores = []
                for storm in range(4):
                    with self.subTest(mounting=mounting, history=history, storm=storm):
                        result = calculate_risk(facts, storm)
                        score = storm + int(mounting == "Overhead") + int(history)
                        self.assertEqual(result.band, expected[score])
                        scores.append(result.score)
                self.assertEqual(scores, sorted(scores))

    def test_risk_missing_inputs_are_not_low_or_zero(self):
        cases = [(self.context.facts, None),
                 (self.context.facts.model_copy(update={"transformer_mounting": "Unknown"}), 2),
                 (self.context.facts.model_copy(update={"historical_circuit_evidence": None}), 2)]
        for facts, storm in cases:
            result = calculate_risk(facts, storm)
            self.assertEqual(result.status, "insufficient_data")
            self.assertIsNone(result.band)
            self.assertIsNone(result.score)
            self.assertTrue(result.missing_inputs)

    def test_duplicate_historical_records_cannot_inflate_risk(self):
        facts = self.context.facts.model_copy(update={"historical_damage_record_count": 280})
        self.assertEqual(calculate_risk(facts, 2), self.clear.risk)

    def test_golden_duration_recomputed_from_workbook_cells(self):
        # Deliberately bypass production rate-reading and calculation functions.
        wb = openpyxl.load_workbook(RAW / "Install_Labor_HackOHIO.xlsx", data_only=True, read_only=True)
        try:
            sheet = wb["Labor time material related"]
            source_direct = sum(float(sheet[c].value) for c in ("A90", "B90", "C25", "D25"))
            ilm = float(wb["Indirect Labor Multiplier"]["B1"].value)
            adder = float(wb["Labor only work"]["D2"].value)
        finally:
            wb.close()
        expected_clear = source_direct * ilm
        expected_restricted = (source_direct + 2 * adder) * ilm
        for actual, expected in ((self.clear, expected_clear), (self.restricted, expected_restricted)):
            self.assertAlmostEqual(actual.restoration.total_person_hours, expected, places=10)
            self.assertAlmostEqual(actual.restoration.raw_hours.upper, expected, places=10)
            self.assertAlmostEqual(actual.restoration.raw_hours.lower, expected / 4, places=10)
            self.assertLessEqual(actual.restoration.raw_hours.lower, actual.restoration.raw_hours.upper)
            self.assertEqual(actual.restoration.display_hours.lower, math.floor((expected / 4) * 2) / 2)
            self.assertEqual(actual.restoration.display_hours.upper, math.ceil(expected * 2) / 2)
        self.assertEqual(self.clear.restoration.display_hours, Bounds(lower=2.5, upper=12))
        self.assertEqual(self.restricted.restoration.display_hours, Bounds(lower=4, upper=16.5))

    def test_blocked_access_withdraws_finite_estimate(self):
        result = self.blocked.restoration
        self.assertEqual(result.status, "pending_clearance")
        self.assertIsNone(result.raw_hours)
        self.assertIsNone(result.display_hours)
        self.assertIsNone(result.access_labor_hours)
        self.assertIn("access_clearance_time", result.missing_inputs)
        self.assertEqual(self.blocked.risk, self.clear.risk)

    def test_restricted_access_never_improves_bounds(self):
        self.assertGreater(self.restricted.restoration.raw_hours.lower, self.clear.restoration.raw_hours.lower)
        self.assertGreater(self.restricted.restoration.raw_hours.upper, self.clear.restoration.raw_hours.upper)
        self.assertEqual(self.restricted.risk, self.clear.risk)

    def test_repeated_evaluation_is_byte_identical_and_reset_restores_result(self):
        baseline = self.clear.model_dump_json()
        evaluate(self.context, default_scenario(self.context, access="restricted"))
        self.assertEqual(evaluate(self.context, self.base).model_dump_json(), baseline)
        self.assertEqual(evaluate(self.context, self.base).model_dump_json(), baseline)

    def test_serial_crew_plateau_and_zero_crew_gate(self):
        for count in (1, 2, 3, 4):
            result = evaluate(self.context, default_scenario(self.context, crew_count=count))
            self.assertEqual(result.restoration.raw_hours, self.clear.restoration.raw_hours)
            self.assertEqual(result.risk, self.clear.risk)
        zero = evaluate(self.context, default_scenario(self.context, crew_count=0))
        self.assertEqual(zero.restoration.status, "pending_assignment")
        self.assertIsNone(zero.restoration.raw_hours)

    def test_quantity_and_access_invariants_across_supported_range(self):
        previous = 0
        for quantity in range(1, 11):
            items = tuple(w.model_copy(update={"quantity": quantity}) if w.recipe.startswith("transformer-") else w for w in self.base.work_items)
            clear = evaluate(self.context, default_scenario(self.context, work_items=items))
            restricted = evaluate(self.context, default_scenario(self.context, work_items=items, access="restricted"))
            self.assertGreater(clear.restoration.raw_hours.lower, previous)
            self.assertGreaterEqual(restricted.restoration.raw_hours.lower, clear.restoration.raw_hours.lower)
            self.assertGreaterEqual(restricted.restoration.raw_hours.upper, clear.restoration.raw_hours.upper)
            self.assertEqual(restricted.restoration.worksite_count, 2)
            self.assertEqual(restricted.risk, self.clear.risk)
            previous = clear.restoration.raw_hours.lower
            if quantity == 2:
                self.assertEqual(clear.restoration.display_hours, Bounds(lower=5, upper=22))

    def test_synthetic_colocated_jobs_pay_access_once(self):
        # Explicit unit-test counterexample, not a claim about the actual golden geometry.
        assets = (replace(self.context.assets[0], point=self.context.assets[1].point), *self.context.assets[1:])
        colocated = replace(self.context, assets=assets)
        result = evaluate(colocated, default_scenario(colocated, access="restricted"))
        self.assertEqual(result.restoration.worksite_count, 1)
        self.assertAlmostEqual(result.restoration.access_labor_hours, float(self.context.labor.restricted_access_hours))
        self.assertEqual(result.restoration.display_hours, Bounds(lower=3, upper=14))

    def test_actual_dependency_order_is_reversed_for_repairs(self):
        stages = self.clear.restoration.repair_stages
        self.assertEqual([s.node_alias for s in stages], [a.alias for a in reversed(self.context.assets[:-1])])
        self.assertEqual(stages[0].depends_on_task_ids, ())
        self.assertEqual(stages[1].depends_on_task_ids, (stages[0].task_id,))

    def test_no_damage_input_is_not_a_zero_hour_restoration_claim(self):
        result = evaluate(self.context, default_scenario(self.context, work_items=()))
        self.assertEqual(result.restoration.status, "insufficient_data")
        self.assertIsNone(result.restoration.raw_hours)
        self.assertIsNone(result.confirmed_utility.outage_status)

    def test_aep_unit_semantics_and_unknown_efficiency_are_separate(self):
        result = self.clear
        self.assertEqual(result.source_facts.labor_unit_status, 'AEP_direct_labor_times_4_5_is_person_hours')
        self.assertEqual(result.restoration.effort_unit, 'person-hours')
        self.assertEqual(result.restoration.unit, 'elapsed hours')
        self.assertIsNone(result.restoration.actual_conversion_efficiency)
        self.assertAlmostEqual(result.restoration.installation_direct_hours * 4.5, 6.912)
        self.assertAlmostEqual(result.restoration.removal_direct_hours * 4.5, 4.824)
        self.assertEqual(result.restoration.total_person_hours, 11.736)
        self.assertNotEqual(result.restoration.raw_hours.lower, result.restoration.total_person_hours)
        self.assertEqual(next(a.classification for a in result.assumptions if a.id == 'productivity'), 'unavailable')
        self.assertFalse(hasattr(ASSUMPTIONS, 'reference_crew_hours_per_labor_hour'))

    def test_synthetic_changed_source_rate_changes_output(self):
        # Proves the engine uses rates, not hard-coded final golden numbers.
        recipes = tuple(replace(r, install_hours=r.install_hours + Decimal("1")) if r.asset_kind == "Distribution" else r for r in self.context.labor.recipes)
        changed = replace(self.context, labor=replace(self.context.labor, recipes=recipes))
        result = evaluate(changed, default_scenario(changed))
        self.assertAlmostEqual(result.restoration.raw_hours.lower - self.clear.restoration.raw_hours.lower,
                               float(self.context.labor.indirect_multiplier) / self.base.crew_size)

    def test_comparison_exposes_causal_delta_without_llm(self):
        comparison = compare_access(self.clear, self.restricted)
        lower = next(c for c in comparison.changes if c.field.endswith("raw_hours.lower"))
        self.assertEqual(lower.delta, 1.125)
        self.assertIn("restricted-access-work", lower.cause_factor_ids)
        available_ids = {f.id for f in self.restricted.restoration.factors}
        self.assertTrue(all(set(c.cause_factor_ids) <= available_ids for c in comparison.changes))
        self.assertEqual(comparison.explanation_kind, "deterministic_calculation_summary")
        self.assertIsNone(self.restricted.generated_explanation)
        self.assertIn("withdrawn", compare_access(self.clear, self.blocked).explanation)

    def test_comparison_rejects_other_changed_assumptions(self):
        changed = evaluate(self.context, default_scenario(self.context, access="restricted", storm_level=3))
        with self.assertRaisesRegex(CheckpointError, "identical non-access"):
            compare_access(self.clear, changed)

    def test_comparison_rejects_synthetic_changed_labor_context(self):
        recipes = tuple(replace(r, install_hours=r.install_hours + Decimal("1")) for r in self.context.labor.recipes)
        changed = replace(self.context, labor=replace(self.context.labor, recipes=recipes))
        result = evaluate(changed, default_scenario(changed, access="restricted"))
        with self.assertRaisesRegex(CheckpointError, "identical non-access"):
            compare_access(self.clear, result)

    def test_comparison_exposes_withdrawal_and_recovery_as_null_transitions(self):
        for before, after in ((self.clear, self.blocked), (self.blocked, self.clear)):
            comparison = compare_access(before, after)
            lower = next(c for c in comparison.changes if c.field.endswith("raw_hours.lower"))
            self.assertIsNone(lower.delta)
            self.assertEqual(lower.before, None if before.restoration.raw_hours is None else before.restoration.raw_hours.lower)
            self.assertEqual(lower.after, None if after.restoration.raw_hours is None else after.restoration.raw_hours.lower)
            self.assertTrue(lower.cause_factor_ids)

    def test_public_contract_roundtrip_and_no_source_identity_leak(self):
        raw = self.clear.model_dump_json()
        self.assertEqual(Evaluation.model_validate_json(raw), self.clear)
        private_values = [self.context.private_premise, self.context.private_customer_id]
        for asset in self.context.assets:
            private_values += [asset.token.identifier, asset.token.location_code, asset.circuit_id, asset.circuit_alias, asset.station_alias]
        for value in private_values:
            if value:
                self.assertNotIn(json.dumps(value), raw)
        forbidden = {"premise_nu", "location_n", "aep_xfmr_l", "road_name", "anno_strin", "critical_c", "Reporting_", "Reporting1", "ADDRESS", "NAME", "private_premise", "private_customer_point"}
        def inspect(obj):
            if isinstance(obj, dict):
                self.assertFalse(forbidden & obj.keys())
                for value in obj.values(): inspect(value)
            elif isinstance(obj, list):
                for value in obj: inspect(value)
        inspect(json.loads(raw))
        self.assertTrue(self.clear.location.map_position.approximate)
        p = self.clear.location.map_position
        self.assertNotEqual((p.longitude, p.latitude), self.context.private_customer_point)
        self.assertLessEqual(abs(p.longitude-self.context.private_customer_point[0]), 0.00500001)
        self.assertLessEqual(abs(p.latitude-self.context.private_customer_point[1]), 0.00500001)
        self.assertIsNone(self.clear.location.upstream_assets[-1].map_position)

    def test_unknown_or_mismatched_repairs_fail_even_if_access_blocked(self):
        for changes, code in (({"recipe": "wire-repair"}, "unsupported_recipe"),
                              ({"node_alias": "invented-node"}, "unknown_repair_node"),
                              ({"recipe": "transformer-100kva-replace"}, "recipe_asset_mismatch")):
            items = (self.base.work_items[0].model_copy(update=changes), self.base.work_items[1])
            with self.subTest(code=code), self.assertRaises(CheckpointError) as caught:
                evaluate(self.context, default_scenario(self.context, work_items=items, access="blocked"))
            self.assertEqual(caught.exception.code, code)

    def test_invalid_numeric_and_duplicate_task_inputs(self):
        for field, value in (("crew_count", -1), ("crew_count", True), ("crew_count", 1.5), ("crew_count", 5),
                             ("storm_level", 4), ("storm_level", float("nan")), ("storm_level", "2"), ("scenario_revision", 0)):
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                default_scenario(self.context, **{field: value})
        for quantity in (0, -1, 1.5, True, 11, float("nan")):
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                WorkItem(task_id="test", node_alias="protective-a", recipe="fuse-cutout-replace", quantity=quantity)
        with self.assertRaises(ValidationError):
            default_scenario(self.context, work_items=(self.base.work_items[0], self.base.work_items[0]))
        bad = self.base.model_copy(update={"crew_count": -1})
        with self.assertRaises(ValidationError): evaluate(self.context, bad)

    def test_actual_path_validation_rejects_missing_or_inconsistent_assets(self):
        customer = {"aep_xfmr_l": self.context.assets[0].token.location_code, "circuit_id": self.context.assets[0].circuit_id}
        path = tuple(a.token for a in self.context.assets)
        with self.assertRaises(CheckpointError): validate_resolved_path(customer, path, self.context.assets[:-1])
        altered = (replace(self.context.assets[0], upstream_location="not-the-real-parent"), *self.context.assets[1:])
        with self.assertRaises(CheckpointError): validate_resolved_path(customer, path, altered)

    def test_modified_source_copy_is_rejected_before_golden_lookup(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "raw"
            shutil.copytree(RAW, copied)
            with (copied / "Data1.zip").open("ab") as f:
                f.write(b"test mutation of a disposable copy")
            with self.assertRaises(CheckpointError) as caught:
                prepare_context(copied)
            self.assertEqual(caught.exception.code, "source_hash_mismatch")
        self.assertEqual(source_hashes(), self.hashes_before)

    def test_unknown_location_is_rejected_not_replaced_with_golden(self):
        with self.assertRaises(CheckpointError) as caught:
            prepare_context(location_alias="unverified-customer")
        self.assertEqual(caught.exception.code, "unsupported_location")

    def test_cli_complete_flow_is_reproducible_across_processes(self):
        command = [sys.executable, "-m", "backend.demo", "--json"]
        first = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        second = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, "")
        payload = json.loads(first.stdout)
        self.assertEqual([r["simulated_inputs"]["access"] for r in payload["results"]], ["clear", "restricted", "blocked"])
        self.assertEqual(len(payload["comparisons"]), 2)
        for result in payload["results"]: Evaluation.model_validate(result)

    def test_cli_unsupported_location_exits_clearly(self):
        result = subprocess.run([sys.executable, "-m", "backend.demo", "--location", "unknown", "--json"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["error"]["code"], "unsupported_location")


class TopologyAndContractTests(unittest.TestCase):
    def test_synthetic_leading_zero_premise_is_preserved(self):
        index = parse_topology(["000123\teo_power_xfrmr_inst*10*Distribution*loc\teo_circuit*20*Circuit Breaker*0007\n"])
        self.assertIn("000123", index.paths)
        self.assertNotIn("123", index.paths)
        self.assertEqual(len(select_path(index, "000123")), 2)
        with self.assertRaises(CheckpointError): select_path(index, "123")

    def test_synthetic_conflicting_parent_is_not_silently_chosen(self):
        index = parse_topology([
            "p1\teo_power_xfrmr_inst*10*Distribution*t\teo_circuit*20*Circuit Breaker*c1",
            "p2\teo_power_xfrmr_inst*10*Distribution*t\teo_circuit*21*Circuit Breaker*c2",
        ])
        with self.assertRaises(CheckpointError) as caught: select_path(index, "p1")
        self.assertEqual(caught.exception.code, "ambiguous_parent")

    def test_malformed_duplicate_repeated_and_union_cycle_rejected(self):
        cases = [(["p\tbad-token"], "malformed_topology"),
                 (["p\tx*1*a*l", "p\tx*1*a*l"], "duplicate_premise"),
                 (["p\tx*1*a*l\tx*1*a*l"], "topology_cycle"),
                 (["p1\tx*1*a*l1\tx*2*b*l2", "p2\tx*2*b*l2\tx*1*a*l1"], "topology_cycle"),
                 (["p1\tx*1*a*l1", "p2\tx*1*a*l2"], "conflicting_node_metadata")]
        for lines, code in cases:
            with self.subTest(code=code), self.assertRaises(CheckpointError) as caught: parse_topology(lines)
            self.assertEqual(caught.exception.code, code)

    def test_actual_documented_circuit_conflict_is_rejected(self):
        # Two observed CIR6 mappings from the audit, isolated as a regression fixture.
        with self.assertRaises(CheckpointError):
            validate_crosswalk("0000005", "CIR6", {("0000005", "CIR6"), ("0000006", "CIR6")})
        with self.assertRaises(CheckpointError):
            validate_crosswalk("0000005", "CIR6", {("0000005", "CIR6"), ("0000005", "CIR7")})
        validate_crosswalk("0000072", "CIR72", {("0000072", "CIR72")})

    def test_invalid_labor_values_cannot_become_zero(self):
        for value in (None, -1, "0.5", float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(CheckpointError): labor_decimal(value)
        self.assertEqual(labor_decimal(0), Decimal(0))

    def test_bounds_validate_and_extra_public_fields_are_rejected(self):
        with self.assertRaises(ValidationError): Bounds(lower=5, upper=4)
        with self.assertRaises(ValidationError): Bounds(lower=float("nan"), upper=4)
        with self.assertRaises(ValidationError): Bounds(lower=1, upper=2, premise_nu="private")

    def test_source_pins_match(self):
        self.assertEqual(verify_sources(), SOURCE_SHA256)


if __name__ == "__main__":
    unittest.main()
