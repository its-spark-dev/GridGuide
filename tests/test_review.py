"""G7 boundary tests: actual recomputation, tampering, privacy and replay."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import review
from backend.operator_api import create_operator_app
from benchmarks.validation import validate
from scripts.prepare_operator_catalog import prepare

ACK={k:True for k in ['fictional','modeled_not_field_confirmed','gaps_and_unresolved','objective_and_tradeoffs','experimental_and_simulation_limits']}

class ReviewTests(unittest.TestCase):
    def request(self,name='weighted',**extra):
        s=next(s for s in review.catalog().scenarios if s.scenario_id=='syn-micro-'+name)
        return dict(scenario_id=s.scenario_id,scenario_fingerprint=s.scenario_fingerprint,**extra)

    def artifact(self,**extra):
        c=review.compare(self.request(**extra))
        return review.export_review(dict(request=c.request.model_dump(),result_fingerprint=c.result_fingerprint,
            reason='conservative-baseline-preference',acknowledgements=ACK)).artifact.model_dump(mode='json')

    def test_all_cases_identical_inputs_and_independent_metrics(self):
        for s in review.catalog().scenarios:
            c=review.compare(dict(scenario_id=s.scenario_id,scenario_fingerprint=s.scenario_fingerprint,include_experimental=True))
            self.assertEqual(len(c.results),5)
            self.assertEqual(c.recommended_policy,review.FIXED)
            for r in c.results:
                self.assertEqual(r.schedule.problem_fingerprint,c.problem.fingerprint)
                self.assertEqual(validate(c.problem,r.schedule,r.metrics.model_dump(mode='json')),[])
            self.assertEqual(c.problem.actual_efficiency,None)

    def test_tradeoff_and_censoring_are_not_hidden(self):
        c=review.compare(self.request('critical'))
        critical=c.results[3];self.assertIn('modeled_customer_outage_hours: regression versus fixed baseline',critical.tradeoffs)
        self.assertIn('Critical syn-group-0: improvement',critical.tradeoffs)
        c=review.compare(self.request('censored'));m=c.results[2].metrics
        self.assertEqual(m.modeled_customer_outage_hours,202)
        self.assertEqual(m.restricted_horizon_customer_hours,169)
        self.assertEqual(m.censored_customers,1)
        for name in ['blocked','unknown']:
            m=review.compare(self.request(name)).results[2].metrics
            self.assertIsNone(m.modeled_customer_outage_hours)
            self.assertGreater(m.unresolved_customers,0)

    def test_valid_override_recomputes_and_changes_binding(self):
        original=review.compare(self.request())
        changed=review.compare(self.request(precedence=[dict(before='syn-task-0',after='syn-task-1')],revision=2,include_experimental=True))
        self.assertNotEqual(original.result_fingerprint,changed.result_fingerprint)
        self.assertEqual(changed.results[2].metrics.modeled_customer_outage_hours,54)
        self.assertEqual(changed.experimental_status,'unsupported_override')
        self.assertEqual(len(changed.results),4)

    def test_invalid_overrides_and_evidence_rejected(self):
        for edges in [[dict(before='syn-unknown',after='syn-task-1')],
                      [dict(before='syn-task-0',after='syn-task-0')],
                      [dict(before='syn-task-0',after='syn-task-1')]*2,
                      [dict(before='syn-task-0',after='syn-task-1'),dict(before='syn-task-1',after='syn-task-0')]]:
            with self.assertRaises(ValueError):review.compare(self.request(precedence=edges))
        for extra in [dict(evidence={'observed':True}),dict(clearance_hours=0),dict(include_experimental='yes')]:
            with self.assertRaises(ValueError):review.compare(self.request(**extra))
        with self.assertRaises(ValueError):review.compare(self.request('chain-eight',precedence=[dict(before='syn-task-0',after='syn-task-1')]))
        with self.assertRaises(ValueError):review.compare(self.request(selected_policy=review.EXPERIMENTAL))

    def test_policy_choice_also_invalidates_fingerprint(self):
        a=review.compare(self.request());b=review.compare(self.request(selected_policy='fifo-v1'))
        self.assertNotEqual(a.result_fingerprint,b.result_fingerprint)
        with self.assertRaises(ValueError):review.export_review(dict(request=b.request.model_dump(),result_fingerprint=a.result_fingerprint,reason='demonstration-comparison',acknowledgements=ACK))

    def test_cross_scenario_and_revision_bindings_reject(self):
        original = self.request()
        for update in [dict(scenario_id='syn-micro-critical'), dict(scenario_revision=2),
                       dict(scenario_fingerprint='0'*64)]:
            with self.assertRaises(ValueError):
                review.compare(dict(original, **update))
        a = review.compare(original)
        b = review.compare(dict(original, revision=2))
        self.assertNotEqual(a.result_fingerprint, b.result_fingerprint)
        with self.assertRaises(ValueError):
            review.export_review(dict(request=b.request.model_dump(), result_fingerprint=a.result_fingerprint,
                                      reason='demonstration-comparison', acknowledgements=ACK))

    def test_actual_crew_overlap_is_independently_rejected(self):
        original = review.schedule
        def overlap(problem, policy):
            plan = original(problem, policy)
            first, second = plan.assignments
            duration = second.end_tick-second.start_tick
            second = second.model_copy(update={'crew_id': first.crew_id,
                'start_tick': first.start_tick, 'end_tick': first.start_tick+duration})
            return plan.model_copy(update={'assignments': (first, second)})
        problem, _ = review.problem_for(review.CompareRequest.model_validate(self.request()))
        self.assertIn('crew_overlap', validate(problem, overlap(problem, review.FIXED)))
        with patch('backend.review.schedule', side_effect=overlap):
            with self.assertRaises(ValueError):
                review.compare(self.request())

    def test_best_of_four_is_separate_and_experimental_override_rejected(self):
        c = review.compare(self.request(include_experimental=True))
        self.assertEqual(c.best_of_four_policy, 'customer-count-v1')
        self.assertEqual(c.recommended_policy, review.FIXED)
        self.assertEqual(c.results[-1].relative_gap, 0)
        self.assertIsNone(c.results[0].relative_gap)
        with self.assertRaises(ValueError):
            review.compare(self.request(include_experimental=True, selected_policy=review.EXPERIMENTAL,
                precedence=[dict(before='syn-task-0', after='syn-task-1')]))

    def test_missing_ack_and_nonboolean_ack_rejected(self):
        c=review.compare(self.request())
        for ack in [{},dict(ACK,fictional=False),dict(ACK,fictional=1)]:
            with self.assertRaises(ValueError):review.export_review(dict(request=c.request.model_dump(),result_fingerprint=c.result_fingerprint,reason='demonstration-comparison',acknowledgements=ack))

    def test_export_replay_does_not_run_solver_or_read_sources(self):
        a=self.artifact(include_experimental=True)
        with patch('backend.optimization.optimize',side_effect=AssertionError('No runtime solver')):
            self.assertIn('Reviewed in demo',review.replay(a))
        payload=json.dumps(a)
        for forbidden in ['road_name','critical_c','latitude','longitude','phone','email','credential','data/raw','source_id']:
            self.assertNotIn(forbidden,payload)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'review.json';path.write_text(payload)
            code="""import runpy,sys
root=sys.argv[1];artifact=sys.argv[2];sys.path.insert(0,root)
def guard(event,args):
 if event=='socket.connect':raise RuntimeError('network denied')
 if event=='open' and any(s in str(args[0]) for s in ('data/raw','data/processed')):raise RuntimeError('source denied')
sys.addaudithook(guard);sys.argv=['replay_review.py',artifact];runpy.run_path(root+'/scripts/replay_review.py',run_name='__main__')
"""
            result=subprocess.run([sys.executable,'-I','-c',code,str(Path(__file__).resolve().parents[1]),str(path)],cwd=d,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Replay verified',result.stdout)

    def test_replay_from_source_free_extraction_and_malformed_imports(self):
        # The fresh tree contains no challenge data, research downloads, solver library,
        # source loader or application API. This is a CLI extraction, not a release package.
        root = Path(__file__).resolve().parents[1]
        files = ['backend/__init__.py', 'backend/contracts.py', 'backend/risk_rules.py',
                 'backend/review.py', 'backend/review_contracts.py', 'backend/optimization.py',
                 'benchmarks/__init__.py', 'benchmarks/contracts.py', 'benchmarks/metrics.py',
                 'benchmarks/policies.py', 'benchmarks/validation.py',
                 'data/operator/catalog.json', 'scripts/replay_review.py']
        artifact = self.artifact(include_experimental=True)
        with tempfile.TemporaryDirectory() as d:
            extracted = Path(d)
            for relative in files:
                target = extracted/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root/relative, target)
            path = extracted/'review.json'
            path.write_text(json.dumps(artifact))
            run = lambda: subprocess.run([sys.executable, '-I', str(extracted/'scripts/replay_review.py'), str(path)],
                cwd=d, capture_output=True, text=True)
            success = run()
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn(review.summary(review.ReviewArtifact.model_validate(artifact)), success.stdout)
            for payload in ['{"version":"secret","version":"secret2"}', 'x'*1000001,
                            json.dumps(dict(artifact, version='secret-unsupported'))]:
                path.write_text(payload)
                failure = run()
                self.assertEqual(failure.returncode, 1)
                self.assertEqual(failure.stderr.strip(),
                    'Replay rejected: invalid, unsupported or mismatched review artifact.')

    def test_adversarial_rehash_does_not_make_forged_results_valid(self):
        original=self.artifact()
        for mutate in [lambda a:a['comparison']['results'][0]['metrics'].update(modeled_customer_outage_hours=0),
                       lambda a:a['comparison']['results'][0]['metrics']['milestones'][0].update(cumulative_customers=99),
                       lambda a:a['comparison']['results'][0]['schedule']['assignments'][0].update(crew_id='syn-forged'),
                       lambda a:a['comparison'].update(explanation='Explanation for another scenario'),
                       lambda a:a['comparison']['problem']['groups'][0]['customer_ids'].append('syn-invented'),
                       lambda a:a['comparison']['evidence'].update(topology_effort_crews='source-derived'),
                       lambda a:a['review'].update(result_fingerprint='f'*64),
                       lambda a:a['comparison']['request'].update(scenario_revision=2),
                       lambda a:a['comparison']['problem'].update(contact='private')]:
            a=copy.deepcopy(original);mutate(a);a['checksum']=review.digest({k:v for k,v in a.items() if k!='checksum'})
            with self.assertRaises(ValueError):review.replay(a)

    def test_invalid_schedule_from_dependency_is_not_returned(self):
        original=review.schedule
        def bad(p,policy):
            s=original(p,policy);a=s.assignments[0].model_copy(update={'end_tick':0})
            return s.model_copy(update={'assignments':(a,*s.assignments[1:])})
        with patch('backend.review.schedule',side_effect=bad):
            with self.assertRaises(ValueError):review.compare(self.request())

    def test_catalog_pin_and_frozen_extraction(self):
        self.assertEqual(prepare(),review.CATALOG.read_bytes())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('{}')
            with patch('backend.review.CATALOG',p):
                with self.assertRaises(ValueError):review.catalog()

    def test_api_safe_errors_bounds_and_no_dispatch(self):
        with TestClient(create_operator_app()) as c:
            r=c.post('/api/v2/operator/compare',json=self.request());self.assertEqual(r.status_code,200)
            self.assertEqual(r.headers['cache-control'],'no-store')
            bad=c.post('/api/v2/operator/compare',json=self.request(private='SECRET-PRIVATE'))
            self.assertEqual(bad.status_code,422);self.assertNotIn('SECRET-PRIVATE',bad.text)
            self.assertEqual(c.post('/api/v2/operator/compare',content='x'*32769).status_code,413)
            for path in ['dispatch','notify','confirm','simulations']:
                self.assertEqual(c.post('/api/v2/operator/'+path,json={}).status_code,404)
