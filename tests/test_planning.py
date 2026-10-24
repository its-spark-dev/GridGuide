"""Pinned repair catalog arithmetic, bounded scheduling, uncertainty and privacy."""
from dataclasses import replace
import json
from unittest import TestCase

from pydantic import ValidationError

from backend.config import RAW
from backend.contracts import CandidateAccess, PlanRequest
from backend.data import CheckpointError, layer, source_hashes
from backend.network import public_asset_alias
from backend.plan_explanations import build_plan_context
from backend.planning import Candidate, make_plan, prepare_planning


class PlanningTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_hashes()
        cls.context = prepare_planning()
        cls.plan = make_plan(cls.context, PlanRequest())
        cls.by_label = {c.label: c for c in cls.plan.candidates}

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.before:
            raise AssertionError("Planning tests changed raw source bytes")

    def id_for(self, label):
        return self.by_label[label].id

    def request_with_access(self, label, state, **kwargs):
        return PlanRequest(access=(CandidateAccess(candidate_id=self.id_for(label), access=state),), **kwargs)

    def task_for(self, plan, label):
        return next(t for t in plan.tasks if t.candidate_id == self.id_for(label))

    def test_pinned_catalog_union_deduplication_and_labor_arithmetic(self):
        plan = self.plan
        self.assertIs(self.context, prepare_planning())
        self.assertEqual([c.dependent_premises for c in plan.candidates], [4, 1, 23, 1])
        self.assertEqual(plan.unique_dependent_premises, 28)
        self.assertEqual(plan.summed_memberships, 29)
        self.assertEqual(plan.overlap_memberships, 1)
        self.assertEqual([c.overlap_premises for c in plan.candidates], [1, 1, 0, 0])
        self.assertEqual([c.repair_person_hours for c in plan.candidates], [1.728, 10.008, 1.728, 1.728])
        self.assertAlmostEqual(plan.repair_person_hours, 15.192)
        self.assertAlmostEqual(plan.total_person_hours, 15.192)
        self.assertAlmostEqual(sum(c.direct_labor_hours for c in plan.candidates) * 4.5, 15.192)
        self.assertAlmostEqual(plan.completion_hours.lower, 3.798)
        self.assertAlmostEqual(plan.completion_hours.upper, 15.192)
        self.assertEqual((plan.display_completion_hours.lower, plan.display_completion_hours.upper), (3.75, 15.25))
        self.assertEqual(self.by_label["Golden transformer"].prerequisite_ids,
                         (self.id_for("Golden upstream fuse"),))
        self.assertEqual(self.by_label["Historical fuse replay"].damage_source, "historical ARCOS replay")
        self.assertEqual(self.by_label["Critical-context fuse"].damage_source, "declared damage scenario")

    def test_critical_proxy_toggle_changes_priority_but_not_evidence_or_effort(self):
        no_proxy = make_plan(self.context, PlanRequest(use_critical_proxy=False))
        self.assertEqual(self.plan.recommended_id, self.id_for("Critical-context fuse"))
        self.assertEqual(no_proxy.recommended_id, self.id_for("Historical fuse replay"))
        self.assertEqual([t.candidate_id for t in self.plan.tasks],
                         [self.id_for(label) for label in ("Critical-context fuse", "Historical fuse replay", "Golden upstream fuse", "Golden transformer")])
        self.assertEqual([t.candidate_id for t in no_proxy.tasks],
                         [self.id_for(label) for label in ("Historical fuse replay", "Golden upstream fuse", "Critical-context fuse", "Golden transformer")])
        for name in ("repair_person_hours", "total_person_hours", "unique_dependent_premises", "completion_hours"):
            self.assertEqual(getattr(self.plan, name), getattr(no_proxy, name))
        self.assertEqual([c.critical_proxies for c in self.plan.candidates], [c.critical_proxies for c in no_proxy.candidates])
        proxy = self.by_label["Critical-context fuse"].critical_proxies[0]
        self.assertEqual(proxy.kind, "fire_station")
        self.assertEqual((proxy.distance_m, proxy.runner_up_distance_m), (14.8, 51.0))
        self.assertIsNone(proxy.verified_electrical_attachment)

    def test_ranking_is_repeatable_and_equal_jobs_use_stable_alias(self):
        self.assertEqual(make_plan(self.context, PlanRequest()), self.plan)
        reverse = make_plan(replace(self.context, candidates=tuple(reversed(self.context.candidates))), PlanRequest())
        self.assertEqual(reverse.tasks, self.plan.tasks)
        equal = next(c for c in self.context.candidates if c.label == "Critical-context fuse")
        key = self.context.network.key_for_locator("Fuse_Bank_Clip", 2300)
        other = Candidate(key, "Equivalent effort fuse", "fuse-cutout-replace")
        context = replace(self.context, candidates=(equal, other), proxies=())
        a = make_plan(context, PlanRequest())
        b = make_plan(replace(context, candidates=(other, equal)), PlanRequest())
        self.assertEqual(a.tasks, b.tasks)
        self.assertEqual([t.candidate_id for t in a.tasks], sorted((public_asset_alias(equal.key), public_asset_alias(other.key))))

    def test_two_crews_overlap_independent_jobs_without_splitting_tasks(self):
        two = make_plan(self.context, PlanRequest(crew_count=2))
        self.assertEqual(two.repair_person_hours, self.plan.repair_person_hours)
        self.assertEqual(two.total_person_hours, self.plan.total_person_hours)
        self.assertEqual(len(two.tasks), 4)
        self.assertEqual(len({t.candidate_id for t in two.tasks}), 4)
        first, second = two.tasks[:2]
        self.assertNotEqual(first.crew, second.crew)
        self.assertEqual((first.start_hours.lower, first.start_hours.upper), (0, 0))
        self.assertEqual((second.start_hours.lower, second.start_hours.upper), (0, 0))
        self.assertAlmostEqual(two.completion_hours.upper, 13.464)
        self.assertAlmostEqual(two.completion_hours.lower, 3.366)
        self.assertLess(two.completion_hours.upper, self.plan.completion_hours.upper)
        for task in two.tasks:
            original = next(t for t in self.plan.tasks if t.candidate_id == task.candidate_id)
            self.assertAlmostEqual(task.finish_hours.upper-task.start_hours.upper,
                                   original.finish_hours.upper-original.start_hours.upper)
            self.assertAlmostEqual(task.finish_hours.lower-task.start_hours.lower,
                                   original.finish_hours.lower-original.start_hours.lower)
        upstream = self.task_for(two, "Golden upstream fuse")
        downstream = self.task_for(two, "Golden transformer")
        self.assertGreaterEqual(downstream.start_hours.lower, upstream.finish_hours.lower)
        self.assertGreaterEqual(downstream.start_hours.upper, upstream.finish_hours.upper)

    def test_extra_crews_cannot_divide_the_serial_ancestry_chain(self):
        context = replace(self.context, candidates=self.context.candidates[:2], proxies=())
        one = make_plan(context, PlanRequest(crew_count=1))
        two = make_plan(context, PlanRequest(crew_count=2))
        self.assertEqual(one.completion_hours, two.completion_hours)
        self.assertAlmostEqual(two.completion_hours.lower, 2.934)
        self.assertAlmostEqual(two.completion_hours.upper, 11.736)
        self.assertEqual([m.additional_premises for m in two.milestones], [3, 1])

    def test_people_and_crews_are_distinct_and_efficiency_stays_unknown(self):
        for crews in (1, 2):
            small = make_plan(self.context, PlanRequest(crew_count=crews, crew_size=2))
            large = make_plan(self.context, PlanRequest(crew_count=crews, crew_size=8))
            self.assertEqual(small.total_person_hours, large.total_person_hours)
            self.assertEqual(small.completion_hours.upper, large.completion_hours.upper)
            self.assertAlmostEqual(small.completion_hours.lower, large.completion_hours.lower * 4)
            self.assertEqual([t.crew for t in small.tasks], [t.crew for t in large.tasks])
            self.assertIsNone(small.actual_efficiency)
            self.assertIsNone(large.actual_efficiency)

    def test_restricted_access_adds_once_per_worksite_and_affects_effort_ranking(self):
        request = PlanRequest(access=tuple(CandidateAccess(candidate_id=c.id, access="restricted") for c in self.plan.candidates))
        restricted = make_plan(self.context, request)
        self.assertEqual(restricted.repair_person_hours, self.plan.repair_person_hours)
        self.assertAlmostEqual(restricted.total_person_hours, 15.192 + 4*2.25)
        for candidate in restricted.candidates:
            clear = self.by_label[candidate.label]
            self.assertEqual(candidate.access_direct_hours, 0.5)
            self.assertAlmostEqual(candidate.total_person_hours-clear.total_person_hours, 2.25)
        self.assertAlmostEqual(restricted.completion_hours.upper, restricted.total_person_hours)
        self.assertAlmostEqual(restricted.completion_hours.lower, restricted.total_person_hours / 4)
        one_site = make_plan(self.context, self.request_with_access("Golden upstream fuse", "restricted", use_critical_proxy=False))
        self.assertAlmostEqual(one_site.total_person_hours, 17.442)
        self.assertEqual(one_site.recommended_id, self.id_for("Historical fuse replay"))
        critical = next(c for c in one_site.candidates if c.label == "Critical-context fuse")
        self.assertAlmostEqual(critical.release_per_total_person_hour, 1/1.728)

    def test_blocked_parent_defers_descendants_and_independent_work_continues(self):
        request = self.request_with_access("Golden upstream fuse", "blocked", crew_count=2)
        plan = make_plan(self.context, request)
        candidates = {c.label: c for c in plan.candidates}
        self.assertEqual(candidates["Golden upstream fuse"].status, "blocked")
        self.assertEqual(candidates["Golden transformer"].status, "dependency_blocked")
        self.assertEqual({t.candidate_id for t in plan.tasks},
                         {self.id_for("Historical fuse replay"), self.id_for("Critical-context fuse")})
        self.assertIsNone(plan.total_person_hours)
        self.assertIsNone(plan.completion_hours)
        self.assertIsNone(plan.display_completion_hours)
        self.assertIsNotNone(plan.executable_completion_hours)
        self.assertAlmostEqual(plan.executable_completion_hours.upper, 1.728)
        self.assertEqual(plan.repair_person_hours, 15.192)
        self.assertEqual(plan.unique_dependent_premises, 28)
        self.assertEqual(plan.scheduled_release_potential, 24)
        self.assertEqual(plan.milestones[-1].cumulative_premises, 24)
        self.assertIsNone(candidates["Golden upstream fuse"].access_direct_hours)
        self.assertIsNone(candidates["Golden upstream fuse"].total_person_hours)
        self.assertIsNone(candidates["Golden transformer"].elapsed_hours)
        reverse = make_plan(replace(self.context, candidates=tuple(reversed(self.context.candidates))), request)
        self.assertEqual({c.id: c.status for c in reverse.candidates}, {c.id: c.status for c in plan.candidates})

    def test_blocked_downstream_preserves_partial_release_and_all_blocked_withholds_timeline(self):
        partial = make_plan(self.context, self.request_with_access("Golden transformer", "blocked"))
        self.assertEqual(partial.scheduled_release_potential, 27)
        self.assertEqual(partial.milestones[-1].cumulative_premises, 27)
        all_blocked = make_plan(self.context, PlanRequest(access=tuple(
            CandidateAccess(candidate_id=c.id, access="blocked") for c in self.plan.candidates)))
        self.assertEqual(all_blocked.tasks, ())
        self.assertEqual(all_blocked.milestones, ())
        self.assertIsNone(all_blocked.recommended_id)
        self.assertIsNone(all_blocked.executable_completion_hours)
        self.assertIsNone(all_blocked.completion_hours)
        self.assertEqual(all_blocked.scheduled_release_potential, 0)

    def test_release_milestones_are_unions_and_equal_completion_times_are_grouped(self):
        self.assertEqual([m.additional_premises for m in self.plan.milestones], [1, 23, 3, 1])
        self.assertEqual([m.cumulative_premises for m in self.plan.milestones], [1, 24, 27, 28])
        two = make_plan(self.context, PlanRequest(crew_count=2))
        self.assertEqual([m.additional_premises for m in two.milestones], [24, 3, 1])
        self.assertEqual(len(two.milestones[0].candidate_ids), 2)
        self.assertEqual(sum(m.additional_premises for m in two.milestones), 28)
        self.assertEqual(two.scheduled_release_potential, 28)
        for milestone in two.milestones:
            self.assertLessEqual(milestone.display_hours.lower, milestone.elapsed_hours.lower)
            self.assertGreaterEqual(milestone.display_hours.upper, milestone.elapsed_hours.upper)
        self.assertIsNone(two.actual_switching_restorable_premises)
        self.assertIsNone(two.verified_critical_electrical_dependencies)
        self.assertTrue(all(c.actually_restorable_via_switching is None for c in two.candidates))

    def assert_evidence_unavailable(self, context):
        plan = make_plan(context, PlanRequest())
        for field in ("unique_dependent_premises", "summed_memberships", "overlap_memberships", "scheduled_release_potential"):
            self.assertIsNone(getattr(plan, field))
        self.assertEqual(plan.tasks, ())
        self.assertEqual(plan.milestones, ())
        self.assertIsNone(plan.recommended_id)
        self.assertIsNone(plan.completion_hours)
        self.assertTrue(all(c.status == "evidence_unavailable" for c in plan.candidates))
        for candidate in plan.candidates:
            if candidate.dependent_premises is None:
                self.assertIn("unavailable", candidate.evidence_note.lower())
                self.assertNotIn("all dependent paths independently validated", candidate.evidence_note.lower())
                self.assertNotIn("all dependent paths verified", candidate.evidence_note.lower())

    def test_incomplete_or_mismatched_historical_association_withholds_whole_plan(self):
        observed = next(c for c in self.context.candidates if c.match is not None)
        for match in (replace(observed.match, status="unavailable", asset_key=None),
                      replace(observed.match, asset_key=self.context.candidates[0].key)):
            candidates = tuple(replace(c, match=match) if c == observed else c for c in self.context.candidates)
            self.assert_evidence_unavailable(replace(self.context, candidates=candidates))

    def test_incomplete_reverse_membership_does_not_silently_shrink_damage_union(self):
        target = self.context.candidates[0]
        reasons = dict(self.context.network.asset_reasons)
        reasons[target.key] = ("missing_customer",)
        network = replace(self.context.network, asset_reasons=reasons)
        self.assert_evidence_unavailable(replace(self.context, network=network))

    def test_unavailable_explanation_context_does_not_certify_missing_spatial_evidence(self):
        observed = next(c for c in self.context.candidates if c.match is not None)
        candidates = tuple(replace(c, match=replace(observed.match, status="unavailable", asset_key=None))
                           if c == observed else c for c in self.context.candidates)
        critical = next(c for c in self.context.candidates if c.label == "Critical-context fuse")
        reasons = dict(self.context.network.asset_reasons)
        reasons[critical.key] = ("missing_customer",)
        network = replace(self.context.network, asset_reasons=reasons)
        plan = make_plan(replace(self.context, network=network, candidates=candidates), PlanRequest())
        explanation = build_plan_context(plan)
        clauses = {clause.id: clause.text.lower() for clause in explanation.clauses}
        self.assertEqual(explanation.restoration_status, "unavailable")
        self.assertIsNone(explanation.restoration_bounds)
        self.assertIn("unavailable", clauses["damage-match"])
        self.assertNotIn("passed the disclosed", clauses["damage-match"])
        self.assertIn("no supported critical-premise proxy", clauses["criticality-context"])
        self.assertNotIn("has a critical-facility/nearest-premise spatial proxy", clauses["criticality-context"])
        self.assertIn("no candidate can be recommended", clauses["priority-summary"])

    def test_invalid_and_duplicate_input_cannot_select_arbitrary_assets(self):
        with self.assertRaises(CheckpointError) as error:
            make_plan(self.context, PlanRequest(access=(CandidateAccess(candidate_id="unapproved-candidate", access="clear"),)))
        self.assertEqual(error.exception.code, "unknown_candidate")
        self.assertNotIn("unapproved-candidate", str(error.exception))
        item = CandidateAccess(candidate_id=self.id_for("Golden transformer"), access="clear")
        with self.assertRaises(ValidationError):
            PlanRequest(access=(item, item))
        for invalid in ({"crew_count": 0}, {"crew_count": 3}, {"crew_count": True},
                        {"crew_size": 1}, {"crew_size": 9}, {"crew_size": 4.0},
                        {"scenario_revision": 0}, {"premise_nu": "private"}):
            with self.subTest(keys=tuple(invalid)):
                with self.assertRaises(ValidationError):
                    PlanRequest(**invalid)

    def test_revision_and_scenario_bind_the_result_identifier(self):
        changed = make_plan(self.context, PlanRequest(scenario_revision=2))
        self.assertNotEqual(changed.result_id, self.plan.result_id)
        self.assertEqual(changed.scenario_revision, 2)
        self.assertEqual(changed.tasks, self.plan.tasks)
        self.assertNotEqual(make_plan(self.context, PlanRequest(crew_count=2)).result_id, self.plan.result_id)
        self.assertNotEqual(make_plan(self.context, PlanRequest(use_critical_proxy=False)).result_id, self.plan.result_id)

    def test_public_payload_contains_only_generalized_locations_and_safe_aliases(self):
        payload = self.plan.model_dump(mode="json")
        serialized = json.dumps(payload)
        forbidden = {"premise_nu", "premise", "source_row", "customer_row", "device_row", "pole_row",
                     "circuit_id", "circuit_alias", "station_alias", "location_code", "asset_key", "critical_c",
                     "address", "road_name", "anno_strin", "private_premise", "NAME", "ADDRESS"}

        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden.intersection(value), "Private source fields reached the public plan")
                for child in value.values():
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        inspect(payload)
        network = self.context.network
        members = network.affected_union(c.key for c in self.context.candidates)
        private_strings = set(members)
        private_points = []
        for candidate in self.context.candidates:
            asset = network.equipment_by_key[candidate.key]
            private_strings.update((asset.key[1], asset.location_code, asset.circuit_id, asset.circuit_alias, asset.station_alias))
            private_points.append(asset.point)
        for premise in members:
            private_points.append(network.customers_by_premise[premise][0].point)
        for value in private_strings:
            self.assertFalse(json.dumps(value) in serialized, "A private source identifier reached the public plan")
        for point in private_points:
            for coordinate in point:
                self.assertFalse(str(coordinate) in serialized, "A precise source coordinate reached the public plan")
        with layer(RAW, "Data1.zip", "Fire_Stations_E_Pairwis_Clip") as (reader, _):
            private_facility = reader.record(24)
            for field in ("NAME", "ADDRESS", "PERMANENT_"):
                self.assertFalse(private_facility[field] in serialized, "A facility identifier reached the public plan")
        for candidate in self.plan.candidates:
            self.assertTrue(candidate.id.startswith("asset-"))
            for point in [candidate.position, *(c.position for c in candidate.customer_cells)]:
                self.assertEqual(point.longitude, round(point.longitude, 2))
                self.assertEqual(point.latitude, round(point.latitude, 2))
                self.assertTrue(point.approximate)
            self.assertIsNone(candidate.current_damage_confirmed)
