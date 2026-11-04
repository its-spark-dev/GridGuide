"""Independent episode aggregation and historical selector audit (no fits)."""
from collections import Counter, defaultdict
import hashlib
from statistics import mean

from .evidence import ROOT, canonical
from .statistics import ceiling, comparison, distribution, grouped, planning_budget

FIXED = "fixed-order:legacy-release-per-person-hour-adapter-v1"
REACTIVE = "reactive:downstream"
MEDIAN = "search:support-median"
EIGHT = "search:stochastic-8"
STUDENTS = ("forest-depth4", "ridge-alpha10")
METRICS = ("waiting", "critical", "p95", "branch")


def metric(row, name):
    m = row["metrics"]
    if name == "waiting":
        return None if m["modeled_customer_outage_hours"] is None else m["modeled_customer_outage_hours"]/m["customers"]
    if name == "critical":
        values = list(m["critical_service_latency_hours"].values())
        return max(values) if values and None not in values else None
    return m[{"p95": "weighted_p95_hours", "branch": "branch_mean_disparity_hours"}[name]]


def identity(row):
    return row["case_id"], row["profile"], row["episode_seed"]


def state_signature(record):
    return hashlib.sha256(canonical({k: record[k] for k in ("now", "active", "completed")})).hexdigest()


def recomputed_metrics(problem, row):
    """Independent complete-scope cost/tail/critical calculation from retained schedules."""
    assignments = row["schedule"]["assignments"]
    ends = {a["task_id"]:a["end_tick"] for a in assignments}
    if len(ends) != len(assignments):
        raise ValueError("Duplicate task in schedule")
    groups = problem["groups"]
    if any(g.get("unresolved_dependency", False) or not set(g["required_tasks"]) <= ends.keys() for g in groups):
        raise ValueError("Primary adaptive metric requires complete group outcomes")
    released = [(g, max([0]+[ends[t] for t in g["required_tasks"]])) for g in groups]
    customers = sum(len(g["customer_ids"]) for g in groups)
    if customers != row["metrics"]["customers"]:
        raise ValueError("Customer denominator mismatch")
    cost = sum(len(g["customer_ids"])*tick for g, tick in released)/(3600*customers)
    cumulative, p95 = 0, None
    for g, tick in sorted(released, key=lambda x:x[1]):
        cumulative += len(g["customer_ids"])
        if cumulative*100 >= customers*95:
            p95 = tick/3600
            break
    critical = [tick/3600 for g,tick in released if g.get("critical_service",False)]
    branches = defaultdict(list)
    for g,tick in released:
        branches[g["branch"]].append((len(g["customer_ids"]),tick))
    branch_means = [sum(n*t for n,t in pairs)/(3600*sum(n for n,_ in pairs)) for pairs in branches.values()]
    values = dict(waiting=cost, critical=max(critical) if critical else None,
                  p95=p95, branch=max(branch_means)-min(branch_means))
    for name, actual in values.items():
        recorded = metric(row,name)
        if (actual is None) != (recorded is None) or (actual is not None and abs(actual-recorded)>1e-8):
            raise ValueError("Schedule-derived metric differs from recorded metric")
    return values


def cohort(sources, study, stage):
    base = f"docs/{study}/evidence/{stage}"
    numerical, timing = {}, {}
    if study == "learned-dispatch":
        dataset = sources.rows(f"docs/{study}/evidence/dataset/{stage}.jsonl.gz")
        nums = sorted((ROOT/base/"shards").glob("*.jsonl.gz"))
        nums = [p for p in nums if not p.name.endswith(".timings.jsonl.gz")]
        times = [p.with_name(p.name.replace(".jsonl.gz", ".timings.jsonl.gz")) for p in nums]
    else:
        dataset = sources.rows(f"docs/{study}/evidence/dataset/cases.jsonl.gz")
        nums, times = [ROOT/base/"episodes.jsonl.gz"], [ROOT/base/"timings.jsonl.gz"]
    problems_by_case = {r["problem"]["id"]:r["problem"] for r in dataset}
    for path in nums:
        for row in sources.rows(path.relative_to(ROOT)):
            k = (row["method"], identity(row))
            if k in numerical:
                raise ValueError("Duplicate episode")
            numerical[k] = dict(group=row["group_id"], family=row["mechanism"],
                values=recomputed_metrics(problems_by_case[row["case_id"]],row),
                durations=hashlib.sha256(canonical(row["durations"])).hexdigest(),
                agreement=row.get("agreements", []),
                trace=[state_signature(t) for t in row.get("trace", [])],
                invalid=row.get("invalid_actions"), fallback=len(row.get("fallbacks", [])))
    for path in times:
        for row in sources.rows(path.relative_to(ROOT)):
            k = (row["method"], identity(row))
            if k in timing:
                raise ValueError("Duplicate timing")
            if len(row.get("decision_nanoseconds", [])) != len(row.get("decision_choice_counts", [])):
                raise ValueError("Unmatched callback timing/choice counts")
            timing[k] = row
    if not numerical or numerical.keys() != timing.keys():
        raise ValueError("Numerical/timing coverage mismatch")
    methods = sorted({m for m, _ in numerical})
    keys = {k for m, k in numerical if m == REACTIVE}
    for method in methods:
        if {k for m, k in numerical if m == method} != keys:
            raise ValueError("Unpaired method coverage")
        for k in keys:
            a, b = numerical[REACTIVE, k], numerical[method, k]
            if (a["group"], a["durations"]) != (b["group"], b["durations"]):
                raise ValueError("Unpaired exogenous draws")
            if any((a["values"][m] is None) != (b["values"][m] is None) for m in METRICS):
                raise ValueError("Unpaired outcome support")
    selected_keys = sorted(k for k in keys if k[1] != "deterministic")
    aggregates, group_values = {}, {}
    for method in methods:
        own = [numerical[method, k] for k in selected_keys]
        group_values[method] = {m: grouped((r["group"], r["values"][m]) for r in own) for m in METRICS}
        timed = [timing[method, k] for k in selected_keys]
        all_ns, choice_ns, by_group = [], [], defaultdict(list)
        for r in timed:
            all_ns.extend(r.get("decision_nanoseconds", []))
            vals = [v for v, n in zip(r.get("decision_nanoseconds", []), r.get("decision_choice_counts", [])) if n > 1]
            choice_ns.extend(vals)
            by_group[r["group_id"]].extend(vals)
        agreements = [a for r in own for a in r["agreement"]]
        aggregate = dict(episodes=len(own), groups=len(group_values[method]["waiting"]),
            metrics={m: dict(groups=len(v), mean_hours=mean(v.values()) if v else None,
                            per_group=v) for m, v in group_values[method].items()},
            all_callback_ms=distribution(v/1e6 for v in all_ns),
            discretionary_callback_ms=distribution(v/1e6 for v in choice_ns),
            mean_group_median_callback_ms=mean(distribution(v)["p50"] for v in by_group.values() if v)/1e6 if choice_ns else None,
            group_median_callback_ns={g: distribution(v)["p50"] for g, v in sorted(by_group.items()) if v},
            mean_episode_callback_cpu_ms=mean(sum(r["decision_cpu_nanoseconds"])/1e6 for r in timed) if all("decision_cpu_nanoseconds" in r for r in timed) else None,
            planning_ms=distribution(r["planning_nanoseconds"]/1e6 for r in timed if "planning_nanoseconds" in r),
            agreement=dict(n=len(agreements), tie_aware=sum(a["tie_aware"] for a in agreements),
                           exact=sum(a["exact"] for a in agreements),
                           teacher_regret=distribution(a["teacher_regret"] for a in agreements)),
            invalid=sum(r["invalid"] for r in own) if all(r["invalid"] is not None for r in own) else None,
            fallbacks=sum(r["fallback"] for r in own))
        # Cost and complete callback timing frontier; fixed planning is not callback latency.
        aggregates[method] = aggregate
    frontier = [m for m, a in aggregates.items() if a["discretionary_callback_ms"]["p50"] is not None and not any(
        b["discretionary_callback_ms"]["p50"] is not None and
        b["metrics"]["waiting"]["mean_hours"] <= a["metrics"]["waiting"]["mean_hours"] and
        b["discretionary_callback_ms"]["p50"] <= a["discretionary_callback_ms"]["p50"] and
        (b["metrics"]["waiting"]["mean_hours"] < a["metrics"]["waiting"]["mean_hours"] or b["discretionary_callback_ms"]["p50"] < a["discretionary_callback_ms"]["p50"])
        for n, b in aggregates.items() if n != m)]
    comparisons = {m: {ref: {metric_: comparison(group_values[ref][metric_], group_values[m][metric_])
                    for metric_ in METRICS if group_values[ref][metric_]}
                    for ref in (REACTIVE, MEDIAN)} for m in methods}
    # Independent summary consistency, at the final step rather than taking stored aggregates as input.
    stored = sources.json(base+"/summary.json")
    stored_key = "mean_waiting_hours" if study == "learned-dispatch" else "mean_customer_wait_hours"
    historical = stored["aggregates"]["stochastic_pooled"]
    errors = {m: aggregates[m]["metrics"]["waiting"]["mean_hours"]-historical[m][stored_key] for m in methods}
    if max(abs(x) for x in errors.values()) > 1e-10:
        raise ValueError("Independent summary disagrees with history")
    if study == "learned-dispatch":
        for method in methods:
            for metric_ in ("critical", "p95", "branch"):
                actual = aggregates[method]["metrics"][metric_]["mean_hours"]
                if abs(actual-historical[method][f"mean_{metric_}_hours"]) > 1e-10:
                    raise ValueError("Critical/tail summary disagrees with history")
            recorded = historical[method]["timing"]["discretionary"]
            if recorded is not None and abs(aggregates[method]["discretionary_callback_ms"]["p50"]-recorded["median_ms"]) > 1e-10:
                raise ValueError("Complete callback summary disagrees with history")
    result = dict(aggregates=aggregates, comparisons=comparisons, frontier=frontier,
                  max_summary_wait_error=max(abs(x) for x in errors.values()),
                  power=planning_budget(group_values[REACTIVE]["waiting"], group_values[MEDIAN]["waiting"]))
    if all(m in methods for m in STUDENTS):
        result["restricted_ceiling"] = ceiling({m: group_values[m]["waiting"] for m in (REACTIVE, *STUDENTS)}, REACTIVE)
        result["trajectory_overlap"] = {}
        for method in STUDENTS:
            counts = Counter()
            on_regret, off_regret, group_error, worst = [], [], defaultdict(list), []
            for k in selected_keys:
                own, teacher = numerical[method, k], numerical[MEDIAN, k]
                choices = timing[MEDIAN, k]["decision_choice_counts"]
                if len(teacher["trace"]) != len(choices):
                    raise ValueError("Trace/timing mismatch")
                teacher_states = {s for s, n in zip(teacher["trace"], choices) if n > 1}
                for agreement in own["agreement"]:
                    shared = own["trace"][agreement["decision"]] in teacher_states
                    counts["shared" if shared else "student_only"] += 1
                    counts["agrees"] += agreement["tie_aware"]
                    (on_regret if shared else off_regret).append(agreement["teacher_regret"])
                    group_error[own["group"]].append(agreement["teacher_regret"])
                ratio = own["values"]["waiting"]/teacher["values"]["waiting"]
                worst.append(dict(case_id=k[0], profile=k[1], episode_seed=k[2], ratio=ratio))
            result["trajectory_overlap"][method] = dict(counts=dict(counts),
                shared_regret=distribution(on_regret), student_only_regret=distribution(off_regret),
                group_mean_teacher_regret={g: mean(v) for g, v in sorted(group_error.items())},
                worst_episode=max(worst, key=lambda r:r["ratio"]),
                caveat="Exact public-state overlap within paired episode; mismatch is associated, not a causal DAgger effect")
        result["speed_teacher_over_forest"] = comparison(
            aggregates[STUDENTS[0]]["group_median_callback_ns"], aggregates[MEDIAN]["group_median_callback_ns"])
    return result


def static_audit(sources):
    base = "docs/ml-lab/evidence"
    training = sources.json(base+"/training/training.json")
    final = list(sources.rows(base+"/final/cases.jsonl.gz"))
    result, ranges = {}, {}
    train = list(sources.rows(base+"/training/train-labels.jsonl.gz"))
    dev = list(sources.rows(base+"/training/dev-labels.jsonl.gz"))
    for r in train:
        for k, v in r["features"].items():
            if v is not None:
                ranges.setdefault(k, []).append(v)
    ranges = {k: (min(v), max(v)) for k, v in ranges.items()}
    fixed = training["baselines"]["fixed"]
    if not isinstance(fixed, str):
        raise ValueError("Unexpected fixed policy contract")
    for part, all_rows in [("train", train), ("dev", dev), *( (p, [r for r in final if r["partition"] == p]) for p in ("final_id", "final_shift"))]:
        rows = [r for r in all_rows if r["eligible"]]
        fixed_cost, oracle_cost, model_cost, fixed_regret, model_regret = [], [], [], [], []
        tie_n, fixed_optimal = 0, 0
        margins, family_labels, critical_differences = [], defaultdict(Counter), []
        feature_labels = defaultdict(set)
        for r in rows:
            costs = {m: v["cost_ticks"]/3600 for m, v in r["outcomes"].items()}
            best = min(costs.values())
            tie_n += len(r["ties"]) > 1
            fixed_optimal += fixed in r["ties"]
            ordered = sorted(costs.values())
            margins.append((ordered[1]-ordered[0])/ordered[0])
            family_labels[r["family"]][r["label"]] += 1
            feature_labels[canonical(r["features"])].add(r["label"])
            fixed_cost.append((r["group_id"], costs[fixed]))
            oracle_cost.append((r["group_id"], best))
            fixed_regret.append((r["group_id"], costs[fixed]-best))
            if "predictions" in r:
                cost = costs[r["predictions"]["champion"]]
                model_cost.append((r["group_id"], cost))
                model_regret.append((r["group_id"], cost-best))
                a = metric(r["outcomes"][fixed], "critical")
                b = metric(r["outcomes"][r["predictions"]["champion"]], "critical")
                if a is not None and b is not None:
                    critical_differences.append((r["group_id"], b-a))
        fc, oc = grouped(fixed_cost), grouped(oracle_cost)
        output = dict(cases=len(all_rows), eligible=len(rows), groups=len(fc), label_counts=dict(Counter(r["label"] for r in rows)),
            tied_cases=tie_n, fixed_policy=fixed, fixed_cost_customer_hours=mean(fc.values()),
            fixed_tie_optimal_cases=fixed_optimal, relative_best_second_margin=distribution(margins),
            family_label_counts={f:dict(v) for f,v in sorted(family_labels.items())},
            exact_feature_vectors=len(feature_labels), inconsistent_feature_labels=sum(len(v)>1 for v in feature_labels.values()),
            oracle_cost_customer_hours=mean(oc.values()), fixed_regret_customer_hours=mean(grouped(fixed_regret).values()),
            four_policy_ceiling_ratio_of_means=1-mean(oc.values())/mean(fc.values()),
            oracle_comparison=comparison(fc, oc),
            feature_outside_train_range={k: sum(r["features"][k] is not None and not lo <= r["features"][k] <= hi for r in rows) for k, (lo, hi) in ranges.items()})
        if model_cost:
            output.update(champion_regret_customer_hours=mean(grouped(model_regret).values()),
                          champion_vs_fixed=comparison(fc, grouped(model_cost)),
                          champion_critical_degradation_hours=mean(grouped(critical_differences).values()) if critical_differences else None,
                          supported_critical_cases=len(critical_differences))
        result[part] = output
    return result
