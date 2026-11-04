# Event-driven adaptive research architecture

This research imports the fictional G2 schema and numerical checker. It adds no
application route, UI, utility data, switching, travel model, deployment or release.
Every task, dependency, customer membership and duration distribution is an authored
scenario assumption. Dispatch rules, search budgets and acceptance thresholds are
prototype policies. Observed utility outcomes and actual productivity are unavailable.

## Modules and information boundary

| Module | Responsibility |
|---|---|
| `environment.py` | Frozen public observations, private keyed durations, legal assignments and physical-event advancement |
| `validation.py` | Independent trace replay; imports neither environment nor policies |
| `exact.py` | Finite-support Bellman recursion on public observations, <=5 tasks, exact rational expectation |
| `policies.py` | Five reactive rules, median/stochastic root-action rollouts, eight fixed-plan controls |
| `dataset.py` | Fresh configuration groups, paired 2/3-crew variants, input-only manifests and disjoint stage seeds |
| `experiment.py` | Common-draw runs, independent validation, discovery selection, confirmation gate, read-only replay |

An observation contains immutable known task/customer/crew characteristics, current
time, completed assignments, and active task/crew/start records. A policy can derive
remaining customer dependencies by removing completed tasks from each required set.
The callback never receives an Environment, episode seed, private duration map or
future end-time queue. This boundary prevents accidental lookahead; Python introspection
by deliberately malicious code is outside its scope.

Dispatch starts one ready task on one idle crew at the current timestamp. Successive
assignments take zero simulation time. Waiting advances to the next completion or crew
arrival; every tied completion is processed before the next decision. Completion reveals
actual duration. There is no time-step approximation, preemption or crew-size division
beyond the original problem's explicit duration convention.

The public support for an active task is conditioned on total duration being greater
than elapsed time. Independently sampled hypothetical futures use a separate hash
namespace derived from public state. A teacher compares each root action using the same
eight hypothetical worlds. It chooses the continuation with lowest **average** cost
across those worlds, avoiding a privileged per-world best-continuation oracle.
Every continuation sees only its simulated public observations. Search is bounded
one-step rollout, not a global stochastic optimum or full Monte Carlo tree search.

## Independent checks and exact expectations

Every actual online episode is replayed by the independent trajectory checker, including
its action validity, public state, crew arrivals, simultaneous completions and terminal
scope. Every online and fixed episode is independently validated through G2 for all
schedule constraints and the entire metric object.

For that second check, a private conditional problem encodes sampled integer seconds
as `(seconds - 0.1) / 3600` under the one-effective-worker convention. This lies strictly
inside the interval whose ceiling equals the intended duration. It is solely a validator
adapter, **not a claim about new person-hours or productivity**. Both original and
conditional fingerprints remain in the result. The original problem is unchanged.

The exact tiny solver enumerates conditional active-task outcomes and merges identical
observable successor states. Unstarted task draws remain unknown. Its Bellman value is
remaining customer-hours: waiting through Δt adds `unreleased customers × Δt / 3600`;
assignment adds zero immediate cost. It minimizes expected remaining cost over valid
actions, including wait. It refuses unresolved customer scope and a finite state-budget
overrun. Exact results validate tiny cases only; they do not certify large-instance search.

One deterministic four-task fixture has a meaningful wait decision: a one-hour active
repair unlocks two one-hour repairs serving 100 customers each. The idle crew could start
a ten-hour repair serving one customer. Reserving it gives 413 total customer-hours;
starting the long repair immediately gives 511. Exact recursion and online rollout agree.
Separate intervention tests show identical decisions under identical public histories,
then different ready tasks once different completions become observable.

## Experimental separation and runtime

Discovery selects fixed/reactive/cheap-dynamic comparators. Confirmation uses independent
configuration and duration-seed namespaces and the frozen selections. Both crew variants,
profiles and repeated draws stay inside their original configuration for uncertainty.
The procedural freeze is developer-controlled, not a third-party blind study.

Each method runs on exactly the same case-specific exogenous durations. Fixed plans
retain original crew assignments/order; both planned-floor and earliest-feasible controls
are reported. The latter prevents idle-time reclamation from being the sole explanation
for an apparent adaptive gain. These schedules may intentionally idle between physical
events; they obey the same capacity/precedence/nonpreemption constraints as online methods.

Timing separates one-time fixed planning, all online callbacks, and discretionary
callbacks with more than one legal canonical action. Forced waits are cheap for every
online method and can otherwise hide search cost in a median. The learning pilot's
inference-speed comparison, if justified, will use discretionary decisions and also
publish all-decision times. Timing excludes independent post-episode validation.
Machine, environment, peak RSS, complete-command wall time and counts remain explicit.

Incomplete fixtures retain null complete-restoration outcomes and separate restricted
horizon cost. The primary opportunity cohort deliberately has complete scope; it cannot
establish learned behavior under unknown dependencies, correlated durations, unknown
damage, travel, switching, heterogeneous crew skills or real utility conditions.
