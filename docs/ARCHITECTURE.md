# Architecture

## v1.1 Phase 1 mode boundary

The canonical entrypoint is `backend.runtime:app`. `GRIDGUIDE_MODE=challenge-local`
explicitly selects the preserved application described below; invalid mode values
fail startup. The old `backend.api:app` remains a challenge-only compatibility entrypoint.
Source pins, preparation, numerical behavior and UI routes are unchanged. Health now
identifies the active mode and prepared capabilities.

The default `synthetic-demo` prepares a hash-pinned, immutable fictional catalog once
through `backend/scenarios.py` and `backend/synthetic_api.py`. It serves
`GET /api/v2/scenarios`, `GET /api/v2/scenarios/{scenario_id}`, and `/api/v2/health`
(with `/api/health` as an alias). It imports no challenge loader, source configuration
or AI provider. Missing/corrupt fixtures withhold startup; no source fallback exists.
Every definition has a revision, evidence lineage and canonical input fingerprint.
Incomplete dependencies and blocked clearance stay unavailable.

The API remains **catalog-only**. Phase 6 adds a separate fictional preparedness frontend described below.
The original dashboard still requires challenge-local mode. Numerical v2 routes and hosting remain separately gated work. One mode is
selected per process; no second service or database is introduced.

Public contracts stay centralized in `backend/contracts.py`. The export script merges
both modes' schemas for TypeScript generation; each running app's OpenAPI serves only
its own routes. Unchanged ordinal thresholds moved to `backend/risk_rules.py`,
re-exported by `backend/config.py`, removing source configuration from contract imports.

`scripts/check_phase1_artifact.py` builds a catalog-only ZIP using an exact allowlist,
checksums and entry/content checks. Extracted startup requires no challenge files or
external network. No Git history, raw/processed data, private caches, source configuration
or provider code enters the archive. Notices are preserved; no license is added and
historical repository exposures remain. See [G1](planning/V1_1_0_PHASE1.md).

## Preserved challenge-local application

React/TypeScript + Leaflet consumes one Python/FastAPI service. Pinned local sources prepare once at startup. Deterministic backend rules own all numerical results and customer policy; optional Gemini selects explanation references. No database, external weather, notification delivery, authentication or training pipeline is involved.

| Module | Responsibility / boundary |
|---|---|
| `backend/data.py` | Hash/identity/CRS checks, private paths and labor cells; all-path asset→premise reverse index. Never serialize private source objects. |
| `backend/impact.py` | Validate reverse memberships against customer/transformer GIS; public counts and spatial facility inventory. Missing joins withhold impact. No proximity-based electrical links. |
| `backend/network.py` | Reusable private full-source reverse index with complete-path and membership validation. |
| `backend/spatial.py`, `damage.py`, `criticality.py` | Metric spatial hypotheses, ARCOS pole/device bridge, facility/premise proxy; no proximity-derived electrical truth. |
| `backend/planning.py`, `plan_explanations.py` | Four-candidate lexicographic prototype policy, constrained crew schedule, union/release milestones, server-owned plan clauses. |
| `backend/geography.py` | Separate public map DTO, 0.01° generalized geometry and exact circuit-matched lines; absent terminal remains unlocated. |
| `backend/engine.py` | Risk, AEP person-hours, explicit conditional crew envelope, access/crew comparisons and bounded dependency release. |
| `backend/contracts.py` | Frozen typed public contracts, nulls, provenance/classifications and result binding. |
| `backend/customer.py` | Adapt teammate guidance/messages to finite/null elapsed results; explicit optional needs; preview-only alerts. |
| `backend/explanations.py` | Strip needs; create approved clauses; canonicalize questions; validate model reference IDs; render all claims. |
| `backend/ai_provider.py` | Optional Gemini/OpenAI transport, strict schema, bounded deadlines and validated response cache. No numerical authority. |
| `backend/api.py` | Prepare once, sanitize validation failures, recompute previous/current inputs, bind result/revision IDs. |
| `frontend/` | Render API values, crew/access/needs controls, map/schematic, declarations, explanations and communication previews. No copied formulas. |

## Data and evidence flow

In the customer-v2 journey, historical ARCOS circuit context contributes to a disclosed risk indicator. It is not a verified asset-damage join. Golden damage is explicitly declared on two GIS/topology-verified assets → reverse premise sets → union impact → repair scope/cells → direct labor × 4.5 person-hours → crew/access conditional duration → bounded repair order → preparation/communication → constrained explanation. Original guide statements and missing links are documented in [AEP_REALIGNMENT.md](AEP_REALIGNMENT.md) and formulas in [MODEL_SPEC.md](MODEL_SPEC.md).

Keep three relations separate: customer→upstream; damaged asset→dependent premises; damaged section→customers restorable through switching. The first two are source-defensible for the bounded scenario. The third remains unavailable as an actual operation. Spatial facility context changes the verification questions asked before prioritization, never creates an affected-facility count or numerical criticality weight.

The separate restoration-plan-v1 journey prepares a full private network index, all historical damage associations and facility proximity hypotheses once. A curated qualified historical replay plus three declared source assets produce a 28-premise union. Independent source branches support separate crews under an explicit prototype concurrency policy; source ancestry conservatively sequences dependent tasks. A facility proxy may influence priority only with clear spatial-hypothesis labeling; verified facility electrical dependency remains null.

`POST /api/restoration-plan` exposes only aggregates, opaque aliases and generalized cells. `/api/restoration-plan/explain` binds recomputed plan/revision/settings to scope-specific approved questions. The optional planning subsystem returns safe 503 if preparation fails; baseline customer analysis remains available. No per-request raw GIS loading occurs.

## Requests and session behavior

`GET /api/locations`, `GET /api/map?location_alias=demo-a`, `GET /api/health` and `/docs` retain their boundaries. `POST /api/evaluate` accepts location alias, access, crew size, explicit optional declared-needs enum selections, revision and optional previous access/crew/revision. It returns result, comparison and customer journey. Extra/private fields are rejected without echo. `/api/explain` recomputes those numerical inputs and verifies current/previous IDs. It never trusts client-supplied calculation fields.

Browser selection refs preserve combined fast crew/access/need changes. Abort controllers, revisions and result/selection checks prevent stale results. Pending/error states hide old restoration, effort, sequence, assumptions and guidance. Separate analysis/map/explanation retries preserve working subsystems. Refresh resets four-person CLEAR, no declarations, no comparison or answer. No local/session storage, contact collection or real delivery.

## Privacy and external services

Within the running application, private IDs, precise customer/facility positions, `road_name`, `anno_strin`, `critical_c` and source records stay server-side. Only aggregate impact/facility counts and generalized map geometry are exposed. AI receives no location coordinates, identities, raw user questions or declared-needs selections/actions. The provider key exists only in the server environment; `.env` remains ignored. Provider logs/answers cannot expose it. These are runtime boundaries; identifying fields remain in tracked source data as documented in the [publication assessment](releases/PUBLIC_RELEASE_AUDIT.md#findings).

Optional OSM tiles have attribution and an offline-vector fallback. Missing map geometry does not fabricate a point. Missing Gemini key, quota, invalid output or timeout yields Standard explanation. Offline means the local backend/frontend remain running without external AI/tiles, not a standalone offline browser.

## Ownership and verification

Preserve teammate `pipeline/`, data/raw and data/processed. Call `pipeline/guidance.py` only; do not import `pipeline/build.py` (import side effects, inferred sensitive flags) or substitute its CSV. `pipeline/restore.py` has alternate aggregation assumptions and is not the browser's numerical engine. Existing safety templates remain teammate-owned; new explicit-needs copy is reviewed separately.

Run full Python tests, golden CLI, generated-type consistency and TypeScript/production build. Browser regression covers mobile/keyboard, combined changes, reverse impact, declared guidance, stale answers, four preview states, GIS failure/retry and Standard/live AI. See [release verification](releases/VERIFICATION.md) and [historical live-provider checks](DEMO_FREEZE.md).

## Offline Phase 2 measurement boundary

`benchmarks/` contains offline problem contracts, four baseline adapters, independent
validation/metric code, bounded exhaustive reference enumeration, frozen generators and
separate execution/reporting modules. It imports shared schema primitives but no source
loaders or AI. Only the explicitly invoked `benchmarks.legacy` lane imports the original
planner. No endpoint, browser behavior or Phase 1 package input changes. See the
[benchmark specification](benchmarks/PHASE2_SPEC.md) and [G2 record](planning/V1_1_0_PHASE2.md).

## Optional Phase 3 optimization boundary

`backend/optimization.py` consumes the unchanged G2 benchmark problem and emits a
versioned validated schedule plus solver/fallback metadata. OR-Tools is lazy and optional;
no application endpoint, provider or source loader is added. The original planner and
Phase 1 package remain unchanged. Execution/reporting tools live in separate new modules.
See [model](research/phase3/MODEL.md), [protocol](research/phase3/EVALUATION_PROTOCOL.md) and
[G3 evidence](planning/V1_1_0_PHASE3.md).

## Offline Phase 5 uncertainty boundary

`backend/simulation_contracts.py` embeds the unchanged offline benchmark problem and
exact validated schedule. `backend/simulation.py` draws keyed fictional duration/hold
realizations and propagates delays through fixed crew orders and repair prerequisites.
Planned starts remain lower bounds, so faster work cannot advance the original timetable.
Customer release dependencies remain separate. No solver, source loader, provider, API
route or browser engine is invoked. Public contracts and both application modes are unchanged.

`benchmarks/simulation_experiment.py` executes bounded suites; `research/uncertainty.py`
summarizes numerical uncertainty; `benchmarks/simulation_reporting.py` reconstructs and
checks lossless trial statistics before rendering. Complete standard/convergence reports
and bounded fictional demo trials are preserved by `scripts/package_simulation_review.py`.
Full standard trial caches stay outside Git and reproduce from pinned inputs without
challenge data. The source-free checker repeats the complete suite with source reads and
network connections forbidden. Numerical hashes and wall/RSS measurements are separate.

These are assumed distributions, not learned restoration outcomes. The original concern
band, null outage probabilities and deterministic envelopes remain intact. G4 is an
accepted evidence-bounded No-Go; reopening needs a new versioned evidence review and
data-quality gate. See the [simulation protocol](research/phase5/SIMULATION_PROTOCOL.md),
[artifact instructions](research/phase5/ARTIFACTS.md) and [G5 packet](planning/V1_1_0_PHASE5.md).

## Phase 6 customer preparedness boundary

`/preparedness/` is a separate React/Vite entry linked from the original preparation
page. The legacy dashboard retains its numerical behavior and session-only declarations.
The generic kit works without API access. Python's `prepare_customer_paths.py` prepares
18 immutable milestones from the six unchanged Phase 1 definitions, using the unchanged
G2 fixed release/person-hour baseline and independent validator. The browser displays
selected prepared frames, not a JavaScript numerical engine. This creates no API route,
risk probability, optimizer integration, Monte Carlo run or simulation interval.

`offline.ts` verifies mode, catalog/scenario provenance and approved frame content
hashes. A saved record is opened explicitly as historical fiction. Mode/selection
changes cancel saves, and cross-tab storage changes invalidate the saved view.
Challenge mode disables snapshots and removes a prior fictional record on this origin.

The production build emits a worker scoped to `/preparedness/`, with an exact hashed
shell allowlist. Cache versions bind both resources and worker implementation. APIs,
POSTs, prepared frame downloads, tiles, third-party fonts and the legacy dashboard are
not cached. An explicit action installs/verifies the kit; readiness is never inferred
from service-worker registration alone. Print/download are storage-free fallbacks.
Only localhost/HTTPS supports this workflow. Vite development mode has no generated
worker: use the production preview commands in [G6](planning/V1_1_0_PHASE6.md).

Checksums are integrity controls, not authentication against same-origin compromise.
No hosting/deployment or history-exposure remediation is included.
