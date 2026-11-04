"""Read-only, evidence-bound portfolio figures; never fits or selects a model."""
from pathlib import Path
import numpy as np

from research.ml_lab.artifacts import digest, file_hash, read_json, read_rows, write_json
from .analysis import value
from .experiment import audit
from .rollout import FIXED, REACTIVE, MEDIAN, EIGHT
from .training import approved_models

LABELS = {FIXED: "Fixed order", REACTIVE: "Reactive downstream", MEDIAN: "Median teacher",
          EIGHT: "Eight-future search"}
COLORS = {FIXED: "#8a95a3", REACTIVE: "#db851c", MEDIAN: "#087e8b", EIGHT: "#335c67"}


def render(evidence: Path, output: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if output.exists():
        raise ValueError("Presentation destination already exists")
    inputs = read_json(evidence/"dataset/manifest.json")
    if inputs["profile"] != "full" or inputs["counts"]["partitions"] != dict(train=96, dev=32, final_id=48, final_shift=48):
        raise ValueError("This portfolio report requires the registered full scientific cohort; smoke is not scientific evidence")
    frozen = read_json(evidence/"freeze.json")
    training = read_json(evidence/"training/training.json")
    approved_models(evidence/"training")
    teacher_states = []
    for name, expected in training["binding"]["teacher_shards"].items():
        path = evidence/"teacher"/name
        if file_hash(path) != expected:
            raise ValueError("Teacher presentation source changed")
        shard, = read_rows(path)
        teacher_states.extend(shard["states"])
    discretionary = [s for s in teacher_states if s["label"]["discretionary"]]
    label_diagnostics = dict(
        discretionary_wait_states=sum(s["label"]["teacher"]["task_id"] is None for s in discretionary),
        discretionary_states=len(discretionary),
        multiple_best_task_states=sum(len({a["task_id"] for a in s["label"]["ties"]}) > 1 for s in discretionary),
        zero_regret_rows=sum(v == 0 for s in discretionary for v in s["label"]["targets"]),
        action_rows=sum(len(s["label"]["actions"]) for s in discretionary),
        legal_action_count_quantiles=np.quantile([len(s["label"]["actions"]) for s in discretionary], [0, .5, .95, 1]).tolist())
    for part in ("dev", "final_id", "final_shift"):
        audit(evidence/"dataset", evidence/"training", evidence/part)
    results = {p: read_json(evidence/p/"summary.json") for p in ("final_id", "final_shift")}
    champion = frozen["selection"]["champion"]
    winners = frozen["selection"]["family_winners"]
    labels = {**LABELS, winners["ridge"]: "Learned Ridge", winners["forest"]: "Learned forest"}
    colors = {**COLORS, winners["ridge"]: "#4766cc", winners["forest"]: "#8750b4"}
    methods = list(BASE for BASE in frozen["methods"])
    output.mkdir(parents=True)
    figures = output/"figures"
    figures.mkdir()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.titlesize": 14,
        "axes.labelsize": 11, "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.edgecolor": "#d7dfe8", "text.color": "#18283b",
        "axes.labelcolor": "#18283b", "xtick.color": "#516175", "ytick.color": "#516175",
        "figure.facecolor": "#f7f9fc", "axes.facecolor": "#f7f9fc", "savefig.facecolor": "#f7f9fc",
        "svg.hashsalt": "gridguide-learned-dispatch-v1"})
    def save(fig, name):
        fig.savefig(figures/f"{name}.png", dpi=170, bbox_inches="tight", metadata={"Software": "GridGuide evidence renderer"})
        fig.savefig(figures/f"{name}.svg", bbox_inches="tight", metadata={"Date": None, "Creator": "GridGuide evidence renderer"})
        svg = figures/f"{name}.svg"
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
        plt.close(fig)
    def title(fig, headline, subtitle):
        fig.suptitle(headline, x=.06, ha="left", fontsize=20, fontweight="bold", y=.99)
        fig.text(.06, .925, subtitle, fontsize=11, color="#516175")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.7))
    title(fig, "Trained dispatch, tested in complete episodes", "24 independent configurations per cohort · 384 stochastic episodes per method · fictional duration supports")
    for ax, (part, heading) in zip(axes, (("final_id", "Fresh in-distribution"), ("final_shift", "Topology + scale + crew shift"))):
        result = results[part]
        estimates = [result["comparisons"][m][MEDIAN]["waiting"] for m in methods]
        means = [100*(x["ratio"]-1) for x in estimates]
        lo = [100*(x["ratio"]-x["ratio_ci95"][0]) for x in estimates]
        hi = [100*(x["ratio_ci95"][1]-x["ratio"]) for x in estimates]
        y = np.arange(len(methods))
        ax.barh(y, means, color=[colors[m] for m in methods], alpha=.9, height=.57)
        ax.errorbar(means, y, xerr=[lo, hi], fmt="none", color="#18283b", capsize=3, linewidth=1.2)
        ax.set_yticks(y, [labels[m]+(" *" if m == champion else "") for m in methods])
        ax.invert_yaxis()
        ax.axvline(0, color="#607184", linewidth=1)
        ax.axvline(2, color="#b25e58", linestyle=":", linewidth=1)
        ax.set_xlabel("Mean waiting relative to teacher (%)\nLower is better; paired 95% configuration intervals")
        ax.set_title(heading, loc="left", pad=12)
        ax.grid(axis="x", alpha=.12)
        ax.set_axisbelow(True)
    fig.text(.06, .02, "* Development-selected champion. Dotted line: +2% quality threshold. Promotion also requires speed, reactive and tail/critical guards.", fontsize=9, color="#516175")
    fig.subplots_adjust(top=.81, bottom=.22, left=.19, right=.98, wspace=.65)
    save(fig, "quality")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.7))
    title(fig, "What computation buys in this simulator", "Complete callback timing includes validation, legal-action enumeration, feature extraction and prediction")
    for ax, (part, heading) in zip(axes, (("final_id", "Fresh in-distribution"), ("final_shift", "Shifted configurations"))):
        agg = results[part]["aggregates"]["stochastic_pooled"]
        teacher_wait = agg[MEDIAN]["mean_waiting_hours"]
        for method in methods:
            if method == FIXED:
                continue
            x = agg[method]["timing"]["discretionary"]["median_ms"]
            y = 100*(agg[method]["mean_waiting_hours"]/teacher_wait-1)
            ax.scatter(x, y, s=135 if method == champion else 80, color=colors[method], edgecolors="white", linewidth=1.3, zorder=4,
                       label=labels[method]+(" *" if method == champion else ""))
        ax.set_xscale("log")
        ax.axhline(0, color="#087e8b", linewidth=1)
        ax.axhline(2, color="#b25e58", linestyle=":", linewidth=1)
        ax.set_xlabel("Pooled median discretionary callback (ms, log scale)")
        ax.set_ylabel("Mean waiting relative to teacher (%)")
        ax.set_title(heading, loc="left", pad=12)
        ax.grid(alpha=.15)
    handles, names = axes[0].get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(.53, .025))
    fig.subplots_adjust(top=.80, bottom=.26, left=.08, right=.98, wspace=.30)
    save(fig, "quality-latency")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.8))
    title(fig, "Learned parameters you can inspect", "Actual fitted family winners · coefficient sign predicts teacher-regret cost · importance is not causal")
    for ax, family in zip(axes, ("ridge", "forest")):
        name = winners[family]
        payload = read_json(evidence/"training"/training["models"][name]["file"])
        importance = payload["importance"]
        top = sorted(importance, key=lambda k: abs(importance[k]), reverse=True)[:10][::-1]
        vals = [importance[k] for k in top]
        ax.barh(range(len(top)), vals, color=colors[name], height=.65)
        ax.set_yticks(range(len(top)), [k.replace("_", " ") for k in top], fontsize=9)
        ax.axvline(0, color="#607184", linewidth=1)
        ax.set_title(name, loc="left")
        ax.set_xlabel("Standardized Ridge coefficient" if family == "ridge" else "Forest impurity importance")
        ax.grid(axis="x", alpha=.15)
        ax.set_axisbelow(True)
    fig.subplots_adjust(top=.82, bottom=.12, left=.22, right=.97, wspace=1.15)
    save(fig, "learned-parameters")

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.7))
    title(fig, "Generalization includes failures", f"Frozen champion: {champion} · each point is one independent configuration's paired stochastic mean")
    worst = {}
    for ax, (part, heading) in zip(axes, (("final_id", "Fresh in-distribution"), ("final_shift", "Shifted configurations"))):
        compare = results[part]["comparisons"][champion][MEDIAN]["waiting"]
        ratios = sorted((100*(compare["per_group_candidate"][g]/v-1), g) for g, v in compare["per_group_reference"].items())
        ax.bar(range(len(ratios)), [v for v, _ in ratios], color=[colors[champion] if v <= 2 else "#b25e58" for v, _ in ratios])
        ax.axhline(0, color="#607184", linewidth=1)
        ax.axhline(2, color="#b25e58", linestyle=":", linewidth=1)
        ax.set_title(heading, loc="left")
        ax.set_xlabel("Configurations sorted by paired waiting difference")
        ax.set_ylabel("Mean waiting relative to teacher (%)")
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
        rows = [r for p in sorted((evidence/part/"shards").glob("*.jsonl.gz")) if not p.name.endswith(".timings.jsonl.gz") for r in read_rows(p)]
        refs = {(r["case_id"], r["profile"], r["episode_seed"]): r for r in rows if r["method"] == MEDIAN}
        candidates = [r for r in rows if r["method"] == champion]
        failure = max(candidates, key=lambda r: value(r)/value(refs[(r["case_id"], r["profile"], r["episode_seed"])]))
        ref = refs[(failure["case_id"], failure["profile"], failure["episode_seed"])]
        worst[part] = dict(case_id=failure["case_id"], mechanism=failure["mechanism"], profile=failure["profile"],
            episode_seed=failure["episode_seed"], ratio=value(failure)/value(ref), student_wait=value(failure), teacher_wait=value(ref),
            disagreements=[a for a in failure["agreements"] if not a["tie_aware"]],
            student_schedule=failure["schedule"], teacher_schedule=ref["schedule"])
    fig.text(.08, .025, "The 2% line is the aggregate quality reference. The separate configuration catastrophe screen is +25%.", fontsize=9, color="#516175")
    fig.subplots_adjust(top=.80, bottom=.19, left=.08, right=.98, wspace=.30)
    save(fig, "configuration-errors")
    write_json(output/"failure-cases.json", worst)
    write_json(output/"label-diagnostics.json", label_diagnostics)

    diag = training["diagnostics"]
    totals = {k: sum(d[k] for d in diag.values()) for k in ("episodes", "visits", "unique_states", "discretionary_states", "action_rows", "teacher_wait_visits")}
    runtime = read_json(evidence/"training/runtime.json")
    lines = ["# Learned Adaptive Dispatch v1 — measured research report", "",
        f"**Real trained models; promotion: {'PASS' if all(r['promotion']['pass'] for r in results.values()) else 'FAIL — do not promote'}.**",
        f"The development-selected champion is **{champion}**. Both learned families and all five fitted artifacts remain available.", "",
        "This prospective study distills conditional-support-median search into a GridGuide state/action cost ranker. "
        "It does not reopen PR #20's failed eight-future headroom test or repeat ML Lab I/II. All outcomes are fictional simulator results.", "",
        "## Actual training", "",
        f"48 training configurations, 96 crew variants, {totals['episodes']:,} independently validated trajectories, "
        f"{totals['visits']:,} visits, {totals['unique_states']:,} unique public states and {totals['discretionary_states']:,} discretionary states "
        f"produce **{totals['action_rows']:,} action rows × 46 features**. {totals['visits']-totals['unique_states']:,} duplicate visits are retained as lineage but not extra fit weight.", "",
        f"Among unique discretionary states, WAIT is the teacher choice in {label_diagnostics['discretionary_wait_states']:,}/{len(discretionary):,}; "
        f"{label_diagnostics['multiple_best_task_states']:,} states tie across multiple distinct tasks/WAIT. "
        f"{label_diagnostics['zero_regret_rows']:,}/{label_diagnostics['action_rows']:,} action rows have zero teacher regret. "
        "Forced decisions are retained separately and do not inflate the fit or agreement denominators. "
        "[Label diagnostics](label-diagnostics.json) retain legal-action count quantiles.", "",
        "Three weighted, standardized Ridge regressors (alpha 0.1, 1, 10) and two 64-tree forests (depth 4, 8) "
        "minimize dimensionless excess median-teacher rollout cost. Each configuration, then unique state, then legal action "
        "receives equal weight within its parent. The fitted scaler sees training only. No IDs, private durations, final outcomes or teacher costs enter features.", "",
        f"Every fit repeated with exact export equality. Portable predictions matched the fitted estimators on training and "
        f"{training['dev_export_probe_rows']:,} development parity-probe rows within 1e-10. Total fitting pipeline: {runtime['elapsed_seconds']:.3f} s; peak RSS {runtime['peak_rss_mib']:.1f} MiB.", "",
        "| Candidate | Weighted training MSE | Development mean wait (h) | First fit (s) | Load (ms) | Bytes |", "|---|---:|---:|---:|---:|---:|"]
    for name, model in training["models"].items():
        rt = runtime["candidates"][name]
        lines.append(f"| {name} | {training['scores'][name]['weighted_train_mse']:.8f} | {frozen['selection']['development_means'][name]:.6f} | {rt['fit_seconds']:.4f} | {rt['load_nanoseconds']/1e6:.4f} | {model['bytes']:,} |")
    lines += ["", "Selection uses stochastic complete student rollouts on 16 development configurations, 32 variants and "
        "160 episodes per method (128 stochastic). Training MSE and agreement are diagnostics, not selection criteria.", "",
        "![Actual learned coefficients and importance](figures/learned-parameters.png)", "",
        "Shared state features are constant across an observation's candidate actions. In additive Ridge they shift all "
        "predicted costs equally and cannot themselves change the within-state ranking; state/action interactions can. "
        "In a forest, shared features can select different branches and thereby change action comparisons. "
        "The figure describes the fitted cost regressor, not causal importance or a pure ranking-effect measure.", "",
        "## One-time held-out results", "",
        "Each cohort has 24 independent configurations and 48 crew variants: 432 episodes per method, including "
        "384 stochastic and 48 deterministic episodes. Six methods yield 2,592 method-episodes per cohort. All metrics and "
        "trajectories are independently checked. The tables below use stochastic episodes only; configuration means receive equal weight. "
        "Intervals use 2,000 paired configuration bootstrap resamples. Shift jointly changes topology, scale and crew count.", "",
        "![Quality relative to median teacher](figures/quality.png)", ""]
    for part, result in results.items():
        command_runs = [read_json(p) for p in sorted((evidence/part).glob("command-runtime-*.json"))]
        lines += [f"### {part}", "", "| Policy | Mean wait (h) | p95 wait (h) | Critical maximum (h) | Branch disparity (h) | Callback median / p95 (ms) |", "|---|---:|---:|---:|---:|---:|"]
        agg = result["aggregates"]["stochastic_pooled"]
        for method in methods:
            r = agg[method]
            timing = r["timing"]["discretionary"]
            display = f"{timing['median_ms']:.4f} / {timing['p95_ms']:.4f}" if timing else "one-time fixed plan"
            lines.append(f"| {labels[method]}{' *' if method == champion else ''} | {r['mean_waiting_hours']:.6f} | {r['mean_p95_hours']:.6f} | {r['mean_critical_hours']:.6f} | {r['mean_branch_hours']:.6f} | {display} |")
        q, react = result["comparisons"][champion][MEDIAN]["waiting"], result["comparisons"][champion][REACTIVE]["waiting"]
        speed = result["speed_comparison"]
        own = agg[champion]
        lines += ["", f"Champion/teacher mean wait ratio: **{q['ratio']:.6f}**, 95% CI [{q['ratio_ci95'][0]:.6f}, {q['ratio_ci95'][1]:.6f}]. "
            f"Champion minus reactive mean wait: **{react['degradation']:.6f} h**, CI [{react['degradation_ci95'][0]:.6f}, {react['degradation_ci95'][1]:.6f}].", "",
            f"Teacher/student ratio of mean configuration-median callback times: **{speed['ratio']:.3f}×**, CI [{speed['ratio_ci95'][0]:.3f}, {speed['ratio_ci95'][1]:.3f}]. "
            f"This differs from the pooled medians plotted below. Student full-episode decision CPU averages "
            f"{own['timing']['mean_episode_decision_cpu_ms']:.3f} ms; teacher {agg[MEDIAN]['timing']['mean_episode_decision_cpu_ms']:.3f} ms.", "",
            f"On visited discretionary states, tie-aware teacher agreement is {own['agreement']['tie_aware']:,}/{own['agreement']['decisions']:,} "
            f"({100*own['agreement']['rate']:.2f}%). Invalid actions: {own['invalid_actions']}; fallbacks: {own['fallbacks']}. "
            f"Worst configuration mean ratio: {result['maximum_group_wait_ratio']:.4f}; worst episode ratio, including deterministic: {result['maximum_episode_wait_ratio']:.4f}.", "",
            "| Preregistered guard | Pass? |", "|---|---|"]
        lines += [f"| {k.replace('_', ' ')} | {'PASS' if v else 'FAIL'} |" for k, v in result["promotion"].items()]
        lines += ["", "Critical/tail guard details (champion minus teacher; hours):", "",
                  "| Outcome | Mean degradation | 95% interval | Allowed upper degradation |", "|---|---:|---:|---:|"]
        for metric in ("critical", "p95"):
            guard = result["comparisons"][champion][MEDIAN][metric]
            lines.append(f"| {metric} | {guard['degradation']:.6f} | [{guard['degradation_ci95'][0]:.6f}, {guard['degradation_ci95'][1]:.6f}] | {max(.25,.05*guard['reference_mean']):.6f} |")
        if command_runs:
            lines += ["", f"Total measured evaluation batches: {sum(r['wall_seconds'] for r in command_runs):.3f} s wall, "
                f"{sum(r['cpu_seconds'] for r in command_runs):.3f} s process CPU, across {len(command_runs)} bounded invocations. "
                "This includes loading, simulation, agreement queries, validation, artifact writing and final aggregation."]
        failure = worst[part]
        lines += ["", f"Worst episode: `{failure['case_id']}`, {failure['mechanism']}, {failure['profile']}, "
            f"student {failure['student_wait']:.6f} h versus teacher {failure['teacher_wait']:.6f} h. "
            f"Its {len(failure['disagreements'])} non-tied action disagreements and both complete schedules are in [failure-cases.json](failure-cases.json).", ""]
    lines += ["![Quality and callback computation](figures/quality-latency.png)", "", "![All configuration errors](figures/configuration-errors.png)", "",
        "## Interpretation and limits", "",
        "Engineering completion and scientific promotion are separate. The JSON files contain actual learned parameters and "
        "the optional callable executes whole episodes. A failed guard keeps the existing default and research recommendations unchanged. "
        "No final result was used to retune or retrain. The primary teacher is an approximate median-world rollout search, not an optimal or calibrated dispatcher. "
        "Equal-crew aliases, synthetic graph mechanisms, limited training groups, incomplete-state exclusion and joint shift constrain generalization.", "",
        "Action agreement queries are outside callback timers. Full-episode wall/CPU includes those queries, environment work and independent validation; "
        "summed callback CPU is separate. Timing is local hardware-dependent, single-thread measurement, not a production throughput claim. "
        "The frozen developer-controlled reveal is procedural isolation, not external blind testing. Bounds and hashes validate this interface, not utility safety.", "",
        "## Artifacts and reproduction", "", "| Candidate | SHA-256 |", "|---|---|"]
    lines += [f"| [{name}](../evidence/training/{m['file']}) | `{m['sha256']}` |" for name, m in training["models"].items()]
    lines += ["", "[Protocol](../PROTOCOL.md) · [Public-state and inference contracts](../INTERFACES.md) · "
        "[Feature schema](../feature-schema.json) · [Reproduction and runnable inference](../REPRODUCE.md) · "
        "[Selection freeze](../evidence/freeze.json)", ""]
    (output/"REPORT.md").write_text("\n".join(lines))
    sources = [evidence/"freeze.json", evidence/"dataset/manifest.json", evidence/"training/training.json", evidence/"training/runtime.json"]
    sources += [evidence/p/f for p in ("dev", "final_id", "final_shift") for f in ("summary.json", "completion.json")]
    sources += [evidence/"training"/m["file"] for m in training["models"].values()]
    sources += [evidence/"teacher"/name for name in training["binding"]["teacher_shards"]]
    sources += [p for stage in ("dev", "final_id", "final_shift") for p in (evidence/stage).glob("command-runtime-*.json")]
    manifest = dict(version="learned-dispatch-presentation-v1",
        source_evidence={str(p.relative_to(evidence)): file_hash(p) for p in sorted(sources)},
        artifacts={str(p.relative_to(output)): file_hash(p) for p in sorted(output.rglob("*")) if p.is_file()})
    write_json(output/"manifest.json", manifest)
    return manifest
