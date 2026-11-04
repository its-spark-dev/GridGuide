# v1.1.0 Phase 5 — G5 simulation review packet

**Owner independently approved G5 at reviewed head
`aece0448cbee6b3e7d3404843334e4e77c4dd94f`, subject to the handoff constraints below.
Merge is authorized after documentation and preservation verification. Phase 6/later
work, release publication and deployment remain unauthorized.** Base main is
`551313140d70e6e57412d55a239bf9fdaa9336bf`; branch is
`feat/v1.1-phase5-probabilistic-simulation`.

The complete experiment executed: **9,730 standard runs × 2,000 trials**, zero execution
failures, and **210 convergence runs × 10,000 trials**, zero execution failures.
Convergence is a separate result: **195 combinations stable, 15 unstable at the cap**.
All 15 failed quantile checks remain in the report and affected demo presets are flagged.
The complete standard and convergence suites reproduced in source-free, network-denied
extractions with identical numerical hashes. No empirical restoration calibration follows.

Start with the [preregistered protocol](../research/phase5/SIMULATION_PROTOCOL.md),
[paired comparisons and sensitivity](../research/phase5/COMPARISONS.md),
[artifact/reproduction instructions](../research/phase5/ARTIFACTS.md), and
[verification record](../research/phase5/verification.json).

## 1. Mathematical definitions and evidence

For each task, use the existing G2 elapsed-time assumption:
`d_i = ceil(3600 * total_person_hours_i / effective_workers)` in seconds.
The standard matrix uses one effective worker per crew. People and crew counts retain
their distinct G2 meaning. Fictional effort is already total person-hours; no 4.5
multiplier or additional travel/setup term is introduced. Sample
`D_i = ceil(d_i * M_i)` using float64 transforms and integer-second durations.
Nonfinite, nonpositive or out-of-range draws cause an explicit failure, never clipping.

Let `s_i` be the original planned start, `a_c` the assigned crew's availability,
`P_i` the union of explicit repair predecessors and the previous task on that fixed crew,
and `H` the event-wide hold in seconds. Topologically replay:

```text
S_i = max(s_i + H, a_c + H, max(E_j for j in P_i))
E_i = S_i + D_i
T_g = max(E_i for i in the customer's required repairs)
```

An empty repair dependency set releases at zero. An unresolved dependency or unscheduled
required repair makes `T_g` unavailable. Customer energization dependencies do not become
repair prerequisites. Crew ordering and non-preemption remain fixed throughout sampling.

The original planned start is an explicit floor: deliberate idle/slack stays in place,
and faster repairs cannot advance subsequent work beyond the original timetable. This
is fixed-timetable delay propagation, not adaptive earliest-start dispatch. It is stated
before implementation in commit `24a8c68`; the numerical implementation was committed
at `22fdd76` before standard evaluation. No post-result policy retuning occurred.

| Ingredient | Evidence class / provenance |
|---|---|
| Fictional effort, groups, critical flags, availability and damage | Scenario assumption; unchanged independently authored G2 inputs |
| Distributions and response hold | Scenario assumption; user-approved values and protocol, never fitted utility observations |
| Duration conversion, repair order, timetable floors, quantile/rounding and experiment rules | Prototype policy; documented numerical conventions |
| Unknown clearance, true productivity, observed outcomes, real calibration | Unavailable; remain unknown/null |

The [G4 No-Go](../research/RISK_FINDINGS.md) found that acquired evidence did not justify
the proposed supervised outage task; it did not establish universal public-data
infeasibility. NOAA reports remain storm context rather than outage labels, missing
records are not zeros, and unknown permissions/real-data split validation remain open.
No empirical task/customer restoration outcomes validate these distributions. Reopening
research requires a new versioned evidence review and data-quality gate; never manually
reinterpret the current No-Go ledger as Go. The original concern band and null outage
probabilities are unchanged.

## 2. Distribution provenance and correlation

All seven IDs are in [simulation_profiles.json](../../benchmarks/simulation_profiles.json).
The first six instantiate the four requested families; the seventh is the preregistered
different-family sensitivity. With independent standard normal `Z_i` and `Z_e`:

| Profile | Definition | Provenance and limit |
|---|---|---|
| `deterministic-v1` | `M_i=1`, `H=0` | Exact numerical reference |
| `independent-025-v1` | `M_i=exp(0.25 Z_i)` | Requested assumed log SD 0.25 |
| `independent-050-v1` | `M_i=exp(0.5 Z_i)` | Requested assumed log SD 0.5 |
| `shared-025-v1` | `M_i=exp(0.25/sqrt(2) * (Z_e+Z_i))` | Equal shared/task log variance |
| `shared-050-v1` | `M_i=exp(0.5/sqrt(2) * (Z_e+Z_i))` | Equal shared/task log variance |
| `storm-hold-v1` | Shared-0.5 durations plus `H=ceil(3600 U)`, `U~Uniform[0,4)` | Requested synthetic event-wide response delay; added once to planned starts/crew availability |
| `uniform-sensitivity-v1` | Independent `M_i~Uniform[0.5,1.5)`, `H=0` | Protocol-authored family sensitivity; deliberately not variance matched |

The lognormal median is one but mean is `exp(sigma²/2)`, greater than one. For shared
profiles, independent components each contribute `sigma²/2`; marginal log variance
is `sigma²`, pairwise log correlation is 0.5 and multiplier correlation is
`(exp(sigma²/2)-1)/(exp(sigma²)-1)`. It is not 0.5 on the original multiplier scale.

The [controlled 10,000-draw check](../research/phase5/sampling_check.json) measured
shared-0.5 log correlation **0.49825** (target 0.5), multiplier correlation **0.46886**
(target 0.46879), and log variances **0.24574/0.25349** (target 0.25). Independent-0.5
multiplier correlation was **0.00093**; the stress hold mean was **2.00296 h**.
Tick rounding is included. These validate a generating implementation, not a utility
correlation model. Analytical one-task lognormal quantiles/80% central probability and
uniform quantiles/support are also tested against known generating values.

The hold shifts the modeled response clock before all planned work and all crew
availability, once per event. It is not task-by-task travel, observed storm clearance,
or measured productivity. Unknown blocked work stays unknown. No synthetic clearance
experiment is included. Empty repair groups still release at response origin zero.

## 3. Architecture and input validation

The simulator remains an offline Python extension. `SimulationInput` embeds the strict
G2 problem and exact schedule and runs the independent G2 validator before sampling,
including when passed an unchecked Pydantic copy. It accepts only the synthetic contract.
Output metadata binds problem, schedule, input and profile fingerprints; policy identity;
numerical/profile versions; seed; trial count; elapsed-time assumption; units; environment
and canonical array digest. Full manifests retain exact inputs and all five schedules.

`backend/simulation.py` owns draws/replay/metrics; `research/uncertainty.py` owns numerical
summaries; `benchmarks/simulation_experiment.py` executes bounded suites. Reporting is a
separate CLI that reads lossless sufficient statistics, reconstructs all metrics, verifies
their hashes and requires the complete Cartesian run matrix. There is no solver call in
simulation, arbitrary public endpoint, frontend engine, source loader or new service.

Crew predecessors and repair prerequisites form the replay DAG. Every trial checks
availability, planned starts, predecessor completion and duration consistency. The input
contract requires disjoint customer membership; each group's single last-required-repair
release produces deduplicated, nondecreasing release milestones. Independent scalar G2
validation checks adversarial sampled trials, including overlap, delayed crews, critical
groups and fairness metrics.

## 4. Deterministic equivalence

With `M_i=1,H=0`, induction on the combined DAG gives original starts/finishes: the
feasible original start satisfies availability and every original predecessor finish,
and is itself the replay lower bound. This covers CP-SAT's deliberate slack as well as
heuristic schedules. A specific idle-time regression protects that interpretation.

All **1,390 standard deterministic runs** (278 cases × five schedules) compare every
start, finish and generated metric against the original schedule and unchanged G2
metric implementation: exact equality, including nulls, group releases, branches and
critical groups. All passed across 2,000 repeated trials. The tests additionally compare
all 40 microcase/policy combinations and sampled scalar schedules. No frozen input,
baseline, validator, solver setting or G3 result was changed to obtain equivalence.

## 5. Trial counts and reproducibility

| Suite | Cases / profiles / policies | Trials per run | Runs | Policy-trial evaluations |
|---|---|---:|---:|---:|
| Smoke | Eight microcases × seven × five | 32 | 280 | 8,960 |
| Standard | 270 frozen matrix + eight microcases × seven × five | 2,000 | 9,730 | 19,460,000 |
| Convergence | Six finite microcases × seven × five | 10,000 | 210 | 2,100,000 |

Policy-trial counts are not independent draws. Standard policies share **3,892,000**
case/profile trial realizations; identical schedules can share stored files. Convergence
uses the same first 2,000 draws as standard microcases. No trial is omitted for finishing
after 168 hours; unknown scope is retained. All runs succeeded; no partial suite is
presented as complete.

Seed **20261103**; numerical version `fixed-timetable-simulation-v1`; NumPy **2.5.4**,
Python **3.12.14**, macOS arm64. SHA-256 of numerical version, whole scenario fingerprint,
profile ID, seed and task/event/hold stream ID seeds PCG64. Two uniforms per trial feed
the documented Box–Muller cosine transform. Keys exclude policy and execution order;
increasing trial count preserves the original prefix. No global RNG or parallel workers
are used. Tests verify prefix/seed behavior and common draws across policies.

| Suite | Numerical SHA-256 | Independent extracted replay |
|---|---|---|
| Standard | `889f0dd54d5234d0f6ff280e261ba9f160e8c194d4912f6f26f5266becaabe1f` | All 9,730 runs matched |
| Convergence | `bcf22abb0918ab656bd1c4a27bc9637363ab3dd470188ffa3c64cfb3ed62b343` | All 210 runs matched |

These repeats deny source-data reads and network connections and assert no optimizer or
challenge-loader import. They use the same pinned installed numerical environment, not
a newly provisioned OS; cross-platform bit identity of float transforms is unverified.
Runtime, compressed-file metadata and memory are separate from numerical hashes.

Final range review added a rejection guard for the product of large planned/crew-start
offsets and customer count. Offset/hold contributions reserve less than `2^52`
customer-seconds; existing sampled-duration bounds reserve at most another `2^52`,
keeping weighted integer arithmetic within float64's exact-integer range and int64's
capacity. This changes rejection of extreme unsupported inputs, not any profile, seed,
frozen case or policy. Original execution manifests retain the original implementation
hashes; [final standard](../research/phase5/final_standard_reproduction.json) and
[final convergence](../research/phase5/final_convergence_reproduction.json) replays record
both implementation hashes and verify identical complete numerical results after the guard.

## 6. Fixed-policy comparisons and retained regressions

Schedules are selected before sampling: the recommended fixed
`legacy-release-per-person-hour-adapter-v1`, frozen G3 protected result, FIFO,
customer-count, and deterministic per-instance best-of-four. The latter is a separately
labeled non-deployable reference, never a per-trial hindsight winner. Frozen G3 inputs
and schedules are hash-checked. No per-trial optimization or adaptation occurs.

The [complete paired table](../research/phase5/COMPARISONS.md) reports candidate-minus-
reference differences (negative is better), both completed and restricted customer-hours,
ties and worse cases. The full report retains paired trial quantiles/counts and every
secondary metric. Completed aggregates have **225 finite cases and 45 unavailable**;
restricted aggregates include **all 270**. Microcases remain in full outputs but do not
enter these descriptive matrix aggregates. Case variants and trials shared across policies
are correlated; no bootstrap, population confidence interval or significance claim is made.

For independent-0.5 variability, the combined CP-SAT result has mean paired completed
cost **25.537992 customer-hours lower** than fixed, yet **six case means regress**.
Versus best-of-four it is **4.528810 customer-hours lower**, with **eight regressions**.
There are **16,374 worse paired trials** versus fixed out of 450,000 finite pairs in that
profile. Its restricted mean difference is **−20.800534 customer-hours** across all 270
cases. These are absolute descriptive differences, not the G3 percentage statistic.

Critical/fairness costs are not hidden in the objective. Compared with fixed, independent-
0.5 CP-SAT has worse mean critical latency in **five of 45 critical-service cases** and
worse branch disparity in **14 of 225 finite cases**. Deterministic counts are four and
20 respectively. All cases and trial-level differences remain available, including ties.

G3's combined best-of-four-plus-CP-SAT **0.351% mean** gain versus fixed is distinct from
its **0.174% incremental mean** gain beyond best-of-four. **The 5% median promotion target
failed.** Keep the strongest fixed baseline as default and CP-SAT only as an optional
validated experimental comparison. Synthetic Monte Carlo findings do not overturn G3.

## 7. Convergence and misspecification

Compare full-release p10/p50/p90 from the nested 2,000 trials and all 10,000 trials on
six finite microcases. Each tolerance is `max(0.25 h, 0.02 * abs(q_10000))`.
There are **630 quantile checks; 615 pass and 15 fail**. Consequently 195 of 210
case/profile/policy combinations pass all three; 15 are `unstable_at_cap`.

| Case / profile | Affected policies | Failed quantile | Absolute change, h | Allowed, h |
|---|---|---|---:|---:|
| Censored / storm hold | Fixed, CP-SAT, best-of-four | p50 | 4.749444 | 4.082128 |
| Chain-eight / storm hold | All five | p90 | 0.389722 | 0.315594 |
| Two-crews / shared-0.5 | Fixed | p90 | 0.281944 | 0.250000 |
| Two-crews / shared-0.5 | FIFO | p90 | 0.260556 | 0.250000 |
| Weighted / independent-0.5 | Fixed, CP-SAT, customer-count, best-of-four | p90 | 0.282222 | 0.250000 |
| Weighted / independent-0.5 | FIFO | p90 | 0.265278 | 0.250000 |

The cap was reached; no seed, fixture, distribution or tolerance was changed to turn
failures into passes. The full [convergence report](../research/phase5/convergence/report.json.gz)
preserves all values. Passing microcase checks does not certify convergence for larger
scenarios, every metric, or actual restoration. Batch quantile standard errors from ten
disjoint batches are numerical sensitivity diagnostics, not empirical confidence limits.

Across fixed-baseline finite matrix cases, mean full completion / mean case p90–p10 width
is **197.796 / 0 h** for deterministic, **232.546 / 48.076 h** for independent-0.5,
**245.102 / 142.868 h** for shared-0.5, and **247.286 / 143.572 h** with storm hold.
Uniform-family sensitivity gives **205.491 / 16.635 h**. These are means of case statistics,
not a pooled population quantile. Increasing log SD changes mean as well as spread;
shared correlation and timetable floors alter delay propagation. Uniform variance is not
matched, so this does not isolate distribution shape. All seven profiles and both cost
definitions appear in the sensitivity table. Profiles use distinct streams; common-random-
number pairing applies to policies within a profile, not comparisons between profiles.

## 8. Quantiles, censored outcomes and retained artifacts

Quantiles use nearest rank with no interpolation. Report p10/p50/p90 and their width for
completion/release, customer-hours, critical groups, branch and small-group waits, plus
50/90/100% release thresholds, weighted median/p95/max and paired differences.
Full-scope totals remain null when scope is unresolved. A finite-subset quantile is never
substituted. Reachable release thresholds retain the full population denominator.
The generic summary field `unresolved_trials` counts unavailable metric values, including
not-applicable small-group means when no small groups exist; customer-level unknown mass
is separately reported by `unresolved_customers` and must not be inferred from that counter.

Known releases later than 168 hours are **censored for horizon reporting**, not unknown;
their finite completion remains available. Unknown releases remain unknown. Restricted
cost is the integral of uncredited release through 168 hours, not an assertion that unknown
restoration occurs then. Known-later and unresolved customer masses remain separate.
Simulation quantiles are conditional on declared assumptions, not the original elapsed
envelope, observed ETRs, empirical interval coverage or calibrated confidence.

Local complete NPZ trial caches retain group-release ticks and makespan arrays, sufficient
to reconstruct every metric and milestone exactly from immutable group memberships.
The full standard cache is roughly 1 GiB and remains ignored, rather than permanently
entering Git. The PR retains **all** compressed manifests/reports/timing records, numerical
hashes, reproduction records and complete paired summaries. Fresh clones can regenerate
all raw trials offline after dependency installation. This is not a claim that committed
quantile summaries are lossless trial data.

All **56 fixed-baseline microcase/profile presets**, including unknown/unstable ones, also
retain lossless NPZ trial data in Git under [demo](../research/phase5/demo/presets.json).
Their inputs, schedules, profile binding and convergence flags are explicit: 38 stable,
four unstable at the cap, and 14 unavailable full completions. They are
prepared for future review, not approved for product display or served by an endpoint.
`CHECKSUMS.json` verifies the report/demo bundle. Source/real geometry, customer declarations,
credentials and downloaded observations are absent from these independently authored inputs.

## 9. Computational performance and limitations

The standard numerical run took **195.494 s**, peak process RSS **308,854,784 bytes**
(294.55 MiB). Median per-policy run time was **0.009129 s**, maximum **0.239061 s**.
The six small convergence fixtures took **1.447 s**, peak **100,990,976 bytes**
(96.31 MiB). These are local Python 3.12.14/macOS arm64 observations, including validation,
sampling and compressed writes, on an Apple M4 Pro (12 CPU cores, 24 GiB memory).
Other verification processes shared this host; these are not isolated latency trials.
RSS is the process high-water mark, including NumPy/native
memory. Cases execute serially and retain only current numerical arrays plus metadata.
Report rendering is separate and these timings do not include it.

No web response-time SLA or deterministic timing claim is made. Standard tasks span
10/25/100 and crews 1/2/4. Trial limits, input-size/range checks and one worker bound
execution. Fresh package installation and cross-platform reproduction remain unverified;
source-free extraction on this installed host is verified. No heavy endpoint or browser
simulation is added.

## 10. Tests and executable reproduction

| Check | Observed result |
|---|---|
| Full Python regression, G1–G4 plus simulation | 322 passed (301 prior + 21 simulation); final record linked above |
| Browser regression | 49 passed, 58.1 s |
| Strict TypeScript/Vite production build | Passed |
| API type regeneration | Byte-identical |
| Original golden CLI | Passed; original labor/envelope/null semantics intact |
| Four source pins / 24 legacy cases | Match / passed |
| Frozen G2 integrity / G3 regression | Covered by unchanged existing suites; all historical artifacts preserved |
| G4 No-Go decision and cached-source replay | Byte-identical; source-free/network-denied decision test passed |
| Standard/convergence source-free simulation | Complete numerical hashes match |
| Report and demo trial integrity | Complete matrix, canonical digest and packaged checksums verified |
| Dependency consistency, links and whitespace | Final verification record |

Tests cover known distributions, rounding, deliberate idle, crew/task dependencies,
common randomness, prefixes, nulls, censoring equality, empty dependencies, corrupt
schedules/arrays, overflow, invalid evidence/profile/trial counts, report tampering and
refused overwrite. During development one censoring test wrongly assumed FIFO while
using the default short-task-first policy; the test was corrected to request FIFO.
No production algorithm, fixture or expected historical artifact was changed for it.
The initial failure is not presented as a passing run; final runs pass.

```sh
.venv/bin/python -m pip install -r requirements-simulation.txt
.venv/bin/python scripts/run_simulation.py --suite smoke --output /tmp/gridguide-g5-smoke
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-smoke
.venv/bin/python scripts/run_simulation.py --suite standard --output /tmp/gridguide-g5-standard
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-standard
.venv/bin/python scripts/run_simulation.py --suite convergence --output /tmp/gridguide-g5-convergence
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-convergence
.venv/bin/python scripts/check_simulation_reproduction.py --reference /tmp/gridguide-g5-standard --output /tmp/gridguide-g5-replay.json
.venv/bin/python scripts/package_simulation_review.py --standard /tmp/gridguide-g5-standard --convergence /tmp/gridguide-g5-convergence --output /tmp/gridguide-g5-review
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m unittest discover -s tests -q
.venv/bin/python scripts/run_legacy_benchmark.py --output /tmp/gridguide-g5-legacy.json
.venv/bin/python scripts/evaluate_risk_feasibility.py --output /tmp/gridguide-g5-risk.json
cmp docs/research/phase4/feasibility.json /tmp/gridguide-g5-risk.json
.venv/bin/python -m backend.demo
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run types:generate
git diff --exit-code -- frontend/src/api.generated.ts
```

Use fresh output paths; numerical execution refuses overwrites. Full source-dependent
regressions need authorized challenge files; no skipped source suite is counted as passed.
No real-data split, empirical interval evaluation, model training, operational validation,
deployment or live AI provider test was performed or claimed in Phase 5.

## 11. Future integration and effort

The following requirements bind downstream customer and operator interfaces. This is
handoff guidance only, not authorization to implement those interfaces.

| Output state | Required presentation and behavior |
|---|---|
| Stable | Identify the specific fixture, profile, policy, quantiles and trial-count check that passed. Microcase success does not establish convergence for larger cases or other metrics. |
| Unstable | Preserve the failed numerical checks and diagnostics; visibly flag the affected quantiles. Never present them as converged estimates. |
| Unresolved | Keep unknown completion times and full-scope quantiles unavailable. Never turn them into finite ETRs, including by substituting the 168-hour scoring horizon. Retain unresolved customer mass separately from known-later censoring. |
| Unsupported | Explicitly withhold results when no vetted matching artifact exists, its binding/version fails validation, or the requested scope is outside supported presets. Do not fabricate or silently substitute an estimate. |

Numerical convergence and completeness of evidence are distinct dimensions; one badge
must not erase another limitation. When convergence was not assessed, say so rather than
infer stability or confuse that absence with a failed check or unresolved completion.

All simulation intervals must be labeled **conditional on synthetic assumptions, not
empirically calibrated restoration confidence**. Preserve the fixed planned-start-floor
interpretation as fixed-timetable delay propagation, not adaptive dispatch. Keep the
original conditional envelope distinct from simulation quantiles. Same-environment
numerical reproduction is verified; cross-platform bitwise equivalence and empirical
calibration remain unverified.

Use only vetted, bounded, precomputed fictional artifacts for future public demonstration,
with exact input/profile/policy/version bindings. The 56 committed fictional presets
retain their stable, unstable and unavailable diagnostics; they do not authorize arbitrary
inputs or implied convergence outside checked scope. No browser numerical engine or
unrestricted Monte Carlo route. Complete regenerable trial caches may remain outside Git;
committed reports, manifests, numerical checksums and all 15 failed convergence combinations
and their diagnostics must remain preserved.

Future Phase 7 comparisons should show fixed/default and optional CP-SAT separately,
paired cost distributions and critical/fairness regressions under identical assumptions,
bind selection to the artifact fingerprint and require human review. Retain G3's combined
versus incremental distinction and explicit failed 5% target. Neither stochastic sensitivity
nor G4 No-Go warrants changing the default or describing a policy as operationally safe.
Keep `legacy-release-per-person-hour-adapter-v1` as the strongest fixed baseline default
and CP-SAT optional/experimental. Retain case-level regressions and fairness/critical-service
tradeoffs in downstream comparisons; aggregate gains must not hide them.
No Phase 6/7 implementation is included.

This agent-assisted session is not a measured human engineering-day sample. The roadmap's
6–9-day Phase 5 estimate was provisional. Removing that allowance from the previous
24–37-day required-work estimate leaves roughly **18–28 provisional engineering days**;
review/integration and archival effort remain uncertain. No deadline or automatic phase
transition follows. Stop after the authorized G5 merge; do not expand into fitting distributions,
additional optimizer tuning or new UI features to resolve the disclosed numerical limits.

## 12. Acceptance checklist and reviewer decisions

- [x] Contract, profiles and replay convention committed before implementation/evaluation.
- [x] Required profile families, exact deterministic reference and family sensitivity implemented.
- [x] Fixed assignments/orders, common random numbers and independent feasibility checks.
- [x] Complete 2,000-trial matrix and designated 10,000-trial convergence runs retained.
- [x] Every failed convergence check, paired regression, tie and null preserved.
- [x] Source-free full reproduction, reports, lossless demo trials and checksums delivered.
- [x] Applicable regressions executed; source data, application defaults and G2–G4 preserved.
- [x] G3 failed target and G4 evidence-bounded No-Go explicitly carried forward.
- [x] Independent reviewer accepts the fixed planned-start-floor replay interpretation.
- [x] Reviewer accepts the assumption provenance, descriptive comparisons and 15 flagged
      convergence failures as an honest bounded experiment, without empirical calibration.
- [x] Reviewer accepts regenerable full caches plus committed reports/demo trial evidence,
      same-host reproducibility limits and separately gated future integration.
- [x] Owner approves G5 and authorizes merge after documentation/preservation checks.
- [ ] Owner separately authorizes Phase 6 or later work; no such authorization is included.

G5 requests review of numerical correctness, evidence boundaries and reproducibility,
not certification of utility restoration accuracy, operational safety or a new default.
