# v1.1.0 Phase 7 — G7 operator review packet

**Implemented for independent review; G7 is not self-approved. Do not merge, start
Phase 8/9, publish a release or deploy.** Base main / approved G6 merge:
`a5d17abad366e5ca41df35f46a687c0d6fbb8bf8`. Branch:
`feat/v1.1-phase7-operator-review`.

## Journey and actual interface

The original restoration decision page links to `/operator/` without transferring its
challenge scenario, declarations or locations. The separate entry reuses G6 typography,
controls, focus styling and responsive layout. Select a fictional example, inspect its
assumptions, compare four policies, optionally inspect the frozen experimental result,
select a policy/reason, acknowledge five limitations and export a reviewed demonstration.
This is a local fictional review workflow, not dispatch or operational authorization.

Authentic production-browser captures: [desktop comparison](../research/phase7/operator-desktop.png)
and [mobile reviewed state](../research/phase7/operator-mobile-review.png). Screenshots
and checkbox interaction were produced by Playwright, not a human accessibility review.

Run with the existing pinned web/benchmark dependencies installed:

```sh
# Terminal 1: the opt-in fictional service, no challenge files or credentials required
.venv/bin/python -m uvicorn backend.operator_api:app --host 127.0.0.1 --port 8000 --no-access-log
# Terminal 2: production frontend
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:5173/operator/`. This service also supports G6's catalog and kit.
The original dashboard still needs its explicitly selected challenge-local service.
Use one service at a time on this port. `backend.runtime` and the G1 catalog-only
publication package remain unchanged; operator composition does not silently expand that
historical package. The browser cannot review/recompute without the Python service.
No Phase 8 production distribution, hosting, authentication or security certification is implied.

## Exact comparison and evidence semantics

Eight unchanged G2 microcases cover weighted choices, overlapping release dependencies,
an eight-task chain, two crews, blocked work, unknown effort, horizon censoring and
critical-service tradeoffs. They are examples for interaction/correctness, not a new
performance evaluation suite. `data/operator/catalog.json` embeds their complete
independently authored fictional inputs and matching frozen G3 protected schedules.
Its SHA256 is pinned in `backend/review.py`; [catalog provenance](../../data/operator/README.md)
and the extraction command make every input/result traceable. No anonymized challenge
customer, source identity, geometry or outcome was used.

| Input/rule | Evidence classification |
|---|---|
| Fictional topology, efforts, crews, customer groups and critical flags | Scenario assumption |
| Duration conversion, original precedence convention, ranking, metrics and validation | Prototype policy |
| Additional declared precedence and policy/reason selection | User-declared |
| Observed outcomes, actual efficiency and unknown clearance | Unavailable |

Origin is separately `independently_authored_synthetic`. Existing six-class taxonomy
is retained; no fictional record is relabeled AEP-specified or source-derived. The
embedded G2 problem preserves its original rule classifications; explicit override
edges retain their separate user-declared lineage in the request/evidence record.

Every comparison recomputes all four unchanged G2 policies on the **same** overridden
problem: FIFO, customer count, release/person-hour and critical-proxy-first. Exact
person-hours and one-effective-worker assumption convert to the existing upward-rounded
seconds. Extra crews cannot split a task; there is no duplicate AEP multiplier. The G2
independent validator checks every returned schedule and every metric, including crew
exclusivity, repair prerequisites, executable scope and deduplicated customer release.

- Completed modeled customer-hours sum customer counts × last required repair completion
  from the common response origin. Unknown full customer scope stays null.
- Restricted-horizon customer-hours score every customer through 168 hours, retaining
  unresolved customers without assigning them a finite completion time.
- Known releases beyond that horizon are censored for horizon reporting. They are not
  unresolved; finite complete-case costs may remain available.
- Full task makespan differs from full customer release. Release milestones, critical
  group latency, median/p95/max wait, branch disparity and small-group mean wait retain
  G2 definitions. Small groups contain at most five fictional customers; these metrics
  do not establish demographic fairness. Null is displayed as **Unavailable**, never zero.

The fixed release/person-hour baseline remains recommended, using G3's preregistered
selection from the published G2 suite. It is not guaranteed best on an individual case.
The view separately identifies best-of-four by the unchanged G3 incumbent rule: integer
completed customer-seconds if all customers have finite outcomes, otherwise restricted
customer-seconds; ties use executable makespan then policy ID. It does not promote that
per-instance reference to the fixed statistical comparator or application default.

Optional CP-SAT is the **frozen protected G3 result**, not a fresh solve. The catalog is
content-pinned, its schedule is independently revalidated, and metrics are recalculated
under the exact matching original problem. Original solver status, returned source,
baseline provenance, fallback, proof status, bound and historical wrapper time remain
separate. Relative gap is `max(0, objective_ticks-bound)/max(1, abs(objective_ticks))`;
null bounds yield null gaps. Baseline computation times are not recorded and stay null;
historical solver timing is not current API latency. No solver is needed at runtime.
Changed precedence makes CP-SAT unsupported; selecting that unavailable result is rejected.

**G3's 5% median promotion target failed.** Its 0.351% mean paired gain versus the fixed
baseline belongs to the combined best-of-four incumbent plus CP-SAT. The incremental
mean beyond best-of-four is 0.174%; these have different denominators and are not additive.
Limited cluster-bootstrap interpretation and absence of a blind holdout remain unchanged.
No new solver tuning, benchmark selection, performance claim or operational approval occurs.

[All eight displayed case results](../research/phase7/case-results.json) retain every policy,
null, tie and secondary tradeoff. For example, the critical microcase's fixed baseline
has 15 completed customer-hours and 5 h critical latency. Critical-first gives **54**
customer-hours and **4 h** latency: a disclosed primary regression for earlier critical
release. The censored fixed case reports **202 completed / 169 restricted customer-hours**,
zero unresolved and one censored customer. A weighted-case precedence override increases
the fixed baseline from **15 to 54** customer-hours. Overrides are permitted hypotheses,
not promises of improvement.

## Contracts, validation and explanations

Shared operator schemas are centralized in `backend/review_contracts.py` and included in
the generated TypeScript/OpenAPI union. This module composes unchanged benchmark types;
putting those imports into `backend/contracts.py` would create a circular import because
benchmark types already depend on its primitives. No generated TypeScript is hand-edited.

The opt-in application adds only:

- `GET /api/v2/operator/scenarios`: the pinned catalog and definitions.
- `POST /api/v2/operator/compare`: bounded request → Python recomputation/validation.
- `POST /api/v2/operator/review-export`: recompute again, bind acknowledgement and export.

Operator bodies are capped at 32,768 bytes; calculation concurrency is two per process.
The request contains a known scenario ID, revision/fingerprint, request revision, selected
policy, explicit experimental flag and at most 16 additional before/after edges. Unknown
fields/tasks, self edges, duplicate/existing edges and cycles are rejected. Evidence,
clearance, effort, customer membership and arbitrary graph edits are not request fields.
A bad schedule or crew overlap cannot pass validation. Blocked tasks remain explicitly
unscheduled; a valid partial schedule is not represented as full completion.

Errors disclose no submitted data or stack traces. No request-body logging, provider calls,
free-form explanation prompt, training or simulation route is added. Deterministic server
explanations and case tradeoff labels are part of the result fingerprint. Browser checks
scenario/revision/selection bindings and cancels stale requests; mismatches hide the result.
It formats metrics and labels but performs no scheduling or objective calculation.

## Review state machine

`loading → validated/unreviewed → acknowledged → reviewed in demo`.
A failed comparison goes to unavailable with the old result hidden. A draft precedence
edit clears acknowledgements and blocks review until applied or explicitly discarded.
Policy, scenario, override or result changes recompute with a new request revision and
result fingerprint. Reason/acknowledgement changes invalidate export readiness too.
Late comparisons and exports cannot restore an obsolete reviewed state.

All five checkboxes must be explicit JSON `true`: fiction, modeled/not field-confirmed,
evidence gaps, objective/tradeoffs, and experimental/simulation limits. `1`, missing fields
and false values fail validation. Reasons are five fixed enums, including demonstration
comparison; there is no arbitrary text or identity. Server recomputation binds the selected
policy and timestamp to the exact result before it emits **Reviewed in demo**.

State is React memory only: no localStorage, sessionStorage, cookies, accounts, database
or service-worker persistence. Reload clears the review. Only explicit JSON/text downloads
persist it. The G6 worker remains scoped to `/preparedness/`; the operator entry/API are
excluded. The additional shared bundle changes its generated shell to seven exact entries,
without changing the allowlist algorithm or historical G6 artifacts.

## Export, replay and tampering boundary

Root JSON fields are exactly `version`, `comparison`, `review`, `checksum`.
`comparison` includes the request/overrides, exact fictional problem, evidence, catalog
fingerprint, fixed and best-of-four policy IDs, all policy schedules/metrics/provenance,
unsupported-uncertainty marker, explanation and result fingerprint. `review` includes
status, UTC timestamp, reason, five acknowledgements, selected policy and result binding.
The schema is `operator-review-artifact-v1`; request, comparison, evidence and catalog
also have versioned identities. Embedded model, policy and metric versions remain explicit.

Canonical hashing uses UTF-8 JSON with sorted keys, compact separators and no nonfinite
numbers. Result hash excludes only itself; artifact hash excludes only its checksum.
There is no signature, secret, authenticated reviewer, trusted identity or proof of human
attention. A person controlling a file can author another internally valid record and
recompute its checksum; replay proves internal consistency, not authenticity or history.

```sh
.venv/bin/python scripts/replay_review.py docs/research/phase7/critical-review.json
.venv/bin/python scripts/replay_review.py docs/research/phase7/override-review.json
# Or supply the JSON explicitly downloaded from /operator/.
```

The separate CLI bounds reads to 1,000,000 bytes, rejects duplicate JSON keys, reparses
strict schemas, rebinds the pinned catalog, rebuilds the overridden problem and recomputes
all four baselines. The independent validator reconstructs metrics and customer milestones.
The optional G3 schedule must match its pinned reference; replay does **not** rerun CP-SAT.
The complete reconstructed comparison must match, including explanation and fingerprints.
Forged results remain rejected after rehashing. Errors are non-sensitive.

The [critical example](../research/phase7/critical-review.json),
[override example](../research/phase7/override-review.json), readable summaries and
[CLI transcript](../research/phase7/replay.log) demonstrate successful replay. These are
**programmatically generated demonstration records**, not human acceptance records.
A fresh extracted CLI tree with no challenge files/source loader also passes replay;
a separate audit-hook run denies source opens and network connections. Full dependency
installation on another OS and cross-platform bitwise reproduction were not established.

## Tests actually executed and preservation

[Verification](../research/phase7/verification.json) records exact commands, result counts,
logs, preservation findings and artifact checksums. Tests added in this phase cover
identical inputs, independent metrics, stale/cross-scenario bindings, cycles/duplicates,
unknown evidence/tasks, actual crew overlap, metric/milestone/provenance forgery, rehashed
artifacts, explicit acknowledgements, exported JSON, session-only state, stale network
responses, no external-action endpoints and source-free replay.

| Check | Observed result |
|---|---|
| Full Python suite | 342 passed: 327 prior + 15 new operator tests |
| Existing browser suite | 49 passed |
| Production browser suite | 20 passed: 13 G6 + 7 operator tests |
| Accessibility | Zero serious/critical axe findings on all eight operator scenarios, reviewed/mobile states and existing G6 flows |
| Strict TypeScript / Vite build / generated-type byte consistency | Passed |
| Golden CLI / four source pins / 24 legacy cases | Passed / matched / passed |
| G2/G3 integrity and regressions | Existing full-suite checks passed; numerical code and frozen artifacts unchanged |
| G4 No-Go decision replay | Byte-identical; no model or prediction metric introduced |
| G5 / G6 committed checksums | 66 / 10 verified; original artifacts unchanged |
| G1 catalog isolation/publication boundary | Existing full-suite extraction/allowlist tests passed |
| Operator catalog reproduction / CLI examples | Pin-identical / both verified |

One added stale-response browser assertion initially named the wrong unknown task
(`syn-task-1` instead of the unchanged fixture's `syn-task-0`). Only that test assertion
was corrected after inspecting the fixture and actual response. The failed run is not
counted as a pass; final production run passed all 20. No numerical case was changed.

Manual G7 VoiceOver/focus observations and other-browser coverage are **unknown** and
not claimed. Automated keyboard activation, mobile/reduced-motion and axe checks do
not substitute for human screen-reader testing or establish WCAG certification. No
material accessibility defect was found in executed checks. G6's owner-accepted missing
speech/focus/environment details remain unchanged limitations, with no retest claimed.

Source data, teammate pipeline/attribution, v1.0.0 identity/history, original concern band,
null outage probabilities and application defaults remain unchanged. G3 numerical results
and methods remain frozen. G4 is an evidence-bounded No-Go, not proof of universal
public-data infeasibility; reopening requires a new versioned evidence review and quality
gate. NOAA is storm context, missing is not zero, permissions remain unverified, and
real-data split validation is unexecuted.

G5 visualization is explicitly deferred: no new intervals or Monte Carlo/API work. Its
planned-start-floor model is fixed-timetable delay propagation, not adaptive dispatch.
All 195 stable/15 unstable combinations, diagnostics and 56 presets are preserved.
Future display must distinguish stable, unstable, unresolved and unsupported/unassessed;
withhold finite ETRs for unresolved outcomes; never label synthetic conditional intervals
empirically calibrated confidence. Historical full numerical reproduction is reused
unchanged evidence, not millions of newly executed trials.

## G7 acceptance and remaining reviewer decisions

- [x] Strict versioned fictional catalog, evidence, comparison, override and review contracts.
- [x] Four identical-assumption baselines; optional validated frozen G3, fixed default.
- [x] Completed/restricted/null/censored distinctions and case-level tradeoffs displayed.
- [x] Bounded precedence, Python recomputation and independent feasibility checks.
- [x] Five explicit acknowledgements, structured rationale and stale-review invalidation.
- [x] Sanitized JSON/text export and source-free recomputation/replay with tampering tests.
- [x] Accessible native UI, production screenshots, applicable regression/preservation evidence.
- [x] No dispatch, accounts, provider call, browser engine or protected-source export.
- [ ] Independent reviewer accepts the bounded eight-case workflow and frozen-only CP-SAT integration.
- [ ] Reviewer accepts detailed G5 deferral, non-authenticating replay and documented manual/browser limits.
- [ ] Owner approves G7 and separately authorizes merge. This PR does not authorize it.

Scope is frozen here. The initial 4–6 engineering-day estimate remains provisional;
this agent-assisted session is not a measured human effort sample. Removing that
allowance from the previous 13–20-day estimate leaves approximately **9–14 provisional
engineering days** for required distribution/preservation work, plus review fixes.
Recalibrate after review; no deadline or automatic next-phase permission follows.
