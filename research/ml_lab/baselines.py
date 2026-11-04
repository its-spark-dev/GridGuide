"""Training-only fixed/majority fitting and a preregistered static heuristic."""
from __future__ import annotations

from collections import Counter
from typing import Any

from benchmarks.contracts import BenchmarkProblem
from benchmarks.policies import POLICIES
from .features import extract_features, inference_supported

BASELINE_VERSION = "ml-baselines-v1"


def fit_baselines(rows: list[dict[str, Any]], *, partition: str = "train") -> dict[str, str]:
    if partition != "train" or any(row.get("partition") != "train" for row in rows):
        raise ValueError("Baseline fitting requires explicit training partition on every row")
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise ValueError("No eligible training cases")
    for row in eligible:
        if set(row["outcomes"]) != set(POLICIES) or row["label"] not in row["ties"]:
            raise ValueError("Invalid labeled training row")
        costs = [row["outcomes"][policy]["cost_ticks"] for policy in POLICIES]
        if any(type(cost) is not int or cost < 0 for cost in costs):
            raise ValueError("Expected nonnegative exact customer-second costs")
        ties = sorted(policy for policy in POLICIES if row["outcomes"][policy]["cost_ticks"] == min(costs))
        if row["ties"] != ties or row["label"] != ties[0]:
            raise ValueError("Target disagrees with exact costs")
    totals = {policy: sum(row["outcomes"][policy]["cost_ticks"] for row in eligible) for policy in POLICIES}
    labels = Counter(row["label"] for row in eligible)
    return {"fixed": min(POLICIES, key=lambda policy: (totals[policy], policy)),
            "majority": min(POLICIES, key=lambda policy: (-labels[policy], policy))}


def heuristic(problem: BenchmarkProblem | dict[str, Any]) -> str | None:
    """Multiple direct repair dependencies favor membership count; otherwise release/effort.

    This threshold is fixed before experiments, not selected from outcomes.
    """
    if not inference_supported(problem):
        return None
    features = extract_features(problem)
    return POLICIES[1] if features["requirements_mean"] > 1.5 else POLICIES[2]
