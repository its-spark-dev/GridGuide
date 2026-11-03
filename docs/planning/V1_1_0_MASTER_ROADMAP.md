# GridGuide v1.1.0 — Evidence-driven final feature release

Approved November 3, 2026. This document preserves the complete approved roadmap; repository links are made relative for portability. Approval authorizes phased execution, not automatic passage through review gates. **Only Phase 1 is currently authorized. Do not merge its PR or begin Phase 2 without owner approval.** The public README remains product-focused.

## Approval refinements (controlling interpretation)

1. The 5% optimization improvement is a preregistered target, not a mandatory outcome or permission to change evaluation data. Negative/inconclusive results are valid outcomes.
2. Deterministic solver reproducibility (pinned versions, seed, workers and deterministic work budget) is assessed separately from wall-clock response time. A hard wall-time interruption can change the incumbent and is recorded; it cannot earn a deterministic-reproduction claim.
3. Completed modeled customer-outage hours require known completion for the entire declared scope. Restricted-horizon customer-hours integrate waiting only through a declared horizon; report censored known-later completions and unresolved outcomes separately, retain them in the denominator, and never label their restricted total as completed outage hours.
4. Engineering-day estimates are provisional. Record actual scope and verification effort and recalibrate remaining estimates after each phase; they are not deadlines or evidence that research must succeed.
5. Phase 1 must document source licensing, observation coverage and data-use feasibility separately. Public accessibility does not establish redistribution permission; metadata review does not establish acquired/validated observation coverage.

## 1. Release intent and verified baseline

**Deliver a reproducible restoration decision-support project with measured scheduling performance, explicitly conditional uncertainty, improved customer preparedness, and an isolated synthetic demonstration.** Validated outage prediction is a conditional research outcome, not a release requirement.

The release should support a clear portfolio narrative:

> Inspect the evidence, compare repair policies, understand dependencies and uncertainty, review a recommendation, and prepare for an outage—without confusing simulations with utility observations.

### Findings from the planning inspection

| Area | Verified current state | Implication for v1.1.0 |
|---|---|---|
| Release history | v1.0.0 points to `b324c1b355cda60035fb11fa32bcddf10931f649`. GitHub `main` is the subsequent documentation merge `166c170`. The local checkout has the same tree as that merge. | Branch future work from current `main`; preserve the original tag, release, commits, and attribution. |
| Architecture | One FastAPI service, Python numerical rules, React/TypeScript presentation, prepared in-memory source context, optional constrained AI explanations. | Extend these boundaries; no service decomposition or database is needed. |
| Topology | 117,599 indexed paths; 40,779 pass complete validation. Complete reverse memberships cover 8,093 physical assets. | Reuse the validators and reverse index. Do not equate syntactic coverage with validated connectivity. |
| Scheduling | Four curated candidates, 28 distinct premise dependencies, two priority policies, one/two crews, separate people-per-crew controls. | Preserve this implementation as a named baseline and regression fixture. |
| Risk | An uncalibrated ordinal rule; probability is always null. | Keep it available unless a separately validated research model earns a narrower claim. |
| Restoration | Workbook effort multiplied by 4.5 once; conditional elapsed envelopes with unknown actual productivity. | Preserve person-hour semantics. Introduce simulation separately from these envelopes. |
| Data | 1,659 historical damage records; unusable outage/event identifiers, date-only report/repair fields, no verified outage controls or customer restoration outcomes. | Current challenge data remains unsuitable for supervised outage probabilities or empirical ETR calibration. |
| Customer experience | Existing schematic, generalized maps, preparation, session-only declarations, four communication previews, stale-response protection. | Improve the journey incrementally. |
| Offline support | Local services work without external tiles or AI. No standalone cached preparedness experience exists. | Add explicit preparedness caching and saved synthetic snapshots. |
| Distribution | Raw and processed challenge data remain in Git history; the publication audit records unresolved exposure and permission findings. No tracked CI workflow exists. | Isolate hosted artifacts from the repository’s data-bearing history; do not claim that hosting isolation remediates historical exposure. |

These findings agree with the [model specification](../MODEL_SPEC.md), [data audit](../DATA_AUDIT.md), and [published v1.0.0 release](https://github.com/its-spark-dev/GridGuide/releases/tag/v1.0.0).

**Checks rerun during the planning pass:** 194 Python tests passed; 49 browser tests passed; strict TypeScript/Vite build passed; generated API types matched; golden CLI scenarios passed; the complete source audit reproduced all four pinned hashes. No source files, commits, tags, or repository history were changed during that planning pass. These are dated baseline checks, not evidence that later phases are complete.

### Release boundaries

**Required:** evidence audit, reproducible benchmarks, dependency-aware optimization, synthetic uncertainty simulation, power-path improvements, offline preparedness, review/export workflow, CI, and an archival release package.

**Conditional:** county-level predictive research and empirical uncertainty evaluation, only where suitable observations exist.

**Excluded:** operational dispatch, switching recommendations, power-flow reconstruction, live utility integration, real alert delivery, arbitrary address lookup, multiuser operator accounts, inferred medical needs, paid-data dependencies, and browser duplication of the numerical engine.

## 2. Architecture and interfaces

### Preserve the core; introduce explicit execution modes

Keep one Python/FastAPI application and the existing React frontend.

Introduce two startup modes:

- **`challenge-local`**: explicitly selected, pinned challenge files required, current source validation preserved.
- **`synthetic-demo`**: default for the public package; independently authored fictional networks, customers, labor assumptions, and scenarios. No challenge files, source locators, real coordinates, or source-derived customer tables are required or loaded.

Synthetic fixtures must be generated from documented rules, not created by anonymizing or translating real customer records. Their topology is **valid by construction**, not “source-verified utility topology.”

Use a small adapter boundary around prepared scenario inputs. Extract reusable arithmetic and release calculations only where necessary; retain legacy wrappers and golden results. Do not pass synthetic inputs through contracts that automatically label them as verified challenge observations.

### Contract additions

Keep public Pydantic contracts centralized in [contracts.py](../../backend/contracts.py), with generated TypeScript.

Add versioned types for:

- **Scenario metadata:** mode, scenario ID/revision, input fingerprint, evidence lineage, model/policy versions.
- **Scheduling problem:** tasks, effort/duration assumptions, repair prerequisites, customer release groups, crew availability, blocked/unknown conditions.
- **Schedule result:** assignments, release milestones, objective values, feasibility, solver status, objective bound/gap, runtime, and unresolved scope.
- **Simulation result:** assumption-profile version, seed, trial count, conditional quantiles, unresolved/censored mass, and numerical convergence evidence.
- **Review/export record:** bound result and scenario fingerprints, comparison, review disposition, structured reasons, timestamp, and artifact checksum.
- **Offline snapshot:** synthetic results and settings only, creation time, application/model versions, and explicit historical-snapshot status.

Retain the existing six evidence classes. Add data-origin metadata separately; do not replace the evidence taxonomy with a single “verified” badge.

### API compatibility

Preserve current endpoint semantics in local challenge mode. Introduce a `/api/v2` surface for the new frontend:

| Interface | Responsibility |
|---|---|
| `GET /api/v2/scenarios` | List the allowlisted scenario catalog and capabilities. |
| `POST /api/v2/evaluate` | Evaluate a selected scenario through Python-owned calculations. |
| `POST /api/v2/plans/compare` | Compare policies under identical validated inputs. |
| `POST /api/v2/simulations` | Retrieve a matching, versioned simulation artifact for an approved preset. |
| `POST /api/v2/explain` | Render explanations bound to validated results. |
| `POST /api/v2/review-export` | Validate/recompute the selected plan and return a sanitized review artifact. |

Heavy benchmarks, model training, and Monte Carlo runs remain command-line workflows. The hosted application does not accept arbitrary datasets, arbitrary graphs, or training requests.

Extend health reporting to identify the active mode, artifact versions, and available capabilities. Synthetic hosting must never advertise challenge-source coverage.

Result IDs bind mode, inputs, versions, policies, and simulation configuration. Preserve cancellation, revision validation, sanitized errors, null states, and independent subsystem failures.

## 3. Phased implementation roadmap

Each phase has a separate review gate. Acceptance thresholds below are **prospective engineering requirements**, not claims of achieved performance. Proposed file paths below are implementation targets; a path being listed does not imply that it exists yet.

### Phase 1 — Dataset feasibility, evidence validation, and synthetic isolation

**Objective:** establish what can be measured, what remains hypothetical, and what can safely ship.

**Reuse:** source hashing and preparation, topology/reverse-membership validators, damage and facility matching audits, existing evidence classifications, and release privacy findings.

**Proposed files:** add `research/datasets.py`, `backend/scenarios.py`, and `data/synthetic/`. Extend existing contracts and startup dependency injection.

**Tasks and data prerequisites**

- Create a versioned dataset register recording source/version, checksum, access terms, schema, units, spatial/temporal resolution, observation process, missingness, and permitted claims.
- Reproduce topology and damage coverage, including rejection reasons and denominators. Keep overlapping failure categories explicitly non-additive.
- Produce separate feasibility decisions for outage risk, repair-task duration, customer restoration time, and aggregate outage recovery.
- Investigate a bounded public-data shortlist:
  - **ORNL EAGLE-I:** candidate county-level outage observations. Its documented data are county counts at 15-minute intervals, with coverage limitations; this does not supply premise identities or repair-task outcomes. [ORNL dataset](https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1), [data descriptor](https://www.nature.com/articles/s41597-024-03095-5).
  - **NOAA Storm Events:** retrospective event grouping and weather context. Event/episode identifiers are useful evidence, but reported events are not themselves outage labels or necessarily features available before an outage. [NOAA format specification](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf).
  - **DOE-417:** corroborating major-event context, not an all-customer exposure panel. [DOE reporting program](https://doe417.energy.gov/).
- Define optional partner-data requirements: stable event/asset identifiers, outage onset and restoration timestamps, observation coverage, verified negatives, crew assignments, task timestamps, and permitted use.
- Create independent synthetic scenarios covering a simple path, branching repairs, overlapping dependencies, blocked access, missing evidence, and synthetic critical-service dependencies.
- Keep new external caches and private prepared outputs ignored and outside `data/raw/`.

**Validation and acceptance**

- Every proposed model target has a documented unit, horizon, observation process, inclusion rule, and go/no-go decision.
- Every important input/rule has exactly one evidence classification.
- Synthetic startup succeeds with challenge files entirely absent.
- Synthetic results contain no inherited “AEP-observed” or “source-verified” claims.
- Existing challenge goldens remain unchanged.
- Public artifact inspection finds no challenge archives, processed customer tables, source locators, or real customer/facility geometry.

**Risks, fallback, and boundary:** spend at most four engineering days investigating external access and label feasibility before recording a no-go or bounded research protocol. Do not expand into indefinite data acquisition. Missing original challenge attachments remain documented; do not invent citations.

**PRs:** evidence register and feasibility report; then scenario isolation/contracts.

**Gate G1:** approve evidence boundaries and synthetic mode before new modeling.

### Phase 2 — Reproducible restoration scheduling benchmarks

**Objective:** establish a fair, independent measurement system before improving the scheduler.

**Reuse:** existing four-candidate plans, golden labor arithmetic, release-group set logic, and planning regressions.

**Proposed files:** add `benchmarks/scenarios.py`, `benchmarks/metrics.py`, and `scripts/run_benchmarks.py`.

**Benchmark definition**

For a complete scenario, minimize:

`modeled customer-outage hours = sum(n_g * T_g)`

Here, `g` is a disjoint customer group, `n_g` its size, and `T_g` the completion time of its last required repair. The clock begins at the common modeled response origin. This measures modeled waiting after that origin, not an observed outage’s full duration.

For blocked or incomplete scenarios, report restricted customer-hours through a fixed **168-hour scenario horizon**, unreleased customers, and unavailable full completion. Never omit unresolved groups to improve the score. Per the approval refinement, distinguish known completions beyond the horizon (censored for horizon reporting) from unknown completion, and never substitute this restricted measure for completed customer-outage hours.

Report separately:

- Makespan and time to 50%, 90%, and 100% conditional dependency release.
- Critical-service latency where dependencies are synthetic or explicitly verified; otherwise null.
- Customer-weighted median, p95, and maximum waiting time.
- Waiting time for small customer groups and branch-level disparities.
- Runtime, memory, feasibility failures, solver bound/gap, and timeouts.

**Required baselines**

1. FIFO by declared task-report order; synthetic ties use stable IDs.
2. Customer-count prioritization among ready tasks, without duration normalization.
3. Existing GridGuide release-per-person-hour policy.
4. Existing GridGuide critical-proxy-first policy.

All policies receive identical tasks, durations, crews, prerequisites, availability, and release groups. Real date-only reports do not acquire invented within-day FIFO order. Preserve exact legacy results separately from normalized benchmark adaptations.

**Scenario suite**

- Hand-computable cases of up to eight tasks with an exhaustive small-instance oracle.
- Six structural families: serial chain, independent branches, shared upstream bottleneck, overlapping customer dependencies, blocked prerequisites, and critical-service tradeoffs.
- Standard scale matrix: 10/25/100 tasks × 1/2/4 crews × five fixed seeds per family.
- Separate the challenge-backed regression results from fully synthetic performance results.

**Validation and acceptance**

- An independent validator detects precedence violations, crew overlap, double-counted customers, early release, missing tasks, and false finite completion.
- Every policy passes the same validator.
- Fixed manifests reproduce inputs and deterministic metrics.
- Reports contain every scheduled case, including ties, failures, and timeouts.
- Benchmark configurations are frozen before optimizer tuning; development and evaluation seeds are separate.

**Risks/fallback:** synthetic benchmarks demonstrate algorithmic behavior, not utility benefit. Poorly supported challenge cases remain regression evidence only.

**PRs:** problem/metric contracts and oracle; then baseline runner/report generation.

**Dependency:** G1. **Gate G2:** approve benchmark fairness before optimization.

### Phase 3 — Dependency-aware multi-crew optimization

**Objective:** improve the declared customer-hours objective while preserving feasibility and transparent limitations.

**Reuse:** complete reverse memberships, release groups, source ancestry, labor recipes, blocked-state handling, and existing policy implementations.

**Proposed files:** add `backend/scheduling.py` and `backend/optimization.py`; extend existing planning/API adapters.

**Implementation**

- Represent work as non-preemptive tasks assigned to one crew.
- Separate **repair precedence** from **customer energization dependencies**. Source ancestry supports the existing conservative upstream-first policy; it does not prove that physical repairs must always occur serially.
- Support one through four crews, each with two through eight people. Additional crews enable independent work; they do not divide one task’s duration.
- Model supplied crew/task availability explicitly. Unknown clearance remains unknown.
- Retain the AEP multiplier once. Do not add speculative travel or setup on top.
- Use OR-Tools CP-SAT with task intervals, crew non-overlap, prerequisite constraints, and group release times. Its integer constraints and distinct feasible/optimal statuses fit this bounded problem. [CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver), [scheduling constraints](https://developers.google.com/optimization/scheduling/job_shop).
- Use one-second scheduling ticks, rounding durations upward consistently for every compared policy. Preserve exact labor values and disclose quantization separately.
- Optimize customer-hours first, makespan second. Report critical-service and fairness metrics without silently adding policy weights.
- Seed the search with the best independently validated baseline schedule. Return a better validated incumbent or retain that baseline.
- Cap interactive cases at 25 tasks/four crews and two seconds of solver time. Larger runs use the offline benchmark runner.
- Pin solver version, seed, worker count, and deterministic search budget. Distinguish reproducible completed runs from wall-time-interrupted runs. Deterministic work and wall-clock response gates are separate requirements.

**Validation and acceptance**

- Match the exhaustive oracle’s objective on all small cases within the declared tick model.
- Zero feasibility violations across the frozen benchmark suite.
- Returned recommendations never worsen the primary objective relative to their best valid incumbent under identical assumptions.
- Timeouts, missing solver capability, infeasibility, and invalid outputs have tested baseline/unavailable fallbacks.
- “Optimal” appears only when proven for that specific encoded problem.
- Demonstrate strict improvement on preregistered cases where the baseline is suboptimal.
- Promotion target: at least 5% median improvement over the strongest baseline on the frozen synthetic evaluation suite, with a paired uncertainty interval excluding zero. Failure to meet this target produces an honest experimental result; it does not trigger benchmark redesign. This is a preregistered target, not a mandatory release outcome.

**Risks/fallback:** retain the best verified heuristic as the default if broad gains are weak or solver cost is excessive. Route optimization, skill certification, switching, and field dispatch remain outside scope.

**PRs:** generic scheduler/validator integration; then solver and comparisons.

**Dependency:** G2. **Gate G3:** approve correctness and measured results before UI recommendation changes.

### Phase 4 — Outage risk research with event-level validation

**Objective:** determine whether a defensible predictive task exists and publish a reproducible answer either way.

**Reuse:** current ordinal model, source-quality reporting, evidence taxonomy, and unavailable states.

**Proposed files:** add `research/risk/`, `docs/research/RISK_PROTOCOL.md`, and `docs/research/RISK_FINDINGS.md`.

**Prerequisites and implementation**

- Challenge data alone remains a supervised-learning no-go.
- Candidate public-data task: predict whether **reported county outages exceed 100 customers for at least one hour during the next 24 hours**. Label this as a county-level reported-outage target, not a household failure probability.
- Require adequate observation coverage across the target window. Missing records never become non-outage labels.
- Freeze geographic scope, source versions, target definition, feature availability, and exclusions before model fitting.
- Use 2018–2020 training, 2021 validation, and 2022 final testing for the documented EAGLE-I release, subject to the coverage gate.
- Group correlated storm episodes across counties. Purge overlapping feature/target windows and boundary-spanning events; use at least a 24-hour boundary embargo.
- Keep retrospective storm severity, damage reports, repair status, and future weather outside predictor inputs.
- Where publication latency cannot be verified, label experiments retrospective and withhold deployment/as-of forecasting claims.
- Compare seasonal/climatology and persistence baselines, regularized logistic regression, and one tree-based model. No broad hyperparameter search or deep-learning workstream.
- Fit preprocessing and calibration only on training/validation data.
- Add a held-out geographic evaluation to expose transfer limitations.

**Testing and acceptance**

- Automated tests prove no event/group overlap, future-feature leakage, duplicate leakage, or fit-on-test preprocessing.
- Report Brier score, log loss, PR-AUC, reliability diagrams, alert precision/recall, prevalence, and event-level uncertainty intervals. ROC-AUC is supplementary.
- Report results by geography, event severity, and observation coverage.
- Require at least 30 independent evaluation event clusters and both outcome classes before making a performance claim; this floor does not replace uncertainty analysis.
- A probability-model promotion requires positive held-out Brier skill with its 95% event-bootstrap interval above zero, no material log-loss regression, and acceptable reliability under the preregistered calibration check.
- Unsupported or inconclusive results remain research findings. Do not replace the customer concern band or label synthetic inference as validated ML.

**Stop conditions:** finish feasibility in three–four days. If feasible, cap the initial modeling effort at another six–ten days, two learned model families, and one frozen test evaluation. Do not tune against final test failures.

**Fallback:** publish the no-go report, missing-data specification, and executable validation protocol. This satisfies the release requirement.

**PRs:** protocol/data quality gate; then conditional experiments and findings.

**Dependency:** G1; metric/report tooling from Phase 2. **Gate G4:** evidence review determines permitted claims.

### Phase 5 — Probabilistic restoration simulation and uncertainty evaluation

**Objective:** quantify the implications of explicit assumptions without presenting invented distributions as observed utility behavior.

**Reuse:** scheduling constraints, customer release groups, exact effort calculations, and null handling.

**Proposed files:** add `backend/simulation.py`, `research/uncertainty.py`, and `benchmarks/simulation_profiles.json`.

**Implementation**

- Keep the legacy conditional envelope distinct from simulation quantiles.
- Create versioned synthetic duration profiles:
  - Deterministic reference.
  - Independent task variability.
  - Shared-event variability plus task variability.
  - Explicit synthetic storm-hold stress.
- Use documented lognormal duration multipliers with median one; initial log-scale standard deviations 0.25 and 0.5. For correlated trials, split log variance equally between shared-event and task effects.
- Apply multipliers to the explicitly selected elapsed-time assumption, not to an alleged measured efficiency.
- Model synthetic storm holds separately as a declared 0–4-hour uniform stress. Do not reinterpret that as observed clearance or add duplicate travel/setup.
- Keep unknown blocked clearance unresolved. A synthetic clearance experiment requires a separately declared scenario.
- Compare fixed, precomputed repair policies using common random draws. Schedulers cannot inspect future sampled durations.
- Run 2,000 trials per standard report case and 10,000 for convergence checks.
- Precompute approved public demonstration artifacts. The browser and public API do not launch unrestricted Monte Carlo jobs.

**Validation and acceptance**

- Seeded reruns reproduce results under the pinned numerical environment.
- Deterministic trials reproduce scheduler results.
- Release counts remain deduplicated and nondecreasing.
- Report p10/p50/p90 conditional completion, customer-hours distributions, interval widths, and unreleased/censored mass.
- Withhold finite quantiles where unresolved mass prevents their identification; do not drop unfinished trials.
- Convergence checks require reported quantiles to change by no more than the larger of 0.25 hours or 2% on designated finite fixtures; otherwise increase trials within the cap or mark them numerically unstable.
- Synthetic coverage tests verify implementation against known generating processes. Misspecification tests show sensitivity to different distributions and correlations.
- Empirical interval coverage, sharpness, and interval scores are evaluated only if compatible real outcomes pass Phase 1. County aggregate recovery cannot validate premise ETRs or task durations.

**Risks/fallback:** absent outcomes mean “assumption-based simulation,” never “calibrated restoration confidence.” If convergence or runtime fails, retain deterministic scenarios and publish the limitation.

**PRs:** simulation engine/profiles; then uncertainty evaluation/artifacts.

**Dependencies:** G2 and G3. **Gate G5:** approve uncertainty wording and numerical validation.

### Phase 6 — Customer power paths and offline preparedness

**Objective:** make dependencies, unavailable evidence, and preparation understandable without expanding unsupported claims.

**Reuse:** existing topology schematic, geographic context, preparation adapter, navigation, accessibility patterns, and request cancellation.

**Proposed files:** extract/add `frontend/src/PowerPath.tsx`, `frontend/src/offline.ts`, and `frontend/public/service-worker.js`. Extend the existing customer journey.

**Implementation**

- Add an interactive power-path view synchronized with selected repairs and server-owned release states.
- Visually distinguish intact assumptions, declared damage, blocked work, completed simulated repairs, and unresolved links.
- Keep abstract supply terminals unlocated; map lines remain geographic context, not inferred electrical edges.
- Provide an equivalent keyboard-operable ordered list and textual dependency explanation.
- Add a cached preparedness shell with reviewed generic safety content.
- Require an explicit “Save this demo snapshot” action. Save only synthetic settings/results, timestamps, and versions.
- Exclude declarations, tailored medical/accessibility guidance, contacts, real locations, challenge topology, and free text from persistent storage.
- In challenge-local mode, offline persistence is limited to the generic preparedness kit.
- Display saved results as historical snapshots immediately; age does not imply utility validity. Disable recalculation when the Python service is unreachable.
- Provide delete/reset controls and cache-version migration. Do not cache POST responses or external map tiles.

**Validation and acceptance**

- A saved synthetic snapshot and generic safety kit open after browser restart with all network access blocked.
- No new numerical results are calculated in the browser.
- Storage inspection confirms excluded fields never persist.
- Stale snapshots, schema upgrades, storage failures, and deleted data behave explicitly.
- Existing mobile, keyboard, reduced-motion, null-state, and stale-response tests remain green.
- Automated accessibility checks find no serious/critical issues in the changed flows; manual keyboard and screen-reader smoke checks are recorded.

**Risks/fallback:** failed storage still leaves printable/downloadable generic preparedness content. Offline availability is never described as live outage awareness.

**PRs:** power-path interaction; then offline preparedness/snapshot lifecycle.

**Dependencies:** G1 and stable v2 contracts; integrate G5 only where simulation is shown. **Gate G6:** customer/privacy review.

### Phase 7 — Operator comparison, human review, and auditability

**Objective:** make recommendations inspectable, reproducible, and explicitly subject to human judgment.

**Reuse:** restoration comparison UI, provenance ledger, grounded explanations, and scenario/result binding.

**Proposed files:** add `backend/review.py` and `frontend/src/OperatorReview.tsx`; extend the existing restoration decision screen.

**Implementation**

- Show policy comparisons using identical assumptions, including customer-hours, makespan, critical-service latency, fairness measures, runtime, and unresolved work.
- Show objective tradeoffs without calling one policy operationally safest.
- Require explicit review of unavailable evidence before marking a scenario “reviewed in demo.”
- Allow structured policy selection or additional precedence constraints. Recompute and validate overrides; reject cycles and crew conflicts.
- Record recommendation, chosen alternative, structured reason, scenario revision, evidence/model versions, and review timestamp.
- Export a sanitized JSON record plus readable summary. Include sufficient synthetic inputs to reproduce it.
- Keep review state session-local; exported artifacts provide persistence. No identity verification, durable multiuser workflow, or dispatch action is implied.
- Explain that checksums detect artifact changes; they are not authenticated signatures or tamper-proof audit infrastructure.

**Validation and acceptance**

- Exported synthetic cases reproduce objective values and release milestones.
- Changed settings invalidate prior review status.
- Stale result IDs, forged metrics, contradictory overrides, and cross-scenario explanations are rejected.
- Source-derived exports expose no private membership sets or source identifiers.
- Every recommendation identifies its policy, objective, assumptions, and feasibility status.
- Review buttons cannot change utility confirmation or send messages.

**Risks/fallback:** if review workflow complexity grows, retain comparison plus validated export; do not add accounts or a database.

**PRs:** artifact contract/replay; then review UI and override validation.

**Dependencies:** G3 and v2 contracts; G5 for uncertainty comparison. **Gate G7:** independent review/replay acceptance.

### Phase 8 — Responsible AI, privacy, CI, and hosted demonstration

**Objective:** continuously enforce the evidence boundaries and distribute a standalone synthetic application.

**Reuse:** strict reference-selection AI, server-rendered claims, safe validation errors, Python/browser suites, and source-integrity tests.

**Proposed files:** add `.github/workflows/ci.yml`, `scripts/package_demo.py`, and `deploy/`.

**Implementation**

- Start the synthetic CI lane immediately after Phase 1; expand it throughout development.
- Separate:
  - Public synthetic unit/contract/property/browser tests.
  - Authorized challenge-source regression tests.
  - Slower benchmark/research jobs.
- Missing challenge data must be reported as an unexecuted source-dependent suite, never counted as passed.
- Add meaningful generated-case tests for graph validity, crew exclusivity, release deduplication, null propagation, and schema rejection.
- Check generated-type drift, pinned dependency installation, build, artifact contents, secrets, dependency findings, and source-hash preservation.
- Extend AI tests to reject invented optimality, simulated quantiles represented as confidence guarantees, fabricated facility attachment, and claims of observed restoration.
- Keep Standard explanations fully functional. Disable external AI by default in the archived and hosted demo.
- Build a deployment artifact using an explicit allowlist. Never use a broad repository copy that includes `.git`, raw/processed data, research downloads, or `.env`.
- Serve the compiled frontend and API from one origin in one container, with immutable prepared synthetic files.
- Enforce request size limits, bounded scenario catalogs, calculation concurrency limits, sanitized errors, and no request-body logging.
- Keep external tiles off by default for the fictional demonstration.

**Validation and acceptance**

- A clean synthetic package installs, starts, and completes the journey without challenge data or provider credentials.
- The published image/archive passes a recursive contents scan.
- Public CI exercises the production synthetic application, not a frontend-only mock.
- Golden challenge tests still pass locally.
- Interactive planning meets the two-second solver cap and five-second end-to-end response budget on the documented reference host, or returns the tested fallback.
- Release has no unresolved critical security/privacy defect in its distributed scope; remaining findings are explicitly dispositioned.
- Hosted outage and cold-start behavior are tested against the offline kit and local fallback.

**Risks/fallback:** cap hosting-specific troubleshooting at three engineering days after packaging works locally. If no practical host is available, release the same local container/package, demonstration recording, screenshots, and benchmark reports. No hosting subscription is a release dependency.

**PRs:** early CI foundation; later privacy/AI expansion; finally packaging/hosting configuration.

**Dependencies:** begins after G1 and continues across all phases. **Gate G8:** artifact and deployment review.

### Phase 9 — Final reports, demonstration, and preservation release

**Objective:** leave a coherent project that another engineer can understand and reproduce after active development ends.

**Reuse:** v1.0.0 release structure, verification records, source attribution, screenshots, and requirements traceability.

**Proposed files:** add `docs/releases/v1.1.0.md`, `docs/benchmarks/v1.1.0.md`, and `docs/REPRODUCING_V1_1.md`.

**Tasks**

- Publish the complete benchmark manifest, machine-readable results, report-generation commands, reference hardware, dependency locks, and solver settings.
- Separate four evidence categories in the final report: regression correctness, synthetic optimization performance, simulation sensitivity, and real-data predictive findings.
- Include unsuccessful experiments, timeouts, scope exclusions, and no-go decisions.
- Update architecture, model specification, requirements traceability, and risk register.
- Preserve teammate guidance and pole-replacement attribution. Do not infer missing contributor identities or change project licensing without the relevant agreement.
- Record a concise demonstration:
  1. Select a fictional location and inspect its power path.
  2. Explain the concern band and conditional timing.
  3. Compare FIFO, customer-count, legacy, and optimized schedules.
  4. Change crews and block an upstream task.
  5. Inspect uncertainty and unresolved mass.
  6. Review/export the selected plan.
  7. Open the saved preparedness snapshot offline.
- Produce authentic screenshots and a recording from the release candidate.
- Align application/package release versions to v1.1.0 while preserving numerical-model version identifiers.
- Provide a checksum manifest, third-party notices, local startup instructions, and a maintenance/end-of-development statement.

**Acceptance**

- A fresh environment reproduces the synthetic journey and standard benchmark report from the documented package.
- A reviewer can trace every headline metric to a manifest and result artifact.
- v1.0.0 tag/commit identity and existing history remain unchanged.
- No predictive, calibration, operational, deployment, or safety claim exceeds its evidence.
- All required gates pass; conditional research concludes with either supported results or an explicit no-go.
- Final PR approval precedes tagging/publishing. The planning task does not authorize those actions.

**Fallback:** hosting may be absent; reproducible local artifacts, reports, and demonstration evidence may not be absent.

**PRs:** reports/documentation; then release-candidate verification and packaging.

**Dependencies:** G1–G8, with G4 satisfied by a valid research disposition. **Gate G9:** release approval.

## 4. Dependency graph, milestones, and execution order

```text
P1 Evidence + synthetic isolation
 ├── P8a Synthetic CI foundation
 ├── P2 Benchmark specification + independent validator
 │    └── P3 Multi-crew optimization
 │         ├── P5 Restoration simulation
 │         └── P7 Operator comparison/review
 ├── P4 Conditional outage-risk research
 └── P6 Power-path + offline preparedness

P5 ──> uncertainty integration in P6/P7
P2–P7 ──> P8b Final privacy/security/package validation
P4 findings + P6 + P7 + P8b ──> P9 Reports, demonstration, release
```

**Critical path:** evidence/contracts → benchmark validity → scheduler correctness → simulation validation → integrated review experience → distribution validation → release evidence.

Prediction research runs alongside this path and terminates with a documented decision. Hosting is also non-blocking because local distribution is an accepted fallback.

| Milestone | Completion evidence | Estimated engineering effort |
|---|---|---:|
| M1: Evidence and isolation | G1; synthetic application boundary established | 6–8 days |
| M2: Measurement foundation | G2; baselines, oracle, frozen manifests | 5–7 days |
| M3: Scheduling improvement | G3; feasibility and benchmark results | 8–12 days |
| Research disposition | G4; no-go or approved experiment | 3–4 days, plus 6–10 conditional |
| M4: Uncertainty | G5; reproducible simulation and sensitivity report | 6–9 days |
| Customer completion | G6; power path and offline kit | 5–8 days |
| Operator completion | G7; review/export replay | 4–6 days |
| M5: Distribution readiness | G8; CI and isolated package | 5–8 days |
| M6: Preserved final release | G9; reports, reproduction, demo | 4–6 days |

**Total:** approximately **46–68 engineering days**, plus **6–10 days** if predictive modeling passes feasibility. These are provisional effort estimates, not a calendar commitment; review waits and optional partner access are excluded. Recalibrate after each phase without treating elapsed agent time as measured human engineering days.

Recommended execution order: **P1 → P8a → P2 → P3 → P5 → P7 → P8b → P9**, with P4 and the independent parts of P6 progressing alongside stable contracts.

Use small, dependency-linked PRs. Each PR must include its evidence classification changes, relevant tests, before/after results, and limitations. Shared contract changes receive review before dependent frontend work. No phase may silently redefine an earlier benchmark or evidence gate. The latest owner instruction narrows the current execution authorization to Phase 1 and its focused PR only.

## 5. Scope control and final release decision

Freeze v1.1.0 around the nine phases above. A new feature enters only if it replaces planned work or resolves a demonstrated acceptance failure.

Apply these stop rules:

- **Data:** stop acquisition research at the feasibility budget; publish missing prerequisites.
- **ML:** stop after the bounded model comparison and frozen evaluation; retain negative or inconclusive findings.
- **Optimization:** retain the best verified baseline when improvements are weak; do not select easier benchmarks.
- **Simulation:** publish assumptions and numerical limits when empirical validation is unavailable.
- **Hosting:** use the local package after the hosting troubleshooting cap.
- **Topology:** preserve unresolved cases; do not weaken identity or reverse-membership validation to increase coverage.
- **Feature freeze:** after integration gates pass, accept only correctness, privacy, accessibility, reproduction, and documentation fixes.
- **History:** never retag v1.0.0, rewrite history, remove teammate work, or present synthetic hosting as remediation of existing repository exposure.

The final release succeeds when its strongest claims are independently reproducible: **the schedules are feasible, comparisons are fair, uncertainty is honestly characterized, evidence gaps remain visible, and the customer/operator journey works without private data or external AI.**
