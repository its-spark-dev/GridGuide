from decimal import Decimal
from benchmarks.contracts import BenchmarkProblem


def problem(ticks=(3600, 7200), weights=(1, 2), prerequisites=None, crews=1,
            arrivals=None, blocked=(), unresolved=False, people=4, assumption="one_effective_worker"):
    prerequisites = prerequisites or {}
    return BenchmarkProblem.model_validate(dict(id="syn-adaptive-fixture", family="hand-authored",
        seed=0, split="micro", duration_assumption=assumption,
        tasks=[dict(id=f"syn-t{i}", total_person_hours=(Decimal(t)-Decimal("0.1"))/3600,
                    report_order=i, prerequisites=[f"syn-t{j}" for j in prerequisites.get(i, ())],
                    access="blocked" if i in blocked else "clear") for i, t in enumerate(ticks)],
        groups=[dict(id=f"syn-g{i}", customer_ids=[f"syn-c{i}-{j}" for j in range(w)],
                     required_tasks=[f"syn-t{i}"], unresolved_dependency=unresolved and i == 0,
                     branch=f"syn-b{i}", critical_service=i == 0) for i, w in enumerate(weights)],
        crews=[dict(id=f"syn-crew{i}", people=people, available_tick=(arrivals or {}).get(i, 0)) for i in range(crews)]))
