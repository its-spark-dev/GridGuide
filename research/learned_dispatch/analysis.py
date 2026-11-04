"""Predeclared grouped estimands, paired intervals and promotion guards."""
from collections import defaultdict
import numpy as np

from . import VERSION, SEED
from .models import CANDIDATES
from .rollout import MEDIAN, REACTIVE


def value(row, metric="waiting"):
    m = row["metrics"]
    if metric == "waiting":
        return None if m["modeled_customer_outage_hours"] is None else m["modeled_customer_outage_hours"]/m["customers"]
    if metric == "critical":
        values = list(m["critical_service_latency_hours"].values())
        return max(values) if values and None not in values else None
    if metric == "p95":
        return m["weighted_p95_hours"]
    if metric == "branch":
        return m["branch_mean_disparity_hours"]
    raise ValueError("Unknown metric")


def key(row):
    return row["case_id"], row["profile"], row["episode_seed"]


def group_mean(rows, metric="waiting"):
    grouped = defaultdict(list)
    for row in rows:
        v = value(row, metric)
        if v is not None:
            grouped[row["group_id"]].append(v)
    return {g: float(np.mean(v)) for g, v in sorted(grouped.items())}


def paired_arrays(reference, candidate):
    groups = sorted(reference.keys() & candidate.keys())
    if not groups:
        return dict(groups=0, reference_mean=None, candidate_mean=None, ratio=None,
                    ratio_ci95=None, degradation=None, degradation_ci95=None)
    a = np.array([reference[g] for g in groups])
    b = np.array([candidate[g] for g in groups])
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Nonfinite estimand")
    indices = np.random.default_rng(SEED).integers(0, len(a), size=(2000, len(a)))
    ma, mb = np.mean(a[indices], axis=1), np.mean(b[indices], axis=1)
    ratio = float(b.mean()/a.mean()) if a.mean() > 0 else None
    ratio_ci = np.quantile(mb/ma, [.025, .975]).tolist() if np.all(ma > 0) else None
    return dict(groups=len(a), reference_mean=float(a.mean()), candidate_mean=float(b.mean()),
        ratio=ratio, ratio_ci95=ratio_ci, degradation=float((b-a).mean()),
        degradation_ci95=np.quantile(mb-ma, [.025, .975]).tolist(),
        per_group_reference=dict(zip(groups, a.tolist())), per_group_candidate=dict(zip(groups, b.tolist())))


def paired(rows, reference, candidate, metric="waiting"):
    a = {key(r): r for r in rows if r["method"] == reference}
    b = {key(r): r for r in rows if r["method"] == candidate}
    if not a or a.keys() != b.keys():
        raise ValueError("Paired episode coverage mismatch")
    for k, r in a.items():
        if r["durations"] != b[k]["durations"] or r["group_id"] != b[k]["group_id"]:
            raise ValueError("Paired exogenous input mismatch")
    result = paired_arrays(group_mean(a.values(), metric), group_mean(b.values(), metric))
    differences, ratios = [], []
    for k in a:
        va, vb = value(a[k], metric), value(b[k], metric)
        if va is not None and vb is not None:
            differences.append(vb-va)
            if va > 0:
                ratios.append(vb/va)
    result.update(episodes=len(differences), max_episode_ratio=max(ratios) if ratios else None,
        wins=sum(d < -1e-12 for d in differences), ties=sum(abs(d) <= 1e-12 for d in differences),
        losses=sum(d > 1e-12 for d in differences))
    return result


def timing_summary(timings, method):
    own = [r for r in timings if r["method"] == method]
    all_times, discretionary, by_group = [], [], defaultdict(list)
    for row in own:
        all_times.extend(row.get("decision_nanoseconds", []))
        values = [v for v, n in zip(row.get("decision_nanoseconds", []), row.get("decision_choice_counts", [])) if n > 1]
        discretionary.extend(values)
        by_group[row["group_id"]].extend(values)
    def stats(values):
        return None if not values else dict(count=len(values), median_ms=float(np.median(values))/1e6,
            p95_ms=float(np.quantile(values, .95))/1e6, mean_ms=float(np.mean(values))/1e6)
    return dict(all_callbacks=stats(all_times), discretionary=stats(discretionary),
        group_median_ns={g: float(np.median(v)) for g, v in sorted(by_group.items()) if v},
        mean_episode_decision_cpu_ms=float(np.mean([sum(r.get("decision_cpu_nanoseconds", []))/1e6 for r in own])),
        total_episode_wall_seconds=sum(r["episode_wall_nanoseconds"] for r in own)/1e9,
        total_episode_cpu_seconds=sum(r["episode_cpu_nanoseconds"] for r in own)/1e9,
        fixed_planning=stats([r["planning_nanoseconds"] for r in own if "planning_nanoseconds" in r]))


def summarize(rows, timings, methods, champion=None):
    if len(set(methods)) != len(methods):
        raise ValueError("Repeated comparator")
    episodes = defaultdict(set)
    for r in rows:
        k = key(r)
        if r["method"] in episodes[k]:
            raise ValueError("Duplicate method episode")
        episodes[k].add(r["method"])
    if not episodes or any(v != set(methods) for v in episodes.values()):
        raise ValueError("Incomplete comparator coverage")
    if {(key(r), r["method"]) for r in rows} != {(key(r), r["method"]) for r in timings} or len(rows) != len(timings):
        raise ValueError("Timing/numerical coverage mismatch")
    stochastic = [r for r in rows if r["profile"] != "deterministic"]
    aggregates = {}
    for profile in ("stochastic_pooled", "low", "high", "deterministic"):
        subset = stochastic if profile == "stochastic_pooled" else [r for r in rows if r["profile"] == profile]
        times = [r for r in timings if r["profile"] != "deterministic"] if profile == "stochastic_pooled" else [r for r in timings if r["profile"] == profile]
        aggregates[profile] = {}
        for method in methods:
            own = [r for r in subset if r["method"] == method]
            agreements = [a for r in own for a in r["agreements"]]
            aggregates[profile][method] = dict(episodes=len(own), groups=len(group_mean(own)),
                **{f"mean_{metric}_hours": float(np.mean(list(group_mean(own, metric).values())))
                   if group_mean(own, metric) else None for metric in ("waiting", "critical", "p95", "branch")},
                agreement=dict(decisions=len(agreements), exact=sum(a["exact"] for a in agreements),
                    tie_aware=sum(a["tie_aware"] for a in agreements),
                    rate=sum(a["tie_aware"] for a in agreements)/len(agreements) if agreements else None),
                invalid_actions=sum(r["invalid_actions"] for r in own), fallbacks=sum(len(r["fallbacks"]) for r in own),
                timing=timing_summary(times, method))
    comparisons = {method: {ref: {metric: paired(stochastic, ref, method, metric)
        for metric in ("waiting", "critical", "p95", "branch")} for ref in (MEDIAN, REACTIVE)} for method in methods}
    result = dict(version=VERSION, aggregates=aggregates, comparisons=comparisons,
        estimand="Mean of configuration means; stochastic profiles and crew variants equally weighted within configuration",
        uncertainty="2000 paired configuration bootstrap resamples; seed 2026110404; fictional population only")
    if champion is not None:
        agg = aggregates["stochastic_pooled"]
        # reference=student, candidate=teacher produces the desired teacher/student speed ratio.
        speed = paired_arrays(agg[champion]["timing"]["group_median_ns"], agg[MEDIAN]["timing"]["group_median_ns"])
        quality, reactive = comparisons[champion][MEDIAN]["waiting"], comparisons[champion][REACTIVE]["waiting"]
        guards = {}
        for metric in ("critical", "p95"):
            guard = comparisons[champion][MEDIAN][metric]
            guards[metric] = (guard["groups"] >= 12 and guard["degradation"] <= max(.25, .05*guard["reference_mean"])
                             and guard["degradation_ci95"][1] <= max(.25, .05*guard["reference_mean"]))
        ratios = [quality["per_group_candidate"][g]/a for g, a in quality.get("per_group_reference", {}).items() if a > 0]
        all_own = [r for r in rows if r["method"] == champion]
        timing_counts = [agg[m]["timing"]["discretionary"]["count"] if agg[m]["timing"]["discretionary"] else 0
                         for m in (champion, MEDIAN)]
        # Catastrophe checks include deterministic episodes too; primary quality/speed use stochastic only.
        all_quality = paired(rows, MEDIAN, champion)
        gate = dict(speed=bool(speed["ratio"] is not None and speed["ratio"] >= 3 and speed["ratio_ci95"][0] >= 3),
            teacher_quality=bool(quality["ratio"] is not None and quality["ratio"] <= 1.02 and quality["ratio_ci95"][1] <= 1.02),
            reactive_noninferiority=bool(reactive["degradation"] is not None and reactive["degradation"] <= 0
                                        and reactive["degradation_ci95"][1] <= .01*reactive["reference_mean"]),
            **guards, validity=all(r["invalid_actions"] == 0 and not r["fallbacks"] for r in all_own),
            support=quality["groups"] >= 20 and speed["groups"] >= 12 and min(timing_counts) >= 200,
            catastrophe=bool(ratios and max(ratios) <= 1.25 and all_quality["max_episode_ratio"] <= 2))
        gate["pass"] = all(gate.values())
        result.update(champion=champion, promotion=gate, speed_comparison=speed,
                      maximum_group_wait_ratio=max(ratios) if ratios else None,
                      maximum_episode_wait_ratio=all_quality["max_episode_ratio"])
    return result


def select(summary):
    means = {n: summary["aggregates"]["stochastic_pooled"][n]["mean_waiting_hours"] for n in CANDIDATES}
    def best(names):
        minimum = min(means[n] for n in names)
        return min(n for n in names if means[n] <= minimum+1e-9)
    winners = {family: best([n for n, c in CANDIDATES.items() if c["family"] == family]) for family in ("ridge", "forest")}
    return dict(family_winners=winners, champion=best(list(CANDIDATES)), development_means=means,
                objective="stochastic full-rollout configuration mean customer wait; 1e-9 h tie by candidate ID")
