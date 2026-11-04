"""Render measured tables and a restrained research figure from the independent audit."""
from pathlib import Path
import json

from .audit import REACTIVE, MEDIAN, EIGHT, FIXED, STUDENTS

NAMES = {FIXED:"Fixed order", REACTIVE:"Reactive downstream", MEDIAN:"Median search",
         EIGHT:"Eight-future search", "forest-depth4":"Frozen forest", "ridge-alpha10":"Frozen Ridge"}


def interval(values):
    return f"[{values[0]:.4f}, {values[1]:.4f}]"


def overview(audit, exact):
    lines = ["""# GridGuide ML opportunity audit

**NO-GO for an immediate new training pilot.** Decision-focused action ranking is the
best candidate for a future controlled investigation, but its incremental value remains
unproven. The existing trained dispatcher, dynamic baselines and historical conclusions
are preserved. **Zero new research fits; zero new final holdouts; no application changes.**

[Detailed measured report](REPORT.md) · [Protocol](PROTOCOL.md) ·
[Reproducible evidence](evidence/audit.json) · [Verification](VERIFICATION.md) ·
[Issue #22](https://github.com/its-spark-dev/GridGuide/issues/22)

![Waiting quality and full callback cost on separate historical cohorts](quality-cost.png)

## Verified findings

Independent code recalculates waiting, critical, p95 and branch outcomes from archived
schedules/customer dependencies, then aggregates paired configuration groups. Historical
point estimates match. Bootstrap intervals use 2,000 paired configuration resamples;
the full report distinguishes fresh retrospective intervals from the old frozen tests.

| Historical dispatch cohort | Reactive wait, h | Median teacher, h | Frozen forest, h | Teacher gain over reactive |
|---|---:|---:|---:|---:|"""]
    for key,label in (("adaptive_confirmation","PR20 confirmation"),("final_id","PR21 ID"),("final_shift","PR21 joint shift")):
        c=audit[key]; a=c['aggregates']
        forest=f"{a['forest-depth4']['metrics']['waiting']['mean_hours']:.6f}" if 'forest-depth4' in a else 'not trained'
        gain=1-c['comparisons'][MEDIAN][REACTIVE]['waiting']['ratio']
        lines.append(f"| {label} | {a[REACTIVE]['metrics']['waiting']['mean_hours']:.6f} | {a[MEDIAN]['metrics']['waiting']['mean_hours']:.6f} | {forest} | {100*gain:.3f}% |")
    lines.append("""
Each cohort has 24 configurations. PR20 uses 1,536 stochastic episodes/method; PR21
uses 384 per final cohort. These are separate fictional populations, never paired
across studies. The forest remains faster than its teacher but fails its historical
quality gate; the shifted forest also performs worse than cheap reactive downstream.

- **Restricted hindsight routing:** choosing among downstream, frozen forest and Ridge
  after seeing each configuration's outcomes yields **1.85945% ID / 1.30358% shift**
  ratio-of-means improvement. This is outcome-informed and bounds only that fixed
  three-policy-per-configuration selector on these results, not novel policies.
- **Teacher signal:** 5,352 discretionary training states, 24,240 action rows, 46 public
  features; 1,347 states have tied optimal distinct actions. WAIT is selected only
  47 times. The frozen forest matches just 4 of those 47 training WAIT labels.
- **State mismatch is not a demonstrated remedy:** most student states are absent from
  the paired teacher trajectory, yet their mean teacher regret is lower on ID. Exact
  feature collisions show no contradictory targets; this does not prove feature sufficiency.
- **Tiny exact diagnostic:** 12 fresh four-task configurations, two crew variants and
  two uncertainty profiles give 48 non-clairvoyant exact expectations. The optimum
  improves median search by **0.01269%**. Independent solvers and complete duration-world
  rollout expectations agree. This cannot bound headroom on larger problems.
- **Static selection:** ML I's best-of-four hindsight total-cost margin is 5.67% ID,
  1.44% shift; its trained selector's shifted regret remains 714.45% worse than fixed.
  ML II remains a separate source-audit NO-GO, not an untrained dispatch experiment.

## Ranked opportunities

| Rank | Track | Verdict and missing evidence |
|---|---|---|
| 1 | Decision-focused action ranking | **CONDITIONAL GO for a separately registered investigation.** Approximate teacher supervision is valid, but a ranking loss has no measured rollout/latency advantage yet; no pilot now. |
| 2 | On-policy dataset aggregation | **CONDITIONAL GO after a training-only query-value ablation.** Exact-state novelty does not establish causal value of more labels. |
| 3 | Static per-policy prediction/routing | **NO-GO now.** Limited shifted ceiling and unstable generalization; no robust achievable margin established. |
| 4 | New uncertainty predictor | **NO-GO.** No new externally justified input/target; rights and endpoint blockers from ML II remain. |

No track meets every Issue #22 pilot condition. The [full report](REPORT.md) provides
the gate rationale, exact formulas, all comparator/critical/tail tables, per-group
diagnostics, timing caveats, data limitations and a conditional one-factor-at-a-time
next-study design. A normal power approximation suggests 44–50 base groups for a 2%
gain using ID/development teacher-reactive variance; doubled SD requires about 175–197.
These are planning estimates for an untrained candidate, not guaranteed power.

## Reproduce

Use Python 3.12.14 and the existing `requirements-ml.lock` environment:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-ml/bin/python -m research.ml_opportunity \
  --exact --output /tmp/gridguide-opportunity-new
.venv-ml/bin/python -m research.ml_opportunity.report \
  --evidence /tmp/gridguide-opportunity-new --output /tmp/gridguide-opportunity-page
.venv-ml/bin/python -m unittest discover -s research/ml_opportunity/tests -t . -v
.venv-ml/bin/python scripts/check_opportunity_preservation.py
```

[Analysis source](../../../research/ml_opportunity/) · [Input/source hashes](evidence/sources.json) ·
[Fresh exact inputs/results](evidence/exact.json) · [Preservation inventory](PRESERVATION.json)

All data are fictional. No AEP raw files or new real-outage data are used. The audit
preserves 1,062 previous files and checks ten tracked data objects by Git identity
without opening them. No model/default promotion, merge, tag, release or deployment.
Existing regression suites still exercise temporary smoke training; those verification
fixtures are not a new scientific pilot or a reuse of the historical training study.
""")
    return "\n".join(lines).strip()+"\n"


def render(audit, exact):
    text = ["""# GridGuide · Is another dispatch model justified?

**NO-GO for an immediate new training pilot. CONDITIONAL GO for a separately registered
decision-ranking investigation only after the value and validation conditions below are met.**

This audit reproduces historical evidence from merged PRs #18–#21 and adds a small exact
scheduling diagnostic. It trains **zero new models**, opens **zero new final holdouts**,
and changes **no application defaults**. Existing fitted GridGuide models remain available.
All scheduling outcomes are fictional; none predicts actual utility outages or field benefit.

[Issue #22](https://github.com/its-spark-dev/GridGuide/issues/22) · [Audit protocol](PROTOCOL.md) ·
[Machine-readable audit](evidence/audit.json) · [Exact diagnostic](evidence/exact.json) ·
[Source hashes](evidence/sources.json) · [Verification ledger](VERIFICATION.md)

![Waiting quality and complete callback cost on separate historical cohorts](quality-cost.png)

## What was independently reproduced

The implementation reads individual archived episodes, not their published averages.
It independently recomputes customer waiting, critical, p95 and branch metrics from
retained schedules and fictional customer dependencies before aggregating them.
It rejects duplicate or missing method episodes, mismatched exogenous duration draws,
unpaired metric support and timing/episode coverage mismatches. Independent means agree
with published waiting values within 1e-10 hours; PR #21 critical, p95, branch and median
callback values are also checked. Historical evaluator/aggregation code is not imported.

For a method m and configuration g, W(g,m) is the average of completed customer-hours /
customer count over its stochastic episodes. The reported cost is the equal-weight mean
of W over configurations. Crew variants and low/high draws are balanced in these archives.
Critical means average each episode's maximum declared-critical group wait; p95 means
average customer-weighted episode p95. Unsupported critical outcomes are excluded on
matched support, never changed to zero. These are different metrics and denominators.

Intervals below use **2,000 paired configuration bootstrap resamples**, Python random
seed 2026110422. They are new retrospective uncertainty summaries, not new confirmatory
tests. Independent RNG implementation changes interval endpoints slightly from the old
NumPy bootstrap, without changing historical point estimates or promotion decisions.
Configuration groups, not actions or repeated episodes, are the resampling unit.
"""]
    for key, label in (("adaptive_confirmation","PR #20 confirmation"), ("final_id","PR #21 ID"), ("final_shift","PR #21 joint shift")):
        c = audit[key]
        text += [f"\n### {label}\n",
                 "| Method | Mean wait, h | Critical maximum, h (groups) | Customer p95, h | Complete discretionary callback median / p95, ms |\n|---|---:|---:|---:|---:|"]
        for method in NAMES:
            if method not in c["aggregates"]:
                continue
            a = c["aggregates"][method]
            t, metrics = a["discretionary_callback_ms"], a["metrics"]
            timing = "one-time plan" if t["p50"] is None else f"{t['p50']:.4f} / {t['p95']:.4f}"
            text.append(f"| {NAMES[method]} | {metrics['waiting']['mean_hours']:.6f} | {metrics['critical']['mean_hours']:.6f} ({metrics['critical']['groups']}) | {metrics['p95']['mean_hours']:.6f} | {timing} |")
        a = c["aggregates"][REACTIVE]
        text.append(f"\nPrimary denominator: **{a['episodes']} stochastic episodes/method, {a['groups']} configurations**. "
                    "Deterministic episodes are excluded from this audit's primary quality and timing tables.")
        if key == "adaptive_confirmation":
            text.append("All 15 archived comparators are aggregated in JSON, including the weaker fixed-floor controls. "
                        "The original PR #20 timing table includes deterministic episodes; its median of 3.490396 ms "
                        "therefore differs slightly from this stochastic-only 3.495125 ms. Its 8.056× timing ratio is preserved.")
        text += ["\n| Candidate versus reference | Candidate − reference, h | Paired 95% interval | Relative cost change |\n|---|---:|---:|---:|"]
        pairs = [(MEDIAN, REACTIVE), (EIGHT, MEDIAN)]
        if "forest-depth4" in c["aggregates"]:
            pairs += [("forest-depth4", REACTIVE), ("forest-depth4", MEDIAN)]
        for method, ref in pairs:
            d = c["comparisons"][method][ref]["waiting"]
            text.append(f"| {NAMES[method]} vs {NAMES[ref]} | {d['delta']:+.6f} | {interval(d['delta_ci95'])} | {(d['ratio']-1)*100:+.4f}% |")
    text.append("""
Median search has measurable value against downstream on each historical cohort. The
extra eight-future computation is not a consistently stronger teacher: its PR #20 gain
was 0.1128%, while PR #21 ID improves 0.4907% and the joint shift regresses 0.6469%.
These are separate cohorts, not paired replications of an identical population.

The forest loses 0.483471 h / 1.674118 h to median search on ID/shift. Its old teacher-quality
gate remains failed. Ridge dominates the forest on the ID waiting/callback point frontier;
both students are dominated by reactive downstream on shift. This is descriptive Pareto
dominance in two metrics, not statistical dominance or permission to reselect a champion.
Critical/p95 tradeoffs and uncertainty remain in the tables/JSON.

Complete callback timings include PR #21 public validation, legal-action enumeration,
features and prediction. They exclude the separately instrumented teacher agreement query.
PR #20 did not use PR #21's public-validator wrapper, so absolute latency is not paired
across studies. Fixed-plan time is not interchangeable with callback time. Forced decisions
make all-callback medians misleading; both distributions and counts are retained in JSON.
""")
    text += ["\n| PR #21 resource measure | ID | Joint shift |\n|---|---:|---:|"]
    for method in (REACTIVE, MEDIAN, *STUDENTS):
        values = [audit[k]["aggregates"][method]["mean_episode_callback_cpu_ms"] for k in ("final_id","final_shift")]
        text.append(f"| {NAMES[method]} full-episode callback CPU, ms | {values[0]:.3f} | {values[1]:.3f} |")
    speed = [audit[k]["speed_teacher_over_forest"] for k in ("final_id","final_shift")]
    text.append(f"\nThe original speed estimand is teacher/student **ratio of mean configuration-median** "
                f"callback times: {speed[0]['ratio']:.3f}× {interval(speed[0]['ratio_ci95'])} ID, "
                f"{speed[1]['ratio']:.3f}× {interval(speed[1]['ratio_ci95'])} shift. It is not the ratio of pooled medians.")
    runtime = audit["resources"]
    text.append(f"\nArchived training wall time: {runtime['elapsed_seconds']:.3f} s; process peak RSS {runtime['peak_rss_mib']:.1f} MiB. "
                "Forest/Ridge artifact loads: 2.112 / 0.279 ms; sizes 211,281 / 16,869 bytes. "
                "These are recorded local measurements. Incremental per-model RSS and production throughput are unavailable; "
                "peak process memory is not model memory. PR #20 confirmation recorded 901.750 s and 430.375 MiB; "
                "its aggregate run is not a model-memory comparison.")
    text.append("""
## Restricted hindsight ceilings: exact scope matters

For each already-observed configuration, pick the minimum W among **downstream, frozen
forest-depth4 and frozen ridge-alpha10**. Let B(g) be that minimum. The Issue #22 number
is **1 − mean(B) / mean(Wreactive)**. A different estimand, mean(1 − B/Wreactive), averages
relative configuration improvements. The audit computes and preserves both, plus every
group winner and cost, rather than treating them as interchangeable.

| Historical cohort | Reactive mean, h | Hindsight mean, h | Ratio-of-means gain (Issue #22) | Mean group-relative gain |
|---|---:|---:|---:|---:|""")
    for key, label in (("final_id","ID"),("final_shift","Joint shift")):
        c = audit[key]["restricted_ceiling"]
        text.append(f"| {label} | {c['comparison']['reference']:.6f} | {c['comparison']['candidate']:.6f} | {c['ratio_of_means_improvement']*100:.5f}% | {c['mean_group_relative_improvement']*100:.5f}% |")
    text.append("""
This is a ceiling only for **one fixed choice from those three policies per configuration
on these realized group averages**. It sees outcomes before choosing and is not deployable.
It does not bound a state-dependent router, a novel ranker, or population-optimal behavior.
The selector class can include reactive, so its nonnegative gain is partly guaranteed by
construction. Bootstrap intervals describe selected empirical gains; they do not debias
selection or establish that a predictor can achieve them. No episode-level hindsight
minimum is mislabeled a configuration selector ceiling. Both spent final sets remain spent.

## Signal, identifiability and imitation
""")
    s = audit["signal"]; counts = s["counts"]
    text.append(f"{counts['episodes']} historical training trajectories give {counts['visits']:,} visits, "
                f"{counts['unique_states']:,} unique states, {counts['discretionary_states']:,} discretionary states "
                f"and {counts['action_rows']:,} action rows with {s['feature_count']} public features. "
                f"{counts['forced_states']:,} forced states are excluded from the supervised denominator.")
    text.append(f"\n- Legal actions: median {s['legal_action_counts']['p50']:.0f}, p95 {s['legal_action_counts']['p95']:.0f}, "
                f"maximum {s['legal_action_counts']['p100']:.0f}; after crew-alias collapse, maximum {s['distinct_task_or_wait_counts']['p100']:.0f}.\n"
                f"- {counts['distinct_optimal_tie_states']:,}/{counts['discretionary_states']:,} states tie across distinct tasks/WAIT; "
                f"{counts['zero_regret_rows']:,}/{counts['action_rows']:,} action rows have zero teacher regret.\n"
                f"- Best/second-distinct-action margin: median {s['best_second_distinct_action_margin']['p50']:.6f}, "
                f"p95 {s['best_second_distinct_action_margin']['p95']:.6f}, dimensionless normalized teacher regret. "
                "Tied best actions have zero margin. These are not realized outage-hour gains.\n"
                f"- WAIT is legal in {counts['wait_legal_states']:,} states but selected in only {counts['wait_teacher_states']}: "
                f"{100*counts['wait_teacher_states']/counts['discretionary_states']:.3f}% of discretionary states. "
                "On the same in-sample states, forest chooses WAIT 41 times but matches only 4 of the 47 teacher-WAIT labels; "
                "Ridge chooses WAIT 49 times and matches none. Tie-aware overall agreement hides this rare-action failure.\n"
                f"- {s['unique_feature_vectors']:,} exact feature vectors; {s['repeated_feature_vectors']:,} repeated vectors, "
                f"{s['inconsistent_target_vectors']} contradictory targets; {s['pair_vectors']:,} distinct feature-vector pairs, "
                f"{s['opposing_rank_pairs']} opposing strict ranks. No within-state equal-vector/distinct-task contradictions were found.")
    text.append("""
Zero exact collisions **does not prove sufficient features**: 46 continuous summaries
and report rank can make collisions rare while discarding relevant graph structure.
Near-neighbor conditional rank noise, representation sufficiency, and intervention-based
value of teacher queries are unmeasured. Targets are deterministic approximate median-world
rollout costs, not expected Bayes-optimal action values or realized future outcomes.

Each shared-state additive Ridge term cancels when comparing actions within a state;
existing interaction features can still change ranking. Raw action-cost MSE therefore
does not directly optimize the decision. Historically the depth-8 forest halved training
MSE relative to depth 4 yet had worse development rollout cost. That motivates testing a
ranking loss, but it is not evidence that a new loss will beat cheap downstream or median search.

The forest agrees with the teacher on 4,018/5,352 training states (75.07%), versus
2,940/4,359 ID student decisions (67.45%) and 4,227/6,580 shift decisions (64.24%).
Training agreement is in-sample and unique-state weighted here; evaluation agreements
are decision visits on new groups. Their difference cannot isolate covariate shift.

The training mixture already includes 1,882 discretionary states not seen on its pure
teacher trajectories, alongside 3,470 teacher-seen states. Exact public-state comparison
within each paired student/teacher evaluation episode gives:

| Frozen forest trajectory | Teacher-shared states | Student-only states | Mean teacher regret: shared / student-only |
|---|---:|---:|---:|""")
    for key, label in (("dev","Development"),("final_id","ID"),("final_shift","Joint shift")):
        r = audit[key]["trajectory_overlap"]["forest-depth4"]
        text.append(f"| {label} | {r['counts']['shared']} | {r['counts']['student_only']} | {r['shared_regret']['mean']:.6f} / {r['student_only_regret']['mean']:.6f} |")
    text.append("""
State overlap uses the same case, profile and exogenous draw, excluding forced decisions.
Different previous actions naturally change later exact states. Student-only states do
**not** have higher average teacher regret on ID/development; they do on shift. This
association does not establish that on-policy aggregation cures the failure. No counterfactual
new-query intervention or causal estimate exists. Complete per-group cost/error values
and worst episodes are retained in JSON, rather than selecting only favorable examples.

## Static selection and data rights

ML Lab I has a different task and objective: whole-case selection among four static policies,
measured in **customer-hours**, not the adaptive per-customer waiting hours above.

| ML I partition | Eligible cases / groups | Fixed regret, customer-hours | Four-policy hindsight total-cost gain | Fixed tie-optimal cases |
|---|---:|---:|---:|---:|""")
    for key in ("train","dev","final_id","final_shift"):
        r = audit['static'][key]
        text.append(f"| {key} | {r['eligible']} / {r['groups']} | {r['fixed_regret_customer_hours']:.6f} | {100*r['four_policy_ceiling_ratio_of_means']:.4f}% | {r['fixed_tie_optimal_cases']} |")
    text.append("""
The old logistic selector's ID regret is 325.400170 customer-hours, a 33.44% **regret**
reduction, not a 33.44% reduction in total waiting cost. Shift regret is 1,965.070166,
714.45% worse than fixed. Its critical degradation reproduces +3.580759 h (78 supported
ID cases) and +34.983304 h (84 shifted cases). Neither historical promotion gate changes.
All 99 eligible shifted cases have task counts outside the training range; topology and
scale changed jointly. Training labels span all four policies, but critical-first labels
rise from 133/297 training cases to 66/99 shift cases. This supports neither causal
attribution to scale nor a stable shifted routing advantage. Integer policy costs,
best/second margins, family labels and feature-range counts are independently summarized.

ML Lab II is a **separate source audit**, not dispatch training. Its [NO-GO](../../outage-ml/FEASIBILITY.md)
remains authoritative: PNNL endpoint/coverage/incident identity, Purdue artifact-specific
rights, and Zenodo segmentation/coverage limitations are unresolved. We did not acquire
new real outage data or open AEP raw files. Existing static/public dispatch inputs are
genuine pre-decision *simulator* observations; they are not evidence of a new externally
calibrated uncertainty predictor. No future outcome, private duration, identity or split
marker is added as a feature. MIT attribution/licenses remain unchanged.

## Fresh exact non-clairvoyant check

The predeclared diagnostic uses 12 fresh four-task configurations, 1/2 crews and low/high
finite duration supports: 24 variants and 48 exact expectations. Graph edges, repair
efforts and overlapping customer requirements are sampled before evaluating algorithms.
Four-task size excludes the 10+ task historical graphs; no model training occurs.

At state s, the Bellman recursion minimizes over legal actions **before** the next event
is observed. WAIT transitions integrate only conditional active-duration supports given
survival; unstarted durations remain unknown. Immediate cost is unreleased customers ×
elapsed seconds. A complete independent duration-world enumeration checks each fixed
policy expectation, while the old Bellman solver separately checks each new optimum.
This is stochastic scheduling with known authored supports, not perfect future information.

| Four-task policy | Mean expected wait, h | Exact optimum reduction | Paired 95% reduction interval, h |
|---|---:|---:|---:|""")
    for method in ("fifo","downstream","median"):
        c=exact['comparisons'][method]
        text.append(f"| {method} | {c['reference']:.6f} | {(1-c['ratio'])*100:.5f}% | {interval([-c['delta_ci95'][1],-c['delta_ci95'][0]])} |")
    text.append(f"\nExact optimum mean: **{exact['comparisons']['median']['candidate']:.6f} h**. "
                f"All 48 solves and policy expectation checks agree exactly as rational customer-seconds. "
                f"Maximum states in one new solve: {max(r['bellman_states'] for r in exact['results']):,}, "
                f"below the 100,000 cap. Fixed-policy checks enumerate {sum(r['duration_worlds'] for r in exact['results']):,} "
                "duration worlds per policy across the 48 cases. No Monte Carlo approximation enters those expectations.")
    text.append("""
The tiny optimum improves median search by only 0.01269%, but this is **not** an upper
bound for the larger dispatch problems. Four-task structure, no arrival delays and a
small authored sample limit transfer. Twelve-group bootstrap intervals describe this
sample only. The diagnostic offers no evidence for a materially stronger scalable teacher;
it does not prove one cannot exist.

## Opportunity ranking and pilot gate

No track currently meets **all** Issue #22 conditions. The missing condition for A/B is
a demonstrated, appropriately priced improvement attributable to the proposed intervention,
not a lack of a runnable model or computable supervision. A plausible objective or more
data is insufficient to claim that condition. The exact diagnostic and observed teacher
advantage bound the argument locally; neither establishes ranking/aggregation efficacy.

| Rank / track | Input and target | Empirical value / compute | Robustness and validity | Verdict now |
|---|---|---|---|---|
| 1 · A: decision-focused ranking | Public state/action inputs and teacher preference pairs are identifiable; teacher is approximate | 3.62% / 2.99% teacher advantage over reactive leaves a distillation target; frozen students do not robustly capture it. A compact ranker could be cheap, but neither its gain nor latency is measured | Ties, rare WAIT, summary representation and joint shift remain; MSE/rollout discrepancy is motivation, not a win | **CONDITIONAL GO for a new prospective investigation; NO-GO for this issue's immediate pilot gate** |
| 2 · B: on-policy teacher queries | New training/dev states can be labeled without hidden futures | State mismatch is observed, but regret is not consistently worse there; existing mixture already broadens coverage. Teacher querying adds ms per state | No controlled query-budget ablation or causal benefit; adaptively choosing final-derived targets would leak | **CONDITIONAL GO only after a training-only mismatch/query-value experiment; no pilot now** |
| 3 · C: static cost prediction/routing | Static features and exact four-policy costs are valid fictional targets | 5.67% ID hindsight total-cost margin falls to 1.44% on shift; achievable gain lower. Adaptive three-policy routing has only 1.86% / 1.30% retrospective group ceiling | Old shifted selector fails strongly; no stable shifted signal established. Neither ceiling bounds novel action policies | **NO-GO for another selector now** |
| 4 · D: new uncertainty prediction | No additional externally justified input/target pair demonstrated | No defensible value/cost estimate | ML II rights, ascertainment and endpoint blockers remain; arbitrary latent signals would manufacture predictability | **NO-GO** |

No new hyperparameter search, learned policy, dataset aggregation or source acquisition was
performed. This is a conservative value-of-information decision under the explicit gate,
not a claim that all future ML approaches must fail. Ranking A first does not promote the
old forest or rewrite the PR #20 / #21 failed gates.

## Conditional next-study design and economics

If A is reopened, register a fresh, development-only objective ablation before generating
data: one compact pairwise regret-weighted linear ranker versus the same feature/weight
pipeline with cost MSE, frozen Ridge/forest, downstream, FIFO and median search. At most
three regularization choices, a single training pass per declared seed, and no neural/RL
expansion. Teacher labels are computed only from public training/development states.
First verify that predicted ranking gains survive full paired rollouts and the runtime
budget; do not substitute action accuracy for episode outcomes. A positive exploratory
result would justify a **separate** sealed confirmation protocol, not a final claim here.

For B, first use a training-only randomized query-budget ablation (teacher-only versus
mixed versus student-visited states with equal total queries) and evaluate complete
rollouts on new configuration groups. Without that intervention, exact-state novelty
cannot tell us where useful labels lie. Do not combine A+B and attribute the result to one.

One-factor shifts should preserve each base configuration in one split/group: base
10–14 tasks, original four topology mechanisms, 2/3 crews; change topology alone to
preferential/deep-sparse at the same size/crews, scale alone to 18–24 tasks with base
mechanisms/crews, and crew count alone to 1/4 on the same base graphs. Related variants
remain grouped. Predeclare generation parameters and seeds; compare each intervention
with its matched control and avoid pooling shift arms. Historical joint shift cannot
identify a causal driver. Also retain a joint-shift stress test without causal attribution.

Prospective practical thresholds, explicitly prototype choices: **≥2% wait improvement
against downstream at ≤1 ms median full callback**, or **≤2% degradation from median
search at ≥3× speed**. Require critical/p95 upper degradation ≤max(0.25 h, 5% reference),
zero invalid actions and worst configuration ratio ≤1.25. Include fallbacks, p95 callback,
load, memory and full-episode CPU. These planning thresholds never replace old gates.

For a paired group difference with SD s, planning minimum effect δ = 0.02 × reference
mean, normal approximation n = ceil(((1.96 + 0.84)s/δ)²) gives 80% power against zero
at two-sided 5%. It does **not** give 80% power to certify a lower bound of 2%. To test
a 2% superiority margin, replace δ with expected gain minus 2%; equal-to-margin effects
cannot reliably clear that gate at finite n. Historical teacher/reactive variance is only
a proxy for an untrained ranker. No variance estimate from a future final cohort is used.

| Historical variance proxy | 2% effect, h | Paired SD, h | Approx. groups | Groups if SD doubles |
|---|---:|---:|---:|---:|""")
    for key,label in (("adaptive_confirmation","PR20"),("dev","PR21 dev"),("final_id","PR21 ID"),("final_shift","PR21 shift")):
        p=audit[key]['power']
        text.append(f"| {label} | {p['minimum_hours']:.4f} | {p['historical_paired_sd']:.4f} | {p['normal_approx_groups']} | {p['doubled_sd_groups']} |")
    text.append("""
A subsequent small development study could cap at 48 training + 24 development groups,
four shift arms kept within their parent groups, 2 variants × 2 profiles × 4 paired draws
per arm and six policies: 9,216 development method-episodes if all four arms are used.
Cap teaching at 25,000 unique states and combined collection/fitting/evaluation at two
single-core hours and 1 GiB RSS; stop and report incomplete evidence on a cap, never
quietly drop slow configurations. This is a proposed budget, not an executed pilot or a
measured capacity promise. Empirical callbacks suggest benchmarking feasibility first.

The 24-group development proposal is for exploration, not adequately powered confirmation.
For a later confirmation, plan at least 50 independent base groups per required arm using
the current SD proxy, and consider approximately 200 under doubled-SD sensitivity; re-plan
from **new development** variance before sealing final inputs. At 50 groups × 4 arms ×
2 variants × 2 profiles × 8 draws × 6 policies, evaluation costs 38,400 method-episodes.
At 200 groups it costs 153,600. These are simulation budgets, not independent sample counts.
Use simultaneous or predeclared hierarchical inference if making claims across several arms.

## Reproduce and preserve

Use the existing Python 3.12.14 environment and `requirements-ml.lock`. No new dependency,
GPU, API key, raw dataset, retraining command or network access is required during analysis.
Statistics/aggregation are standard-library code; frozen feature/model adapters use the
already-pinned numerical dependencies. All commands operate inside the raw-data/network
denial guard. New output directories are required; historical paths are rejected.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-ml/bin/python -m research.ml_opportunity \
  --exact --output /tmp/gridguide-opportunity-new
.venv-ml/bin/python -m research.ml_opportunity.report \
  --evidence /tmp/gridguide-opportunity-new --output /tmp/gridguide-opportunity-page
.venv-ml/bin/python -m unittest discover -s research/ml_opportunity/tests -t . -v
.venv-ml/bin/python scripts/check_opportunity_preservation.py
.venv-ml/bin/python scripts/check_learned_preservation.py
.venv-ml/bin/python scripts/check_frozen_artifacts.py
```

The [preservation inventory](PRESERVATION.json) covers 1,062 baseline files. Ten tracked
data objects are checked by Git blob identity without opening raw/processed data. Existing
historical checks remain intact. Root README, maps, attribution, MIT license, all prior
research, numerical rules and application behavior are unchanged. Reproduction code is
under [research/ml_opportunity](../../../research/ml_opportunity/). New hashes bind source
and evidence, not independent authorship or utility validity.

### Remaining uncertainty

No feature-sufficiency theorem, causal query-value estimate, scalable exact optimum,
real-outage outcome validation, heterogeneous-crew/travel/switching model or external
deployment evidence was produced. Non-collision and a failed pilot gate cannot establish
that ML has no possible value. The concrete result is narrower: **a new training run is
not yet justified by demonstrated incremental value under Issue #22's gate**. Preserve
the trained artifacts and strong dynamic baselines; reopen a specific controlled study
only with its missing evidence and prospective protocol made explicit.
""")
    return "\n".join(text).strip()+"\n"


def figure(audit, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10, "svg.hashsalt":"opportunity-v1"})
    fig, axes = plt.subplots(1,2,figsize=(11.8,4.4), layout="constrained")
    colors = {REACTIVE:"#166680",MEDIAN:"#13946c",EIGHT:"#7b63af","forest-depth4":"#bd6831","ridge-alpha10":"#b34265"}
    for ax, key, title in zip(axes, ("final_id","final_shift"), ("Historical ID · 24 groups", "Historical joint shift · 24 groups")):
        for i,m in enumerate((REACTIVE,MEDIAN,EIGHT,*STUDENTS)):
            a=audit[key]['aggregates'][m]
            x=a['discretionary_callback_ms']['p50']; y=a['metrics']['waiting']['mean_hours']
            ax.scatter(x,y,s=70,color=colors[m],zorder=3)
            offset = (7, 9 if m != 'forest-depth4' else -17)
            if key == 'final_shift' and m == REACTIVE: offset=(7,-18)
            if m == EIGHT: offset=(-7,9)
            ax.annotate(NAMES[m], (x,y), xytext=offset,textcoords="offset points", fontsize=9,
                        ha="right" if m==EIGHT else "left",color=colors[m])
        ax.set_xscale('log');ax.set_xlim(.045,150)
        ax.margins(y=.30);ax.set_title(title,loc='left',fontweight='bold')
        ax.set_xlabel('Complete discretionary callback median, ms (log scale)')
        ax.set_ylabel('Configuration-mean customer wait, hours')
        ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Strong baselines remain: faster students do not retain teacher quality',fontsize=14,fontweight='bold')
    fig.savefig(output/'quality-cost.png',dpi=170,metadata={"Software":"GridGuide opportunity audit"})
    fig.savefig(output/'quality-cost.svg',metadata={"Date":None})
    plt.close(fig)


def main():
    import argparse
    from research.ml_lab.access import isolated
    from .evidence import save_new
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    path=args.output.resolve()
    if path.exists():
        parser.error('Use a new output directory outside source/evidence')
    with isolated():
        audit=json.loads((args.evidence/'audit.json').read_text())
        exact=json.loads((args.evidence/'exact.json').read_text())
        save_new(path,{})
        (path/'README.md').write_text(overview(audit,exact))
        (path/'REPORT.md').write_text(render(audit,exact))
        figure(audit,path)


if __name__=='__main__':
    main()
