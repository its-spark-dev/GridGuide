# Restoration benchmark specification v1

This is an offline, synthetic measurement system. No new optimizer, empirical prediction,
restoration calibration or application endpoint is introduced. The 5% Phase 3 improvement
is still a preregistered target, not a required outcome or reason to alter evaluation cases.

## Problem and provenance

`benchmarks/contracts.py` owns versioned **offline** problem/schedule contracts; public
HTTP contracts remain in `backend/contracts.py` unchanged. Each problem identifies its
revision, generator, family, seed, split, fictional origin, response origin and duration
assumption. Its fingerprint is SHA-256 of sorted compact JSON with all defaults included.
String identities are explicit and unique. Groups enumerate disjoint fictional customer
IDs; their sizes are the lengths of those lists, never separately inconsistent counts.

Tasks carry total repair person-hours, authored report order, access status and repair
prerequisites. Groups independently carry required damaged tasks, branch labels, unknown
additional dependencies and explicitly fictional critical-service flags. Prerequisite DAGs
are conservative repair-order policies; customer release dependencies are a different
relation. No geography is present or used to construct either relation.

Every problem input (labor, membership, damage, supply implicit in release, report order,
crew composition/availability, critical-service and branch declarations) is a **scenario
assumption**. Duration conversion and repair precedence are **prototype policy**. Missing
effort, clearance, operational authorization and actual efficiency are **unavailable**.
The contract fixes these classifications and independent-fiction origin; no AEP-specified
or source-derived claim enters the synthetic benchmark. All observations remain null.

Crews are interchangeable, with equal composition (2–8 people), a count of 1–4 and declared
nonnegative availability from the modeled response origin. Tasks are non-preemptive and
assigned to exactly one crew. No travel/setup increment, routing, skill constraints,
calendars, switching or operational clearance model is added. `blocked` and `unresolved`
access have unknown duration; their prerequisite descendants cannot execute. Unknown
customer connectivity does not prohibit independent repair work, but withholds release.

## Conditional duration, units and time

One tick is one second. Every policy uses `ceil(3600 * total_person_hours / effective_workers)`.
The standard suite chooses **one effective worker per crew**. This is an explicit conditional
elapsed-time policy, not an equality of person-hours and observed elapsed hours. A separate
`ideal_all_people` contract option divides by the declared equal crew size; tests cover its
rounding and labor invariance. Neither assumption measures actual efficiency. Additional
crews allow independent work; they never divide a task. Effort is independently authored
as total person-hours; no 4.5 multiplier is applied to synthetic inputs. AEP arithmetic
and dual envelopes remain untouched in the separate source regression lane.

Availability and prerequisites constrain starts. Equality of predecessor finish and next
start is allowed. Intervals are half-open `[start,end)`; touching work does not overlap.
Durations round upward consistently for all policies; exact person-hours remain in inputs.

## Baselines and deterministic ties

All policies consume the identical validated problem and return the same schedule schema.
They construct an ordered plan: choose a task whose prerequisites have already been assigned,
then the crew with earliest **feasible** finish (including prerequisites and availability),
then stable crew ID. Committed assignments are not claimed to have physically completed.
Blocked/unavailable tasks and descendants are explicitly listed as unscheduled.

| Policy | Task selection among precedence-ready eligible tasks |
|---|---|
| `fifo-v1` | Lowest declared report order, then stable task ID |
| `customer-count-v1` | Highest total membership count of groups requiring that task, then stable ID; no duration normalization |
| `legacy-release-per-person-hour-adapter-v1` | Highest marginal group-release count per total person-hour, then higher marginal count, lower effort, stable ID |
| `legacy-critical-proxy-first-adapter-v1` | First prefer tasks on explicit fictional critical-service dependencies and their repair ancestors, then the preceding release/effort rules |

Marginal release is the additional membership whose required tasks are all in the committed
plan after adding the candidate; unresolved groups cannot earn release credit. This preserves
the legacy planning-order interpretation, not a claim about releases at the candidate's
start. The critical adapter translates a prototype preference into explicitly fictional
critical dependencies; it creates no spatial proxy or real facility attachment. Generalized
adapters select a feasible crew and one tick duration instead of the UI's two envelopes.
**Exact equivalence to the original four-candidate scheduler is not claimed.**

FIFO order is independently authored, with intentional deterministic ties. No historical
date-only record is assigned an invented within-day order. There are no sampled future
durations or stochastic policy draws in Phase 2.

## Metrics and nulls

For each disjoint customer group `g`, known release tick `T_g` is the maximum completion
of all its required repairs, or zero for an empty required set. Unknown connectivity or
an unscheduled required repair makes `T_g` null. All time values below divide ticks by 3600.

| Field | Exact definition |
|---|---|
| `customers` | Full declared membership denominator; never drops unresolved groups |
| `modeled_customer_outage_hours` | `sum(n_g*T_g)/3600` only when every group has a known release; otherwise null, never a completed-subset sum |
| `restricted_horizon_customer_hours` | Waiting integral through 604800 ticks (168 h), crediting only modeled known releases; known times contribute `n_g*min(T_g,H)`, unknown times contribute `n_g*H` |
| `unresolved_customers` | Membership with unknown release time |
| `censored_customers` | Membership with known release **strictly after** H; separate from unresolved |
| `unreleased_customers_at_horizon` | Censored plus unresolved; release exactly at H is released |
| `known_release_customers` | Full denominator minus unresolved, including known releases beyond H |
| `makespan_hours` | Last task finish only if all declared tasks execute; null otherwise |
| `full_customer_release_hours` | Last group release only if all customer releases are known; distinct from task makespan |
| `release_50/90/100_hours` | First time known credited releases reach `ceil(q*N)` of the full denominator; null when unreachable from known releases |
| `weighted_median/p95_hours` | Nearest-rank customer-weighted quantiles (`ceil(q*N)`, no interpolation); conservatively withheld if any customer release is unknown |
| `maximum_wait_hours` | Maximum known wait only when all releases are known |
| `critical_service_latency_hours` | Map of explicitly fictional critical groups to full group release time (or null); empty map means none declared |
| `branch_mean_wait_hours` | Customer-weighted mean per authored branch, null if any member is unresolved |
| `branch_mean_disparity_hours` | Maximum minus minimum branch mean; null if any branch mean is unknown |
| `small_group_customers` | Number of customers in groups of size at most 5 |
| `small_group_mean_wait_hours` | Customer-weighted mean for those groups; null for empty or unresolved small-group scope |
| `milestones` | Distinct known release ticks sorted ascending; simultaneous releases grouped; additional and cumulative customer counts |

The unknown contribution to restricted scoring is a **no-credited-release convention**,
not a claim that actual unknown restoration takes 168 hours or cannot occur sooner.
Null release times remain null in the artifact. The threshold-release fields similarly
measure credited modeled release, not identified quantiles of unknown real outcomes.
Fairness measures describe these authored branches/group sizes, not demographic equity
or ethical weights. Critical latency is reported separately from customer-hours.

Aggregation groups by split, family, task count, crew count and policy. It includes every
scheduled case. Means of completed customer-hours use only finite cases **with an explicit
finite denominator**; restricted means use all valid cases with a distinct denominator.
Failures and unavailable full cases are counted, never converted to zero. No combined
ranking across incomparable completed/restricted totals is produced. The per-case result
retains all secondary metrics; group summaries focus on primary and restricted totals.

## Independent validator and oracle

`validation.py` imports neither baseline logic nor metric generation. It reparses the
problem/schedule, finds executable work by fixed-point reachability, uses rational duration
arithmetic, checks crew intervals, availability, precedence and all task dispositions.
It expands explicit customer memberships to independently reconstruct every reported metric,
including releases, quantiles, branches and milestones. Errors are retained by name.
Negative tests corrupt each output field, task scope, overlap, IDs, duration, clearance,
availability, membership and prerequisites. Input fingerprints bind every result.

`oracle.py` independently enumerates every precedence-feasible task order and crew choice,
left-shifting each assignment to its earliest feasible start. For identical crews, fixed
durations, no calendars and a regular customer-wait objective, a left-shifted optimal
schedule exists in this enumeration: take an optimal schedule's per-crew order and a
compatible precedence order; moving each task earlier cannot worsen any group release.
No policy ranks, marginal scores, duration helper or generated objective calculation are
shared. The objective is independently computed from terminal task finishes and groups.
Returned assignments are also checked by the independent validator.

Support is bounded to at most eight tasks, fully known duration/access/connectivity,
one to four identical crews, and **250,000 recursive nodes**. The eight-task independent
one-crew case and eight-task chain are tested. Multi-crew combinations may exceed the cap.
`optimal` requires completed enumeration; `budget_exhausted` is an incumbent only and
cannot supply an optimality gap. Blocked/unknown or larger inputs return `unsupported`.
The runner only reports a baseline optimality gap when exhaustive optimality was proved.
No CP-SAT or new optimization policy exists; this reference enumeration is test machinery.

## Frozen inputs and reproducibility

`benchmarks/frozen/evaluation-v1.json` was committed before baseline evaluation at
`b32156f`. It binds 270 cases: six families × 10/25/100 tasks × 1/2/4 crews × five seeds
(101, 211, 307, 401, 503). Development seeds are 17 and 29. Hash-derived integer draws
avoid global RNG state. The generator version, family, scale, seed and whole-problem
content hash are recorded. Standard runs verify both the manifest byte pin and regenerated
case content, and cannot update them. Changing the official evaluation requires a new
suite version and review, never retuning against observed results.

Families are serial chains, independent branches, shared upstream bottlenecks, overlapping
customer dependencies without implied repair precedence, blocked upstream prerequisites,
and explicit critical-service tradeoffs. Each group gets 1–20 fictional customers; total
repair effort is 1–12 person-hours; additional crews have authored 0–2 h availability.
Blocked-family cases intentionally leave all work unresolved behind the blocked root;
microcases separately test partial release and independent work. These structural examples
are not an empirical distribution or representative utility population.

Eight microcases accompany every run for hand arithmetic, overlap, an eight-task chain,
delayed crew availability, blocked and unknown work, beyond-horizon completion and critical
tradeoffs. They are correctness cases, not held-out improvement evidence. Their full
fingerprints are recorded in each run manifest.

The standard runner is offline and needs only Python 3.12 and pinned Pydantic; no GIS,
source files, provider keys or network. A source-free extraction test runs the **full**
standard suite with source reads and outgoing socket connections forbidden. Application
and Phase 1 contracts/fixtures are unchanged.

Deterministic numerical results live in `results.jsonl.gz` (zero gzip timestamp), bound by
an uncompressed content hash. `manifest.json` records every input hash, implementation
hash, policy, dependency/runtime version and execution setting. Runtime observations are
separate: wall seconds, CPU seconds and peak traced Python allocations per scheduler +
metrics + validation call. Tracing overhead is included; this is not process RSS/native
memory or pure scheduler latency. No wall-time promise or reproducible-timing claim is made.
Baselines have bounded input sizes and no wall-time cutoff; the oracle has a deterministic
node budget. Failures/invalid output are retained and cause a nonzero CLI exit.

Generation and presentation are separate commands. The renderer checks the result hash,
case/policy Cartesian product and input bindings before producing aggregates and Markdown.
Existing output directories cannot be overwritten by the runner. Default output is not
silently regenerated. Exact commands and observed results appear in [G2](../planning/V1_1_0_PHASE2.md).

## Separate legacy regression lane

`benchmarks/legacy.py` lazily imports the original planner only when explicitly invoked.
The frozen legacy record contains 24 combinations: 1/2 crews × 2/4/8 people × two original
policies × clear/blocked upstream. It records original public labels, effort, dual-envelope
assignments and milestones, with source/code hashes. No customer IDs or geometry are
exported. It neither adapts those observations into synthetic benchmarks nor invents FIFO
order. Missing authorized files fail this lane; an omitted lane is not counted as passed.
