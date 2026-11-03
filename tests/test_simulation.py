"""Assumption-based numerical and structural verification; no utility outcomes."""
from decimal import Decimal, ROUND_FLOOR
import json
from pathlib import Path
from statistics import NormalDist
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from backend.simulation import simulate,draws,replay,metrics,digest,PROFILES
from backend.simulation_contracts import SimulationInput
from benchmarks.contracts import BenchmarkProblem,Schedule,Assignment
from benchmarks.scenarios import microcases,microcase
from benchmarks.policies import POLICIES,schedule
from benchmarks.metrics import calculate
from benchmarks.validation import validate
from benchmarks.simulation_experiment import run,frozen_schedules,policies
from benchmarks.simulation_reporting import report,read_arrays
from research.uncertainty import summarize,paired,convergence


def request(p=None,profile='deterministic-v1',trials=32,policy=POLICIES[2]):
    p=p or microcases()[0]
    return SimulationInput(problem=p,schedule=schedule(p,policy),profile=profile,trials=trials)


class ReplayTests(unittest.TestCase):
    def test_deterministic_all_frozen_micro_schedules(self):
        frozen,_=frozen_schedules()
        for p in microcases():
            for s in policies(p,frozen).values():
                r=SimulationInput(problem=p,schedule=s,profile='deterministic-v1',trials=3)
                _,a,starts,ends=simulate(r)
                for x in s.assignments:
                    self.assertTrue(np.all(starts[x.task_id]==x.start_tick));self.assertTrue(np.all(ends[x.task_id]==x.end_tick))
                expected=calculate(p,s)
                for key in ('modeled_customer_outage_hours','restricted_horizon_customer_hours','makespan_hours','release_50_hours','unresolved_customers'):
                    if expected[key] is None:self.assertTrue(np.all(np.isnan(a[key])))
                    else:self.assertTrue(np.all(a[key]==expected[key]))
    def test_deliberate_idle_time_is_preserved(self):
        p=microcase('idle',[1,1],[1,1]);s=schedule(p,POLICIES[0])
        assignments=tuple(a.model_copy(update={'start_tick':a.start_tick+7200,'end_tick':a.end_tick+7200}) for a in s.assignments)
        r=SimulationInput(problem=p,schedule=s.model_copy(update={'assignments':assignments}),profile='deterministic-v1',trials=2)
        _,_,starts,_=simulate(r);self.assertTrue(np.all(starts[p.tasks[0].id]==7200))
    def test_stochastic_trials_match_independent_scalar_validation(self):
        p=microcase('cross',[1,2,3],[4,5,1],deps={0:(0,2),1:(1,),2:(0,1,2)},prerequisites={2:(0,)},crews=2,availability={1:3600},critical=(1,))
        for profile in PROFILES:
            r=request(p,profile,8);_,arrays,starts,ends=simulate(r);ds,hold=draws(r)
            for j in range(8):
                raw=p.model_dump()
                for t in raw['tasks']:
                    t['total_person_hours']=(Decimal(int(ds[t['id']][j]))/3600).quantize(Decimal('.000000000001'),rounding=ROUND_FLOOR)
                for c in raw['crews']:c['available_tick']+=int(hold[j])
                trial=BenchmarkProblem.model_validate(raw)
                s=Schedule(problem_fingerprint=trial.fingerprint,policy='simulation-test',assignments=tuple(Assignment(task_id=a.task_id,crew_id=a.crew_id,start_tick=int(starts[a.task_id][j]),end_tick=int(ends[a.task_id][j])) for a in r.schedule.assignments),unscheduled_tasks=r.schedule.unscheduled_tasks)
                expected=calculate(trial,s);self.assertEqual(validate(trial,s,expected),[])
                for k in ('modeled_customer_outage_hours','restricted_horizon_customer_hours','branch_mean_disparity_hours','small_group_mean_wait_hours','weighted_p95_hours'):
                    self.assertAlmostEqual(arrays[k][j],expected[k])
                milestones=expected['milestones'];self.assertEqual(milestones[-1]['cumulative_customers'],10)
                self.assertEqual(sum(m['additional_customers'] for m in milestones),10)
    def test_blocked_mass_never_acquires_finite_completion(self):
        for profile in PROFILES:
            _,a,_,_=simulate(request(microcases()[4],profile))
            self.assertTrue(np.all(np.isnan(a['full_customer_release_hours'])))
            self.assertTrue(np.all(a['unresolved_customers']==6));self.assertTrue(np.all(a['restricted_horizon_customer_hours']==1008))
    def test_partial_unknown_retains_denominator(self):
        _,a,_,_=simulate(request(microcases()[5]))
        self.assertTrue(np.all(np.isnan(a['modeled_customer_outage_hours'])))
        self.assertTrue(np.all(a['unresolved_customers']==2));self.assertTrue(np.all(a['release_50_hours']==1))
        self.assertTrue(np.all(np.isnan(a['release_90_hours'])))
    def test_censored_is_distinct_from_unknown_and_boundary_is_released(self):
        p=microcase('edge',[168],[2]);_,a,_,_=simulate(request(p))
        self.assertTrue(np.all(a['censored_customers']==0))
        _,a,_,_=simulate(request(microcases()[6],policy=POLICIES[0]))
        self.assertTrue(np.all(a['unresolved_customers']==0));self.assertTrue(np.all(a['censored_customers']==2))
        self.assertTrue(np.all(a['restricted_horizon_customer_hours']==336))
    def test_empty_customer_dependencies_release_at_zero(self):
        p=microcase('empty',[1],[2],deps={0:()});_,a,_,_=simulate(request(p,'storm-hold-v1'))
        self.assertTrue(np.all(a['full_customer_release_hours']==0))
    def test_storm_hold_is_event_wide_not_added_per_task(self):
        r=request();ds,h=draws(r);h[:]=7200
        starts,ends=replay(r,ds,h)
        self.assertEqual(int(max(v[0] for v in ends.values())),7*3600)
    def test_rounding_and_people_semantics(self):
        p=microcase('round',['0.0003'],[2]);raw=p.model_dump();raw['duration_assumption']='ideal_all_people'
        p=BenchmarkProblem.model_validate(raw);_,a,_,ends=simulate(request(p))
        self.assertEqual(ends[p.tasks[0].id][0],1)
    def test_bad_schedules_profiles_and_trial_counts_rejected(self):
        r=request();raw=r.model_dump()
        for change in ({'trials':0},{'trials':10001},{'profile':'utility-calibrated'},{'evidence_class':'source-derived'}):
            with self.assertRaises(ValueError):simulate({**raw,**change})
        raw['schedule']['assignments']=[]
        with self.assertRaises(ValueError):simulate(raw)
    def test_wrong_problem_fingerprint_and_unchecked_copy_rejected(self):
        r=request();bad=r.model_copy(update={'schedule':r.schedule.model_copy(update={'problem_fingerprint':'forged'})})
        with self.assertRaises(ValueError):simulate(bad)
    def test_corrupted_draws_and_overflow_rejected(self):
        r=request();ds,h=draws(r);ds[next(iter(ds))][0]=0
        with self.assertRaises(ValueError):replay(r,ds,h)
        with self.assertRaises(ValueError):simulate(request(microcase('huge',[10**14],[2])))


class SamplingTests(unittest.TestCase):
    def test_common_draws_ignore_policy_execution_order(self):
        a=request(profile='shared-050-v1',trials=2000);b=request(profile='shared-050-v1',trials=2000,policy=POLICIES[0])
        da,ha=draws(a);db,hb=draws(b)
        for key in da:np.testing.assert_array_equal(da[key],db[key])
        np.testing.assert_array_equal(ha,hb)
    def test_prefix_reproducibility_and_seed_changes(self):
        a=request(profile='independent-050-v1',trials=2000);b=a.model_copy(update={'trials':10000})
        da,_=draws(a);db,_=draws(b)
        for key in da:np.testing.assert_array_equal(da[key],db[key][:2000])
        dc,_=draws(a.model_copy(update={'seed':12}));self.assertFalse(np.array_equal(da[next(iter(da))],dc[next(iter(dc))]))
    def test_known_lognormal_quantiles_and_synthetic_coverage(self):
        p=microcase('one',[1],[1]);r=request(p,'independent-050-v1',10000)
        _,a,_,_=simulate(r);values=a['full_customer_release_hours'];s=summarize(values)
        for key,q in [('p10',.1),('p50',.5),('p90',.9)]:
            expected=np.exp(.5*NormalDist().inv_cdf(q));self.assertLess(abs(s[key]-expected),.04*expected)
        lower=np.exp(.5*NormalDist().inv_cdf(.1));upper=np.exp(.5*NormalDist().inv_cdf(.9))
        self.assertLess(abs(np.mean((values>=lower)&(values<=upper))-.8),.025)
    def test_shared_correlation_and_marginal_log_variance(self):
        p=microcase('corr',[1,1],[1,1]);r=request(p,'shared-050-v1',10000);ds,_=draws(r)
        x,y=[v/3600 for v in ds.values()];logs=np.log([x,y])
        self.assertLess(abs(np.corrcoef(logs)[0,1]-.5),.035)
        target=(np.exp(.125)-1)/(np.exp(.25)-1)
        self.assertLess(abs(np.corrcoef([x,y])[0,1]-target),.04)
        self.assertTrue(np.all(abs(logs.var(axis=1)-.25)<.02))
    def test_independent_correlation_uniform_support_and_hold(self):
        p=microcase('ind',[1,1],[1,1]);ds,_=draws(request(p,'independent-050-v1',10000))
        self.assertLess(abs(np.corrcoef(list(ds.values()))[0,1]),.04)
        ds,_=draws(request(p,'uniform-sensitivity-v1',10000))
        self.assertTrue(all(np.all((v>=1800)&(v<=5400)) for v in ds.values()))
        _,hold=draws(request(p,'storm-hold-v1',10000));self.assertTrue(np.all((hold>=0)&(hold<=14400)))
        self.assertLess(abs(hold.mean()-7200),150)
    def test_numerical_repeat(self):
        a=simulate(request(profile='shared-025-v1'));b=simulate(request(profile='shared-025-v1'))
        self.assertEqual(a[0],b[0]);self.assertEqual(digest(a[1]),digest(b[1]))


class ReportTests(unittest.TestCase):
    def test_unresolved_quantiles_and_paired_negative_results(self):
        self.assertIsNone(summarize([1,np.nan])['p50'])
        r=paired(np.array([1.,4.,3.]),np.array([2.,3.,3.]))
        self.assertEqual((r['better'],r['worse'],r['ties']),(1,1,1))
    def test_convergence_failure_is_explicit(self):
        values=np.r_[np.zeros(2000),np.full(8000,10.)]
        self.assertEqual(convergence(values)['status'],'unstable_at_cap')
        self.assertEqual(convergence(np.ones(10000))['status'],'stable')
    def test_smoke_archive_reconstruction_and_corruption(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'run';m=run(path,'smoke');r=report(path)
            self.assertEqual(r['runs'],280);self.assertFalse(r['failures'])
            row=m['records'][0];p=BenchmarkProblem.model_validate(m['inputs'][row['case']]['problem'])
            arrays=read_arrays(path,row,p);self.assertEqual(digest(arrays),row['metadata']['numerical_sha256'])
            with np.load(path/row['file']) as z:release=z['group_release_ticks'].copy();span=z['makespan_hours'].copy()
            release[0,0]+=1;np.savez_compressed(path/row['file'],group_release_ticks=release,makespan_hours=span)
            with self.assertRaises(ValueError):report(path)
            with self.assertRaises(FileExistsError):run(path,'smoke')

if __name__=='__main__':unittest.main()
