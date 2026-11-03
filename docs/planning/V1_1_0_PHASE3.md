# v1.1.0 Phase 3 — G3 review packet

**Implemented for independent review; G3 is not approved. Do not merge or begin later
phases without owner approval.** Based on merged G2 at
`8f1b0640f7a080de1578fc10dc195182fd7fec80`, on branch
`feat/v1.1-phase3-restoration-optimization`.

## Outcome and default recommendation

The optimizer returns independently verified schedules and improves some cases, but
**misses the preregistered 5% median promotion target**. Against the selected strongest
fixed baseline, completed-customer-hour median improvement is **0%**, clustered 95%
median interval **[0%, 0%]**; mean paired improvement is **0.3510349569%**. No benchmark,
comparison method or search budget was changed to manufacture success.

Keep the strongest fixed baseline as the recommended default for future integration.
Offer the validated incumbent-protected optimizer as an explicit experimental comparison
only after G3 review. This PR changes no application default or endpoint. It does not
claim reduced real restoration times, operational safety or an untouched final holdout.

## Implementation and mathematical design

- `backend/optimization.py`: optional, lazy OR-Tools CP-SAT 9.14.6206; versioned
  `restoration-cpsat-v1`; existing benchmark contracts and independent G2 validator.
- One non-preemptive interval per task, exactly one assigned crew, per-crew non-overlap,
  declared availability and separate repair-precedence/customer-release constraints.
- Primary integer customer-weighted release ticks; restricted-horizon objective with
  constant unresolved membership for partial scope. Unknown completion stays null.
- Same G2 upward-rounded one-second durations; standard one-effective-worker assumption;
  no AEP multiplier applied to synthetic effort and no source planner change.
- Secondary executable makespan only after proven primary optimum, with primary equality
  fixed. No weighted objective can trade away customer-hours.
- Validated best-of-four incumbent/hints and objective ceiling. Every candidate and
  reported metric independently checked; explicit baseline fallback on absence, unknown,
  infeasibility, invalid output, mismatch, range error or worse objective.
- Offline 0.2 deterministic primary / 0.05 secondary budgets, one worker, seed 20261103.
  Interactive <=25 tasks/four crews, shared two-second solve wall budget and separately
  measured five-second wrapper budget. Raw status/proof and returned provenance differ.

The [model specification](../research/phase3/MODEL.md) details the horizon proof,
objective, nulls, two-stage rationale, failure boundary, alternatives and official API
references. Dependency versions are in `requirements-optimization.txt` and each manifest.
The original planner, baseline policies, validation, contracts, metrics, frozen manifests,
source data, Phase 1 artifact, frontend, notices and contributor work are unchanged.

## Preregistration and comparison integrity

[Protocol v1](../research/phase3/EVALUATION_PROTOCOL.md) was committed at **5ac55cd**,
before implementation. Solver/model/testing commit **44d58ad** preceded the full published
evaluation. No implementation or solver configuration change followed that evaluation.
The unchanged G2 artifact verifies the fixed comparator by lowest mean completed cost
on common finite cases, with stable policy-ID tie-breaking:
`legacy-release-per-person-hour-adapter-v1`.

Per-instance best-of-four is reported separately; FIFO, customer count and both legacy
policies remain visible. Paired percentage = 100*(baseline-optimizer)/baseline. Zero/zero
is a tie; undefined percentages and absolute regressions are preserved. Macro equal-family,
scenario mean/median and micro aggregate summaries are all in the report.

The 270-case suite was already published and inspected. It is **not blind**. Development
used only seeds 17/29 and micro/adversarial correctness cases. No new final holdout was
sealed or claimed; this bounded phase measures engineering behavior on the public suite.
Further tuning/generalization claims would require a separately preregistered untouched
set and one final evaluation, not repeated tuning against these published results.

The uncertainty procedure resamples structural-family and generator-seed labels independently
with replacement, taking their Cartesian cells with multiplicity and retaining all task-scale
and crew variants together. Fixed scale/crew levels are not treated as independent replicates.
5,000 resamples, seed 20261103, nearest-rank percentile endpoints. Only five finite families
and five seeds (six families for restricted scoring) make these intervals limited design
sensitivity evidence, not calibrated utility-population confidence.

## Complete experiment artifacts

- [Published report](../benchmarks/phase3/published/REPORT.md) and [machine-readable report](../benchmarks/phase3/published/report.json).
- [All case-level results](../benchmarks/phase3/published/results.jsonl.gz), [manifest](../benchmarks/phase3/published/manifest.json), [separate timings](../benchmarks/phase3/published/timings.json).
- [All development results](../benchmarks/phase3/development/results.jsonl.gz) and [development report](../benchmarks/phase3/development/REPORT.md).
- [Full source-free repeat](../benchmarks/phase3/sourcefree_check.json), [interactive measurements](../benchmarks/phase3/interactive_check.json), [legacy verification](../benchmarks/phase3/legacy_check.json).
- [Standalone reproduction command verification](../benchmarks/phase3/script_reproduction_check.json), an additional identical full run to verify the distributed reproduction script.

The development artifact is retained as an earlier development snapshot. A later range-guard
hardening and failed-artifact renderer correction occurred before publication evaluation;
its implementation hashes are historical, not a claim it matches the final code byte-for-byte.
One initial correctness test wrongly demanded strict improvement over an already-optimal
best-of-four incumbent. The solver correctly tied; the assertion was corrected to compare
with the demonstrably suboptimal FIFO schedule. This did not change any evaluation case,
solver algorithm or budget. No unsuccessful published experiment was discarded.

## Exact published benchmark findings

270 evaluation cases plus eight microcases = **278 returned schedules**. All passed the
unchanged independent feasibility/metric validator. No missing, invalid or failed case;
all ties, unavailable full outcomes, budget stops and fallbacks remain recorded.

Completed results use the 225 finite evaluation cases; the 45 blocked-root cases have
null full totals. Restricted results include all 270, retaining unresolved customer mass
through 168 hours without assigning it a finite restoration time.

| Comparator | Completed mean paired improvement | Completed median | Completed wins / ties / regressions | Restricted mean paired improvement (270) |
|---|---:|---:|---|---:|
| Fixed release/person-hour baseline | 0.3510349569% | 0% | 30 / 195 / 0 | 0.2925302099% |
| Per-instance best-of-four | 0.1736351944% | 0% | 27 / 198 / 0 | 0.1446970745% |
| FIFO | 28.1299001884% | 32.3283082077% | 180 / 45 / 0 | 21.3791504581% |
| Customer count | 8.9021363013% | 8.0143211237% | 176 / 49 / 0 | 7.2990305546% |
| Critical-proxy-first adapter | 3.0239948055% | 0% | 71 / 154 / 0 | 2.5598245122% |

Fixed-baseline mean paired improvement interval: **[0.0066916122%, 1.1119193977%]**;
median interval **[0%, 0%]**. A positive small mean does not satisfy the median target.
Completed optimizer mean cost is **63,540.28908024691 customer-hours** over 225 cases;
restricted mean is **45,761.540900205764** over 270. Mean paired percentages differ from
aggregate cost percentages; both are explicitly labeled in the machine-readable report.

| Structural family | Mean completed paired improvement vs fixed | Wins / 45 cases |
|---|---:|---:|
| Serial chain | 0% | 0 |
| Independent branches | 0.0626590951% | 4 |
| Shared upstream bottleneck | 0.0432666271% | 3 |
| Overlapping dependencies | 1.5865899672% | 19 |
| Critical-service tradeoffs | 0.0626590951% | 4 |
| Blocked prerequisites | Full objective unavailable | Restricted ties on all 45 |

Mean completed improvement by task count: **0.6633032603%** (10), **0.3831969943%** (25),
**0.0066046162%** (100). Every task-scale median is zero. Means by crew count are
0.0873382759%, 0.3198343542%, 0.6459322406% for 1/2/4 crews. Detailed macro/micro and
family/scale/crew breakdowns remain in `report.json`; no easier subset replaces the target.

## Solver bounds, fallbacks and secondary tradeoffs

Across all 278 cases: **52 OPTIMAL, 177 FEASIBLE, 3 UNKNOWN, 46 NOT_RUN**.
The 46 non-runs are no-executable-work cases (45 evaluation roots plus one microcase).
Three UNKNOWN searches explicitly returned validated baselines. FEASIBLE denotes an
incumbent without proof under the deterministic work cap, not an optimal solution or
wall-time timeout. No offline wall cutoff was used. The worst recorded relative solver
gap is approximately **96.61%**; weak bounds and small budgets limit optimality evidence.
The case-level raw bounds/objectives and status are retained for all attempted solves.

There are no returned primary-cost regressions on this suite. That does not imply every
secondary metric improves. Across all 278 cases versus the fixed baseline:

- Makespan increases in **5** cases, at most **1 hour**.
- Branch mean disparity increases in **20** cases, at most **24.3059291 hours**.
- Small-group mean waiting increases in **17** cases, at most **16.75 hours**.
- **5** explicit critical-group latencies increase, at most **3 hours**.

These are deliberate disclosures, not hidden objective weights. Improving total customer
waiting can delay particular groups. Future operator review must show these tradeoffs.

## Correctness, performance and reproduction

All six supported complete G2 microcases match the independent exhaustive oracle exactly
in integer customer-seconds; blocked and unknown microcases remain explicitly unsupported.
Tests cover shared dependencies without repair precedence, bottlenecks, delayed crews,
critical tradeoffs, ties, already-optimal incumbents, highly unequal groups, long/short
jobs, ideal-person rounding, cycles, missing evidence, blocked ancestors, malformed
candidates, bad baselines, missing solvers, status injection, zero work budget and overflow.
The validator and oracle were not weakened or changed.

| Verification | Result |
|---|---|
| Full Python suite | **281 passed**, 101.043 s (256 existing + 25 optimizer tests) |
| Browser suite | **49 passed**, 54.1 s |
| Strict TypeScript/Vite build | Passed |
| Generated API types | Byte-identical after regeneration |
| Golden CLI / source audit | Passed; all four pinned source hashes match |
| Legacy four-candidate lane | **24 exact cases passed** |
| Development experiment | 80 cases, zero returned violations or oracle mismatches |
| Published experiment | 278 cases, zero returned violations or oracle mismatches |
| Full source-free repeat | Identical numerical hash, raw/processed file opens and external connections forbidden |
| Dependency consistency | `pip check` passed |

Published numerical payload SHA-256:
`c438686e6f62c62dc31fd4871b80f1f8cab0b90434378b7d78d8fc676c9c8f49`.
Timing fields are separate. Repeated execution was solely a reproduction check, not tuning.
The reference environment is Python 3.12.14, macOS arm64, OR-Tools 9.14.6206. Published
wrapper times sum to **96.908 seconds**, maximum **2.566 seconds** (includes 100-task offline
cases). Six separate 25-task/four-crew development interactive probes had maximum wrapper
**0.364 seconds**, maximum summed solve wall time **0.355 seconds**. Configured solver caps
are not deterministic wall-time promises; no HTTP endpoint or operational SLA was tested.

Install optional dependencies and use new output paths (existing directories are rejected):

```sh
.venv/bin/python -m pip install -r requirements-optimization.txt
.venv/bin/python scripts/run_optimization.py --suite development --output /tmp/gridguide-g3-dev
.venv/bin/python scripts/report_optimization.py /tmp/gridguide-g3-dev
.venv/bin/python scripts/run_optimization.py --suite published --output /tmp/gridguide-g3-review
.venv/bin/python scripts/report_optimization.py /tmp/gridguide-g3-review
.venv/bin/python scripts/check_optimization_reproduction.py --reference docs/benchmarks/phase3/published --output /tmp/gridguide-g3-reproduction.json
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m unittest discover -s tests -q
```

For bounded interactive probes use `--suite development --mode interactive`. A micro-only
smoke run is `--suite micro`. Renderer execution does not run the solver. All source-free
numerical work needs no keys/network after dependency installation; the explicit legacy
lane and source audit still require authorized challenge files. No unexecuted source test
is counted as passed. Dependencies/host/settings and implementation hashes are recorded.

## G3 checklist and integration recommendations

- [x] Protocol/comparator/cluster method committed before implementation.
- [x] Phase 2 frozen inputs, baselines, metrics and validator preserved.
- [x] Mathematically explicit integer model and proof-gated secondary objective.
- [x] Safe validated incumbent and tested failure/status/unknown fallbacks.
- [x] Oracle agreement and zero returned feasibility violations.
- [x] Full matrix retained; paired clustered inference, nulls and tradeoffs disclosed.
- [x] Exact reproducibility and applicable existing/new verification completed.
- [x] Research target assessed honestly: **not met**; no default promotion claimed.
- [ ] Independent reviewer accepts model scope, correctness and negative-result interpretation.
- [ ] Owner approves G3/merge; later phases remain separately gated.

Review questions: accept the conditional integer model and explicit subset objective?
Accept the limited cluster uncertainty interpretation without a blind holdout claim?
Keep strongest fixed baseline default and solver opt-in, given weak large-case bounds
and no median improvement? Are the critical-service/fairness tradeoffs sufficiently visible?

For **Phase 5**, use fixed precomputed validated schedules and common random draws;
never let a policy inspect future sampled durations. Preserve the deterministic tick model,
unknown clearance and unresolved denominator when adding separately labeled uncertainty.
For **Phase 7**, bind results to input fingerprint and versions, show fixed and best-of-four
comparisons, raw solver status versus returned fallback, gaps and secondary regressions,
and require human review. Neither integration is implemented here.

This is an agent-assisted engineering session, not measured human engineering-day evidence.
Reassessment retains roughly 27–41 provisional engineering days for remaining required work,
plus 6–10 conditional research days; review effort remains unknown. No automatic phase
transition, release, deployment, or claim of utility validation follows from these results.
