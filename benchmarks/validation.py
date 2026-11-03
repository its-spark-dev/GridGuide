"""Independent schedule and metric checker: no policy/metric-generator imports."""
from collections import Counter, defaultdict
from fractions import Fraction
import math
from .contracts import BenchmarkProblem, Schedule


def validate(problem, schedule, metrics=None):
    try:
        p = BenchmarkProblem.model_validate(problem.model_dump() if isinstance(problem, BenchmarkProblem) else problem)
    except ValueError:
        return ['invalid_problem']
    try:
        s = Schedule.model_validate(schedule.model_dump() if isinstance(schedule, Schedule) else schedule)
    except ValueError:
        return ['invalid_schedule_schema']
    errors = []
    if s.problem_fingerprint != p.fingerprint:
        errors.append('input_fingerprint')
    tasks, crews = {t.id: t for t in p.tasks}, {c.id: c for c in p.crews}
    counts = Counter(a.task_id for a in s.assignments)
    unassigned = set(s.unscheduled_tasks)
    if any(c != 1 for c in counts.values()) or len(unassigned) != len(s.unscheduled_tasks):
        errors.append('duplicate_task')
    if set(counts) & unassigned or set(counts) | unassigned != tasks.keys():
        errors.append('missing_or_unknown_task')
    ends = {a.task_id: a.end_tick for a in s.assignments}
    # Independent fixed point determines which tasks can actually execute.
    executable = set()
    while True:
        enlarged = executable | {t.id for t in p.tasks if t.access == 'clear' and t.total_person_hours is not None
                                  and all(x in executable for x in t.prerequisites)}
        if enlarged == executable:
            break
        executable = enlarged
    if set(counts) != executable or unassigned != tasks.keys() - executable:
        errors.append('incorrect_executable_scope')
    intervals = defaultdict(list)
    for a in s.assignments:
        if a.task_id not in tasks or a.crew_id not in crews:
            errors.append('unknown_task_or_crew')
            continue
        t, c = tasks[a.task_id], crews[a.crew_id]
        if t.access != 'clear' or t.total_person_hours is None:
            errors.append('blocked_or_unknown_work')
            continue
        divisor = c.people if p.duration_assumption == 'ideal_all_people' else 1
        duration = math.ceil(Fraction(t.total_person_hours)*3600/divisor)
        if a.end_tick-a.start_tick != duration:
            errors.append('duration_arithmetic')
        if a.start_tick < c.available_tick:
            errors.append('crew_availability')
        if any(x not in ends or ends[x] > a.start_tick for x in t.prerequisites):
            errors.append('precedence')
        intervals[a.crew_id].append((a.start_tick, a.end_tick))
    for pairs in intervals.values():
        ordered = sorted(pairs)
        if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
            errors.append('crew_overlap')
    if errors or metrics is None:
        return sorted(set(errors))
    # Expand explicit customer membership, independently of weighted-group calculations.
    times, release, by_branch, small, critical = [], {}, defaultdict(list), [], {}
    for g in p.groups:
        tick = None if g.unresolved_dependency or any(t not in ends for t in g.required_tasks) else max([0]+[ends[t] for t in g.required_tasks])
        release[g.id] = tick
        times.extend([tick]*len(g.customer_ids))
        by_branch[g.branch].extend([tick]*len(g.customer_ids))
        if len(g.customer_ids) <= 5:
            small.extend([tick]*len(g.customer_ids))
        if g.critical_service:
            critical[g.id] = None if tick is None else tick/3600
    known = sorted(t for t in times if t is not None)
    unresolved = times.count(None)
    def q(value):
        index = math.ceil(value*len(times))-1
        return known[index]/3600 if index < len(known) else None
    def mean(values):
        return None if not values or None in values else sum(values)/(3600*len(values))
    branch = {k: mean(v) for k, v in sorted(by_branch.items())}
    cumulative, milestones = 0, []
    for tick, count in sorted(Counter(known).items()):
        cumulative += count
        milestones.append(dict(tick=tick, additional_customers=count, cumulative_customers=cumulative))
    censored = sum(t > p.horizon_ticks for t in known)
    expected = dict(version='benchmark-metrics-v1', customers=len(times), release_ticks=release, milestones=milestones,
        modeled_customer_outage_hours=None if unresolved else sum(known)/3600,
        restricted_horizon_customer_hours=sum(p.horizon_ticks if t is None else min(t,p.horizon_ticks) for t in times)/3600,
        horizon_hours=168, unresolved_customers=unresolved, censored_customers=censored,
        unreleased_customers_at_horizon=unresolved+censored, known_release_customers=len(known),
        makespan_hours=None if unassigned else max(ends.values())/3600,
        full_customer_release_hours=None if unresolved else max(known)/3600,
        release_50_hours=q(.5), release_90_hours=q(.9), release_100_hours=q(1),
        weighted_median_hours=None if unresolved else q(.5), weighted_p95_hours=None if unresolved else q(.95),
        maximum_wait_hours=None if unresolved else q(1), critical_service_latency_hours=critical,
        branch_mean_wait_hours=branch,
        branch_mean_disparity_hours=None if None in branch.values() else max(branch.values())-min(branch.values()),
        small_group_customers=len(small), small_group_mean_wait_hours=mean(small))
    def same(a,b):
        if type(a) is dict and type(b) is dict:
            return a.keys() == b.keys() and all(same(a[k],b[k]) for k in a)
        if type(a) is list and type(b) is list:
            return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        if isinstance(a,(int,float)) and not isinstance(a,bool):
            return isinstance(b,(int,float)) and not isinstance(b,bool) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)
        return type(a) is type(b) and a==b
    if not isinstance(metrics,dict) or metrics.keys()!=expected.keys():
        errors.append('metric_schema')
    else:
        errors.extend('metric:'+key for key in expected if not same(expected[key],metrics[key]))
    return sorted(errors)
