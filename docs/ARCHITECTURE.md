# Architecture

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

Private IDs, precise customer/facility positions, `road_name`, `anno_strin`, `critical_c` and source records stay server-side. Only aggregate impact/facility counts and generalized map geometry are exposed. AI receives no location coordinates, identities, raw user questions or declared-needs selections/actions. The provider key exists only in the server environment; `.env` remains ignored. Provider logs/answers cannot expose it.

Optional OSM tiles have attribution and an offline-vector fallback. Missing map geometry does not fabricate a point. Missing Gemini key, quota, invalid output or timeout yields Standard explanation. Offline means the local backend/frontend remain running without external AI/tiles, not a standalone offline browser.

## Ownership and verification

Preserve teammate `pipeline/`, data/raw and data/processed. Call `pipeline/guidance.py` only; do not import `pipeline/build.py` (import side effects, inferred sensitive flags) or substitute its CSV. `pipeline/restore.py` has alternate aggregation assumptions and is not the browser's numerical engine. Existing safety templates remain teammate-owned; new explicit-needs copy is reviewed separately.

Run full Python tests, golden CLI, generated-type consistency and TypeScript/production build. Browser regression covers mobile/keyboard, combined changes, reverse impact, declared guidance, stale answers, four preview states, GIS failure/retry and Standard/live AI. See [freeze evidence](DEMO_FREEZE.md).
