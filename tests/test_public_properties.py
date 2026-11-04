"""Deterministic generated diagnostics; these fixtures do not replace frozen G2 data."""
import json
from pathlib import Path
import random
import unittest
from benchmarks.contracts import BenchmarkProblem
from benchmarks.policies import POLICIES, schedule
from benchmarks.metrics import calculate
from benchmarks.validation import validate


def fixture(seed):
    r=random.Random(seed);n=r.randint(3,8)
    tasks=[dict(id=f'syn-task-{i}',total_person_hours=str(r.randint(1,12)),report_order=i,
        prerequisites=[f'syn-task-{j}' for j in range(i) if r.random()<.25]) for i in range(n)]
    if seed%3==0:tasks[0]['access']='blocked'
    if seed%5==0:tasks[1]['total_person_hours']=None
    return BenchmarkProblem.model_validate(dict(id=f'syn-generated-{seed}',family='g8-software-property',
        seed=seed,split='development',tasks=tasks,duration_assumption='ideal_all_people' if seed%2 else 'one_effective_worker',
        crews=[dict(id=f'syn-crew-{i}',people=4,available_tick=seed%7) for i in range(1+seed%4)],
        groups=[dict(id=f'syn-group-{i}',customer_ids=[f'syn-person-{i}-{j}' for j in range(r.randint(1,6))],
            required_tasks=[t['id'] for t in tasks if r.random()<.5],branch=f'syn-branch-{i%2}',
            unresolved_dependency=seed%7==0 and i==0) for i in range(4)]))


class PublicProperties(unittest.TestCase):
    def test_seeded_graph_duration_crew_release_and_weighted_cost_invariants(self):
        for seed in range(8100,8136):
            problem=fixture(seed)
            try:
                for policy in POLICIES:
                    plan=schedule(problem,policy);m=calculate(problem,plan)
                    self.assertEqual(validate(problem,plan,m),[])
                    members=[x for g in problem.groups for x in g.customer_ids]
                    self.assertEqual(len(members),len(set(members)))
                    self.assertEqual(m['customers'],len(members))
                    ends={a.task_id:a.end_tick for a in plan.assignments}
                    released=[]
                    for group in problem.groups:
                        end=None if group.unresolved_dependency or not set(group.required_tasks)<=ends.keys() else max([0]+[ends[i] for i in group.required_tasks])
                        released.extend([end]*len(group.customer_ids))
                    self.assertEqual(m['modeled_customer_outage_hours'],None if None in released else sum(released)/3600)
                    self.assertEqual(m['unresolved_customers'],released.count(None))
                    corrupted=dict(m,restricted_horizon_customer_hours=-1)
                    self.assertTrue(validate(problem,plan,corrupted))
                    if len(plan.assignments)>1:
                        first,second=plan.assignments[:2]
                        bad=second.model_copy(update={'crew_id':first.crew_id,'start_tick':first.start_tick,
                            'end_tick':first.start_tick+second.end_tick-second.start_tick})
                        self.assertIn('crew_overlap',validate(problem,plan.model_copy(update={'assignments':(first,bad,*plan.assignments[2:])})))
            except Exception:
                directory=Path('artifacts/phase8/failures');directory.mkdir(parents=True,exist_ok=True)
                (directory/f'seed-{seed}.json').write_text(problem.model_dump_json(indent=2))
                raise

    def test_generated_cycles_unknown_fields_and_duplicate_customers_rejected(self):
        for seed in range(8100,8112):
            for change in ['cycle','unknown','duplicate']:
                raw=fixture(seed).model_dump(mode='json')
                if change=='cycle':raw['tasks'][0]['prerequisites']=[raw['tasks'][0]['id']]
                if change=='unknown':raw['observed_clearance']=0
                if change=='duplicate':raw['groups'][1]['customer_ids']=[raw['groups'][0]['customer_ids'][0]]
                with self.subTest(seed=seed,change=change),self.assertRaises(ValueError):
                    BenchmarkProblem.model_validate(raw)
