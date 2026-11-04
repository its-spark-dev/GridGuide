# Phase 8 — source-free distribution and verification (G8 review)

Base: `ddaccc9fc97fedc01666f38fcebd1f2f3c5c40f3` (approved G7 merge).
Branch: `feat/v1.1-phase8-ci-distribution`. [PR #10](https://github.com/its-spark-dev/GridGuide/pull/10).
This packet requests independent G8 review. It authorizes neither merge, public hosting,
release/tag changes nor Phase 9. The public README remains product-focused and unchanged.

## Delivered scope and evidence boundaries

The new opt-in `backend.public_app` composition serves the existing G6 fictional customer
paths and preparedness kit, and G7 operator review, from one origin. `/` redirects to
`/preparedness/`; its navigation links to `/operator/`. The two bounded catalogs retain
their own identities: six G1 scenarios/18 G6 frames and eight G7 operator microcases.
The original `backend.api`, `backend.runtime`, challenge UI and catalog-only G1 archive
remain unchanged. This is a local deployment rehearsal, not an operating utility service.

No new numerical model, trained model, solver policy, simulation interval or dataset is
introduced. Four baselines are recomputed in Python and independently validated.
Release/person-hour stays the default. CP-SAT is optional and uses the pinned G3 schedule,
never a new solve; precedence overrides make it unsupported. G3's **5% median promotion
target failed**: 0.351% mean versus the strongest fixed baseline describes best-of-four
plus CP-SAT, while 0.174% is incremental beyond best-of-four. Limited cluster-bootstrap
interpretation, no blind holdout, case regressions and critical-service/fairness tradeoffs
are unchanged. Completed customer-hours, 168-hour restricted customer-hours, unresolved
customers and known-later censoring remain separate.

G4 remains an evidence-bounded **No-Go**, not universal public-data infeasibility. NOAA
storm records are not outage labels, missing is not zero, permissions remain unknown,
and real-data split validation is unexecuted. Reopening requires a new versioned evidence
review/quality gate. The original concern band and null probabilities are preserved.

G5 visualization remains deferred/unsupported. Its fixed-timetable planned-start-floor
semantics, 195 stable/15 unstable combinations, diagnostics and 56 presets are unchanged.
No microcase convergence claim is generalized; no unresolved completion becomes a finite
ETR. Future intervals must remain conditional on synthetic assumptions, not empirical
restoration confidence. Same-environment numerical reproduction is historical evidence;
cross-platform bitwise equivalence and empirical calibration remain unverified.

## CI and exact test lanes

[`ci.yml`](../../.github/workflows/ci.yml) uses commit-pinned actions, read-only repository
permissions and sparse, depth-one checkout. Challenge blobs are excluded; explicit absence
checks run before tests. No repository secrets or provider credentials are supplied.
The workflow does not build an image from the checkout: only the inspected extracted
allowlist package becomes its Docker context. No container or release is published.

[`run_test_lane.py`](../../scripts/run_test_lane.py) inventories unittest methods by AST
without importing unavailable source loaders. Every method belongs to exactly one lane;
subtests are diagnostic cases, not independently counted test methods. Reports include
case IDs, collected/executed/passed/failed/error/skipped/unavailable/not-executed counts.

| Lane | Exact matrix | Normal PR behavior |
|---|---|---|
| Public | 102 methods: G1 contracts/archive, G6 frames, G7 review, G4 artificial/ledger checks, selected G2 metrics/baselines/validator, 3 deterministic/unresolved G5 microchecks, 7 G8 tests | Executed with source opens and socket connections denied in the Python parent process |
| Authorized challenge regression | 196 methods, including mixed legacy modules and source-dependent G1/G2 regressions | **NOT EXECUTED; 196 unavailable** because no challenge files are checked out |
| Bounded research regression | 51 remaining benchmark/oracle/optimization/simulation methods | **NOT EXECUTED; 51 deferred**; optional manual workflow input `research=true` runs this lane separately |

Public CI also runs the legacy schema generator before installing the locked public
runtime, checks generated TypeScript byte consistency, builds both existing and public
frontends, regenerates dependency notices, checks frozen hashes, builds two identical
archives in tests, installs a fresh extracted runtime, runs 20 G6/G7 browser checks and
three real production browser checks each on the package and container. Separate JSON
browser reports prevent the container run from overwriting package evidence. Production
tests use the actual `deploy/serve.py`, not the fixture server's test-only worker endpoint.

The authorized source suite is local-only; do not attach protected files to Actions or
run untrusted PR code on an authorized private-data runner. Locally, source-dependent
tests, golden CLI and four source hashes were actually checked. Source absence is never
counted as a pass. Full historical Monte Carlo and full G3 reproduction are **not** rerun
per PR; see the unchanged [G2](V1_1_0_PHASE2.md), [G3](V1_1_0_PHASE3.md) and
[G5 artifact instructions](../research/phase5/ARTIFACTS.md) for complete offline commands.

```sh
# Build first; distribution tests fail explicitly if the build is absent.
npm --prefix frontend ci
.venv/bin/python scripts/build_public_frontend.py
.venv/bin/python scripts/run_test_lane.py --lane public --report /tmp/public.json
# Only in the authorized local checkout, with its existing dependencies/data:
.venv/bin/python scripts/run_test_lane.py --lane challenge --report /tmp/challenge.json
# Optional offline dependencies: requirements-optimization.txt, requirements-simulation.txt
.venv/bin/python scripts/run_test_lane.py --lane research --report /tmp/research.json
.venv/bin/python scripts/check_frozen_artifacts.py
```

The local Python verification comprised the full **348-method suite**, followed by the
new calculation-saturation test in the **102-method public lane**: all **349 distinct
methods** passed, with zero failures/errors/skips. The earlier full-suite log is retained
with its original count; repeated methods are not added to the unique total.
Existing browser **49/49**, G6/G7 production **20/20**, extracted-package **3/3**, and
container **3/3** passed locally. Strict build/types, golden CLI, 24 legacy plan cases,
four source pins and cached G4 No-Go replay passed. See [verification evidence](../research/phase8/verification.json),
[Python log](../research/phase8/python.log), [public cases](../research/phase8/public-python.json),
and [preservation](../research/phase8/preservation.json). GitHub run evidence is recorded
separately from local execution; a deferred lane is never represented as a successful job.
The [first GitHub run](https://github.com/its-spark-dev/GridGuide/actions/runs/41761494199)
passed on Ubuntu amd64 (101 public methods before the added saturation test, 20 G6/G7
browser checks and 3 package + 3 container checks). The challenge/research inventory
records are retained in [CI evidence](../research/phase8/ci-first-run.json). Final-head
checks are linked in the PR. CI verification artifacts, including the inspected ZIP,
expire after 14 days; permanent release archival is deferred to separately approved Phase 9.

## Generated cases and claim safety

New deterministic seeds 8100–8135 exercise 36 independent generated problems × four
unchanged policies (144 schedules). The independent validator checks prerequisites,
crew exclusivity, non-preemption/duration, availability, blocked/unknown work and complete
versus restricted costs. Customer expansion independently checks weighted objectives and
deduplication. Corrupted overlap/metrics are rejected. Twelve additional generated
schema cases reject cycles, unknown fields and repeated customer membership. On failure,
the exact input is retained under ignored `artifacts/phase8/failures/` with seed diagnostics.
These are correctness fixtures, not changes to G2 or a new performance evaluation set.

Seven unfounded claim classes are injected into exported explanations and rehashed:
optimality, calibrated confidence, observed topology, NOAA-as-outage-label, zero unknown
clearance, utility-confirmed restoration and default CP-SAT. Replay rejects each because
the server reconstructs the authoritative explanation. Existing G7 tests cover stale
bindings, forged metrics, overrides and invalid schedules; original AI-reference tests
also passed in the authorized suite. Public Standard explanations need no model provider.

## Explicit package and reproducibility

[`package_demo.py`](../../scripts/package_demo.py) enumerates 25 application/configuration
paths, vetted dependency notices, six fixed static files, and only the transitive JS/CSS
entries named by the two-entry Vite manifest. Unknown output files, dynamic imports,
symlinks, escapes, excessive size, secret patterns and prohibited data fields fail closed.
Both catalogs are content-pinned; prepared frames match the accepted bytes; every offline
cache entry must match its hash. Inspection compares every archive byte against approved
inputs. Extracted startup rejects unexpected files as well as changed hashes.

The [complete manifest](../research/phase8/package.json) records **38 files**, **558,452
uncompressed bytes**, and reproducible archive SHA256
`a5734a145fbf60e0de0e84fd300049b109109464caa32ccb32c3c776843ee1da`.
Two same-environment builds are byte-identical. Cross-platform ZIP/compression identity
is not promised; content hashes are the portable inspection reference.
No `.git`, challenge loader, challenge source records, real geometry, private prepared
output, provider module/credential, Node installation, arbitrary upload or personal
declaration is included. `optimization.py` is included solely for its existing integer
objective helper; OR-Tools is absent and its solver is never invoked in this runtime.

Dependency installation requires package-registry access. Running installed application
calculations does not: a `--network none` container passed readiness and comparison.
Keep virtual environments and exported reviews **outside** the immutable package.
The builder is deliberately not a broad repository copy followed by exclusions.
Repository history still contains source data: this isolated package does **not** remediate
historical exposure or resolve unknown source licensing.

```sh
.venv/bin/python scripts/package_demo.py --build /tmp/gridguide-public.zip
.venv/bin/python scripts/package_demo.py --inspect /tmp/gridguide-public.zip
python3 -m zipfile -e /tmp/gridguide-public.zip /tmp/gridguide-public
python3.12 -m venv /tmp/gridguide-runtime
/tmp/gridguide-runtime/bin/pip install --require-hashes -r /tmp/gridguide-public/deploy/requirements.lock
PORT=8000 /tmp/gridguide-runtime/bin/python /tmp/gridguide-public/deploy/serve.py
# In another shell; local build and loopback-only rehearsal, not publication:
docker build -f /tmp/gridguide-public/deploy/Dockerfile -t gridguide-local /tmp/gridguide-public
python3 scripts/rehearse_container.py --image gridguide-local --output /tmp/container.json
```

The [container](../../deploy/Dockerfile) pins the Python 3.12.14 slim-bookworm multi-arch
digest and all Python dependencies/hashes. UID/GID 10001, read-only filesystem,
capability drop, no-new-privileges and a bounded `/tmp` were tested. Graceful SIGTERM,
readiness and actual stop/restart passed. Every application file in **all image layers**
matched the package manifest, including layers that later changes could otherwise hide.
The [runtime README](../../deploy/README.md) provides standalone startup and replay commands.
Existing teammate notices are copied verbatim; dependency licenses are retained in
[`DEPENDENCY_NOTICES.txt`](../../deploy/DEPENDENCY_NOTICES.txt). No new project/data license
or permission to republish original challenge material is inferred.

## HTTP, dependency and privacy assessment

The public service enforces synthetic mode/provider-none, exact static paths, trusted
hosts, a 32,768-byte body limit before parsing, at most two active calculations, and
uvicorn's 16-connection/task concurrency limit. A saturation test blocks two calculations,
observes 503 for the third, then proves capacity recovers after sanitized failures.
Unknown methods and Range requests are rejected. CSP permits only same-origin scripts,
styles, workers and connections; framing, geolocation, camera and microphone are denied.
No source browsing, interactive docs, arbitrary graphs, uploads, solver jobs, training,
simulation jobs, provider calls or request-body logging are exposed. No outbound tiles or
fonts are required. Tests cover traversal, hostile Host, large bodies, invalid schemas,
safe errors, mode/provider rejection and archive tampering.

| Finding | Distributed scope and disposition |
|---|---|
| Existing Starlette 0.48 Range/FileResponse DoS (CVE-2025-62727) | Reachable when initially composing static serving. Public runtime alone uses FastAPI 0.120.1 / Starlette 0.49.3 and rejects Range entirely. Original challenge pins untouched. |
| Starlette host/path URL reconstruction, PYSEC-2026-161 and -248 | Scanner does not supply severity. Potential authorization/URL confusion upstream; public service rejects hostile Hosts and non-slash scope paths, makes no URL-based authorization decisions and disables proxy-header trust. Retained with bounded mitigation. |
| Starlette Windows StaticFiles UNC SSRF, PYSEC-2026-2281 | Linux container; no StaticFiles resolver in production. User paths never reach filesystem resolution before exact allowlist lookup. Not reachable in this scope. |
| Starlette HTTPEndpoint attribute dispatch, PYSEC-2026-2280 | No HTTPEndpoint subclasses; explicit routes and method allowlist. Not reachable in this scope. |
| Starlette urlencoded form limit bypass, PYSEC-2026-249 | No form parsing/multipart dependency; JSON-only bounded bodies. Not reachable in this scope. |
| npm minimatch GHSA-g3hv-75wg-m249 via openapi-typescript/Redocly | Three moderate affected-package findings, one underlying advisory; zero high/critical. Build-time local trusted schema inputs only, Node/toolchain excluded from runtime. Retained rather than major/downgrade churn. |
| Docker Scout OS/package CVE scan | **NOT EXECUTED:** installed Scout requires Docker login. No account/credential was created or requested. OS-level CVE absence is not established. |

The public pip audit contains ten records representing **five unique advisories**, not
ten independent vulnerabilities. [Python](../research/phase8/python-audit.json) and
[npm](../research/phase8/npm-audit.json) outputs are retained. CI fails for undispositioned
findings or increased npm severity; it does not silently discard accepted advisories.
No actionable severe issue was identified in the tested distributed application scope;
this is not security certification or a zero-vulnerability assertion. G8 review must
accept these dispositions and the missing OS scan, or request a focused correction.

Local HTTP is for loopback rehearsal. Any future host requires HTTPS, explicit
`GRIDGUIDE_ALLOWED_HOSTS`, appropriate network/body/slow-client controls and a new
deployment review. No availability SLA, authenticated reviewer, tamper-proof audit trail
or protection from a compromised same origin is claimed. Hashes check consistency,
not identity/authenticity. Secret scans are pattern/allowlist checks, not proof of absence
against every conceivable secret encoding. Image inspection covers application layers;
the pinned upstream base remains a third-party supply-chain dependency.

## Actual journey, outage and timing observations

Reference host: MacBook Pro, Apple M4 Pro (12 cores), 24 GB RAM, macOS 26.6.2;
Docker Desktop engine 29.8.1, local Linux arm64 image. Google Chrome 156.0.8078.80,
Playwright 1.64.1. CI uses Ubuntu/Chromium; no Safari/Firefox or new manual VoiceOver
verification is claimed. Automated checks do not substitute for a human screen reader.
G6's owner-accepted missing detailed speech/focus/environment observations stay unchanged.

Each environment made 40 sequential HTTP comparisons (eight scenarios × five repeats,
including optional frozen CP-SAT). Timings include client request/response handling:

| Environment | Median | Nearest-rank p95 | Maximum |
|---|---:|---:|---:|
| Clean extracted package | 4.46 ms | 8.94 ms | 10.33 ms |
| Local container | 3.40 ms | 5.35 ms | 11.07 ms |

All were below the 5-second response budget; no parallel-load or remote-host SLA follows.
**No public endpoint performs interactive optimization.** The 2-second solver budget is
therefore not applicable to these timings. Existing G3 budget/fallback tests passed in
the local full suite; deterministic solver reproduction and wall time remain separate.

Fresh package processes became ready in 918/370 ms. Two fresh local-image browser-test
containers became ready in 885/887 ms. The separate Docker CLI rehearsal measured 2,722 ms
initial start and 494 ms restart (includes Docker command overhead). These are few local
samples, not statistical startup guarantees; image pull/build time is excluded.

The browser explicitly saved a fictional snapshot and installed the scoped offline kit,
closed its persistent profile, stopped the actual server/container, restarted the browser
with networking disabled, reopened the timestamped historical snapshot, and kept numerical
controls disabled. After service restart it refreshed and deleted the snapshot. Exported
operator JSON was independently replayed from the extracted package. No external requests
or CSP violations were observed in the connected journey. Operator review remains
session-only and unavailable offline; the worker caches neither POST responses nor operator
pages. Storage eviction, storage denial and same-origin compromise limitations remain.

Authentic automated browser evidence: [customer](../research/phase8/public-customer.png),
[reviewed operator](../research/phase8/public-operator.png),
[offline during service outage](../research/phase8/public-offline-outage.png), and
[downloaded review](../research/phase8/container-actual-browser-review.json).
These are test-generated records, not human acceptance records.

## G8 acceptance and stop boundary

- [x] Explicit source-free package, recursive byte inspection and fresh installation.
- [x] Nonroot one-origin container, safe runtime configuration and shutdown.
- [x] Python-owned comparisons, fixed default, bounded catalogs and unavailable states.
- [x] Generated correctness/claim-safety/privacy checks and precise test lanes.
- [x] Actual package/container browser journey, export/replay, offline restart and outage.
- [x] Source pins, v1.0.0, attribution, original behavior and frozen science preserved.
- [x] Manifest, dependency notices, raw measurements and authentic screenshots supplied.
- [ ] Independent reviewer accepts CI evidence and security/reachability dispositions.
- [ ] Reviewer accepts unexecuted OS CVE scan and remaining browser/manual limitations.
- [ ] Owner approves G8 and separately authorizes merging PR #10.

No new feature is needed to meet this bounded scope. Follow-ups are limited to review
findings, an authenticated or alternate OS vulnerability scan, and future host-specific
HTTPS/resource controls if deployment is separately requested. Phase 9 stays unstarted.
The earlier 5–8-day Phase 8 estimate was provisional, not measured human effort. Recalibrate
after G8 review; the remaining Phase 9 allowance stays **4–6 provisional engineering days**
plus review corrections, with no calendar deadline or automatic permission to proceed.
