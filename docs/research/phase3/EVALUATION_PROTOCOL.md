# Phase 3 evaluation protocol v1 — preregistration

Committed before optimizer implementation. G2 base: 8f1b0640f7a080de1578fc10dc195182fd7fec80.
Frozen Phase 2 manifest: 985b1e1963fa4006f83417586ce3cb18ed6981dc9f77c3e56cc512e007338527.
Do not alter Phase 2 inputs, policies, validator, metrics or artifacts.

## Comparators and estimands

Select the strongest SINGLE fixed baseline by smallest arithmetic mean completed
customer-hours over the common finite 225 evaluation cases in the already published
Phase 2 artifact. Require all 270 cases present and valid per policy. Ties break by
lexicographic policy ID. Verify this rule before solver evaluation; the published
values select legacy-release-per-person-hour-adapter-v1 (63,560.9688889 h mean).
This choice is based on public baseline information, never optimizer outcomes.

Separately report per-instance minimum valid cost among all four baselines, FIFO,
customer-count, and both individual legacy adapters. Best-of-four is a non-deployable
reference; the optimizer may use it as its validated incumbent, but that does not
change the fixed PRIMARY comparator. Attribute gains beyond best-of-four separately.

For case i and comparator B: paired improvement = 100*(B_i-O_i)/B_i.
Zero/zero is a tie (0%); positive optimizer cost against zero baseline is an undefined
percentage and an explicitly reported absolute regression, not dropped as a success.
Report absolute differences as well. The primary target is >=5% median paired
improvement in COMPLETED customer-hours on the 225 finite cases versus the selected
fixed baseline, with a 95% clustered interval for that median strictly above zero.
This is a research target, not a mandatory outcome. Do not retune evaluation inputs,
methods, weightings or solver budgets to meet it.

Also report restricted-horizon customer-hours on ALL 270 cases, including the 45
blocked-root cases. Their full outcomes stay null; unresolved membership contributes
the unchanged no-credited-release horizon convention, never a finite restoration time.
Partial problems optimize this restricted objective including its constant unresolved
mass. Full and restricted improvements are separate; clipping may produce restricted
regressions even when a complete-case full objective improves. Retain those regressions.

## Statistical unit and uncertainty

The paired scenario is the measurement unit, not an independent statistical replicate.
Variants share seeds, structural families, task scales and crew settings. Use a crossed
family/seed (pigeonhole) cluster bootstrap: resample the observed family labels with
replacement and seed labels with replacement independently; take their Cartesian cells
with multiplicity, retaining ALL scale/crew variants together within each cell. This
preserves family effects and seed effects across scales/crews instead of resampling
individual variants. Five finite families × five seeds (six families for restricted)
is a very small cluster sample. Intervals describe sensitivity within this fictional
suite, not utility-population confidence or external generalization.

Use 5,000 resamples, Python Random seed 20261103, percentile endpoints at nearest-rank
2.5% and 97.5%. Report mean and median paired percentages and intervals, equal-family
macro means, scenario mean/median, and micro aggregate percentage 100*(sum B-sum O)/sum B.
Publish family, task-scale and crew breakdowns plus counts, ties, regressions and nulls.
No hypothesis-method shopping after results. No independence claim for 225/270 cases.

## Data partitions and finality

Development: existing seeds 17 and 29 only; microcases and authored adversarial tests
are correctness/debugging fixtures. Published evaluation: unchanged Phase 2 seeds
101,211,307,401,503 and full 270-case matrix. It is previously inspected, not blind.
No additional untouched final holdout is defined for this bounded engineering phase:
these families are already public, and another small draw would not establish utility
validity. Consequently make NO untouched-final-set or generalization claim. An independent
final set would need separate preregistration and sealing before any later tuning.

Freeze one solver configuration before the full evaluation. Run published evaluation
once after development correctness, and repeat identical execution only to verify
reproducibility, not for tuning. If a correctness bug requires a rerun, retain the failed
artifact and explain the fix; never suppress an unsuccessful experiment.

## Model, budgets and gates

OR-Tools CP-SAT 9.14.6206, one worker, seed 20261103. Offline primary deterministic-time
limit 0.2; secondary 0.05 only after proven primary optimality, with primary equality
fixed. No offline wall cutoff: deterministic work does not guarantee wall latency.
Interactive: <=25 tasks, <=4 crews; shared 2-second solve wall budget, at most 1.5 seconds
for primary, remainder for secondary only after proof. Measure total wrapper latency
against 5 seconds on the reference host; return an independently validated baseline
on solver absence, invalid output, unknown/infeasible status, timeout or worse objective.
Do not claim a hard service SLA from local timing tests. Inputs outside interactive scope
return the bounded baseline with an explicit reason. No new API is exposed in this phase.

Use Phase 2 upward-rounded second durations unchanged, all-person/one-worker assumption
as supplied (standard is one worker), non-preemptive single-crew assignments, explicit
repair prerequisites, crew availability, and independent customer dependency groups.
Primary objective is an INTEGER weighted release-tick sum. Do not use floating objective
comparisons to accept a candidate. Bound horizon by max crew availability + sum executable
durations; it admits a serial feasible schedule. Preserve unresolved scope and counts.
No switching, travel, access clearance, skills or real productivity invented.

Warm start from the best independently validated baseline. Every returned schedule and
all its metrics must pass the unchanged independent validator; never return a worse primary
objective than that incumbent. Secondary makespan cannot worsen primary. Keep raw solver
status, bounds, candidate objective, rejection/fallback reason, and returned provenance
separate. Only a solver proof for a validated candidate earns an optimality claim.

Correctness gates: zero returned feasibility violations; exact integer objective agreement
with every completed exhaustive micro-oracle; tested blocked/unknown, delayed crews,
overlap, bottlenecks, ties, critical tradeoffs, invalid prerequisites, unbalanced groups,
long/short tasks, already-optimal baselines, solver absence/invalid/infeasible/unknown and
budget exhaustion. Measure smoke interactive latency. Full matrix and source-free repeat
must preserve numerical hashes under the pinned environment. Wall times are separate.

All failures, ties, timeouts/budget stops, raw candidate regressions, fallbacks, secondary
tradeoffs and negative results remain in case-level results and reports. Missing results
cannot count as success or permit promotion. If the target is missed, report it and
recommend baseline or opt-in validated hybrid rather than silently changing defaults.
No application planner rewrite, frontend numerical engine, Phase 4/5 work, release or merge.
