"""Prospectively staged opportunity experiment; no learned model or actual-future teacher."""
from collections import defaultdict
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
import resource
import sys
import time

import numpy as np

from benchmarks.contracts import Assignment, BenchmarkProblem
from benchmarks.policies import POLICIES
from research.ml_lab.artifacts import (digest, environment, file_hash, read_json, read_rows,
    require_committed, revision, write_json, write_rows)
from . import VERSION
from .dataset import episode_seed, load, source_hashes
from .environment import checked_result, run_episode, sample_durations
from .policies import HEURISTICS, fixed_episode, heuristic, lookahead

FIXED = tuple(f"fixed-{kind}:{p}" for kind in ("floor", "order") for p in POLICIES)
REACTIVE = tuple(f"reactive:{p}" for p in HEURISTICS)
MEDIAN = "search:support-median"
TEACHER = "search:stochastic-8"
METHODS = FIXED + REACTIVE + (MEDIAN, TEACHER)


def execute(p, profile, seed, name):
    if name in FIXED:
        kind, policy = name.split(":", 1)
        return fixed_episode(p, profile, seed, policy, planned_floors=kind == "fixed-floor")
    if name in REACTIVE:
        policy = partial(heuristic, name=name.split(":", 1)[1])
    elif name == MEDIAN:
        policy = partial(lookahead, median=True)
    elif name == TEACHER:
        policy = lookahead
    else:
        raise ValueError("Unknown experiment comparator")
    return run_episode(p, profile, seed, policy, name)


def value(row, metric="waiting"):
    m = row["metrics"]
    if metric == "waiting":
        return m["modeled_customer_outage_hours"] / m["customers"]
    if metric == "critical":
        values = list(m["critical_service_latency_hours"].values())
        return max(values) if values and None not in values else None
    if metric == "p95":
        return m["weighted_p95_hours"]
    raise ValueError("Unknown outcome metric")


def group_mean(rows, metric="waiting"):
    groups = defaultdict(list)
    for row in rows:
        v = value(row, metric)
        if v is not None:
            groups[row["group_id"]].append(v)
    return {g: sum(v)/len(v) for g, v in sorted(groups.items())}


def paired(rows, reference, candidate, metric="waiting"):
    def key(row):
        return row["case_id"], row["profile"], row["episode_seed"]
    refs = {key(r): r for r in rows if r["method"] == reference}
    candidates = {key(r): r for r in rows if r["method"] == candidate}
    if refs.keys() != candidates.keys() or not refs:
        raise ValueError("Paired comparator coverage mismatch")
    by_group, ref_values, cand_values, differences = defaultdict(list), defaultdict(list), defaultdict(list), []
    for k, ref in refs.items():
        cand = candidates[k]
        if ref["durations"] != cand["durations"] or ref["group_id"] != cand["group_id"]:
            raise ValueError("Exogenous draws/configuration mismatch")
        a, b = value(ref, metric), value(cand, metric)
        if a is not None and b is not None:
            g = ref["group_id"]
            by_group[g].append(a-b)
            ref_values[g].append(a)
            cand_values[g].append(b)
            differences.append(a-b)
    if not differences:
        return dict(supported_episodes=0, supported_groups=0, improvement=None, improvement_ci95=None)
    group_differences = np.array([sum(v)/len(v) for _, v in sorted(by_group.items())])
    rng = np.random.default_rng(20261104)
    means = np.mean(rng.choice(group_differences, size=(2000, len(group_differences)), replace=True), axis=1)
    a = sum(sum(v)/len(v) for v in ref_values.values()) / len(ref_values)
    b = sum(sum(v)/len(v) for v in cand_values.values()) / len(cand_values)
    return dict(supported_episodes=len(differences), supported_groups=len(by_group),
        reference_mean=a, candidate_mean=b, improvement=a-b,
        relative_improvement=None if a == 0 else (a-b)/a,
        improvement_ci95=[float(v) for v in np.quantile(means, [.025, .975])],
        wins=sum(v > 1e-12 for v in differences), ties=sum(abs(v) <= 1e-12 for v in differences),
        losses=sum(v < -1e-12 for v in differences),
        per_group_improvement={g: sum(v)/len(v) for g, v in sorted(by_group.items())})


def summarize(rows, selected=None):
    expected = set(METHODS)
    episodes = defaultdict(set)
    for row in rows:
        key = row["case_id"], row["profile"], row["episode_seed"]
        if row["method"] in episodes[key]:
            raise ValueError("Duplicate method/episode")
        episodes[key].add(row["method"])
    if not episodes or any(v != expected for v in episodes.values()):
        raise ValueError("Missing comparator results")
    stochastic = [r for r in rows if r["profile"] != "deterministic"]
    means = {m: sum(group_mean([r for r in stochastic if r["method"] == m]).values()) /
             len(group_mean([r for r in stochastic if r["method"] == m])) for m in METHODS}
    if selected is None:
        selected = {"fixed": min(FIXED, key=lambda m: (means[m], m)),
                    "reactive": min(REACTIVE, key=lambda m: (means[m], m)),
                    "dynamic": min((*REACTIVE, MEDIAN), key=lambda m: (means[m], m))}
    if (selected["fixed"] not in FIXED or selected["reactive"] not in REACTIVE
            or selected["dynamic"] not in (*REACTIVE, MEDIAN)):
        raise ValueError("Invalid discovery selection")
    comparisons = {"adaptive_value": paired(stochastic, selected["fixed"], selected["reactive"]),
        "teacher_headroom": paired(stochastic, selected["dynamic"], TEACHER),
        "teacher_critical": paired(stochastic, selected["dynamic"], TEACHER, "critical"),
        "teacher_p95": paired(stochastic, selected["dynamic"], TEACHER, "p95")}
    gate = {}
    for name, threshold in (("adaptive_value", .02), ("teacher_headroom", .01)):
        c = comparisons[name]
        gate[name] = c["relative_improvement"] is not None and c["relative_improvement"] >= threshold and c["improvement_ci95"][0] > 0
    for name in ("teacher_critical", "teacher_p95"):
        c = comparisons[name]
        gate[name] = bool(c["supported_episodes"]) and -c["improvement"] <= max(.25, .05*c["reference_mean"])
    gate["pass"] = all(gate.values())
    aggregates = {}
    for profile in ("stochastic_pooled", "low", "high", "deterministic"):
        subset = stochastic if profile == "stochastic_pooled" else [r for r in rows if r["profile"] == profile]
        aggregates[profile] = {}
        for method in METHODS:
            own = [r for r in subset if r["method"] == method]
            aggregates[profile][method] = dict(episodes=len(own), groups=len(group_mean(own)),
                mean_customer_wait_hours=float(np.mean(list(group_mean(own).values()))),
                versus_selected_dynamic=paired(subset, selected["dynamic"], method))
    return dict(version=VERSION, selected=selected, gate=gate, comparisons=comparisons, aggregates=aggregates,
        denominator="Whole configurations equally weighted; average both crews and paired stochastic episodes within configuration",
        uncertainty="2000 bootstrap resamples of configuration means; authored scenario population only")


def runtime_summary(timing_rows):
    result = {}
    for method in METHODS:
        own = [r for r in timing_rows if r["method"] == method]
        all_times = [v for r in own for v in r.get("decision_nanoseconds", [])]
        choice_times = [v for r in own for v, n in zip(r.get("decision_nanoseconds", []), r.get("decision_choice_counts", [])) if n > 1]
        def stats(values):
            return None if not values else dict(count=len(values), median_ms=float(np.median(values))/1e6,
                p95_ms=float(np.quantile(values, .95))/1e6, mean_ms=float(np.mean(values))/1e6)
        result[method] = dict(all_decisions=stats(all_times), discretionary_decisions=stats(choice_times),
            initial_fixed_planning=stats([r["planning_nanoseconds"] for r in own if "planning_nanoseconds" in r]))
    return result


def audit(dataset: Path, results: Path, discovery: Path | None = None, replay=False):
    """Read-only verification of spent evidence, never selection on a fresh cohort."""
    manifest, cases = load(dataset)
    receipt = read_json(results / "receipt.json")
    completion = read_json(results / "completion.json")
    if receipt["source_hashes"] != source_hashes() or receipt["input_identity"] != manifest["input_identity"]:
        raise ValueError("Experiment source/input binding mismatch")
    for name in ("receipt", "summary", "episodes"):
        filename = f"{name}.jsonl.gz" if name == "episodes" else f"{name}.json"
        if completion[f"{name}_sha256"] != file_hash(results / filename):
            raise ValueError("Completed evidence file mismatch")
    rows = read_rows(results / "episodes.jsonl.gz")
    if completion["rows"] != len(rows) or completion["numerical_identity"] != digest(rows):
        raise ValueError("Numerical evidence mismatch")
    partition = receipt["partition"]
    own = {r["problem"]["id"]: r for r in cases if r["partition"] == partition}
    n = (8 if partition == "discovery" else 16) if manifest["profile"] == "full" else 1
    expected = {(c, profile, episode_seed(manifest["profile"], partition, i), method)
        for c in own for profile in ("deterministic", "low", "high")
        for i in range(1 if profile == "deterministic" else n) for method in METHODS}
    actual = {(r["case_id"], r["profile"], r["episode_seed"], r["method"]) for r in rows}
    if actual != expected or len(actual) != len(rows):
        raise ValueError("Full cohort/method/episode coverage mismatch")
    problems = {c: BenchmarkProblem.model_validate(row["problem"]) for c, row in own.items()}
    for row in rows:
        p = problems[row["case_id"]]
        if row["group_id"] != own[p.id]["group_id"] or row["mechanism"] != p.family or row["crew_count"] != len(p.crews):
            raise ValueError("Outcome grouping mismatch")
        if row["durations"] != sample_durations(p, row["profile"], row["episode_seed"]):
            raise ValueError("Exogenous duration mismatch")
        verified = checked_result(p, row["durations"], tuple(Assignment.model_validate(a) for a in row["schedule"]["assignments"]), row["schedule"]["policy"])
        if any(row[k] != v for k, v in verified.items()):
            raise ValueError("Independent schedule/metric verification mismatch")
        if replay:
            rerun = execute(p, row["profile"], row["episode_seed"], row["method"])
            for k in ("original_problem_fingerprint", "conditional_problem_fingerprint", "durations", "schedule", "metrics"):
                if row[k] != rerun[k]:
                    raise ValueError("Policy replay mismatch: " + k)
    selected = None
    if partition == "confirmation":
        if discovery is None or file_hash(discovery / "completion.json") != receipt["discovery_identity"]:
            raise ValueError("Missing or changed discovery freeze")
        if file_hash(discovery / "summary.json") != read_json(discovery / "completion.json")["summary_sha256"]:
            raise ValueError("Changed discovery summary")
        selected = read_json(discovery / "summary.json")["selected"]
    summary = summarize(rows, selected)
    summary["stage"] = partition
    summary["gate_authority"] = "confirmation only" if partition == "discovery" else "preregistered confirmation"
    if summary != read_json(results / "summary.json"):
        raise ValueError("Grouped summary replay mismatch")
    return dict(status="PASS", method_episodes=len(rows), numerical_identity=digest(rows),
                independent_schedule_metric_validation=True, policy_replayed=replay)


def run(dataset: Path, output: Path, partition: str, discovery: Path | None = None):
    if partition not in ("discovery", "confirmation") or output.exists():
        raise ValueError("Invalid stage or already-used experiment destination")
    manifest, cases = load(dataset)
    full = manifest["profile"] == "full"
    if manifest["source_hashes"] != source_hashes():
        raise ValueError("Implementation changed since input seal")
    if full:
        load(dataset, committed=True)
    selected = None
    discovery_identity = None
    if partition == "confirmation":
        if discovery is None:
            raise ValueError("Confirmation requires completed discovery selection")
        prior = read_json(discovery / "completion.json")
        prior_receipt = read_json(discovery / "receipt.json")
        if prior_receipt["partition"] != "discovery" or prior_receipt["input_identity"] != manifest["input_identity"]:
            raise ValueError("Discovery receipt/input mismatch")
        if prior["summary_sha256"] != file_hash(discovery / "summary.json") or prior_receipt["source_hashes"] != source_hashes():
            raise ValueError("Discovery identity/implementation mismatch")
        if full:
            require_committed([discovery / name for name in ("summary.json", "receipt.json", "completion.json")])
        selected = read_json(discovery / "summary.json")["selected"]
        discovery_identity = file_hash(discovery / "completion.json")
    write_json(output / "receipt.json", dict(version=VERSION, partition=partition,
        started_at=datetime.now(timezone.utc).isoformat(), revision=revision(), source_hashes=source_hashes(),
        input_identity=manifest["input_identity"], discovery_identity=discovery_identity,
        environment=environment(), methods=METHODS))
    begun = time.perf_counter()
    rows, timing_rows = [], []
    episodes = (8 if partition == "discovery" else 16) if full else 1
    try:
        own_cases = [r for r in cases if r["partition"] == partition]
        for case_index, case in enumerate(own_cases):
            p = BenchmarkProblem.model_validate(case["problem"])
            for profile in ("deterministic", "low", "high"):
                for index in range(1 if profile == "deterministic" else episodes):
                    seed = episode_seed(manifest["profile"], partition, index)
                    common_draws = None
                    for method in METHODS:
                        result = execute(p, profile, seed, method)
                        if common_draws is not None and result["durations"] != common_draws:
                            raise ValueError("Policy-dependent random stream")
                        common_draws = result["durations"]
                        common = dict(case_id=p.id, group_id=case["group_id"], mechanism=p.family,
                            crew_count=len(p.crews), profile=profile, episode_seed=seed, method=method)
                        timing_rows.append({**common, **{k: result.pop(k) for k in
                            ("decision_nanoseconds", "decision_choice_counts", "planning_nanoseconds") if k in result}})
                        result.pop("trace", None)
                        rows.append({**common, **result})
            elapsed = time.perf_counter()-begun
            print(f"{partition}: {case_index+1}/{len(own_cases)} input variants validated; {elapsed:.1f}s", flush=True)
            if elapsed > 1800:
                raise RuntimeError("Prospective 30-minute command resource cap exceeded")
        summary = summarize(rows, selected)
        summary["stage"] = partition
        summary["gate_authority"] = "confirmation only" if partition == "discovery" else "preregistered confirmation"
        write_rows(output / "episodes.jsonl.gz", rows)
        write_json(output / "summary.json", summary)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**2 if sys.platform == "darwin" else 1024)
        write_rows(output / "timings.jsonl.gz", timing_rows)
        write_json(output / "runtime.json", dict(wall_seconds=time.perf_counter()-begun, peak_rss_mib=peak,
            environment=environment(), methods=runtime_summary(timing_rows),
            note="Fixed planning is one-time; online figures time callbacks, separately retaining forced event waits"))
        if peak > 2048:
            raise RuntimeError("Prospective 2-GiB memory resource cap exceeded")
        write_json(output / "completion.json", dict(version=VERSION, rows=len(rows),
            numerical_identity=digest(rows), receipt_sha256=file_hash(output / "receipt.json"),
            summary_sha256=file_hash(output / "summary.json"), episodes_sha256=file_hash(output / "episodes.jsonl.gz")))
        return summary
    except Exception as error:
        write_json(output / "failure.json", dict(type=type(error).__name__, reason=str(error),
            elapsed_seconds=time.perf_counter()-begun, completed_method_episodes=len(rows)))
        raise
