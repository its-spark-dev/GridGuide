"""Bounded exhaustive enumeration, independent of all baseline scoring/metrics.

Enumerate every precedence-feasible task order and crew choice; append each job
at its earliest start. An optimal left-shifted schedule for this regular objective
exists in this enumeration (identical crews, constant durations, no calendars).
No objective pruning or heuristic incumbent. Budget interruption cannot prove optimality.
"""
from fractions import Fraction
import math
from .contracts import Assignment, Schedule


def exhaustive(problem, node_limit=250000):
    if len(problem.tasks) > 8 or any(t.access != 'clear' or t.total_person_hours is None for t in problem.tasks) or any(g.unresolved_dependency for g in problem.groups):
        return {'status':'unsupported', 'nodes':0, 'objective_ticks':None, 'schedule':None}
    tasks = {t.id:t for t in problem.tasks}
    ids = sorted(tasks)
    divisor = problem.crews[0].people if problem.duration_assumption == 'ideal_all_people' else 1
    durations = {i:math.ceil(Fraction(tasks[i].total_person_hours)*3600/divisor) for i in ids}
    nodes, stopped, best, best_assignments = 0, False, None, None
    def visit(done, availability, assignments):
        nonlocal nodes, stopped, best, best_assignments
        if nodes >= node_limit:
            stopped = True
            return
        nodes += 1
        if len(done)==len(ids):
            objective = sum(len(g.customer_ids)*max([0]+[done[t] for t in g.required_tasks]) for g in problem.groups)
            if best is None or objective < best:
                best, best_assignments = objective, tuple(assignments)
            return
        for i in ids:
            if i in done or any(p not in done for p in tasks[i].prerequisites):
                continue
            for c in sorted(availability):
                start = max([availability[c]]+[done[p] for p in tasks[i].prerequisites])
                end = start+durations[i]
                visit({**done,i:end},{**availability,c:end},assignments+[Assignment(task_id=i,crew_id=c,start_tick=start,end_tick=end)])
                if stopped:
                    return
    visit({}, {c.id:c.available_tick for c in problem.crews}, [])
    result = None if best_assignments is None else Schedule(problem_fingerprint=problem.fingerprint, policy='exhaustive-oracle-v1', assignments=best_assignments, unscheduled_tasks=())
    return {'status':'budget_exhausted' if stopped else 'optimal', 'nodes':nodes,
            'objective_ticks': best, 'schedule':result}
