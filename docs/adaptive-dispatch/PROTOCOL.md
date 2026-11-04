# Adaptive dispatch protocol v1 · 2026-11-04

Status: prospective protocol before benchmark outcomes or learned-policy fitting.
Base: main after merged PR #19 (`619797e`). All scenarios are explicitly fictional.
No observed utility calibration, electrical switching, travel, preemption, dispatch
integration, dashboard change or empirical restoration guarantee is introduced.

## Question and architecture

Can sequential task/crew decisions using observed completion information improve
customer waiting over strong online rules, and can a learned task ranker approximate
a more expensive non-clairvoyant search policy at materially lower decision cost?

New isolated package: `research/adaptive_dispatch`. Reuse the immutable G2 problem,
assignment and schedule schemas, customer-release metrics, and independent validator.
Sampled integer durations are supplied to a separately reconstructed conditional G2
problem for validation; preserve its original evidence/fingerprint in the episode record.
An additional trajectory validator checks public states, actions and observations.
The application and all historical source/evidence files remain unchanged.

## Public state and dynamics

At time zero, and after completions or crew arrivals, the dispatcher may assign a ready
unstarted task to an idle available crew or wait for the next physical event. Multiple
assignments at one timestamp are successive zero-time decisions. A wait with no future
completion/crew arrival is invalid. Process all simultaneous completions together before
the next decision. Tasks are nonpreemptive and crews have identical composition.

Expose known task effort, prerequisites, customer membership/dependencies, critical flags,
crew availability, completed assignments and active task/crew/start records. Reveal actual
duration only at completion. Active elapsed time is observed; active end times, unstarted
sampled durations and episode random seed are private. The policy callback receives an
immutable public observation, never the simulator, duration map or future event queue.
This is an architectural separation, not a sandbox against malicious Python introspection.

Blocked or unknown effort propagates through prerequisite closure. Unresolved customer
dependencies retain null full outcomes; restricted 168-hour cost remains a distinct metric.
Never turn unknown work into a sampled completion. One-second ticks and explicit person
hours remain separate; the G2 elapsed-time convention is applied once before sampling.

## Declared stochastic assumptions

Independent per-task finite distributions permit transparent residual-life conditioning
and exact small-instance checks. Primary profiles: deterministic multiplier 1; equal-mass
low variability {.5, 1.5}; equal-mass high variability {.25, 1, 2.75}. Both stochastic
profiles have mean multiplier 1. Integer durations use `ceil(nominal * multiplier)`;
coincident support points retain their probability mass. These distributions are scenario
assumptions, not fitted repair-time models. Independent durations do not model shared
weather/productivity factors; correlated uncertainty remains an explicit generalization gap.

Environment draws use SHA-256 keyed by version, complete input fingerprint, profile,
private episode seed and task ID. No policy identifier or decision order enters the key.
Teacher hypothetical draws use a distinct namespace and public state only. For an active
task, condition its support on total duration > elapsed; never use the environment's draw.

## Comparators and exact verification

Retain all four G2 schedules with G5-style planned-start floors, fixed crew assignment and
crew order. Also include their **fixed-order, earliest-feasible** variants without planned
floors: gains from merely reclaiming planned slack must not masquerade as learned adaptivity.
Reactive FIFO, customer-count, release/person-hour and critical-first recalculate at each
decision using completed work, not eventual scheduled completion. Add a downstream-customer
per-expected-time heuristic to avoid a weak immediate-release-only comparator.

Bounded online search enumerates every ready task on one canonical idle crew (equivalent
idle crews are interchangeable here) plus valid wait. For each root action, evaluate four
reactive continuation rules on eight independently sampled conditional hypothetical futures.
Choose by expected completed customer-hours, deterministic ties. Select continuation rules
by their average across draws, never their per-draw hindsight minimum. Replan at each actual
decision. A nominal-duration rollout is an additional low-cost search comparator.
Neither teacher can inspect the actual future. Exhaustive non-clairvoyant finite-support
dynamic programming is limited to tiny fixtures; a privileged offline optimum, if shown,
is a clearly labeled lower bound, never a teacher or deployment baseline.

## Dataset and staged opportunity gate

Use newly generated configuration groups, not old evaluated cases. Reuse the audited ML I
graph construction mechanisms through an explicitly versioned adapter with new configuration
seeds, 10–14 tasks, 2/3 crews, 8–16 customer groups, varying dependency overlap and criticality.
ID mechanisms: random ordered, layered, bottleneck and modular. Preserve whole graph/customer
configurations across every crew/profile/draw variant; reject duplicate topology signatures
between groups. Incomplete deterministic fixtures are verification/stress cases, outside
finite-outcome primary learning denominators.

Stage O discovery: 12 configurations (3/mechanism), 8 episodes/stochastic profile. Select
the strongest fixed comparator and strongest cheap reactive comparator by mean normalized
completed customer-hours (cost divided by customer count). Stage O confirmation: 24 new
configurations (6/mechanism), 16 episodes/profile. Deterministic profile reported separately.
Average paired differences across episodes/profiles within configuration before uncertainty;
95% bootstrap intervals resample whole configurations, 2,000 draws, seed 20261104.

Opportunity passes only if (1) best reactive improves on selected best fixed by >=2% with
positive paired-improvement interval; (2) stochastic teacher improves on selected strongest
reactive by >=1% with positive paired-improvement interval; (3) teacher mean maximum critical
group wait and mean per-episode p95 customer wait do not worsen by more than max(.25 hour,
5% of comparator value), on common supported cases. Report every comparator, tail failures,
support and runtime even on failure. These are prototype research thresholds, not AEP policy.
Failure stops before learning; do not redesign the suite or move the threshold after reveal.

## Conditional learning pilot

If Stage O passes: 48 independent train configurations, 16 development, 24 final ID and
24 shifted configurations (preferential/deep-sparse graphs, 18–24 tasks). Disjoint configuration
and duration-seed namespaces; commit input manifests before fitting. Teacher labels only
training decision states. Candidate students: standardized linear regression of teacher
action cost and small random-forest regression (64 trees; depth 4/8), static plus observed
state/action features. Mask invalid actions before ranking. No IDs, seeds, episode outcomes
or actual future durations enter features. All visited states from one configuration stay
together. Evaluate student rollouts, not just held-out decision-label accuracy; document
behavior-cloning distribution shift. No RL fine-tuning in this first bounded pilot.

Choose on development complete-episode outcomes and freeze features, preprocessing, model,
hyperparameters, input manifests, evaluation code and criteria before one final evaluation.
A credible computational benefit requires >=5x lower median decision time than the teacher,
mean waiting cost no more than 2% worse than teacher, and no worse than strongest selected
non-learning reactive baseline; critical and p95 guardrails above also apply. Compare all
methods on identical final inputs/draws. Report ID and shifted cohorts separately, grouped
uncertainty, worst cases, resources, and failures. Never retune on final results.

## Budget, tests and delivery

CPU only, existing hash-pinned ML environment; no new large dependencies. Eight search
futures, bounded task counts and one worker. Target <2 GiB peak process memory and <30 minutes
per experiment command. Record actual timings; a cap requires a documented prospective
resource amendment, never dropping unfavorable cases. Smoke fixtures are separate from
scientific configurations. Pin source/environment/input/result hashes; preserve failure receipts.

Tests: event ordering, simultaneous completions, release deduplication, scope/nulls, crew and
prerequisite safety, invalid actions, hidden-future intervention invariance, keyed-stream
pairing, conditional remaining duration, fixed replay equivalence, exact tiny-instance
verification, split/configuration isolation, deterministic replay and report regeneration.
Run existing applicable tests/frozen checks. New bounded source-free CI, one final PR,
no merge/tag/release. Deliver architecture audit, literature review, independent environment,
opportunity results, conditional pilot if justified, honest recommendation for/against full RL.
