# GridGuide v1.2.0 — ML Lab PRD (proposal v0.1)

**Status:** DESIGN PROPOSAL; not a trained model, validated result, release commitment, or authorization for implementation/merge.
**Owner goal:** demonstrate credible applied machine-learning engineering in a public portfolio; real-world utility performance improvement is not the goal.
**Product boundary:** v1.1.0 remains the stable, frozen demonstration. ML Lab is an offline, source-free research track first, optionally a visibly experimental showcase later.

## 1. Product thesis and user story

GridGuide's four deterministic scheduling policies can disagree on a *fictional* restoration problem. ML Lab asks whether a supervised selector can learn **which of those four existing policies has the lowest modeled cost for a new fictional case**, using only inputs available **before** scheduling/evaluation. This is *policy selection under a declared simulator*, not an outage predictor, restoration-time estimator, dispatcher, new optimizer, or evidence of utility performance.

**Portfolio user story:** An engineering reviewer can inspect the task definition, regenerate licensed-for-public synthetic cases, compare naïve and learned selectors against the same four feasible-policy outcomes, replay every metric, and see failures, tradeoffs and generalization limits. The reviewer should not need AEP challenge files, tokens, a hosted site, or a cloud ML platform.

**Not a success claim:** the rule-based selector may tie or outperform ML. Report that outcome faithfully; do not manufacture an ML improvement.

## 2. Why this task and what prior work permits

- G2's frozen benchmark has **six structural families, 270 published evaluation cases** (10/25/100 tasks, 1/2/4 crews, five evaluation seeds) plus eight microcases, totaling **1,112 four-policy runs**. The published suite and its results were inspected during v1.1 research: **not a blind final test**.
- The four policies are `fifo-v1`, `customer-count-v1`, `legacy-release-per-person-hour-adapter-v1`, and `legacy-critical-proxy-first-adapter-v1`. They share validated contracts and independent metrics in `benchmarks/`.
- The current v1 generator is deliberately narrow. Within each family it uses particular task, prerequisite, group and seed templates; random seeds alone do **not** establish generalization to novel graph-generation mechanisms.
- G3 CP-SAT failed the preregistered 5% median improvement gate (0% median); do not describe an ML selector as fixing that result or as replacing CP-SAT.
- G4 found insufficient real outage labels/permission/observation coverage; no real-data predictor was trained. G5 is assumption-based fixed-timetable simulation, not observed-duration calibration. Neither provides labels for real restoration outcomes.

**Source references:** [final v1.1 report](../benchmarks/v1.1.0.md), [G2 specification](../benchmarks/PHASE2_SPEC.md), [frozen G2 results](../benchmarks/phase2/standard/REPORT.md), [G4 findings](../research/RISK_FINDINGS.md), [G5 protocol](../research/phase5/SIMULATION_PROTOCOL.md).

## 3. ML task and objective

### Unit of prediction
One whole validated `BenchmarkProblem`, before the four baseline policies have run. The selector chooses **one of the four existing policies**, not a task, crew assignment or numerical outage probability. Policy execution remains deterministic and is independently validated.

### Target construction
For each fully eligible fictional case, run all four current policies on **identical inputs**. Independently validate schedules and metrics. Label the smallest **completed modeled customer-hours** policy, with deterministic stable policy-ID tie-breaking. For cases with unknown full completion, withhold that label; use a **separate** restricted-horizon task if its interpretation and coverage gate are approved. Do not silently mix finite and censored/unresolved targets, substitute 168 h for unknown time, or drop hard cases from all reporting.

In every report distinguish:
1. **Best-of-four hindsight oracle**: per-case minimum over already-run policies; an *unattainable at prediction time* upper benchmark, never a deployable predictor.
2. **Fixed-policy baseline**: select the best fixed policy on **training data only**, then freeze it.
3. **Simple non-ML selector**: e.g. a training-derived small decision rule, frozen before final test.
4. **ML selector**: trained using training-only labels/features, chooses a policy at inference.
5. **Random/majority baseline**: optional, specified before test.

An ML selector does not compete against the true global scheduling optimum; its regret is relative only to the best of the four existing baseline policies. All cases' per-policy results are simulator outputs, **not real observed outcomes**.

### Primary evaluation
On finite cases, use per-case **relative selection regret**:
`(selected_policy_cost - best_of_four_cost) / max(best_of_four_cost, predeclared_positive_epsilon)`.
Use a predeclared epsilon only for zero-cost numerics; also report absolute customer-hour regret. Primary aggregate is **mean absolute customer-hour regret** plus mean and median relative regret, all with per-family breakdown. Include selection accuracy and tie-aware accuracy as diagnostics; high accuracy alone is not the objective.

Success criterion must be **preregistered before final-set reveal**. Suggested candidate gate: at least **5% lower mean regret than the frozen fixed-policy baseline on the distinct final test**, plus no material critical-group-latency or branch-disparity regression under predeclared tolerances. This is a *proposal*, not an achieved target; verify the gate is meaningful after a training-only pilot. Never tune the goal from final-test results. If the fixed policy already has zero regret on a population, a percent improvement gate is undefined: report no testable gain.

### Secondary metrics
- Mean/median/95th-percentile absolute and relative regret; exact ties, policy confusion matrix, selection coverage and abstention rate.
- Total completed modeled customer-hours and restricted 168-hour customer-hours **reported separately with denominators**.
- Critical-service latency, branch mean disparity and small-group mean waits; compare on same cases and disclose null/unsupported values.
- Feature computation, training and inference wall time with machine metadata (measurements not portable SLAs).
- Reliability: fraction of missing/invalid inputs; inference must fail closed to a documented fixed policy or abstain without invented results.

## 4. Dataset design and leakage discipline

### Data families
Develop a **new** generator/contract namespace, e.g. `research/ml_lab/`, not edits to `benchmarks/scenarios.py` or the hash-pinned G2 manifest. Reuse validated `BenchmarkProblem` contracts and the four policy implementations unchanged. Develop independently parameterized structural families that vary at minimum:
- prerequisite DAG topology (chain, fork/join, bottleneck, mixed),
- overlap and distribution of customer-to-task dependencies,
- task effort distributions and/report ordering,
- crew count/availability,
- critical-group prevalence and blocked/unresolved scope.

Declare exactly which generation parameters are varied and whether families share code templates; simple seed changes do not justify out-of-distribution claims. Validate each new case and avoid duplicates or isomorphic near-duplicates crossing partitions where practical.

### Proposed three-part isolation
- **Train**: new generator families/seeds and parameter ranges; unlimited exploration, versioned.
- **Development/validation**: distinct seeds and **grouped generator configurations**; hyperparameter selection and model family choice here only.
- **Final blind holdout**: separately generated and sealed by a manifest/hash *before* final model choice, with at least one intentionally shifted structural or parameter regime. Do not inspect its policy labels or tuning diagnostics until final promotion gate. A machine-readable precommit protocol should list split IDs, seeds, parameter-range boundaries, inclusion/exclusion rules and evaluation code hash.

Prefer **grouping by structural template / configuration and related seeds** when splitting; report both in-distribution held-out and shifted tests, avoiding a single blended score that masks failure. Freeze all feature selection and preprocessing on train only. If final holdout is examined and then changed, name any subsequent set a **new** final test and disclose that the old set was spent.

The historical G2 data may support a public **historical stress-test appendix** only. It must not be used as a secret final test, and if used in iterative model development, label it development evidence.

### Feature rules
Only pre-decision static inputs: task count, crew count and availability, effort summary, prerequisite DAG depth/width, indegree/outdegree summary, group sizes, overlap indicators, critical-service prevalence, blocked/unresolved counts. For every feature, show how it is computed **without scheduling a candidate policy**.

Strictly ban: actual policy cost/metrics, selected schedules, post-decision completion times, the hindsight-best label, test split, seed, case ID, filename/hash, report artifact paths, and any feature computed by evaluating a policy. Do not leak `family` as an identifier if claiming transfer to unseen families; use structural numerical features instead. Guard against mutable feature scaling after test evaluation.

## 5. Models and experimental protocol

**Minimum viable models:**
- Majority/fixed-policy baseline.
- Multinomial Logistic Regression with train-only standardized features.
- Random Forest / HistGradientBoosting (choose based on verified dependencies and sample scale).
- Optional calibrated per-policy **cost regression** with argmin, clearly separate from classification.

Use scikit-learn if its pinned dependencies/licenses are approved. No neural net or LLM requirement; exclude GPUs, hosted training, external model APIs and pretrained black boxes. A lightweight model with honest out-of-distribution evaluation is preferred over an unvalidated deep network.

**Training-only decisions:** define class imbalance/tie-handling, CV group unit, preprocessing, metric aggregation, sampling weights, hyperparameter budget, deterministic seeds and failure dispositions. Run a leakage sentinel: features derived from costs or labels must be rejected. Model artifacts must record dataset/generator version, split IDs, training code version, dependencies, parameters and SHA-256. No serialized untrusted model loading from downloads.

**Reproducibility:** fresh environment from pinned hashes, deterministic dataset generation, one-command train/evaluate/report, manifests, numeric comparisons within explicit tolerance, and stable output directory naming. Make all private/raw challenge data unavailable in ML CI. Never modify G2/G3/G4/G5 frozen manifests or rewrite research findings.

## 6. Deliverables and UX

### Phase 0 — Design gate (this PR)
- PRD, feasibility risks, label/feature/split schema, candidate metrics and acceptance criteria.
- No model fitting and no new release.

### Phase 1 — Data contract & generation
- New deterministic fictional generator with independent validator and source-free tests.
- Data dictionary, lineage/provenance and train/dev/final partition manifest.
- Demonstrate diversity and explain OOD claim limits. **Seal final holdout before tuning.**

### Phase 2 — Baseline/evaluation harness
- All four policies run on identical inputs, validated results, explicit finite/null/censored handling.
- Training-only fixed baseline and hindsight-oracle comparison; assertions forbid metric leakage into features.
- One-command tabular baseline report.

### Phase 3 — Models
- Logistic Regression plus one tree model, pinned environment, training/test entrypoints, reproducible artifacts.
- Grouped development validation, uncertainty or abstention checks where defensible.
- Freeze champion and final evaluation protocol.

### Phase 4 — One-time final evaluation and portfolio report
- Reveal final holdout once; compute primary and secondary metrics with denominators, failure/censoring cases, distribution shifts, subgroup losses, train-inference runtime.
- Explain why model did or did not beat the fixed policy and what benchmark design does **not** establish.
- Produce simple inspectable comparison figures, report tables and error case studies with exact regeneration commands.

### Phase 5 — Optional interface showcase (separate approval)
Only if results justify it, a dedicated **ML Lab — fictional benchmark** view with feature summary, recommended baseline policy, why/why-not, comparisons and limitations. Keep deterministic production engine and v1.1.0 default unchanged. An offline README research figure is sufficient even if no UI is built. No online inference service or domain.

## 7. Acceptance and stop gates

**Gate A — Dataset validity:** contract-valid, exact provenance, no AEP data, no leakage, truly separate generators/splits. If violated, do not train.

**Gate B — Label and baseline validity:** four policies feasible/validated, target and tie decisions reproducible, missing labels handled explicitly; hindsight oracle correctly marked non-deployable. If violated, do not report model accuracy.

**Gate C — Holdout integrity:** final set frozen before tuning and never reused for selecting models or thresholds. If violated, characterize results as exploratory and construct a newly sealed evaluation cohort.

**Gate D — Evidence-backed ML outcome:** report ML gains or losses, paired uncertainty with structural grouping, support counts, and meaningful OOD breakdown. A failing model is acceptable research; **no performance-success claim** without predeclared gate.

**Gate E — Portfolio quality:** README/technical research note says *synthetic policy selector*, not *real-world restoration predictor*. Full reproducibility and clear failure analysis required; UI optional.

**Gate F — Release:** v1.2.0 naming, tag, Release, package change, or app integration require a separate reviewed approval after evidence. ML Lab milestones are not automatically v1.2.0 Stable.

## 8. Explicit non-goals and constraints

- No new real-data outage prediction, actual duration regression or calibrated restoration probability.
- No AEP/raw GIS/private coordinates or source histories in train/evaluation artifacts; original repository remains preserved.
- No retraining, retuning, or reinterpretation of frozen G2/G3/G4/G5 studies.
- No claim that ML learns a utility-optimal dispatch policy.
- No LLM-only explanation masquerading as ML training.
- No production hosting, external alerting, user accounts, GPU requirement or new UI until evidence supports it.
- MIT covers contributor-owned GridGuide code; AEP and other third-party materials keep their separate terms.

## 9. Decisions requested at Phase 0 review

1. Approve **per-case four-policy selection** (not real-outage forecasting) as the portfolio ML task.
2. Approve a **new synthetic dataset with truly grouped/blind holdout**, not the historically inspected G2 evaluation matrix.
3. Approve **offline, no-UI-first implementation**; optionally revisit UI after evidence.
4. Approve metric/gate preregistration after the training-only data audit and **before final holdout**.
5. Explicitly authorize Phase 1 implementation in a later PR. This proposal itself authorizes no code changes.

**Definition of done for this design PR:** reviewer can identify exact task, permitted features, label provenance, split/holdout plan, baselines, risks, tests, acceptance and stopping criteria. No model performance is asserted.
