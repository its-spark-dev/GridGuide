"""Artificial software fixtures only; none are empirical predictive evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research.risk.validation import (Observation, STEP, DAY, GATES, utc, label_window,
                                      coverage, check_features, check_splits, feasibility)
from research.risk.audit import storm_audit
from scripts.evaluate_risk_feasibility import evaluate

ISSUE = datetime(2020,6,1,tzinfo=timezone.utc)
COUNTY = '39049'


def panel(count=0):
    return [Observation(COUNTY, ISSUE-DAY+STEP*i, count, True, 'test-scope') for i in range(1,193)]


def label(rows): return label_window(COUNTY, ISSUE, rows, {COUNTY})


def splitrow(role, index, outcome=0):
    year={'train':2019,'validation':2021,'test':2022}[role]
    issue=datetime(year,3,1,tzinfo=timezone.utc)+DAY*index
    return dict(id=f'{role}-{index}',county=COUNTY,split=role,cluster=f'{role}-event-{index}',
                issue=issue.isoformat(),feature_start=(issue-DAY).isoformat(),
                target_end=(issue+DAY).isoformat(),label=outcome)


class LabelTests(unittest.TestCase):
    def test_explicit_observed_zero_is_negative(self):
        self.assertEqual(label(panel())['label'],0)
    def test_absent_and_null_are_not_zero(self):
        rows=panel();rows.pop(120)
        self.assertIsNone(label(rows)['label'])
        rows=panel();r=rows[120];rows[120]=Observation(COUNTY,r.time,None,True,'test-scope')
        self.assertIsNone(label(rows)['label'])
    def test_failed_collection_and_unknown_scope_withhold(self):
        for observed,scope in [(False,'test-scope'),(True,None),(True,'changed')]:
            rows=panel();r=rows[130];rows[130]=Observation(COUNTY,r.time,0,observed,scope)
            self.assertFalse(label(rows)['eligible'])
    def test_strict_threshold_and_sampled_hour(self):
        self.assertEqual(label(panel(100))['label'],0)
        self.assertEqual(label(panel(101))['label'],1)
        rows=panel()
        for i in range(96,100):rows[i]=Observation(COUNTY,rows[i].time,101,True,'test-scope')
        self.assertEqual(label(rows)['label'],0)
        rows[100]=Observation(COUNTY,rows[100].time,101,True,'test-scope')
        self.assertEqual(label(rows)['label'],1)
    def test_noncontiguous_spikes_and_issue_boundary_do_not_count(self):
        rows=panel()
        for i in (96,98,100,102,104):rows[i]=Observation(COUNTY,rows[i].time,101,True,'test-scope')
        self.assertEqual(label(rows)['label'],0)
        rows=panel()
        for i in range(95,100):rows[i]=Observation(COUNTY,rows[i].time,101,True,'test-scope')
        self.assertEqual(label(rows)['label'],0)
    def test_positive_partial_window_is_withheld(self):
        rows=panel(200);rows.pop(0)
        self.assertIsNone(label(rows)['label'])
    def test_duplicate_is_rejected(self):
        rows=panel()
        with self.assertRaises(ValueError):label(rows+[rows[0]])
    def test_bad_ids_counts_and_timestamps(self):
        for count in (-1,True,1.2):
            with self.assertRaises(ValueError):Observation(COUNTY,ISSUE,count,True,'x')
        with self.assertRaises(ValueError):Observation('049',ISSUE,0,True,'x')
        with self.assertRaises(ValueError):Observation(COUNTY,ISSUE+timedelta(minutes=1),0,True,'x')
        with self.assertRaises(ValueError):utc('2020-01-01')
        with self.assertRaises(ValueError):label_window(COUNTY,ISSUE,panel(),{'42001'})
    def test_missing_days_remain_in_denominator(self):
        r=coverage([label(panel())],{COUNTY},(2020,))
        self.assertEqual(r['county_years'][0]['expected'],366)
        self.assertEqual(r['county_years'][0]['eligible'],1)
        self.assertFalse(r['passed'])
    def test_complete_coverage_and_duplicate_issues(self):
        rows=[dict(county=COUNTY,issue=(datetime(2020,1,1,tzinfo=timezone.utc)+DAY*i).isoformat(),eligible=True,label=0) for i in range(366)]
        self.assertTrue(coverage(rows,{COUNTY},(2020,))['passed'])
        with self.assertRaises(ValueError):coverage(rows+[rows[0]],{COUNTY},(2020,))
        self.assertFalse(coverage([],set(),())['passed'])


class LeakageTests(unittest.TestCase):
    def test_future_and_retrospective_feature_guards(self):
        f=dict(name='lag_mean',observation_end=ISSUE.isoformat(),available_at=ISSUE.isoformat())
        check_features([f],ISSUE)
        for change in ({'name':'storm_damage'}, {'observation_end':(ISSUE+STEP).isoformat()},
                       {'available_at':(ISSUE+STEP).isoformat()}, {'available_at':None}):
            with self.assertRaises(ValueError):check_features([{**f,**change}],ISSUE)
        check_features([{**f,'available_at':None}],ISSUE,retrospective=True)
    def test_event_overlap_rejected(self):
        a=splitrow('train',0);b=splitrow('test',0);b['cluster']=a['cluster']
        with self.assertRaises(ValueError):check_splits([a,b],set(),set())
    def test_boundary_and_window_overlap_rejected(self):
        a=splitrow('test',0);a.update(issue='2022-01-02T00:00:00+00:00',feature_start='2022-01-01T00:00:00+00:00',target_end='2022-01-03T00:00:00+00:00')
        with self.assertRaises(ValueError):check_splits([a],set(),set())
        a=splitrow('train',0);a['target_end']=a['issue']
        with self.assertRaises(ValueError):check_splits([a],set(),set())
    def test_fit_and_calibration_leakage(self):
        rows=[splitrow(k,0) for k in ('train','validation','test')]
        for fit,cal in [({'test-0'},set()),(set(),{'train-0'}),(set(),{'test-0'})]:
            with self.assertRaises(ValueError):check_splits(rows,fit,cal)
    def test_minimum_events_and_both_classes(self):
        rows=[splitrow(k,i,i%2) for k in ('train','validation') for i in range(2)]
        rows += [splitrow('test',i,i%2) for i in range(30)]
        self.assertTrue(check_splits(rows,{'train-0'},{'validation-0'})['sufficient'])
        self.assertFalse(check_splits(rows[:-1],set(),set())['sufficient'])
        for row in rows:row['label']=0
        self.assertFalse(check_splits(rows,set(),set())['sufficient'])
    def test_duplicate_county_time_with_different_id(self):
        a=splitrow('train',0);b={**a,'id':'duplicate'}
        with self.assertRaises(ValueError):check_splits([a,b],set(),set())


class EvidenceTests(unittest.TestCase):
    def test_every_gate_required_unknown_permissions_fail_closed(self):
        gates={k:{'status':'pass','evidence':['test-only citation']} for k in GATES}
        self.assertTrue(feasibility(gates)['modeling_authorized'])
        for k in GATES:
            changed=deepcopy(gates);changed[k]['status']='unverified'
            self.assertFalse(feasibility(changed)['modeling_authorized'])
        with self.assertRaises(ValueError):feasibility({})
        gates[GATES[0]]['evidence']=[]
        with self.assertRaises(ValueError):feasibility(gates)
    def test_recorded_decision_and_hashes_reproduce(self):
        a=evaluate();self.assertEqual(a,evaluate())
        self.assertEqual(a['decision'],'no_go');self.assertEqual(a['models_fitted'],0)
        self.assertIsNone(a['predictive_metrics'])
        stored=Path('docs/research/phase4/feasibility.json')
        if stored.exists():self.assertEqual(a,json.loads(stored.read_text()))
    def test_no_source_no_network_decision(self):
        code="""
import sys
def audit(event,args):
    if event=='socket.connect':raise AssertionError('Network forbidden')
    if event=='open' and isinstance(args[0],str) and any(p in args[0] for p in ('/data/raw/','/data/processed/','/data/external/')):raise AssertionError('Raw data forbidden')
sys.addaudithook(audit)
from scripts.evaluate_risk_feasibility import evaluate
assert evaluate()['decision']=='no_go'
assert 'backend.config' not in sys.modules
"""
        subprocess.run([sys.executable,'-c',code],check=True,capture_output=True)
    def test_storm_payload_schema_and_duplicate_detection(self):
        header='STATE_FIPS,CZ_FIPS,CZ_TYPE,EPISODE_ID,EVENT_ID,BEGIN_DATE_TIME,END_DATE_TIME,CZ_TIMEZONE,YEAR\n'
        row='39,049,C,e1,id1,a,b,EST-5,2022\n'
        a=storm_audit(gzip.compress((header+row+row).encode()))
        self.assertEqual(a['rows'],2);self.assertEqual(a['duplicate_event_ids'],1)
        self.assertEqual(a['reported_county_codes']['39'],1)
        with self.assertRaises(ValueError):storm_audit(gzip.compress(b'x,y\n1,2\n'))

if __name__=='__main__':unittest.main()
