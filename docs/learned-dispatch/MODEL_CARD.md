# GridGuide learned adaptive dispatch v1 — model card

## Purpose and status

An optional research policy scores feasible task/crew assignments and meaningful WAIT
actions from a validated public fictional restoration state. It imitates the existing
conditional-support-median search policy. It is not outage prediction, utility dispatch,
an estimated restoration time, an operational recommendation or reinforcement learning.
The existing application does not enable it.

Engineering success means the model was genuinely fitted, serialized, loaded and evaluated
through complete episodes. Scientific promotion is a separate, preregistered quality and
computation test; see the [measured report](presentation/REPORT.md). Retaining a working
model does not imply it passed that test.

## Model identity

Development selected **forest-depth4**: `RandomForestRegressor`, 64 trees, maximum depth 4,
minimum leaf samples 5, all 46 candidate features available at each split, bootstrap sampling,
seed 2026110404 and one worker. Training uses configuration/state/action weights. Its
211,281-byte portable JSON artifact has SHA-256:

`8280d3929a316c61bd5f93ef15610d891e0bf2e6cc80b8d9fb262f66cc097e52`

The retained linear-family winner is **ridge-alpha10**, with weighted train-only
`StandardScaler` preprocessing and Ridge alpha 10, cholesky solver. Its 16,869-byte JSON
artifact has SHA-256:

`046911f68c01541474f8b6606b3ceac67ebcae2a51e87f82c4ad3f13e257ef01`

Also retained: Ridge alpha 0.1 and 1, and the depth-8 forest. All five candidates and their
exact SHA-256 values appear in the [approved inventory](evidence/training/training.json).
The [freeze](evidence/freeze.json) identifies family winners and the champion before reveal.

## Learning task and data

- 48 new training configurations, with two/three-crew variants kept in the same group.
- 480 trajectories: 288 pure-teacher and 192 predetermined mixed-behavior trajectories.
- 12,980 public decision visits; 12,055 unique states after within-configuration deduplication.
- 5,352 unique discretionary states, giving 24,240 legal-action rows and 46 numeric features.
- Genuine target: excess median-teacher rollout customer-hours divided by customer count
  and mean nominal task duration in hours. This is a dimensionless approximate cost, not
  observed future loss or a calibrated expectation.
- Forced decisions retain action labels but contribute no invented cost target or fit row.
- Teacher labels may tie; equal-composition idle-crew aliases have equivalent task costs.
- Every configuration has equal total weight; then every discretionary state and each of
  its legal actions receives equal weight within its parent. Duplicated visits add no weight.

Inputs are independently authored fictional DAG/customer scenarios, generated through a
new adapter over ML Lab I's generator. No AEP raw data or observed outage labels are used.
Graph signatures are disjoint from 276 published ML I/PR #20 signatures and from other new
configuration groups. Conservative color refinement is not proof of semantic independence.

Sixteen development groups select candidates using complete stochastic student rollouts.
Final-ID and shift each contain 24 fresh groups, 48 variants, and 432 episodes per method
(384 stochastic). The shift jointly changes topology, task scale and crew count, so it cannot
attribute a failure to one factor. Final inputs were sealed before fitting; models/code and
thresholds were committed before the once-only reveal. This is procedural isolation under
developer control, not external blind testing.

## Inference boundary

Features describe progress, known effort, prerequisites, downstream and marginal customer
release, critical declarations, ready/active/idle counts, observed active elapsed time,
conditional expected remaining time and WAIT. No ID, seed, split, teacher score, environment
private duration or post-action result is a feature. Exact IDs only join known entities and
break ties. [Ordered definitions and units](feature-schema.json).

`LearnedPolicy` enumerates legal actions, predicts approximate costs, and chooses the minimum.
The public `score` method returns negative predicted cost so higher priority is better.
Assignments precede WAIT on exact ties, followed by lexical task and crew IDs. A validated
unsupported scope or numerical prediction failure records an explicit deterministic
downstream/time fallback. Malformed observations and corrupt/unapproved models are rejected.

Supported scope: complete executable inputs, no unresolved customer dependency, at most 64
tasks, one to four identical-composition crews, current time ≤10^12 ticks and nominal task
duration ≤10^9 ticks. These are interface policies, not utility limits. The scientific data
fix four people per crew with the existing one-effective-worker duration convention; adding
crews never divides serial task work. [Full boundary contract](INTERFACES.md).

JSON exports contain actual fitted scaler/coefficient or split/leaf parameters. Loading
requires an expected SHA-256 and strict structural validation, including finite arrays and
bounded acyclic trees. No pickle/joblib deserialization, remote model service or credential
is used. Forest comparisons reproduce scikit-learn's float32 input comparisons. Export parity
is tested within 1e-10 on training and independent development-state probes; all five repeated
fits produced byte-identical exports in the pinned recorded environment.

## Limits and interpretation

The teacher itself is approximate: one conditional median future with the best of four
reactive continuations for each root action. Its labels are not clairvoyant or optimal.
Imitation error can compound when a student visits different states. Small numbers of
configuration groups, many tied/forced decisions, aliases sharing features, authored repair
duration supports and the exclusion of incomplete primary cases limit generalization.

Critical flags are authored declarations. There are no utility productivity measurements,
field logistics, electrical switching approvals, repair safety constraints, weather forecasts
or real dispatch integration. Model importance is descriptive and does not establish cause.
Zero invalid simulated actions does not establish operational safety. Hardware-dependent
latency and synthetic waiting metrics do not establish field benefit. No production/default
promotion follows from successful fitting alone.

The repository's MIT license and existing notices remain unchanged. New fictional inputs,
source and fitted artifacts introduce no AEP redistribution claim. Run the exact [load and
episode examples](REPRODUCE.md) and inspect [per-case failures](presentation/failure-cases.json).
