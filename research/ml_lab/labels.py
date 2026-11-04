"""Four-policy targets, checked independently before any label is emitted."""
from __future__ import annotations

from typing import Any

from benchmarks.contracts import BenchmarkProblem
from benchmarks.metrics import calculate
from benchmarks.policies import POLICIES, schedule
from benchmarks.validation import validate
from .features import validated_problem

LABEL_VERSION = "ml-four-policy-labels-v1"


def evaluate_problem(problem: BenchmarkProblem | dict[str, Any]) -> dict[str, Any]:
    p = validated_problem(problem)
    outcomes = {}
    reasons = set()
    for policy in POLICIES:
        plan = schedule(p, policy)
        metrics = calculate(p, plan)
        errors = validate(p, plan, metrics)
        if errors:
            raise ValueError(f"Independent policy-result validation failed for {policy}: {errors}")
        releases = metrics["release_ticks"]
        known = all(tick is not None for tick in releases.values())
        cost_ticks = sum(len(g.customer_ids) * releases[g.id] for g in p.groups) if known else None
        if plan.unscheduled_tasks:
            reasons.add("incomplete_task_scope")
        if not known:
            reasons.add("unresolved_customer_release")
        outcomes[policy] = {"schedule": plan.model_dump(mode="json"), "metrics": metrics, "cost_ticks": cost_ticks}
    eligible = not reasons
    ties = []
    if eligible:
        best = min(outcomes[policy]["cost_ticks"] for policy in POLICIES)
        ties = sorted(policy for policy in POLICIES if outcomes[policy]["cost_ticks"] == best)
    return {"version": LABEL_VERSION, "problem_fingerprint": p.fingerprint,
            "eligible": eligible, "reason": ",".join(sorted(reasons)) if reasons else None,
            "label": ties[0] if ties else None, "ties": ties, "outcomes": outcomes}
