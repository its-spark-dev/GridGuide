"""G3: unchanged G2 validator/oracle, fault injection, determinism and inference."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from pydantic import ValidationError
from backend.optimization import SolverSettings, optimize, objective_ticks, validated_baselines, VERSION
from benchmarks.contracts import BenchmarkProblem, Schedule
from benchmarks.metrics import calculate
from benchmarks.oracle import exhaustive
from benchmarks.policies import POLICIES, schedule
from benchmarks.scenarios import FAMILIES, generate, microcase, microcases
from benchmarks.validation import validate
from benchmarks.optimization_experiment import run, select_comparator, split_timing
from benchmarks.optimization_reporting import clustered_interval, describe, render


class OptimizerCorrectnessTests(unittest.TestCase):
    def assert_valid(self,p,r):
        s=Schedule.model_validate(r['schedule'])
        self.assertEqual(validate(p,s,r['metrics']),[])
        self.assertLessEqual(r['objective_ticks'],r['baseline_objective_ticks'])
        self.assertEqual(objective_ticks(p,r['metrics']),r['objective_ticks'])
        return s

    def test_all_supported_complete_microcases_match_exhaustive_integer_optima(self):
        supported=0
        for p in microcases():
            r=optimize(p);self.assert_valid(p,r);oracle=exhaustive(p)
            if oracle['status']=='optimal':
                supported+=1
                self.assertEqual(r['objective_ticks'],oracle['objective_ticks'],p.id)
                self.assertTrue(r['primary_optimal'])
        self.assertEqual(supported,6)

    def test_independent_energization_dependencies_need_no_repair_precedence(self):
        p=microcase('cross',[2,3,1],[20,1,10],deps={0:(0,1),1:(1,),2:(0,2)},crews=2)
        r=optimize(p);self.assert_valid(p,r)
        self.assertEqual(r['objective_ticks'],exhaustive(p)['objective_ticks'])

    def test_bottleneck_delayed_crews_and_unbalanced_groups(self):
        cases=[microcase('upstream',[1,2,3],[1,100,1],prerequisites={1:(0,),2:(0,)},crews=2,availability={1:7200}),
               microcase('long',[10,1,1],[1,1000,2],crews=2),
               microcase('crit',[4,1],[1,100],critical=(0,)),
               microcase('tie',[1,1,1],[1,1,1],crews=4)]
        for p in cases:
            r=optimize(p);self.assert_valid(p,r)
            self.assertEqual(r['objective_ticks'],exhaustive(p)['objective_ticks'])

    def test_actual_improvement_over_suboptimal_baselines_without_forced_gain(self):
        # Hand-authored correctness case: FIFO is suboptimal; best-of-four may already win.
        p=microcase('shared',[1,2,3],[10,1,1],deps={0:(0,1),1:(1,),2:(2,)},crews=1)
        r=optimize(p);self.assert_valid(p,r)
        self.assertLess(r['objective_ticks'],objective_ticks(p,calculate(p,schedule(p,POLICIES[0]))))
        already=microcase('already',[1],[10])
        r=optimize(already);self.assertEqual(r['objective_ticks'],r['baseline_objective_ticks'])

    def test_secondary_cannot_worsen_primary_and_is_conditional_on_proof(self):
        p=microcase('secondary',[3,2,1],[1,1,1],crews=2)
        r=optimize(p);self.assert_valid(p,r)
        self.assertEqual(r['objective_ticks'],exhaustive(p)['objective_ticks'])
        self.assertEqual(r['solver']['primary']['status'],'OPTIMAL')
        self.assertIn(r['solver']['secondary']['status'],('OPTIMAL','FEASIBLE','UNKNOWN'))
        z=optimize(p,SolverSettings(primary_deterministic_limit=0))
        self.assertIsNone(z['solver']['secondary']);self.assertFalse(z['primary_optimal'])

    def test_blocked_upstream_preserves_full_scope_and_nulls(self):
        p=microcase('blocked',[1,1,2],[2,3,1],blocked=(0,),prerequisites={1:(0,)})
        r=optimize(p);self.assert_valid(p,r)
        self.assertEqual(r['objective_scope'],'restricted_horizon_customer_ticks')
        self.assertIsNone(r['metrics']['modeled_customer_outage_hours'])
        self.assertEqual(r['metrics']['unresolved_customers'],5)
        self.assertEqual(r['metrics']['restricted_horizon_customer_hours'],842)
        self.assertEqual(len(r['schedule']['unscheduled_tasks']),2)

    def test_unknown_effort_and_evidence_are_not_assumed_complete(self):
        for p in (microcase('effort',[None,1],[2,3]),microcase('topology',[1],[2],unresolved=(0,))):
            r=optimize(p);self.assert_valid(p,r)
            self.assertIsNone(r['metrics']['modeled_customer_outage_hours'])
            self.assertGreater(r['metrics']['unresolved_customers'],0)

    def test_all_blocked_explicitly_skips_solver(self):
        with patch('backend.optimization._cp_solve') as solver:
            r=optimize(microcases()[4]);solver.assert_not_called()
        self.assertEqual(r['fallback_reason'],'no_executable_tasks')
        self.assertFalse(r['primary_optimal'])

    def test_invalid_conflicting_prerequisites_are_rejected(self):
        p=microcases()[0].model_dump()
        p['tasks'][0]['prerequisites']=('syn-task-1',)
        p['tasks'][1]['prerequisites']=('syn-task-0',)
        with self.assertRaises(ValidationError): optimize(p)
        p=microcases()[0].model_copy(update={'groups':()})
        with self.assertRaises(ValidationError): optimize(p)

    def test_rounding_people_and_crews_are_separate(self):
        p=microcase('round',['0.0003','0.001'],[2,3],crews=2)
        raw=p.model_dump();raw['duration_assumption']='ideal_all_people'
        p=BenchmarkProblem.model_validate(raw)
        r=optimize(p);self.assert_valid(p,r)
        self.assertEqual(r['objective_ticks'],exhaustive(p)['objective_ticks'])
        self.assertIsNone(p.actual_efficiency)

    def test_repeated_offline_run_has_same_numerical_result(self):
        p=generate('overlapping-dependencies',25,4,17,split='development')
        a,_=split_timing(optimize(p));b,_=split_timing(optimize(p))
        self.assertEqual(a,b)


class FallbackTests(unittest.TestCase):
    def setUp(self): self.p=microcases()[0]
    def test_missing_dependency(self):
        with patch('backend.optimization._cp_solve',side_effect=ImportError): r=optimize(self.p)
        self.assertEqual(r['fallback_reason'],'solver_dependency_unavailable')
        self.assertEqual(r['returned_source'],'baseline')

    def test_status_unknown_infeasible_model_invalid(self):
        for status in ('UNKNOWN','INFEASIBLE','MODEL_INVALID'):
            with patch('backend.optimization._cp_solve',return_value=(None,{'primary':{'status':status}})):
                r=optimize(self.p)
            self.assertEqual(r['fallback_reason'],'solver_'+status.lower())
            self.assertFalse(r['primary_optimal'])
            self.assertEqual(validate(self.p,r['schedule'],r['metrics']),[])

    def test_invalid_candidate_is_never_returned(self):
        s=schedule(self.p,POLICIES[0]).model_copy(update={'assignments':()})
        with patch('backend.optimization._cp_solve',return_value=(s,{'primary':{'status':'OPTIMAL','objective_ticks':0}})):
            r=optimize(self.p)
        self.assertEqual(r['fallback_reason'],'invalid_candidate');self.assertTrue(r['candidate_violations'])
        self.assertEqual(r['returned_source'],'baseline');self.assertFalse(r['primary_optimal'])

    def test_worse_candidate_and_wrong_objective_are_retained_as_rejections(self):
        s=schedule(self.p,POLICIES[0]);ticks=objective_ticks(self.p,calculate(self.p,s))
        for claimed,reason in ((ticks,'candidate_worse_than_baseline'),(ticks-1,'objective_mismatch')):
            with patch('backend.optimization._cp_solve',return_value=(s,{'primary':{'status':'FEASIBLE','objective_ticks':claimed}})):
                r=optimize(self.p)
            self.assertEqual(r['fallback_reason'],reason);self.assertEqual(r['candidate_objective_ticks'],ticks)

    def test_feasible_incumbent_is_not_labelled_optimal(self):
        s,m=min(validated_baselines(self.p),key=lambda x:objective_ticks(self.p,x[1]))
        with patch('backend.optimization._cp_solve',return_value=(s,{'primary':{'status':'FEASIBLE','objective_ticks':objective_ticks(self.p,m)}})):
            r=optimize(self.p)
        self.assertFalse(r['primary_optimal']);self.assertEqual(r['returned_source'],'solver')

    def test_real_zero_budget_falls_back_and_never_claims_optimality(self):
        r=optimize(self.p,SolverSettings(primary_deterministic_limit=0))
        self.assertEqual(r['fallback_reason'],'solver_unknown');self.assertFalse(r['primary_optimal'])

    def test_solver_failure_and_oversized_exact_range(self):
        with patch('backend.optimization._cp_solve',side_effect=RuntimeError('private')):r=optimize(self.p)
        self.assertEqual(r['fallback_reason'],'solver_error:RuntimeError')
        p=microcase('huge',[10**14],[2]);r=optimize(p)
        self.assertEqual(r['fallback_reason'],'solver_error:ValueError')

    def test_bad_baseline_is_unavailable_not_false_valid(self):
        with patch('backend.optimization.schedule',return_value=schedule(self.p,POLICIES[0]).model_copy(update={'assignments':()})):
            with self.assertRaises(ValueError):optimize(self.p)

    def test_interactive_scope_and_total_latency(self):
        p=generate('overlapping-dependencies',100,4,17,split='development')
        with patch('backend.optimization._cp_solve') as solver:
            r=optimize(p,SolverSettings(mode='interactive'));solver.assert_not_called()
        self.assertEqual(r['fallback_reason'],'interactive_size_limit')
        for f in FAMILIES:
            p=generate(f,25,4,17,split='development');r=optimize(p,SolverSettings(mode='interactive'))
            self.assertLess(r['end_to_end_seconds'],5)
            if r['solver']:
                self.assertLessEqual(sum(r['solver'][phase]['wall_seconds'] for phase in ('primary','secondary') if r['solver'][phase]),2.1)
            self.assertEqual(validate(p,r['schedule'],r['metrics']),[])


class EvaluationTests(unittest.TestCase):
    def test_comparator_rule_is_verified_against_published_data(self):
        policy,scores=select_comparator()
        self.assertEqual(policy,'legacy-release-per-person-hour-adapter-v1')
        self.assertAlmostEqual(scores[policy],63560.96888888889)

    def test_pair_signs_zero_cost_ties_and_negative_results(self):
        r=describe([(100,90),(100,110),(0,0)])
        self.assertEqual((r['wins'],r['ties'],r['regressions']),(1,1,1))
        self.assertEqual(r['median_percent'],0)
        self.assertEqual(describe([(0,1)])['undefined_percentages'],1)

    def test_cluster_variants_stay_together_and_interval_is_deterministic(self):
        cells={(f,s):[float(s)]*9 for f in ('a','b') for s in (1,2,3)}
        a=clustered_interval(cells,100);self.assertEqual(a,clustered_interval(cells,100))
        self.assertEqual(a['families'],2);self.assertEqual(a['seeds'],3)
        doubled={k:v*2 for k,v in cells.items()}
        self.assertEqual(a,clustered_interval(doubled,100))
        self.assertIsNone(clustered_interval({('a',1):[1],('b',2):[2]},100))

    def test_runner_repeat_and_artifact_integrity(self):
        with TemporaryDirectory() as d:
            a,b=Path(d)/'a',Path(d)/'b'
            rows=run(a,'micro');run(b,'micro')
            self.assertEqual(len(rows),8);self.assertTrue(all(r['status']=='ok' for r in rows))
            self.assertEqual((a/'results.jsonl.gz').read_bytes(),(b/'results.jsonl.gz').read_bytes())
            r=render(a);self.assertFalse(r['promotion_target_met_on_published_suite'])
            with self.assertRaises(FileExistsError):run(a,'micro')
            (a/'results.jsonl.gz').write_bytes(gzip.compress(b'{}\n'))
            with self.assertRaises(ValueError):render(a)

    def test_execution_failures_are_preserved_and_renderable(self):
        with TemporaryDirectory() as d,patch('benchmarks.optimization_experiment.optimize',side_effect=RuntimeError):
            rows=run(Path(d)/'failure','micro');report=render(Path(d)/'failure')
            self.assertEqual(len(rows),8);self.assertEqual(len(report['failures']),8)
            self.assertFalse(report['promotion_target_met_on_published_suite'])

if __name__=='__main__': unittest.main()
