"""Result calculation only. The independent validator does not import this module."""
import math


def calculate(problem, schedule):
    ends = {a.task_id: a.end_tick for a in schedule.assignments}
    releases = {g.id: (None if g.unresolved_dependency or any(i not in ends for i in g.required_tasks)
                       else max((ends[i] for i in g.required_tasks), default=0)) for g in problem.groups}
    n = sum(len(g.customer_ids) for g in problem.groups)
    horizon = problem.horizon_ticks
    weighted = sorted((releases[g.id], len(g.customer_ids)) for g in problem.groups if releases[g.id] is not None)
    unresolved = sum(len(g.customer_ids) for g in problem.groups if releases[g.id] is None)
    censored = sum(count for t, count in weighted if t > horizon)
    def quantile(q):
        count = 0
        for t, size in weighted:
            count += size
            if count >= math.ceil(q*n):
                return t / 3600
        return None
    restricted = sum(len(g.customer_ids)*min(releases[g.id] if releases[g.id] is not None else horizon, horizon)
                     for g in problem.groups)
    milestones = []
    for tick in sorted({t for t, _ in weighted}):
        milestones.append({'tick': tick, 'additional_customers': sum(size for t, size in weighted if t == tick),
                           'cumulative_customers': sum(size for t, size in weighted if t <= tick)})
    branches = {}
    for branch in sorted({g.branch for g in problem.groups}):
        gs = [g for g in problem.groups if g.branch == branch]
        branches[branch] = None if any(releases[g.id] is None for g in gs) else (
            sum(len(g.customer_ids)*releases[g.id] for g in gs) / (3600*sum(len(g.customer_ids) for g in gs)))
    small = [g for g in problem.groups if len(g.customer_ids) <= 5]
    full = None if unresolved else sum(t*count for t, count in weighted)/3600
    return {'version': 'benchmark-metrics-v1', 'customers': n, 'release_ticks': releases, 'milestones': milestones,
            'modeled_customer_outage_hours': full, 'restricted_horizon_customer_hours': restricted/3600,
            'horizon_hours': 168, 'unresolved_customers': unresolved, 'censored_customers': censored,
            'unreleased_customers_at_horizon': unresolved+censored, 'known_release_customers': n-unresolved,
            'makespan_hours': None if len(ends) != len(problem.tasks) else max(ends.values())/3600,
            'full_customer_release_hours': None if unresolved else max((t for t, _ in weighted), default=0)/3600,
            'release_50_hours': quantile(.5), 'release_90_hours': quantile(.9), 'release_100_hours': quantile(1),
            'weighted_median_hours': None if unresolved else quantile(.5),
            'weighted_p95_hours': None if unresolved else quantile(.95),
            'maximum_wait_hours': None if unresolved else quantile(1),
            'critical_service_latency_hours': {g.id: None if releases[g.id] is None else releases[g.id]/3600
                                               for g in problem.groups if g.critical_service},
            'branch_mean_wait_hours': branches,
            'branch_mean_disparity_hours': None if any(v is None for v in branches.values()) else max(branches.values())-min(branches.values()),
            'small_group_customers': sum(len(g.customer_ids) for g in small),
            'small_group_mean_wait_hours': None if not small or any(releases[g.id] is None for g in small) else
                sum(len(g.customer_ids)*releases[g.id] for g in small)/(3600*sum(len(g.customer_ids) for g in small))}
