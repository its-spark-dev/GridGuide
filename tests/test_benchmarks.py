"""G2: independent arithmetic, corrupted outputs and frozen inputs."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from pydantic import ValidationError
from benchmarks.contracts import BenchmarkProblem, Schedule, canonical, duration_ticks
from benchmarks.metrics import calculate
from benchmarks.oracle import exhaustive
from benchmarks.policies import POLICIES, schedule
from benchmarks.reporting import report
from benchmarks.runner import run
from benchmarks.scenarios import (FAMILIES, DEVELOPMENT_SEEDS, EVALUATION_SEEDS, FROZEN,
    FROZEN_SHA256, generate, load_evaluation, manifest, microcase, microcases)
from benchmarks.validation import validate


class ProblemTests(unittest.TestCase):
    def test_disjoint_groups_and_strict_identifiers(self):
        p=microcases()[0].model_dump(mode='json')
        for mutation in ('customer','task','crew','prerequisite','cycle'):
            raw=deepcopy(p)
            if mutation=='customer': raw['groups'][1]['customer_ids']=[raw['groups'][0]['customer_ids'][0]]
            if mutation=='task': raw['tasks'][0]['id']=123
            if mutation=='crew': raw['crews'][0]['available_tick']=-1
            if mutation=='prerequisite': raw['tasks'][0]['prerequisites']=['syn-missing']
            if mutation=='cycle': raw['tasks'][0]['prerequisites']=['syn-task-0']
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):
                BenchmarkProblem.model_validate(raw)
            self.assertEqual(validate(raw,{}),['invalid_problem'])

    def test_fictional_origin_and_no_observations(self):
        p=microcases()[0].model_dump()
        for field,value in (('origin','utility_observed'),('observed_outcomes',3),('actual_efficiency',.5),('input_classification','source-derived')):
            with self.assertRaises(ValidationError):
                BenchmarkProblem.model_validate({**p,field:value})

    def test_person_hours_conversion_and_round_up(self):
        p=microcase('round',['0.0003'],[1])
        self.assertEqual(duration_ticks(p,p.tasks[0]),2)
        ideal=BenchmarkProblem.model_validate({**p.model_dump(),'duration_assumption':'ideal_all_people'})
        self.assertEqual(duration_ticks(ideal,ideal.tasks[0]),1)
        self.assertEqual(p.tasks[0].total_person_hours,ideal.tasks[0].total_person_hours)
        for value in ('NaN','Infinity','-1','0'):
            raw=p.model_dump(); raw['tasks'][0]['total_person_hours']=value
            with self.assertRaises(ValidationError): BenchmarkProblem.model_validate(raw)

    def test_frozen_matrix_content_and_split_integrity(self):
        self.assertFalse(set(DEVELOPMENT_SEEDS)&set(EVALUATION_SEEDS))
        ps=load_evaluation()
        self.assertEqual(len(ps),270)
        self.assertEqual(len({p.id for p in ps}),270)
        self.assertEqual(hashlib.sha256(FROZEN.read_bytes()).hexdigest(),FROZEN_SHA256)
        self.assertEqual(json.loads(FROZEN.read_bytes()),manifest())
        for f in FAMILIES:
            self.assertEqual(sum(p.family==f for p in ps),45)
        with patch('benchmarks.scenarios.FROZEN_SHA256','0'*64):
            with self.assertRaises(ValueError): load_evaluation()
        with patch('benchmarks.scenarios.manifest',return_value={}):
            with self.assertRaises(ValueError): load_evaluation()

    def test_generator_is_independent_of_process_hash_seed(self):
        code='from benchmarks.scenarios import generate; print(generate("overlapping-dependencies",25,4,101).fingerprint)'
        outputs=[]
        import os
        for seed in ('1','912'):
            outputs.append(subprocess.check_output([sys.executable,'-c',code],env={**os.environ,'PYTHONHASHSEED':seed},text=True))
        self.assertEqual(*outputs)


class MetricTests(unittest.TestCase):
    def result(self,p,policy=POLICIES[0]):
        s=schedule(p,policy); m=calculate(p,s)
        self.assertEqual(validate(p,s,m),[])
        return m

    def test_hand_calculated_weighted_objective_and_quantiles(self):
        p=microcases()[0]
        m=self.result(p)
        self.assertEqual(m['modeled_customer_outage_hours'],54)
        self.assertEqual(m['weighted_median_hours'],5)
        self.assertEqual(m['weighted_p95_hours'],5)
        self.assertEqual(m['small_group_mean_wait_hours'],4)
        self.assertEqual(m['branch_mean_disparity_hours'],1)
        self.assertEqual(self.result(p,POLICIES[1])['modeled_customer_outage_hours'],15)

    def test_overlap_requires_last_repair_not_sum_of_memberships(self):
        m=self.result(microcases()[1])
        self.assertEqual(m['customers'],3)
        self.assertEqual(m['modeled_customer_outage_hours'],12)
        self.assertEqual(m['release_ticks'],{'syn-group-0':18000,'syn-group-1':7200})
        self.assertEqual(m['milestones'][-1]['cumulative_customers'],3)

    def test_censored_is_known_later_not_unresolved(self):
        m=self.result(microcase('late',[200,1],[1,1]))
        self.assertEqual(m['modeled_customer_outage_hours'],401)
        self.assertEqual(m['restricted_horizon_customer_hours'],336)
        self.assertEqual(m['censored_customers'],2)
        self.assertEqual(m['unresolved_customers'],0)
        self.assertEqual(m['full_customer_release_hours'],201)

    def test_horizon_boundary_and_denominator(self):
        m=self.result(microcase('edge',[168],[3]))
        self.assertEqual(m['censored_customers'],0)
        self.assertEqual(m['restricted_horizon_customer_hours'],504)
        self.assertEqual(m['unreleased_customers_at_horizon'],0)

    def test_incomplete_does_not_report_completed_subset_total(self):
        m=self.result(microcase('partial',[2,1],[4,2],blocked=(0,)))
        self.assertIsNone(m['modeled_customer_outage_hours'])
        self.assertIsNone(m['makespan_hours'])
        self.assertIsNone(m['full_customer_release_hours'])
        self.assertIsNone(m['weighted_median_hours'])
        self.assertEqual(m['restricted_horizon_customer_hours'],674)
        self.assertEqual(m['unresolved_customers'],4)
        self.assertEqual(m['known_release_customers'],2)
        self.assertEqual(m['customers'],6)
        self.assertEqual(m['censored_customers'],0)

    def test_unknown_dependency_even_if_all_repairs_complete(self):
        m=self.result(microcase('missing',[1],[2],unresolved=(0,)))
        self.assertEqual(m['makespan_hours'],1)
        self.assertIsNone(m['modeled_customer_outage_hours'])
        self.assertEqual(m['restricted_horizon_customer_hours'],336)

    def test_simultaneous_completions_and_critical_latency(self):
        m=self.result(microcase('ties',[2,2],[2,3],crews=2,critical=(0,)))
        self.assertEqual(len(m['milestones']),1)
        self.assertEqual(m['milestones'][0]['additional_customers'],5)
        self.assertEqual(m['critical_service_latency_hours'],{'syn-group-0':2})

    def test_no_required_repairs_releases_at_origin(self):
        m=self.result(microcase('empty',[1],[2],deps={0:()}))
        self.assertEqual(m['modeled_customer_outage_hours'],0)
        self.assertEqual(m['release_100_hours'],0)


class BaselineTests(unittest.TestCase):
    def test_all_baselines_same_problem_and_durations(self):
        for p in microcases():
            before=p.fingerprint
            for policy in POLICIES:
                s=schedule(p,policy)
                self.assertEqual(s.problem_fingerprint,before)
                self.assertEqual(validate(p,s,calculate(p,s)),[])
                self.assertEqual(schedule(p,policy),s)
            self.assertEqual(before,p.fingerprint)

    def test_customer_count_has_no_duration_normalization(self):
        p=microcase('counts',[10,1],[11,10])
        self.assertEqual(schedule(p,POLICIES[1]).assignments[0].task_id,'syn-task-0')
        self.assertEqual(schedule(p,POLICIES[2]).assignments[0].task_id,'syn-task-1')

    def test_critical_policy_promotes_prerequisites_without_false_release(self):
        p=microcase('crit-parent',[1,3,1],[1,1,20],prerequisites={1:(0,)},critical=(1,))
        s=schedule(p,POLICIES[3]); m=calculate(p,s)
        self.assertEqual([a.task_id for a in s.assignments],['syn-task-0','syn-task-1','syn-task-2'])
        self.assertEqual(m['critical_service_latency_hours']['syn-group-1'],4)

    def test_stable_tie_breaking_and_input_order(self):
        p=microcase('equal',[1,1],[2,2],crews=2)
        raw=p.model_dump(); raw['tasks']=list(reversed(raw['tasks'])); raw['groups']=list(reversed(raw['groups']));raw['crews']=list(reversed(raw['crews']))
        other=BenchmarkProblem.model_validate(raw)
        for policy in POLICIES:
            self.assertEqual(schedule(p,policy).assignments,schedule(other,policy).assignments)

    def test_availability_and_blocked_descendants(self):
        p=microcase('blocked-child',[1,1,2],[1,1,1],prerequisites={1:(0,)},blocked=(0,),availability={0:7200})
        s=schedule(p,POLICIES[0])
        self.assertEqual(s.unscheduled_tasks,('syn-task-0','syn-task-1'))
        self.assertEqual(s.assignments[0].start_tick,7200)
        self.assertEqual(s.assignments[0].end_tick,14400)

    def test_standard_matrix_all_policies_independently_feasible(self):
        for p in load_evaluation():
            for policy in POLICIES:
                s=schedule(p,policy)
                self.assertEqual(validate(p,s,calculate(p,s)),[],(p.id,policy))


class NegativeValidatorTests(unittest.TestCase):
    def setUp(self):
        self.p=microcase('negative',[2,1,1],[2,3,1],prerequisites={1:(0,)},crews=2,availability={0:3600,1:3600})
        self.s=schedule(self.p,POLICIES[0])

    def bad(self,mutate,code):
        raw=self.s.model_dump(mode='json'); mutate(raw)
        self.assertIn(code,validate(self.p,raw))

    def test_missing_duplicate_unknown_and_conflicting_disposition(self):
        self.bad(lambda s:s['assignments'].pop(),'missing_or_unknown_task')
        self.bad(lambda s:s['assignments'].append(s['assignments'][0]),'duplicate_task')
        self.bad(lambda s:s['assignments'][0].update(task_id='syn-unknown'),'unknown_task_or_crew')
        self.bad(lambda s:s['assignments'][0].update(crew_id='syn-unknown'),'unknown_task_or_crew')
        self.bad(lambda s:s.update(unscheduled_tasks=['syn-task-0']),'missing_or_unknown_task')
        self.bad(lambda s:s.update(problem_fingerprint='wrong'),'input_fingerprint')

    def test_overlap_precedence_duration_availability(self):
        self.bad(lambda s:s['assignments'][1].update(crew_id=s['assignments'][0]['crew_id'],start_tick=3600,end_tick=7200),'crew_overlap')
        self.bad(lambda s:s['assignments'][1].update(start_tick=3600,end_tick=7200),'precedence')
        self.bad(lambda s:s['assignments'][0].update(end_tick=9999),'duration_arithmetic')
        self.bad(lambda s:s['assignments'][0].update(start_tick=0,end_tick=7200),'crew_availability')
        self.bad(lambda s:s['assignments'][0].update(start_tick=-1),'invalid_schedule_schema')

    def test_scheduled_blocked_work_and_omitted_executable_work(self):
        raw=self.p.model_dump();raw['tasks'][0]['access']='blocked'
        p=BenchmarkProblem.model_validate(raw)
        self.assertIn('blocked_or_unknown_work',validate(p,self.s))
        s=self.s.model_dump(mode='json');s['unscheduled_tasks']=[s['assignments'][0]['task_id']];s['assignments'].pop(0)
        self.assertIn('incorrect_executable_scope',validate(self.p,s))

    def test_every_reported_metric_is_independently_checked(self):
        metrics=calculate(self.p,self.s)
        for key,value in metrics.items():
            corrupted=deepcopy(metrics)
            corrupted[key]='forged'
            with self.subTest(key=key):
                self.assertIn('metric:'+key,validate(self.p,self.s,corrupted))
        bad=deepcopy(metrics);bad['milestones'][0]['cumulative_customers']=999
        self.assertIn('metric:milestones',validate(self.p,self.s,bad))
        bad=deepcopy(metrics);bad['release_ticks']['syn-group-1']=0
        self.assertIn('metric:release_ticks',validate(self.p,self.s,bad))
        bad=deepcopy(metrics);bad['modeled_customer_outage_hours']=float('nan')
        self.assertIn('metric:modeled_customer_outage_hours',validate(self.p,self.s,bad))

    def test_finite_completion_for_unresolved_is_rejected(self):
        p=microcases()[4];s=schedule(p,POLICIES[0]);m=calculate(p,s)
        m['modeled_customer_outage_hours']=0;m['full_customer_release_hours']=168
        self.assertIn('metric:modeled_customer_outage_hours',validate(p,s,m))
        self.assertIn('metric:full_customer_release_hours',validate(p,s,m))


class OracleTests(unittest.TestCase):
    def test_independent_known_optimum(self):
        p=microcases()[0];o=exhaustive(p)
        self.assertEqual(o['status'],'optimal')
        self.assertEqual(o['objective_ticks'],15*3600)
        self.assertEqual(validate(p,o['schedule'],calculate(p,o['schedule'])),[])
        self.assertGreater(calculate(p,schedule(p,POLICIES[0]))['modeled_customer_outage_hours'],o['objective_ticks']/3600)

    def test_overlap_optimum_and_delayed_crew(self):
        for p,answer in ((microcases()[1],12),(microcase('delay',[3,2],[1,1],crews=2,availability={1:3600}),6)):
            o=exhaustive(p)
            self.assertEqual(o['objective_ticks'],answer*3600)
            self.assertEqual(validate(p,o['schedule']),[])

    def test_eight_task_support_and_budget_is_not_optimal(self):
        p=microcases()[2]
        self.assertEqual(exhaustive(p)['objective_ticks'],36*3600)
        eight=microcase('eight-independent',[1]*8,[1]*8)
        self.assertEqual(exhaustive(eight)['status'],'optimal')
        self.assertEqual(exhaustive(eight,node_limit=10)['status'],'budget_exhausted')
        self.assertEqual(exhaustive(eight,node_limit=0)['objective_ticks'],None)
        self.assertEqual(exhaustive(microcases()[4])['status'],'unsupported')
        self.assertEqual(exhaustive(generate(FAMILIES[0],10,1,101))['status'],'unsupported')


class RunnerTests(unittest.TestCase):
    def test_repeatable_results_complete_rows_and_separate_presentation(self):
        with TemporaryDirectory() as d:
            a,b=Path(d)/'a',Path(d)/'b'
            r=run(a,'micro');run(b,'micro')
            self.assertEqual(len(r),32)
            self.assertEqual((a/'results.jsonl.gz').read_bytes(),(b/'results.jsonl.gz').read_bytes())
            self.assertEqual(json.loads((a/'manifest.json').read_text()),json.loads((b/'manifest.json').read_text()))
            self.assertEqual(len(report(a)),12)
            self.assertFalse((b/'REPORT.md').exists())
            with self.assertRaises(FileExistsError):run(a,'micro')
            (a/'results.jsonl.gz').write_bytes(gzip.compress(b'{}\n'))
            with self.assertRaises(ValueError):report(a)

    def test_failed_runs_are_retained_not_silently_dropped(self):
        with TemporaryDirectory() as d, patch('benchmarks.runner.schedule',side_effect=RuntimeError('failure')):
            rows=run(Path(d)/'bad','micro')
            self.assertEqual(len(rows),32)
            self.assertTrue(all(r['status']=='failed' for r in rows))
            self.assertEqual(sum(r['failures'] for r in report(Path(d)/'bad')),32)

    def test_full_suite_runs_in_source_free_extraction_without_network(self):
        import shutil
        root=Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as d:
            isolated=Path(d)/'isolated'; isolated.mkdir()
            shutil.copytree(root/'benchmarks',isolated/'benchmarks',ignore=shutil.ignore_patterns('__pycache__'))
            (isolated/'backend').mkdir(); (isolated/'scripts').mkdir()
            for name in ('__init__.py','contracts.py','risk_rules.py'):
                shutil.copyfile(root/'backend'/name,isolated/'backend'/name)
            for name in ('run_benchmarks.py','report_benchmarks.py'):
                shutil.copyfile(root/'scripts'/name,isolated/'scripts'/name)
            code = """
import sys
sys.path.insert(0,sys.argv[1])
def audit(event,args):
    if event=='socket.connect': raise AssertionError('Unexpected external connection')
    if event=='open' and isinstance(args[0],str) and ('/data/raw/' in args[0] or '/data/processed/' in args[0]):
        raise AssertionError('Source access forbidden')
sys.addaudithook(audit)
from benchmarks.runner import run
from benchmarks.reporting import report
rows=run(sys.argv[2],'standard')
assert len(rows)==1112 and all(r['status']=='ok' for r in rows)
report(sys.argv[2])
assert 'backend.config' not in sys.modules and 'backend.planning' not in sys.modules
import json
from pathlib import Path
print(json.loads((Path(sys.argv[2])/'manifest.json').read_text())['results_uncompressed_sha256'])
"""
            result=subprocess.run([sys.executable,'-I','-c',code,str(isolated),str(Path(d)/'results')],
                                  cwd=isolated,capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stderr)
            expected=json.loads((root/'docs/benchmarks/phase2/standard/manifest.json').read_text())
            self.assertEqual(result.stdout.strip(),expected['results_uncompressed_sha256'])

    def test_core_does_not_import_policies_into_validator_or_oracle(self):
        import inspect
        import benchmarks.validation as validator
        import benchmarks.oracle as oracle
        for module in (validator,oracle):
            source=inspect.getsource(module)
            self.assertNotIn('from .policies',source)
            self.assertNotIn('from .metrics',source)
            self.assertNotIn('duration_ticks(',source)


if __name__=='__main__': unittest.main()
