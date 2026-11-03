# v1.1.0 Phase 2 — G2 review packet

The owner approved G1 and PR #3 was merged at `9b04fcf`. This phase implements the
[approved benchmark foundation](V1_1_0_MASTER_ROADMAP.md) on
`feat/v1.1-phase2-benchmark-foundation`. **G2 acceptance is pending owner review.
Do not merge this PR or start Phase 3 without approval.** No release, tag or deployment
is authorized or performed by this phase.

## Deliverables and boundaries

| Deliverable | Implementation / evidence |
|---|---|
| Versioned scheduling problem and metric specification | [Specification](../benchmarks/PHASE2_SPEC.md), `benchmarks/contracts.py` |
| Frozen independent synthetic dataset | `benchmarks/scenarios.py`, [270-case manifest](../../benchmarks/frozen/evaluation-v1.json), preregistration commit `b32156f` |
| Four baseline adapters | `benchmarks/policies.py`; common inputs, tick model, feasibility constraints and stable ties |
| Independent validation | `benchmarks/validation.py`; independent reachability, rational durations, membership expansion and metric reconstruction |
| Exhaustive small-instance reference | `benchmarks/oracle.py`; up to eight tasks, 250,000 nodes, explicit unsupported/interrupted statuses |
| Offline execution and separate rendering | `scripts/run_benchmarks.py`, `scripts/report_benchmarks.py` |
| All machine-readable results | [Deterministic result archive](../benchmarks/phase2/standard/results.jsonl.gz), [run manifest](../benchmarks/phase2/standard/manifest.json) |
| Complete baseline report | [REPORT.md](../benchmarks/phase2/standard/REPORT.md), [aggregates](../benchmarks/phase2/standard/aggregates.json) |
| Runtime/resource observations | [Separate measurements](../benchmarks/phase2/standard/runtime_observations.json) |
| Source-dependent regression lane | `benchmarks/legacy.py`, [24 frozen legacy cases](../../benchmarks/frozen/legacy-v1.json), [verification](../benchmarks/phase2/legacy_check.json) |
| Tests | `tests/test_benchmarks.py`, `tests/test_benchmarks_source.py`, all existing suites |

No application code, Phase 1 contract/fixture, API type, frontend, legacy arithmetic,
raw/processed source, contributor notice or teammate pipeline changes. Offline contracts
are separate from unchanged centralized HTTP contracts. No new dependency beyond the
existing pinned Pydantic is required. No optimizer, training, simulation distributions,
hosting, CI or unrelated refactoring was added.

## Observed baseline results

Standard evaluation: **270 cases × 4 policies = 1,080 runs**. Eight hand-computable
microcases add 32 runs, for **1,112 total**. Every run passed independent feasibility
and metric validation. No case was removed or changed after baseline results.

The following descriptive means are across the complete standard matrix. They are
synthetic waiting costs, not utility benefit or an improved GridGuide optimizer.
Completed means use **225 finite cases per policy**; the 45 blocked-root cases have null
full costs. Restricted means use **all 270 cases per policy** under the no-credited-release
convention. These two columns have different metrics and denominators and must not be
compared as equivalent measures. Family/scale/crew breakdowns and all ties remain in
the full report.

| Policy | Mean completed modeled customer-hours (225) | Mean restricted-horizon customer-hours (270) |
|---|---:|---:|
| FIFO | 89,147.551 | 55,663.400 |
| Customer count | 70,230.987 | 49,542.407 |
| Legacy release/person-hour adapter | 63,560.969 | 45,778.774 |
| Legacy critical-proxy-first adapter | 65,232.116 | 46,876.000 |

The 5% Phase 3 improvement remains a preregistered research target. These are comparisons
among baseline adapters, not evidence that Phase 3 has been implemented or that its
promotion target has been met. No significance or operational-benefit claim is made.

Completed modeled customer-hours sum disjoint group membership × last required repair
completion from modeled response origin. Unknown full release gives null. Restricted
scoring integrates through 168 hours, credits known releases, and retains unresolved
customers for the full horizon **without assigning them a finite restoration time**.
Known releases beyond the horizon are censored for that analysis and separately counted.
Task makespan and complete customer-release time are distinct. Critical latency, nearest-rank
weighted quantiles, small-group waits and branch disparity stay separately reported.
See the specification for every field, tie, null and aggregation rule.

## Validator and oracle evidence

The validator imports neither policy scheduling nor generated metrics. It revalidates
problem membership and identities, executable/unscheduled scope, crew availability,
non-overlap, prerequisite order, blocked work and duration arithmetic. It independently
reconstructs all metric fields and simultaneous milestones. Tests deliberately forge
missing/duplicate/unknown tasks and crews, dates/times, customer membership, early releases,
finite unresolved totals, fingerprint bindings, makespan and customer-hour values.

Six fully known microcases completed exhaustive search, producing **24 policy/oracle
comparisons**. Two blocked/unknown microcases produce eight explicit unsupported entries.
Standard 10/25/100-task problems do not receive optimality claims. Extra tests exercise an
eight-task independent one-crew enumeration, an eight-task chain, delayed crews, overlapping
customer dependencies and forced budget exhaustion. An interrupted enumeration is never
reported optimal, even if it found an incumbent.

Hand-check example: tasks of 4 and 1 assumed person-hours serving disjoint groups of 1
and 10 customers under the one-effective-worker assumption produce FIFO cost
`1*4 + 10*5 = 54` customer-hours. The exhaustive minimum is `10*1 + 1*5 = 15`.
Overlap microcase: a two-customer group needs both 2 h and 3 h tasks, while a one-customer
group needs the first task only; FIFO cost is `2*5 + 1*2 = 12`, not a sum of overlapping
asset-membership releases. A 200 h + 1 h serial case has 401 completed customer-hours
and 336 restricted customer-hours; both releases are known and horizon-censored, not unresolved.

## Reproducibility and checks

Python 3.12.14 and Pydantic 2.12.3 on the reference macOS/arm64 host are recorded in the
manifest. The benchmark uses one worker, no external AI/network, deterministic hash draws,
one-second ticks and a fixed oracle node budget. Runtime observations vary by machine/run;
the standard run's scheduler+metrics+validation measurements sum to 23.367 wall seconds,
with maximum traced Python allocation peak 751,509 bytes. Those numbers include tracing
overhead and exclude oracle/setup time; they are neither RSS nor response-time guarantees.

The result payload's SHA-256 is
`5384203f7d7ced30c1b7bd1f62f7770d18a542f56a47ddc9284f8f7a620a1dc1`.
The evaluation manifest's SHA-256 is
`985b1e1963fa4006f83417586ce3cb18ed6981dc9f77c3e56cc512e007338527`.
Generator drift, altered manifest bytes or missing case/policy rows fail verification.
The full suite also runs in an extracted source-free directory with source opens and
outgoing network connections forbidden, reproducing the same numerical payload hash.
Runtime observations are intentionally excluded from that equality claim.

| Check | Result |
|---|---|
| Final full Python suite | 256 passed (224 existing + 32 new), 91.459 seconds |
| Browser regressions | 49 passed, 56.7 seconds |
| TypeScript/Vite production build | Passed |
| Generated API types | Regeneration byte-identical; no API change |
| Golden CLI | Passed; original person-hour and conditional-envelope values unchanged |
| Full source audit | Completed; all four pinned hashes match |
| Separate original-planner regression | 24 cases passed, including both policies, crew/people combinations and blocked upstream |
| Standard benchmark | 1,112/1,112 validated, zero failed/invalid |
| Determinism | Micro reruns byte-identical; full isolated rerun matches numerical payload hash |
| Dependency consistency | `pip check`: no broken requirements |

The browser checks use the preserved prepared/fixture application, not a new synthetic UI.
No CI result or operational safety certification is implied.

Run into **new** output directories; existing directories are rejected:

```sh
.venv/bin/python scripts/run_benchmarks.py --suite standard --output /tmp/gridguide-g2-reproduce
.venv/bin/python scripts/report_benchmarks.py /tmp/gridguide-g2-reproduce
.venv/bin/python scripts/run_benchmarks.py --suite smoke --output /tmp/gridguide-g2-smoke
.venv/bin/python scripts/report_benchmarks.py /tmp/gridguide-g2-smoke
.venv/bin/python -m unittest discover -s tests -p test_benchmarks.py -v
```

Smoke uses six development-seed 10-task cases plus the eight microcases (56 policy runs).
The full matrix is practical locally; smoke is for routine iteration, not a substitute
for G2 acceptance. Inspect compressed JSONL using Python `gzip.open` or `gzip -dc`.
Compare the manifests' `results_uncompressed_sha256`, not runtime-observation bytes.
A minimal source-free installation needs `requirements-benchmarks.txt`, the `benchmarks/`
package and frozen manifest, shared `backend/__init__.py`, `contracts.py`, `risk_rules.py`,
and the two runner/renderer scripts. The isolation test constructs and verifies that set.

Full developer checks, including explicitly source-dependent tests:

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m unittest discover -s tests -q
.venv/bin/python scripts/run_legacy_benchmark.py --output /tmp/gridguide-g2-legacy-check.json
.venv/bin/python -m backend.demo
.venv/bin/python scripts/audit_data.py --output /tmp/gridguide-g2-source-audit.json
npm --prefix frontend run types:generate
npm --prefix frontend run build
npm --prefix frontend test
```

Missing challenge files make source tests unavailable/failing; synthetic-only execution
never counts them as passed. Source data is not required by the standard benchmark.

## G2 acceptance checklist

- [x] Fetch/verify merged Phase 1, clean tree and dedicated Phase 2 branch.
- [x] Preserve v1.0.0, history, source files, attribution, Phase 1 behavior and legacy rules.
- [x] Versioned identical input contract separates repair and energization dependencies.
- [x] Four stable baseline policies with declared legacy-normalization limitations.
- [x] Independent validator catches structural and metric corruption.
- [x] Exhaustive small-instance reference with enforced limits and honest statuses.
- [x] Six-family complete scale matrix, distinct development seeds and frozen hashes.
- [x] Completed, restricted, censored and unresolved quantities remain distinct.
- [x] All cases retained; deterministic results separated from runtime observations.
- [x] Source-free full reproduction, legacy regression lane and applicable checks.
- [x] Complete results, report, specifications, commands and limitations retained.
- [ ] Owner accepts benchmark fairness and evidence boundaries (G2).
- [ ] Owner authorizes merge; Phase 3 remains separately gated.

## Limitations, effort reassessment and stop

These structural families are independently authored synthetic experiments. Their sizes,
efforts, customer populations and available crews do not estimate a utility population.
The blocked family is deliberately severe; partial-release edge behavior is separately
tested. The benchmark omits routes, skills, calendars, switching, real clearance and
actual productivity. Unknown times remain unknown. Branch/group fairness is descriptive,
not demographic fairness. No real critical attachment is inferred.

The generalized legacy policies preserve ranking ideas, not exact equivalence with the
four-candidate dual-envelope UI. Its exact behavior is independently preserved in the
source regression lane. Exhaustive search is a bounded correctness reference, not a
production optimizer. Statistical promotion and solver runtime gates belong to Phase 3.

G1's acquisition/licensing gaps remain unchanged. No new observations or private/paid-data
dependencies were introduced. Original history exposure is not remediated by this work.

Phase 2 used an agent-assisted implementation and verification session, not a measured
human engineering-day study. The initial 5–7-day estimate remains a provisional planning
estimate. Reassessment retains approximately 35–53 engineering days for remaining required
work, plus 6–10 conditional modeling days, pending actual review burden and later findings.
No deadline, automatic promotion or scope expansion follows from these estimates.

Stop at G2 review. No merge, Phase 3 work, release tag, GitHub Release or deployment.
