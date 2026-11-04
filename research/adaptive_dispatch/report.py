"""Scientific figures and complete comparisons from verified, already-spent evidence."""
from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from research.ml_lab.artifacts import file_hash, read_json, read_rows, write_json
from .experiment import (FIXED, MEDIAN, METHODS, REACTIVE, TEACHER, audit, paired,
                         runtime_summary, value)

LABELS = {"fifo-v1": "FIFO", "customer-count-v1": "Customer count",
    "legacy-release-per-person-hour-adapter-v1": "Release / effort",
    "legacy-critical-proxy-first-adapter-v1": "Critical first",
    "fifo": "FIFO", "customer": "Customer count", "release": "Release / effort",
    "critical": "Critical first", "downstream": "Downstream / time"}


def label(method):
    if method == MEDIAN:
        return "Median-support search"
    if method == TEACHER:
        return "Stochastic search (8 draws)"
    kind, rule = method.split(":", 1)
    prefix = {"fixed-floor": "Fixed floor", "fixed-order": "Fixed order", "reactive": "Reactive"}[kind]
    return f"{prefix}: {LABELS[rule]}"


def verified_timing(directory):
    runtime = read_json(directory / "runtime.json")
    timings = read_rows(directory / "timings.jsonl.gz")
    episodes = read_rows(directory / "episodes.jsonl.gz")
    def key(r):
        return r["case_id"], r["profile"], r["episode_seed"], r["method"]
    if len(timings) != len(episodes) or {key(r) for r in timings} != {key(r) for r in episodes}:
        raise ValueError("Timing coverage mismatch")
    for row in timings:
        if len(row.get("decision_nanoseconds", [])) != len(row.get("decision_choice_counts", [])):
            raise ValueError("Timing/action denominator mismatch")
        if any(type(t) is not int or t < 0 for t in row.get("decision_nanoseconds", [])):
            raise ValueError("Invalid callback timing")
    if runtime["methods"] != runtime_summary(timings):
        raise ValueError("Timing summary mismatch")
    for k in ("wall_seconds", "peak_rss_mib"):
        if not math.isfinite(runtime[k]) or runtime[k] <= 0:
            raise ValueError("Invalid resource measurement")
    return runtime


def render(dataset: Path, discovery: Path, confirmation: Path, output: Path):
    if output.exists():
        raise ValueError("Presentation destination already exists")
    manifest = read_json(dataset / "manifest.json")
    if manifest["profile"] != "full" or manifest["counts"] != {
            "cases": 72, "groups": 36, "partitions": {"discovery": 24, "confirmation": 48}}:
        raise ValueError("Scientific presentation requires the complete preregistered cohort")
    audit(dataset, discovery)
    audit(dataset, confirmation, discovery)
    discovered = read_json(discovery / "summary.json")
    summary = read_json(confirmation / "summary.json")
    runtime = verified_timing(confirmation)
    discovery_runtime = verified_timing(discovery)
    rows = read_rows(confirmation / "episodes.jsonl.gz")
    stochastic = [r for r in rows if r["profile"] != "deterministic"]
    selected = summary["selected"]
    aggregate = summary["aggregates"]["stochastic_pooled"]
    output.mkdir(parents=True)
    figures = output / "figures"
    figures.mkdir()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
        "figure.facecolor": "#f8fafc", "axes.facecolor": "#f8fafc", "svg.hashsalt": "adaptive-v1"})
    palette = {"fixed-floor": "#94a3b8", "fixed-order": "#64748b", "reactive": "#2563eb", "search": "#0f766e"}

    def save(fig, name):
        fig.savefig(figures / f"{name}.png", dpi=170, bbox_inches="tight", metadata={"Software": "GridGuide adaptive research"})
        fig.savefig(figures / f"{name}.svg", bbox_inches="tight", metadata={"Date": None, "Creator": "GridGuide adaptive research"})
        svg = figures / f"{name}.svg"
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
        plt.close(fig)

    order = sorted(METHODS, key=lambda m: aggregate[m]["mean_customer_wait_hours"], reverse=True)
    fig, ax = plt.subplots(figsize=(11, 8))
    values = [aggregate[m]["mean_customer_wait_hours"] for m in order]
    colors = ["#b45309" if m == TEACHER else palette[m.split(":")[0]] for m in order]
    bars = ax.barh([label(m) for m in order], values, color=colors, height=.72)
    ax.bar_label(bars, fmt="%.3f", padding=5, fontsize=9)
    ax.set_xlim(0, max(values)*1.13)
    ax.set_xlabel("Mean modeled customer wait (hours); lower is better")
    ax.set_title("Confirmation: all 15 non-clairvoyant comparators", loc="left", pad=25)
    ax.text(0, 1.015, "24 configuration groups · 1,536 stochastic episodes per method · fictional inputs",
            transform=ax.transAxes, color="#475569", fontsize=10)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    save(fig, "comparators")

    fig, ax = plt.subplots(figsize=(10, 6))
    dynamic = (*REACTIVE, MEDIAN, TEACHER)
    for i, method in enumerate(dynamic):
        timing = runtime["methods"][method]["discretionary_decisions"]
        x, y = timing["median_ms"], aggregate[method]["mean_customer_wait_hours"]
        ax.scatter(x, y, s=75, color="#b45309" if method == TEACHER else "#0f766e" if method == MEDIAN else "#2563eb")
        ax.annotate(label(method), (x, y), xytext=(7, -13 if method == TEACHER else 8), textcoords="offset points", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("Median discretionary callback time (milliseconds, log scale)")
    ax.set_ylabel("Mean modeled customer wait (hours)")
    ax.set_title("Decision quality versus measured computation", loc="left", pad=18)
    ax.grid(alpha=.18)
    ax.margins(x=.4, y=.2)
    save(fig, "quality-runtime")

    comp = summary["comparisons"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    groups = sorted(comp["adaptive_value"]["per_group_improvement"])
    for ax, name, title in zip(axes, ("adaptive_value", "teacher_headroom"),
            ("Reactive vs selected fixed order", "Stochastic vs selected cheap dynamic")):
        differences = [comp[name]["per_group_improvement"][g] for g in groups]
        ax.barh(range(len(groups)), differences, color=["#0f766e" if x >= 0 else "#b45309" for x in differences])
        ax.axvline(0, color="#334155", linewidth=.8)
        ax.set_title(title, fontsize=11, loc="left")
        ax.set_xlabel("Paired mean wait reduction (hours)\npositive favors candidate")
        ax.grid(axis="x", alpha=.15)
    axes[0].set_yticks(range(len(groups)), [g.replace("adaptive-full-confirmation-", "") for g in groups], fontsize=8)
    fig.suptitle("Configuration-level gains and failures remain visible", x=.05, ha="left", fontweight="bold")
    fig.tight_layout()
    save(fig, "paired-configurations")

    def interval(c):
        return f"[{c['improvement_ci95'][0]:.6f}, {c['improvement_ci95'][1]:.6f}]"
    gate = summary["gate"]
    outcome = "PASS — bounded learning pilot justified" if gate["pass"] else "NO-GO for this preregistered learning pilot"
    lines = ["# Adaptive dispatch opportunity report", "", f"**{outcome}.**", "",
        "All results are from fictional, complete-scope scheduling problems. No measured utility",
        "outcomes, calibrated repair-time distribution or operational dispatch claim is involved.", "",
        "![All confirmation comparators](figures/comparators.png)", "", "## Cohorts and decision boundary", "",
        "Discovery: 12 configurations × two crew variants × (one deterministic + 16 stochastic episodes)",
        "= 408 episodes per method / 6,120 method-episodes. Confirmation: 24 new configurations ×",
        "two crew variants × (one deterministic + 32 stochastic episodes) = 1,584 episodes per",
        "method / 23,760 method-episodes. Stochastic confirmation uses **1,536 paired episodes per",
        "method across 24 configuration groups**; deterministic results are separate.", "",
        "The selected fixed comparator and dynamic rules were frozen on discovery before confirmation:", "",
        f"- Fixed: `{selected['fixed']}`.", f"- Reactive: `{selected['reactive']}`.",
        f"- Cheap dynamic: `{selected['dynamic']}`.", "",
        "Waiting cost is completed modeled customer-hours divided by customer count in each case.",
        "Both crew variants, stochastic profiles and draws are averaged within each configuration;",
        "configuration means receive equal weight. Intervals use 2,000 configuration bootstrap",
        "resamples. Repeated episodes are not treated as independent structural samples.", "",
        "## Preregistered confirmation gate", "",
        "| Comparison / guardrail | Reference mean | Candidate mean | Paired reduction, hours | 95% interval | Supported episodes / groups | Pass |",
        "|---|---:|---:|---:|---|---:|---|"]
    for name, c in comp.items():
        lines.append(f"| {name} | {c['reference_mean']:.6f} | {c['candidate_mean']:.6f} | {c['improvement']:.6f} | {interval(c)} | {c['supported_episodes']} / {c['supported_groups']} | {gate[name]} |")
    lines += ["", "Adaptive value requires ≥2% cost reduction with an interval strictly above zero.",
        "Teacher headroom requires ≥1% reduction against the strongest discovery-selected cheap",
        "dynamic method with an interval strictly above zero. Critical and p95 guards limit mean",
        "regression to max(0.25 hour, 5% of the reference mean) on paired supported episodes.", "",
        f"Adaptive relative reduction: **{comp['adaptive_value']['relative_improvement']*100:.4f}%**. "
        f"Teacher relative reduction: **{comp['teacher_headroom']['relative_improvement']*100:.4f}%**.", "",
        "![Paired configuration effects](figures/paired-configurations.png)", "",
        "## Every comparator, with profiles separated", "",
        "| Method | Pooled stochastic mean wait, h | Low variability, h | High variability, h | Deterministic, h |",
        "|---|---:|---:|---:|---:|"]
    for m in METHODS:
        vals = [summary["aggregates"][p][m]["mean_customer_wait_hours"] for p in ("stochastic_pooled", "low", "high", "deterministic")]
        lines.append(f"| {label(m)} | " + " | ".join(f"{v:.6f}" for v in vals) + " |")
    lines += ["", "Fixed-order controls reclaim planned slack while retaining original crew assignments and",
        "task order. The planned-floor variants are reported but are not the sole adaptive comparator.",
        "Search is bounded root-action rollout, not an optimal dispatcher. No hindsight future is",
        "available to any policy; hypothetical draws use public state and a separate namespace.", "",
        "The downstream reactive rule is new, so its comparison with fixed G2 combines a different",
        "priority rule with completion-responsive decisions. This is not a causal decomposition",
        "of the value of uncertainty or adaptivity alone. Deterministic outcomes help expose this",
        "limitation; teacher headroom is assessed against the stronger online search comparator.", "",
        "## Runtime and resource measurements", "", "![Quality versus runtime](figures/quality-runtime.png)", "",
        "| Online method | All callbacks, median ms | Discretionary callbacks, median ms | Discretionary p95 ms | Discretionary count |",
        "|---|---:|---:|---:|---:|"]
    for m in dynamic:
        t = runtime["methods"][m]
        d = t["discretionary_decisions"]
        lines.append(f"| {label(m)} | {t['all_decisions']['median_ms']:.6f} | {d['median_ms']:.6f} | {d['p95_ms']:.6f} | {d['count']} |")
    ratio = runtime["methods"][TEACHER]["discretionary_decisions"]["median_ms"] / runtime["methods"][MEDIAN]["discretionary_decisions"]["median_ms"]
    lines += ["", f"Stochastic search's median discretionary callback costs **{ratio:.3f}×** median-support search on this run.",
        "Forced waits are separately retained; they can dominate an all-callback median. Fixed planning",
        "is a one-time measurement and is not comparable to a per-event callback; its complete timings",
        "remain in `runtime.json`. Verification time is excluded from policy callback time.", "",
        "Timing includes all 1,584 confirmation episodes per method (1,536 stochastic and 48",
        "deterministic); the quality axis and primary cost comparison use only the 1,536 stochastic",
        "episodes. Each runtime distribution reflects that method's own visited decision states.", "",
        f"Discovery command: {discovery_runtime['wall_seconds']:.3f}s; peak RSS {discovery_runtime['peak_rss_mib']:.3f} MiB. "
        f"Confirmation: {runtime['wall_seconds']:.3f}s; peak RSS {runtime['peak_rss_mib']:.3f} MiB.",
        f"Recorded environment: {runtime['environment']['system']} {runtime['environment']['machine']}, "
        f"Python {runtime['environment']['python']}. Timing is local measurement, not a portable latency promise.", "",
        "## Family-specific failures", "",
        "| Mechanism | Groups | Teacher reduction vs cheap dynamic, h | 95% interval | Wins / ties / losses |",
        "|---|---:|---:|---|---:|"]
    for mechanism in sorted({r["mechanism"] for r in rows}):
        c = paired([r for r in stochastic if r["mechanism"] == mechanism], selected["dynamic"], TEACHER)
        lines.append(f"| {mechanism} | {c['supported_groups']} | {c['improvement']:.6f} | {interval(c)} | {c['wins']} / {c['ties']} / {c['losses']} |")
    lines += ["", "Family intervals have only six configuration groups and are descriptive, not separate",
        "multiplicity-adjusted discoveries. They cannot establish broad generalization.", "",
        "## Largest teacher regressions", "",
        "| Configuration | Crews | Profile | Episode seed | Additional mean wait, h |",
        "|---|---:|---|---:|---:|"]
    def episode_key(r):
        return r["case_id"], r["profile"], r["episode_seed"]
    references = {episode_key(r): r for r in stochastic if r["method"] == selected["dynamic"]}
    failures = sorted(((value(r)-value(references[episode_key(r)]), r) for r in stochastic if r["method"] == TEACHER),
                      key=lambda pair: (-pair[0], episode_key(pair[1])))[:10]
    for difference, row in failures:
        lines.append(f"| {row['group_id'].replace('adaptive-full-confirmation-', '')} | {row['crew_count']} | {row['profile']} | {row['episode_seed']} | {difference:.6f} |")
    lines += ["", "Episode seeds and IDs are audit metadata, never policy inputs. All cases, not only the",
        "worst examples, remain in the compressed machine-readable episode evidence.", "",
        "## Scope and interpretation", "",
        "Independent duration supports are deliberately authored, with equal mean multiplier and",
        "different variability. They contain no shared weather factor, unknown damage, travel,",
        "switching or heterogeneous crew skill. Finite supports can make elapsed time unusually",
        "informative. Large or correlated-duration problems are untested generalization regimes.", "",
        "The teacher uses only eight hypothetical futures and four reactive continuations. This",
        "limits its opportunity to outperform a cheap deterministic support-median search; it",
        "does not prove that all possible adaptive algorithms or learned dispatchers lack value.",
        "These results distinguish useful adaptivity from demonstrated headroom for this teacher.", "",
        "Complete-scope primary cases do not evaluate learned treatment of unknown work. Separate",
        "fixtures verify blocked descendants and null complete outcomes without inventing durations.",
        "Tiny exact solutions verify specific expectations and deliberate waits, not global quality.", "",
        "The gate, cohort, policy budget and thresholds were not changed after scientific reveal.",
        "Procedural input/selection freezes are auditable but developer-controlled, not an external blind test.", "",
        "[Protocol](../PROTOCOL.md) · [Architecture](../ARCHITECTURE.md) · [Reproduce](../REPRODUCE.md) · [Literature](../FOUNDATIONS.md)", ""]
    (output / "REPORT.md").write_text("\n".join(lines))
    evidence = {str(p): file_hash(p) for directory in (dataset, discovery, confirmation)
                for p in sorted(directory.iterdir()) if p.is_file()}
    artifacts = {str(p.relative_to(output)): file_hash(p) for p in sorted(output.rglob("*")) if p.is_file()}
    write_json(output / "manifest.json", dict(version="adaptive-presentation-v1", source_evidence=evidence,
        artifacts=artifacts, scope="Verified opportunity evidence; no unmeasured model claims"))
    return dict(gate_passed=gate["pass"], figures=3, report=str(output/"REPORT.md"))
