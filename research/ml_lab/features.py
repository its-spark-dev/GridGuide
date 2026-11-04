"""Versioned pre-decision features. No scheduler, metric or label dependency."""
from __future__ import annotations

from collections import Counter
import math
from statistics import fmean, pstdev
from typing import Any

from benchmarks.contracts import BenchmarkProblem

FEATURE_VERSION = "ml-static-features-v1"

# The ordered dictionary is also the prediction schema; metadata never enters X.
FEATURE_SCHEMA = {
    "task_count": ("count", "len(tasks)"),
    "crew_count": ("count", "len(crews)"),
    "people_per_crew": ("people", "crews[0].people; separate from crew count"),
    "ideal_all_people": ("indicator", "duration_assumption equals ideal_all_people"),
    "effort_mean": ("person-hours", "mean of known task effort"),
    "effort_std": ("person-hours", "population SD of known task effort"),
    "effort_q25": ("person-hours", "linear 25th percentile of known effort"),
    "effort_median": ("person-hours", "linear median of known effort"),
    "effort_q75": ("person-hours", "linear 75th percentile of known effort"),
    "effort_max": ("person-hours", "maximum known effort"),
    "effort_sum": ("person-hours", "sum of known effort; missingness separate"),
    "effort_missing_fraction": ("fraction", "tasks with null effort / task count"),
    "blocked_fraction": ("fraction", "tasks with access other than clear / task count"),
    "dag_depth": ("edges", "longest prerequisite path"),
    "dag_level_width": ("tasks", "largest longest-path-level population; not exact antichain width"),
    "dag_edge_density": ("fraction", "prerequisite edges / n(n-1)/2"),
    "indegree_mean": ("edges", "mean prerequisite count"),
    "indegree_max": ("edges", "maximum prerequisite count"),
    "outdegree_max": ("edges", "maximum direct successor count"),
    "root_fraction": ("fraction", "tasks without prerequisite / task count"),
    "leaf_fraction": ("fraction", "tasks without successor / task count"),
    "bottleneck_fraction": ("fraction", "tasks with at least ceil(n/2) strict descendants / n"),
    "ancestor_mean": ("tasks", "mean distinct prerequisite ancestor count"),
    "group_count": ("count", "len(groups)"),
    "customer_count": ("count", "sum of disjoint group membership sizes"),
    "group_size_mean": ("customers", "mean group membership size"),
    "group_size_std": ("customers", "population SD of group membership size"),
    "group_size_max": ("customers", "maximum group membership size"),
    "small_group_fraction": ("fraction", "groups with <=5 customers / group count"),
    "requirements_mean": ("tasks", "mean direct customer-group required-task count"),
    "requirements_max": ("tasks", "maximum direct customer-group required-task count"),
    "dependency_overlap": ("fraction", "mean pairwise required-task Jaccard; empty/empty defined zero"),
    "task_group_membership_max": ("groups", "maximum groups directly requiring a task"),
    "critical_group_fraction": ("fraction", "explicit critical-service groups / group count"),
    "unresolved_group_fraction": ("fraction", "groups with unresolved_dependency / group count"),
    "branch_count": ("count", "number of distinct branch equivalence classes; no branch label"),
    "crew_available_mean": ("hours", "mean declared crew availability / 3600"),
    "crew_available_std": ("hours", "population SD declared crew availability / 3600"),
    "crew_available_max": ("hours", "maximum declared crew availability / 3600"),
    "report_effort_correlation": ("correlation", "Pearson declared report-order / known effort; constant defined zero"),
    "report_customer_correlation": ("correlation", "Pearson declared report-order / direct customer membership; constant defined zero"),
}
FEATURE_NAMES = tuple(FEATURE_SCHEMA)


def validated_problem(problem: BenchmarkProblem | dict[str, Any]) -> BenchmarkProblem:
    """Reparse even model instances, so unchecked model_copy updates cannot bypass validation."""
    return BenchmarkProblem.model_validate(problem.model_dump() if isinstance(problem, BenchmarkProblem) else problem)


def _mean(values: list[float]) -> float:
    return fmean(values) if values else 0.0


def _std(values: list[float]) -> float:
    return pstdev(values) if values else 0.0


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    return ordered[lower] + (ordered[math.ceil(position)] - ordered[lower]) * (position - lower)


def _correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = fmean(xs), fmean(ys)
    xx, yy = math.fsum((x - mx) ** 2 for x in xs), math.fsum((y - my) ** 2 for y in ys)
    if not xx or not yy:
        return 0.0
    return math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(xx * yy)


def inference_supported(problem: BenchmarkProblem | dict[str, Any]) -> bool:
    """Complete known scope only; no simulated policy result is needed to abstain."""
    p = validated_problem(problem)
    return all(t.access == "clear" and t.total_person_hours is not None for t in p.tasks) and not any(
        g.unresolved_dependency for g in p.groups
    )


def extract_features(problem: BenchmarkProblem | dict[str, Any]) -> dict[str, float]:
    p = validated_problem(problem)
    n = len(p.tasks)
    task_by_id = {t.id: t for t in p.tasks}
    successors = {t.id: set() for t in p.tasks}
    for task in p.tasks:
        for predecessor in task.prerequisites:
            successors[predecessor].add(task.id)
    ancestors: dict[str, set[str]] = {}
    depths: dict[str, int] = {}
    while len(depths) < n:
        for task in p.tasks:
            if task.id not in depths and all(i in depths for i in task.prerequisites):
                depths[task.id] = max((depths[i] + 1 for i in task.prerequisites), default=0)
                ancestors[task.id] = set(task.prerequisites)
                for predecessor in task.prerequisites:
                    ancestors[task.id].update(ancestors[predecessor])
    descendant_counts = Counter(i for predecessors in ancestors.values() for i in predecessors)
    known_tasks = [t for t in p.tasks if t.total_person_hours is not None]
    effort = [float(t.total_person_hours) for t in known_tasks]
    sizes = [len(g.customer_ids) for g in p.groups]
    dependencies = [set(g.required_tasks) for g in p.groups]
    overlaps = [len(a & b) / len(a | b) if a | b else 0.0
                for j, a in enumerate(dependencies) for b in dependencies[j + 1:]]
    task_groups = Counter(i for g in p.groups for i in g.required_tasks)
    task_customers = Counter()
    for group in p.groups:
        for task in group.required_tasks:
            task_customers[task] += len(group.customer_ids)
    availability = [c.available_tick / 3600 for c in p.crews]
    values = [
        n, len(p.crews), p.crews[0].people, p.duration_assumption == "ideal_all_people",
        _mean(effort), _std(effort), _quantile(effort, .25), _quantile(effort, .5),
        _quantile(effort, .75), max(effort, default=0.0), math.fsum(effort),
        (n - len(effort)) / n, sum(t.access != "clear" for t in p.tasks) / n,
        max(depths.values()), max(Counter(depths.values()).values()),
        sum(len(t.prerequisites) for t in p.tasks) / max(1, n * (n - 1) / 2),
        fmean(len(t.prerequisites) for t in p.tasks), max(len(t.prerequisites) for t in p.tasks),
        max(len(s) for s in successors.values()), sum(not t.prerequisites for t in p.tasks) / n,
        sum(not successors[t.id] for t in p.tasks) / n,
        sum(descendant_counts[t.id] >= math.ceil(n / 2) for t in p.tasks) / n,
        fmean(len(a) for a in ancestors.values()), len(p.groups), sum(sizes), _mean(sizes), _std(sizes),
        max(sizes), sum(s <= 5 for s in sizes) / len(sizes),
        fmean(len(d) for d in dependencies), max(len(d) for d in dependencies), _mean(overlaps),
        max((task_groups[i] for i in task_by_id), default=0),
        sum(g.critical_service for g in p.groups) / len(p.groups),
        sum(g.unresolved_dependency for g in p.groups) / len(p.groups), len({g.branch for g in p.groups}),
        _mean(availability), _std(availability), max(availability),
        _correlation([t.report_order for t in known_tasks], effort),
        _correlation([t.report_order for t in p.tasks], [task_customers[t.id] for t in p.tasks]),
    ]
    if len(values) != len(FEATURE_NAMES):
        raise AssertionError("Feature schema/value length mismatch")
    features = dict(zip(FEATURE_NAMES, map(float, values)))
    if not all(math.isfinite(value) for value in features.values()):
        raise ValueError("Nonfinite static feature")
    return features
