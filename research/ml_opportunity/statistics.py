"""Independent standard-library estimands; no historical aggregation imports."""
from collections import defaultdict
import math
import random
from statistics import mean, stdev

SEED = 2026110422


def quantile(values, p):
    xs = sorted(values)
    if not xs or not 0 <= p <= 1:
        raise ValueError("Empty sample or invalid quantile")
    position = (len(xs)-1)*p
    lower = int(position)
    upper = min(lower+1, len(xs)-1)
    return xs[lower] + (xs[upper]-xs[lower])*(position-lower)


def distribution(values):
    xs = list(values)
    if not xs:
        return dict(n=0, mean=None, p0=None, p50=None, p95=None, p100=None)
    if not all(math.isfinite(x) for x in xs):
        raise ValueError("Nonfinite observation")
    return dict(n=len(xs), mean=mean(xs), **{f"p{p}": quantile(xs, p/100) for p in (0, 50, 95, 100)})


def grouped(pairs):
    buckets = defaultdict(list)
    for group, value in pairs:
        if value is not None:
            if not math.isfinite(value):
                raise ValueError("Nonfinite observation")
            buckets[group].append(value)
    return {g: mean(xs) for g, xs in sorted(buckets.items())}


def comparison(reference, candidate, replicates=2000):
    """Candidate minus reference; strict support equality, equal group weights."""
    if not reference or reference.keys() != candidate.keys():
        raise ValueError("Empty or unmatched group support")
    groups = sorted(reference)
    a, b = [reference[g] for g in groups], [candidate[g] for g in groups]
    if not all(math.isfinite(v) for v in a+b):
        raise ValueError("Nonfinite group mean")
    differences = [y-x for x, y in zip(a, b)]
    rng = random.Random(SEED)
    boot, ratios = [], []
    for _ in range(replicates):
        indices = rng.choices(range(len(a)), k=len(a))
        ma, mb = mean(a[i] for i in indices), mean(b[i] for i in indices)
        boot.append(mb-ma)
        if ma > 0:
            ratios.append(mb/ma)
    return dict(groups=len(a), reference=mean(a), candidate=mean(b), delta=mean(differences),
        delta_ci95=[quantile(boot, p) for p in (.025, .975)],
        ratio=mean(b)/mean(a) if mean(a) > 0 else None,
        ratio_ci95=[quantile(ratios, p) for p in (.025, .975)] if len(ratios) == replicates else None,
        sd_delta=stdev(differences) if len(a) > 1 else None)


def ceiling(costs, reference):
    """Restricted per-configuration hindsight; never claims a universal bound."""
    groups = costs[reference].keys()
    if any(v.keys() != groups for v in costs.values()) or not groups:
        raise ValueError("Selector support mismatch")
    winners = {g: min(costs, key=lambda m: (costs[m][g], m)) for g in sorted(groups)}
    best = {g: costs[winners[g]][g] for g in sorted(groups)}
    if any(v <= 0 for v in costs[reference].values()):
        raise ValueError("Relative ceiling requires positive reference costs")
    fractions = {g: 1-best[g]/costs[reference][g] for g in best}
    return dict(methods=sorted(costs), winners=winners, reference_by_group=costs[reference],
        best_by_group=best, relative_by_group=fractions,
        mean_group_relative_improvement=mean(fractions.values()),
        ratio_of_means_improvement=1-mean(best.values())/mean(costs[reference].values()),
        comparison=comparison(costs[reference], best),
        interpretation="Outcome-informed selection on spent evidence, restricted to listed policies")


def planning_budget(reference, candidate, fraction=.02):
    difference = [candidate[g]-reference[g] for g in sorted(reference)]
    if len(difference) < 2 or reference.keys() != candidate.keys():
        raise ValueError("Power planning needs paired configurations")
    target = fraction*mean(reference.values())
    sd = stdev(difference)
    if target <= 0:
        raise ValueError("Positive minimum effect required")
    n = max(2, math.ceil(((1.959963984540054+0.8416212335729143)*sd/target)**2))
    return dict(minimum_relative_gain=fraction, minimum_hours=target, historical_paired_sd=sd,
                normal_approx_groups=n, doubled_sd_groups=max(2, math.ceil(4*((2.801585218112968*sd/target)**2))),
                caveat="Historical variance proxy; 80% power vs zero, not certification of a 2% lower bound")
