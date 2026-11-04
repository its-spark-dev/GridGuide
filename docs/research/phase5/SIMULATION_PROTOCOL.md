# Phase 5 simulation protocol v1

Base main: 551313140d70e6e57412d55a239bf9fdaa9336bf. Commit this contract and
assumption definition before numerical implementation or experiments. G4 is an
evidence-bounded No-Go; no empirical restoration outcomes calibrate this simulation.
G3's 5% median target failed. Retain the strongest fixed baseline default. Its optional
best-of-four-plus-CP-SAT comparison gained 0.351% mean versus fixed, and 0.174% beyond
best-of-four; these are separate denominators, not new Monte Carlo claims.

## Versioned input and output

Simulation input v1 embeds the unchanged validated BenchmarkProblem and exact Schedule,
profile ID/version, numerical version, seed (nonnegative integer), trials (1–10000),
scenario-assumption evidence classification and the problem's elapsed-time assumption.
Reparse all inputs and run the independent G2 schedule validator before sampling.
Only independently authored synthetic benchmark inputs are accepted. Blocked/unknown
scope is inherited verbatim; physical energization dependencies are not repair precedence.

Output v1 binds problem fingerprint, canonical schedule hash/policy identity, input hash,
profile file hash, seed, trials, RNG, software versions, tick units, unresolved scope,
array field definitions and checksum. Trial order is retained. Exact per-trial numerical
metric arrays are retained in compressed archives; null fields have a separate availability
representation, not zero. Group-release arrays retain milestones/critical/branch detail
where needed for replay. Execution writes a manifest; reporting reads completed artifacts
and never samples or optimizes. Runtime and memory measurements are separate from numerical
hashes. Archive bytes may include container metadata; hash canonical uncompressed arrays.

## Profiles (all synthetic assumptions)

1. deterministic-v1: all multipliers 1, no hold.
2. independent-025-v1 and independent-050-v1: M_i=exp(sigma Z_i), Z_i iid N(0,1),
   sigma=.25/.5. Median M=1; mean exp(sigma^2/2), not one.
3. shared-025-v1 and shared-050-v1: M_i=exp(sigma/sqrt(2)*(Z_event+Z_i)).
   Marginal log variance sigma^2; pairwise log correlation .5. Multiplier correlation
   (exp(sigma^2/2)-1)/(exp(sigma^2)-1). Shared factor is common to every task in a trial.
4. storm-hold-v1: shared-.5 duration profile plus one H~Uniform[0,4h) event-wide
   response-start hold, rounded upward to seconds. It shifts all crew availability and
   planned not-before starts by H. Repairs already unavailable remain unavailable; it
   supplies no unknown clearance. Empty customer repair dependencies still release at 0.
5. uniform-sensitivity-v1: task multipliers iid Uniform[.5,1.5), median/mean one,
   no hold. This intentionally different family is a misspecification sensitivity,
   not a fitted substitute or exact variance-matched comparison.

Use the already rounded G2 conditional duration d_i (one second ticks) then
D_i=ceil(d_i*M_i). Never remultiply fictional effort by 4.5. Round once per sampled
duration; deterministic profile gives exact d_i. Float64 transforms; int64 ticks and
customer-seconds. Reject overflow/nonfinite values instead of clipping or dropping trials.

## Fixed-schedule replay

Fix crew assignment and each crew's original order (sort by start, then task ID).
Add crew-predecessor edges to explicit repair prerequisites; topologically replay.
S_i=max(original S_i+H, crew availability+H, all predecessor simulated E_j).
E_i=S_i+D_i. Original planned start limits deliberately preserve idle/slack; this is a
fixed timetable with delay propagation, not an adaptive earliest-start dispatcher.
Faster repairs cannot pull subsequent work earlier than the original timetable.
For M=1,H=0, induction on the combined DAG proves exact original starts/ends because
all original constraints are feasible and the original start is an explicit lower bound.
The hold is response delay, not travel, setup, efficiency or measured weather clearance.
No per-trial ranking, reassignment or optimization is permitted.

G2 release/metric definitions are preserved: T_g=max required finishes, unknown if any
required repair or evidence is unresolved; empty dependency set gives 0. Disjoint group
membership releases once. Full customer-hours/completion stay null with unknown scope.
Restricted cost integrates known waiting through H_out=168h and retains unknown mass at
that horizon as no credited release, not as a finite unknown restoration time. Censored
known-later mass stays separate. Weighted release thresholds use the complete population.

## Randomness, suites and computation

NumPy 2.5.4 PCG64; seed each task/event/hold stream with a SHA-256 integer of numerical
version, whole scenario fingerprint, profile ID, user seed and stream ID. Generate two
uniforms per trial and use Box–Muller cos transform for each normal. Stable stream keys
make policy execution/task ordering irrelevant; increasing trials retains the same prefix.
Trials are paired across policies, never across independently drawn realizations.
Float transforms are pinned to Python 3.12 / NumPy 2.5.4 and recorded host; cross-platform
bit equivalence is tested where available, not assumed. No source files/network/AI needed.

Standard suite: unchanged 270 G2 evaluation cases plus eight microcases, all seven profile
IDs, 2000 trials each, fixed baseline, frozen G3 protected schedule, FIFO, customer-count,
and per-instance deterministic best-of-four reference. The last is selected BEFORE sampling,
never a per-trial hindsight winner. G3 results are loaded and hash-checked, never retuned.
Smoke: eight microcases, all profiles, 32 trials. All failed cases remain in run manifest;
missing/invalid results prohibit a complete report. No global parallel workers.

Convergence: six finite microcases, all profiles/policies, 10000 trials; compare nested
first 2000 versus all 10000 for full release p10/p50/p90. Threshold max(.25h, .02*abs(q_10000)).
Do not hide failures. The 10000 run is the cap; failed checks are marked numerically unstable.
Also report ten disjoint 1000-trial batch quantile standard errors as a Monte Carlo
sensitivity diagnostic, not empirical calibration. For main outputs report ten batches
of 200. No stochastic outcome can promote a policy or recover the G3 failed target.

## Reports, verification and gates

Report p10/p50/p90 via nearest rank, widths, means and null mass for completed/restricted
customer-hours, makespan, full release, 50/90/100% release, median/p95/max customer wait,
critical groups, branch disparity and small-group wait; known-censored/unresolved counts.
Policy contrasts use paired trial differences (candidate minus fixed, lower better),
plus optional CP-SAT minus deterministic best-of-four. Preserve negative improvements,
ties and secondary regressions. No confidence/calibration wording for simulation quantiles.

Every trial checks crew order, availability, precedence, durations and release consistency.
Compare vectorized metrics to independent scalar G2 calculations/validator on deterministic
fixtures and adversarial trials with sampled durations supplied as conditional test inputs.
Test analytical one-task lognormal/uniform quantiles, shared log/multiplier correlation,
nulls/horizon equality, duplicate releases, malformed schedules and RNG alignment.
Report profile sensitivity across the entire suite, not selected winners. Synthetic
known-distribution coverage is an implementation check only. No empirical interval
coverage, sharpness or learned outcomes are supported by G4.

Run all existing regressions, source hashes, legacy cases, G4 replay and source-free
simulation reproduction. Keep heavy work CLI-only, preserve all prior artifacts and
application behavior. Precomputed synthetic microcase artifacts are future demo inputs,
subject to G5 review; no new API/UI/hosting is authorized. Stop at the G5 PR, no merge.
