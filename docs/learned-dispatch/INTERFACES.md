# Public state, training and inference contracts

This is isolated fictional scheduling research. The existing event-driven environment,
reactive rules, search policies and independent schedule/trajectory validators are imported
unchanged from PR #20. ML I's generator supplies authored structures through a new adapter;
ML II remains a separate source audit. No customer application or release behavior changes.

## Legitimate inputs and supervision

`learned-public-state-v1` contains the current time, observed completions, active start
times, known tasks/prerequisites/customer memberships/critical declarations, crew availability,
nominal durations, public duration support and horizon. It contains no scenario seed, problem
identifier, generator family, partition, private duration draw or event queue. IDs are used
only to join known entities and break exact action ties; they never become feature columns.
Critical flags and duration supports are **scenario assumptions**. Structural aggregates are
**source-derived** from those authored inputs. The feature definitions and ranking decisions
are **prototype policy**. Utility calibration and operational outcomes are **unavailable**.

The 46 ordered features are defined in [feature-schema.json](feature-schema.json). The same
extractor runs during fitting and inference. Conditional active remaining time averages only
public support points consistent with the observed elapsed time. It never subtracts elapsed
time from an environment-private sampled completion. Teacher action costs are separately
computed median-world rollout outcomes and enter the target only.

Teacher records deduplicate identical public states within a configuration and preserve every
visit, episode identity, decision index and behavior choice. Static input snapshots are stored
once by content hash. The target is `(action_cost - best_cost) / customers / mean_nominal_hours`.
Forced canonical actions retain exact decisions but have null costs/targets and no fit rows.
The canonical crew's task cost is copied to equivalent currently idle crews; tests independently
roll out each crew alias. Identical crew composition is enforced by the inherited contract.

Each configuration receives equal total fitting weight. Its unique discretionary states split
that weight equally; each state's legal actions split it equally again. Weights are rescaled to
mean one. Ridge's scaler sees weighted training rows only. Development reactive trajectories
provide additional **prediction-export parity probes**, never preprocessing or fit rows; their
outcomes are not used for model selection. Selection uses complete student rollouts.

## Strict boundary and supported scope

Static structure is validated against the inherited immutable benchmark contract, including
DAG, unique memberships, exact IDs and matching nominal duration convention. Dynamic validation
checks conditional support, observed durations, prerequisite completion, arrival times,
duplicate tasks and crew overlaps. Unchecked nested Pydantic copies are reparsed. Malformed
histories raise an error before attempting fallback.

Learned inference supports complete executable scope, no unresolved customer dependencies,
at most 64 tasks, current time at most 10^12 ticks and each nominal duration at most 10^9 ticks.
These are numerical/interface **prototype policies**, not utility limits. The inherited
contract allows one to four identical-composition crews and two to eight people per crew.
The scientific cohort fixes four people with the one-effective-worker duration convention.
Valid unsupported inputs use the existing deterministic downstream/time policy and record
`unsupported-public-scope`; prediction failures record `inference-failure`. A missing model
requires an explicit `allow_no_model=True` and records `explicit-no-model`. These paths are
non-learning. A terminal state has no decision and is rejected by the callable policy.

`LearnedPolicy(model)(observation)` enumerates only legal actions, including WAIT when an
event can advance time. It chooses the minimum predicted cost with assignment-before-WAIT,
task-ID then crew-ID ties. `score(observation, action)` returns **negative predicted cost**,
so higher is better. An invalid candidate is rejected. Raw prediction is not a probability,
utility ETR, calibrated cost or safety certificate.

## Portable learned parameters

The JSON regressor format stores actual fitted scaler moments and Ridge coefficients or all
64 trees' split/threshold/leaf arrays. The approved inventory binds SHA-256, feature order,
feature schema, input/teacher identities, code hashes and candidate specification. Loading
requires the expected SHA-256, a 16-MiB limit, exact fields, finite values, matching dimensions,
valid feature indices and reachable acyclic trees of the registered depth. Duplicate JSON
keys are rejected. There is no pickle/joblib loading or network service.

Forest comparisons cast features to float32 as scikit-learn does. Exports are checked against
the actual fitted estimator on training and development probes within 1e-10. Each candidate is
fitted twice; exact export equality is recorded separately from tolerance-based equivalence.
Teacher and evaluation timing data are outside numerical/label artifact hashes.

## Evaluation safeguards

Scientific train/dev/final-ID/final-shift inputs use separate gzip files. Training/labeling and
development execution install a process-local deny guard for both final files and all raw/
prepared/external data, and block network connections. This is an auditable workflow control,
not a security boundary against a repository author. Small hand-authored tests and the separate
`smoke` namespace may fit before the scientific input seal; they make no scientific claims.

Every online callback includes validation, action enumeration and policy computation. The static
validation cache is cleared at each policy-episode start, so its first callback includes cold
validation. Method order rotates deterministically across configurations/variants/profiles/episodes.
Agreement queries occur after the timed callback. Full-episode CPU/wall measurements additionally
include simulation, independent validation and (for students) agreement queries; summed decision
CPU is reported separately. No timing or agreement metric selects the champion.

Final receipt creation is exclusive and precedes opening final inputs. Its freeze and output
root are binding for both final cohorts. Immutable configuration shards permit resuming only
unfinished groups; failures persist. Completed evaluations reject reruns. A read-only audit
checks exact cohort coverage, common duration draws, independent schedules/metrics/trajectories,
file hashes and regenerated summaries. Once final evaluation starts, fitting, relabeling and
development execution against that scientific workspace are closed.
