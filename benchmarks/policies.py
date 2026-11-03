"""Four deterministic list-scheduling baselines, not an improved optimizer.

Legacy rank rules are normalized to one conditional tick duration and earliest
feasible crew finish. They do NOT reproduce the old dual-envelope UI scheduler.
"""
from fractions import Fraction
from .contracts import Assignment, Schedule, duration_ticks

POLICIES = ('fifo-v1', 'customer-count-v1', 'legacy-release-per-person-hour-adapter-v1',
            'legacy-critical-proxy-first-adapter-v1')


def schedule(problem, policy):
    if policy not in POLICIES:
        raise ValueError('Unknown policy')
    tasks = {t.id: t for t in problem.tasks}
    durations = {i: duration_ticks(problem, t) for i, t in tasks.items()}
    remaining = set(tasks)
    ends, assignments = {}, []
    availability = {c.id: c.available_tick for c in problem.crews}
    critical = set(t for g in problem.groups if g.critical_service for t in g.required_tasks)
    for _ in tasks:
        critical |= {p for i in tuple(critical) for p in tasks[i].prerequisites}
    while remaining:
        ready = [i for i in remaining if durations[i] is not None and set(tasks[i].prerequisites) <= ends.keys()]
        if not ready:
            break
        def marginal(i):
            return sum(len(g.customer_ids) for g in problem.groups if not g.unresolved_dependency
                       and i in g.required_tasks and set(g.required_tasks) <= ends.keys() | {i})
        def rank(i):
            task = tasks[i]
            if policy == POLICIES[0]:
                return (task.report_order, i)
            if policy == POLICIES[1]:
                return (-sum(len(g.customer_ids) for g in problem.groups if i in g.required_tasks), i)
            n = marginal(i)
            return (-int(policy == POLICIES[3] and i in critical),
                    -Fraction(n) / Fraction(task.total_person_hours), -n, task.total_person_hours, i)
        i = min(ready, key=rank)
        earliest = max((ends[p] for p in tasks[i].prerequisites), default=0)
        crew = min(availability, key=lambda c: (max(availability[c], earliest) + durations[i], c))
        start = max(availability[crew], earliest)
        ends[i] = availability[crew] = start + durations[i]
        assignments.append(Assignment(task_id=i, crew_id=crew, start_tick=start, end_tick=ends[i]))
        remaining.remove(i)
    return Schedule(problem_fingerprint=problem.fingerprint, policy=policy,
                    assignments=tuple(assignments), unscheduled_tasks=tuple(sorted(remaining)))
