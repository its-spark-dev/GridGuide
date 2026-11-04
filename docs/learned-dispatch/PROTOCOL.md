# Learned Adaptive Dispatch v1 — prospective distillation protocol

Registered before new scientific inputs, teacher labels, model fitting or final outcomes.
Base main: `740e7ec03c618b9bcb73f0c11a7ccc63a5eb5de9`, merged PR #20.

## New question and mandatory engineering completion

Can a learned state/action ranker approximate conditional-support-median online search
with lower decision cost and acceptable complete-episode scheduling quality on unseen
fictional problems? This is a new policy-distillation experiment. It neither reopens nor
changes PR #20's failed eight-future teacher-headroom hypothesis. Its revealed cases are
historical evidence, not new blind tests. ML I's trained policy selector and ML II's source
audit likewise remain unchanged. No observed utility calibration or operational dispatch
claim is introduced.

**Training and working learned inference are mandatory regardless of performance.**
Fit and retain both linear and tree families, actual learned parameters, public-state
inference, complete student rollouts, all failures and reproducible evaluation. Promotion
is a separate scientific decision. A failed development or final gate never authorizes
stopping before these engineering deliverables. No RL, dashboard integration, deployment,
automatic merge, tag or release is part of this study.

## Isolation, reuse and new data

New code lives in `research/learned_dispatch`; documents/evidence in `docs/learned-dispatch`.
Import the unchanged PR #20 event environment, median teacher, eight-future reference,
reactive rules, fixed-order replay, and independent trajectory/G2 metric validators.
Reuse the audited ML I DAG generator through a separately versioned adapter. Do not edit
any of those historical packages or their sealed evidence. Generic canonical artifact I/O
and offline access guards may be imported unchanged.

Create 48 training, 16 development, 24 final-ID and 24 shifted **configuration groups**.
All related tasks, memberships, crew variants, profiles, episode draws and decision states
remain in their configuration's partition. Train/dev/ID use random-ordered, layered,
bottleneck and modular graphs with 10–14 tasks, 8–16 customer groups, and 2/3-crew variants.
Shift uses preferential/deep-sparse graphs, 18–24 tasks, 12–20 groups and 1/4-crew variants.
Shift deliberately combines topology, scale and crew regimes; it cannot identify a single
cause of generalization failure. Known effort, group sizes/overlap, report order and crew
availability vary through committed generation configurations. Crews have four people and
the existing one-effective-worker duration convention; crew count never divides serial work.

The primary cohort has complete known scope. Ensure at least one declared critical group
per configuration: retain generated flags; if none exist, explicitly flag the first group.
This is an authored scenario assumption, not facility inference. Blocked/missing/unresolved
cases are separately labeled inference/validation stress fixtures, not finite learning targets.

Use new master/configuration/episode namespaces. Reject cross-group topology signatures
and signatures in both published PR #20 and ML I manifests. Document conservative color
refinement's limitations: rejection does not prove semantic independence of all graphs.
Record seeds, complete configurations, eligibility, input fingerprints, source revisions,
partition identities and actual counts. Commit final inputs **before any model fitting**.
Input-only validation may inspect final structure; training/demonstration commands may not
open final examples or outcomes. No final teacher labels exist before the frozen reveal.

Retain PR #20's declared deterministic/low/high duration supports unchanged. They are
fictional assumptions. Median search uses a deterministic conditional-support median
(upper median for even support), not an episode's actual future. The eight-future reference
uses its existing distinct public-state hypothetical namespace. Environment draws are
private and common across policies for identical case/profile/episode inputs.

## Teacher demonstrations and target

Per training case: one deterministic teacher trajectory, plus two episodes for each low/high
profile. Stochastic episode 0 follows the teacher; episode 1 follows a predetermined action
mixture: 60% teacher, 30% downstream/time, 10% critical-first, keyed by a separate behavior
namespace and decision index. Label every visited decision using the median teacher,
regardless of which behavior action is executed. No student-driven aggregation or RL.
This yields 480 training trajectories before counting states; smoke uses a separate namespace.

For each state preserve public current time, completed assignments, active starts/elapsed
time, available crews, ready/unfinished tasks, public static-input reference, every legal
action, teacher action, teacher tie set, behavior action and configuration/state lineage.
Lineage is audit metadata only. No actual future duration, private event queue, episode
outcome, hypothetical future outcome vector or environment seed enters feature extraction
or the teacher callback. Static problem seeds are stripped at the public observation boundary.

The existing `action_values(state, median=True)` supplies genuine **median-rollout** costs:
for each candidate root action, the minimum complete customer-hours across four reactive
continuations in the declared hypothetical median world. These are not calibrated expected
costs or actual episode outcomes. The target is excess teacher cost above that state's best
action, divided by customer count and mean nominal duration in hours. Thus the supervised
target is dimensionless action regret within the teacher's approximation. Lower is better.
One-action states have an exact action label but no fitted cost-regression row; do not invent
an uncomputed cost-to-go value.

Available identical crews are interchangeable. The teacher evaluates a canonical idle crew;
record every legal action and map other idle-crew aliases to its corresponding task cost,
with explicit equivalence metadata/tests. Student features contain no crew identity. Stable
ties choose assignment before WAIT, then lexical task and crew IDs, matching the teacher.
Tie-aware agreement accepts any minimum-cost task/WAIT, including equivalent crew aliases.
Cost ties use absolute tolerance 1e-12 customer-hours. Report forced decisions separately,
WAIT/teacher-action imbalance, duplicate public states, valid-action counts, and visited-state
coverage. Deduplicate exact public states within a configuration for fitting, preserving all
visitation counts/lineage; do not deduplicate across partitions using final observations.

## Features and model families

The versioned feature schema is an explicit numeric allowlist committed before fitting.
It covers elapsed time and completion progress; task/crew/ready/active/idle counts; remaining
customer mass and known work; graph depth/ancestors/descendants and bottlenecks; task duration,
direct/downstream/marginal customer and critical impact; unfinished dependency overlap;
active elapsed and conditional expected remaining durations; future known crew arrivals;
WAIT and relevant duration/impact/progress interactions. Use normalized structural ratios
and explicit units. WAIT has an indicator and zeros for absent task-specific quantities,
not invented repair characteristics. All values derive from legitimate public information.
Names, exact definitions and ordering will be recorded in the feature schema artifact.

Exclude IDs, hashes, generator seeds, partition/family labels, selected teacher actions,
teacher costs, actual remaining durations and post-action metrics. Features accept only a
validated public observation and legal candidate. Validate static structure once per immutable
static-context cache and dynamic consistency on every callback; timing includes both cold
validation and cache accesses. No transforms are fitted on development/final inputs.

Train five candidates using pinned scikit-learn 1.7.2 / existing `requirements-ml.lock`:

- Standardized Ridge regression, alpha in {0.1, 1, 10}, explicit cholesky solver.
- RandomForestRegressor, 64 trees, max_depth in {4, 8}, min_samples_leaf=5,
  max_features=1.0, bootstrap=True, random_state=2026110404, n_jobs=1.

Use weighted squared error. Each configuration has equal total fitting weight; within it,
each unique discretionary state has equal weight; within each state, legal actions have
equal weight. Rescale sample weights to mean one. Ridge scaling uses training rows/weights
only; forest uses finite raw features. This prevents large action sets or long trajectories
from silently dominating the objective. No target imputation, neural model or adaptive search.
Fit every candidate twice and compare learned exports/predictions within 1e-10; record exact
bytes where obtained. Report true fitted coefficients/impurity importance without causal claims.

Export the actual fitted scaler/linear coefficients or tree split/leaf arrays to strict
versioned JSON. Do not deserialize pickle/joblib. Verify exported predictions against fitted
scikit-learn on train/dev feature batches within 1e-10; tree inference preserves scikit-learn's
float32 feature comparisons. Bind artifact SHA-256, feature schema, training/input/source
identities, hyperparameters and environment in an approved local inventory. Validate array
sizes, finite values, feature indices and acyclic tree structure at load; cap artifact size.

## Inference and complete development rollouts

Expose an optional isolated callable policy and `score(public_state, candidate_action)`.
Enumerate/mask legal actions before scoring. Return the minimum predicted teacher-regret
action with the explicit tie rule. Evaluate WAIT only when legal. A valid unsupported scope
or inference failure falls back to deterministic downstream/time and records the reason.
Malformed public states are rejected because no safe feasible action can be certified.
Corrupt/unapproved models fail hash/schema loading; any explicit no-model fallback remains
clearly identified as non-learning. No automatically enabled production ML dispatcher.

Development: one deterministic and two episodes per stochastic profile per case (160 episodes
per method). Compare all five students with fixed-order release/effort, reactive downstream,
median teacher and eight-future search. Select each family winner and overall champion by
mean normalized customer wait on **stochastic complete student rollouts**, equally weighting
configuration means. Tie within 1e-9 hour by candidate ID. Do not select by action agreement,
latency, final outcomes or recommendation preference. Retain all fitted artifacts regardless.

Record exact/tie-aware agreement on visited discretionary student states (teacher queries
occur outside measured inference), invalid actions, fallback counts/reasons, waiting cost,
p95 wait, maximum critical-group latency, branch disparity, disagreements and worst cases.
Measure callback wall and CPU times including validation, enumeration, features and inference;
report discretionary median/p95, summed full-episode decision CPU, model load, fit and total
experiment time, artifact bytes and peak memory. Separate the same stochastic cohort for
quality and primary latency comparisons; deterministic timing/results remain separate.

## Freeze, final evaluation and promotion

Commit the chosen family models/champion, schema, preprocessing, artifacts, input manifests,
evaluation source, environment and criteria before reveal. Final ID and shift each use one
deterministic plus four episodes per stochastic profile per case: 432 episodes per method,
including 384 stochastic episodes / 24 groups. Evaluate both frozen family winners plus all
four preselected baselines on identical exogenous draws. The champion is never reselected
after final outcomes. Model artifacts remain available even if every scientific gate fails.

An exclusive receipt spends the final cohort before any final teacher/student evaluation.
Per-configuration immutable shards permit resumable execution under the same receipt/freeze;
resume processes only unfinished shards, never makes a new model-selection opportunity.
Preserve failures. A completed final invocation cannot be rerun as new evidence; a separate
read-only audit verifies old results and optional exact policy replay. Training against the
spent scientific workspace is rejected. This is procedural isolation, not an external blind test.

Primary comparisons average both crew variants, profiles and episodes within configuration.
Use 2,000 paired configuration bootstrap resamples, seed 2026110404. Report ID and shift
separately. For **both** cohorts, promote the preselected champion only if all hold:

1. Teacher/student ratio of mean configuration-median discretionary wall times >=3,
   and its paired-bootstrap 95% lower bound >=3. Also report pooled callback medians.
2. Mean waiting-cost ratio student/teacher <=1.02 and paired-bootstrap 95% upper bound <=1.02.
3. Mean student waiting <= reactive downstream, and the paired 95% upper bound on mean
   degradation <=1% of reactive mean (a predeclared noninferiority margin).
4. Mean critical maximum and mean episode p95 degradation versus teacher, including their
   paired 95% upper bounds, are <=max(0.25h, 5% of teacher mean).
5. No invalid scheduled action and zero fallback in the complete-scope primary cohort.
   At least 20 supported configuration groups for cost, 12 for critical/speed and at least
   200 discretionary timing observations per policy. Unsupported guards do not pass.
6. No configuration's mean waiting exceeds 1.25× its paired teacher mean, and no episode
   exceeds 2× teacher waiting. These are explicit catastrophic-generalization screens,
   not a guarantee for every possible customer or future distribution.

Do not tune, refit, change thresholds or silently discard cases after reveal. Report failures,
effect sizes, paired intervals, individual/family regressions and limitations. A future study
requires a new protocol and fresh evaluation cohort; this study still delivers trained models.

## Resource and delivery bounds

CPU only, one worker/numerical thread, target <2 GiB process RSS and <30 minutes per command.
Generate/evaluate in immutable configuration shards; bounded final commands may process four
configurations each and resume the same sealed invocation. Splitting commands changes no
case, seed or estimator. Document any material budget amendment before affected scientific
evaluation; never use unfavorable outcomes to reduce the cohort. Smoke has separate small
configuration/episode namespaces and no scientific claims.

Tests cover teacher labels, public-state validity, hidden-future interventions, feature
allowlists and identity invariance, split/duplicate isolation, WAIT masks, real fitting,
serialization/export equivalence, bad hashes/models, deterministic inference, fallback,
complete trajectories, repeat fitting, spent-cohort guards, exact inputs and figure replay.
Run applicable existing tests and frozen preservation checks. Add bounded source-free CI
with genuine smoke training and rollout evaluation; full training remains reproducible
separately. Deliver protocol/feature/data dictionaries, manifests, actual JSON models,
freeze/receipt/results, runnable inference example, polished static figures/report,
phase ledger, preservation audit and one unmerged PR. No performance win is required.

Technical references: [Ridge 1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.Ridge.html)
and [RandomForestRegressor 1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.RandomForestRegressor.html).
The pinned installed source is additionally checked for export/inference behavior.
