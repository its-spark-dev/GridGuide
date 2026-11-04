# ML Lab implementation protocol — 2026-11-04

Status: preregistered implementation plan, before dataset policy labels or model fitting.
Design baseline: PR #17, reviewed against the frozen benchmark contracts and merged
with merge commit `83d34dd54281140410dde3ef5eeaa00a4718900d`. Its PRD remains verbatim.
The owner's November 4 implementation brief authorizes phases through delivery; it
supersedes the proposal's approval pauses. No final PR merge, tag or release is authorized.

## Amendments and architecture

This is a separate offline `research/ml_lab` package. The unchanged `BenchmarkProblem`
is wrapped in a versioned ML case carrying actual generator lineage and partition.
Its legacy generator/split literals are compatibility fields, not ML provenance.
The existing four policy functions, tick arithmetic, metrics and independent validator
are imported unchanged. No API, UI, AEP source, distribution package or historical
G2/G3/G4/G5 evidence changes. The required portfolio is a static research page;
interactive UI is deliberately omitted to preserve runtime and package boundaries.

The current brief makes majority selection and all three model families mandatory,
and strengthens the procedural holdout seal and static showcase requirements.
These are prospective refinements, not retroactive experimental claims.

## Data and prediction contracts

One prediction selects one of four existing policy IDs for a complete fictional
problem. The model never returns a schedule or predicted restoration time. Scheduling
and independent validation remain separate. Missing/blocked task scope or unknown
customer dependencies cause abstention; there is no restricted-horizon learning task.
Known full completion beyond 168 hours remains eligible for the full-outcome task;
known-later censoring and unresolved mass are reported separately.

New generator: four mechanisms (random ordered DAG, layered DAG, bottleneck DAG,
modular DAG), 30 train + 10 development + 10 final-ID configurations per mechanism.
Each configuration has three related crew variants (1, 2, 4): 360/120/120 cases.
Two shifted mechanisms (preferential attachment and deep sparse DAG), 20 configurations
each, three crew variants: 120 final-shift cases. Total: 720 cases / 240 groups.
ID task counts 10–36; shifted task counts 40–64. Every configuration fixes topology,
customer dependencies, effort distribution, report ordering, criticality and missingness;
related crew variants stay in one partition. Input-only integrity/eligibility checks
occur before labels. Exact duplicate and conservative ID-invariant topology signatures
must not cross groups. This is procedural separation, not an externally independent
blind test, and signature checks cannot prove absence of all near-isomorphic similarity.

Historical G2 is inspected background only. New training, development, final-ID and
structural-shift evidence are separate and never pooled into an advertised test score.
All synthetic inputs are scenario assumptions; scheduling/feature/selection rules are
prototype policies; actual productivity and observed utility outcomes are unavailable.

## Features and labels

Only static numeric task/crew counts, effort moments/quantiles, graph depth/width/degree,
bottlenecks, ancestor summaries, group-size distribution, dependency overlap, crew
availability, report-order association, critical-service and missing/blocked indicators.
The exact ordered schema and per-feature provenance are frozen before model fitting.
IDs, seeds, family names, partition markers, hashes, labels, schedules and policy metrics
are forbidden predictors. Train-only imputation/scaling lives inside each fitted pipeline.

All four policies run on identical inputs. Their schedules and complete metric objects
must pass the independent G2 validator. Label comparisons use integer customer-seconds;
all minimum-cost ties are retained, with lexicographic policy-ID class tie-breaking.
Eligibility additionally requires complete scheduled task scope for all four policies.
No missing target is imputed. Best fixed policy minimizes training total cost, majority
uses training class counts; both use policy-ID ties. A predeclared structural heuristic
uses customer-count when mean group dependency count exceeds 1.5, otherwise release/effort.
The hindsight minimum of these four policies is only an unattainable reference.

## Models, search and selection

Python 3.12, isolated pinned scikit-learn 1.7.2, NumPy 2.2.6 and SciPy 1.15.3;
CPU only, single-threaded numerical libraries, seed 20261104. Multinomial logistic
regression: C in {0.1, 1, 10}, lbfgs, max_iter=3000, standardized features.
Random forest: 160 trees, max_depth in {4, 8, null}, min_samples_leaf=3, n_jobs=1.
Gradient boosting: 100 trees, learning_rate in {0.03, 0.1}, max_depth=2.
No class balancing, threshold search, neural models or cost regression in this study.

Three-fold GroupKFold on training configuration IDs reports out-of-fold regret and
accuracy for every configuration. Fit each candidate on all training rows, then select
lowest mean absolute development regret within each family (lexicographic candidate ID
tie-break). Report all eight candidates; choose the strongest learned candidate on that
same development objective. Recommended champion is that model only if strictly better
than fixed on development; otherwise fixed remains champion. Never refit on development.
Record training class counts/ties, coefficients or feature importances and disagreements.
Two deterministic fits must reproduce predictions and learned numeric state within 1e-10.

## Predeclared evaluation and acceptance

Primary: mean absolute selection regret, customer-hours, relative to best-of-four on
common eligible cases. Report mean/median/p95 absolute and relative regret (epsilon
1 customer-second = 1/3600 customer-hour), exact/tie-aware accuracy, coverage/abstention,
completed cost, and restricted cost as a separate descriptive outcome. Zero-cost oracle
cases remain visible. Baseline zero regret makes percentage improvement untestable.
Report per mechanism and scale (10–20, 21–36, 40–64), confusion matrices, ties,
selection frequencies, worst errors, critical-service maximum latency, branch mean
disparity and small-group waits with paired nonnull support counts.

Success gate on final-ID: at least 5% lower mean absolute regret than fixed, with a
strictly positive fixed regret; the 95% grouped bootstrap interval for mean paired
regret improvement must exclude zero; mean critical-service maximum latency and mean
branch disparity may each increase at most 0.25 hour on paired supported cases.
No supported critical cases makes the corresponding guard unverified, not passing.
OOD uses the identical gate separately; never infer transfer from ID success.
Bootstrap 2000 resamples of complete configuration groups, seed 20261104, retaining
crew variants; uncertainty is conditional on authored mechanisms, not utility populations.
No multiplicity-adjusted significance claim for exploratory candidate/subgroup contrasts.
A scientific failure does not block engineering delivery or justify changing the gate.

## Stage A / Stage B protection

A: validate and write immutable input manifests with generator revision, source hashes,
seeds, configurations, fingerprints and partition hashes. Commit the final input manifest
before training. Training may load only train/dev partitions; final labels do not exist.
Freeze all model artifacts, parameters, feature schema, input seal, environment,
acceptance criteria and evaluator source hashes in a committed selection manifest.

B: require the committed seal and frozen model/code hashes; exclusively create an
invocation receipt before computing any final label. A second evaluation invocation
refuses to run, including after a failed attempt. Preserve failure receipts. A distinct
read-only audit replay verifies existing evidence; it is not another model-selection
opportunity. Final results never feed fitting commands. These controls are auditable
workflow protections; a repository author could deliberately bypass them, so this is
not a third-party blind test. No final performance data may change model/gate choices.

## Budget, checks and deliverables

Bound: 720 full cases, eight candidates × three CV fits plus full fits and reproducibility
replay; 100/160-tree limits as above; no GPU/network during experiments. Target <2 GiB
peak memory and <30 minutes per full command; stop and record a resource blocker if
these bounds prevent a defensible run. No performance-triggered generator redesign.
Smoke uses a distinct small profile and must never touch the scientific final receipt.

Phase gates: (0) architecture/design review; (1) deterministic input validation and
split/hash integrity; (2) independently checked labels/features/baselines; (3) trained
models and deterministic replay, committed freeze; (4) one-time final + audit replay;
(5) reproducible static figures and README; (6) existing/new tests, diff review and CI.
Each gate is recorded in `docs/ml-lab/evidence/phase-ledger.json` with actual commands,
results and issues. Implementation commands will be documented exactly as built.

Deliver: generator/data dictionary, input manifests, feature schema/provenance, validated
training labels, candidate/CV/development results, model artifacts/freeze, final receipt,
per-case final errors and aggregate report, runtime/environment measurements, research
figures, public README integration, independent review and scoped source-free ML CI.
Primary entry point: `python -m research.ml_lab` (prepare/train/freeze/evaluate/audit/report).
New tests: `python -m unittest discover -s research/ml_lab/tests -v`.
Existing checks: public/challenge/research lanes where dependencies/sources available,
frozen artifact verification, frontend build and established GitHub Actions unchanged.
