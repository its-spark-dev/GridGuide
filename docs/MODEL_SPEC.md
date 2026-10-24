# GridGuide model specification — v2

Authority: the user supplied authoritative excerpts from the HackOHI/O 2026 AEP AI Outage Concierge Data Guide. They resolve direct-labor × 4.5 → total person-hours, including travel, safety discussions and setup. They do not specify actual conversion efficiency, default crew composition, switching feasibility, alert thresholds, clearance duration or priority weights. See [evidence ledger and requirement matrix](AEP_REALIGNMENT.md). No original guide PDF or page references are claimed.

## 1. Source, damage and dependency identity

Pinned source hashes and snapshot live in `backend/config.py`. `prepare_context()` verifies them before reading. Demo A is anchored by 1-based Customer_Clip row 1077 in that exact snapshot. Identifiers stay strings. Exact `(entity, id)` topology keys must match GIS `id`, type, location, circuit and parent relationships; circuit aliases must be unique in both directions. Unknown IDs never receive a guessed location match.

The source path is Customer → Distribution transformer → Fuse → abstract Circuit Breaker terminal. The transformer contains a 100-kVA phase specification. The scenario explicitly declares one replacement unit on that verified transformer and one cutout replacement on that verified fuse. Their identity is source-derived; damage and quantity are **scenario assumptions**. Historical same-circuit ARCOS evidence does not establish failure of either asset.

The ARCOS schema has no verified equipment ID/pole-location key for these repairs. `NEAR_FID` has no established source-table identity and is not an equipment key. Poles and primary segments are absent from the upstream token identities. A nearest-pole hypothesis permitted by the guide would still need a defensible pole-to-equipment/section join; none is silently added. ARCOS-observed affected-customer count remains **null**.

`TopologyIndex.premises_by_asset` reverses ALL supplied paths to private premise sets. For each declared asset, the engine checks every indexed premise against unique customer GIS, first-transformer typed identity/location, circuit/station, supported downstream path and terminal. It does not first filter away contradictory memberships. Any unresolved membership withholds the complete dependent count. Unknown asset identity is unavailable, never zero. Premise identities remain private.

The golden fuse has **4** dependent premises; the transformer has **1**, contained in those four. Union impact is **4**, not five. There are **1,563** source-matched circuit paths, **1,559** outside this declared damage scope. These are approximate source dependencies under declared damage, not live outage counts or claims of complete regional electrical modeling.

## 2. Risk — unchanged prototype policy

`score = storm_level + overhead_indicator + historical_circuit_indicator`. Storm level 0–3 is a scenario assumption. Mounting and binary historical context are source-derived. Score-to-band policy: 0 LOW; 1–2 MODERATE; 3–4 HIGH; 5 SEVERE. Missing required inputs produce null score/band. Probability is always null; predictive confidence LOW. Golden: 2 + 1 + 1 = **4 / HIGH**. Crew, access and declared needs cannot alter it.

## 3. Direct labor and person-hours

Rates below are **source-derived** from `Labor time material related`; quantities and replacement scope are **scenario assumptions**.

| Work | Install cell / direct hours | Remove cell / direct hours | Quantity | Direct replacement hours | Repair person-hours |
|---|---|---|---:|---:|---:|
| 100-kVA transformer unit | C25 / 1.28 | D25 / 0.944 | 1 | 2.224 | 10.008 |
| Fuse cutout | A90 / 0.256 | B90 / 0.128 | 1 | 0.384 | 1.728 |
| Total | 1.536 | 1.072 | | **2.608** | **11.736** |

AEP-specified rule: `person_hours = direct_hours × 4.5`, once. Installation alone is `1.536 × 4.5 = 6.912 person-hours`; removal is `1.072 × 4.5 = 4.824`. Full replacement requires both. The guide's installation example is not permission to omit removal.

CLEAR adds zero access work by scenario assumption. RESTRICTED uses `Labor only work!D2 = 0.5` direct hours; applying one access task per modeled worksite is a scenario assumption. The 50 m grouping radius is a prototype policy; source points are 140.266 m apart, producing two modeled sites. Restricted total: `(2.608 + 2 × 0.5) × 4.5 = 16.236 person-hours`. The 4.5 access person-hours are additional direct work expanded once; there is no second travel/setup allowance.

BLOCKED has unknown clearance: access work, complete total effort and duration bounds are null. Known repair-only effort remains 11.736 person-hours. Zero available crews also withholds duration; unsupported/incorrect recipes fail validation. Invalid work is validated before access gating. Source rates are loaded at runtime with pinned hashes, not frozen result constants.

## 4. Conditional elapsed-time envelope

AEP specifies a reasonable **2–8 people** and leaves crew assumptions open. Default **4 people, 1 available crew** is a scenario assumption. API accepts integer 2–8; UI offers 2/4/8. Actual productivity, skill mix and task parallelizability are **unavailable**, represented as null, not a chosen efficiency factor.

Prototype policy: keep the declared repair tasks serial. For total person-hours P and selected people N, display a conditional envelope from ideal all-person contribution to one effective worker:

`raw elapsed hours = [sum(P_task / N), sum(P_task / 1)] = [P / N, P]`

This does not measure actual efficiency or promise that an eight-person crew works four times faster than two people. Only the ideal boundary scales; the single-effective-worker scenario remains fixed. Extra available crews never divide this serial path. The old fixed unit conversion and arbitrary upper multiplier are removed.

Round the lower boundary down and upper boundary up to 0.5 elapsed hours (prototype display policy). No clipping to attractive prior results. This is a **what-if envelope, not a calibrated confidence interval or guaranteed bound on restoration**. Actual inefficiency, dispatch queues, storm holds, switching authorization, material shortages or unlisted damage can exceed the upper value. The nominal time origin is assigned-crew response; the excluded delays are not set to zero as known facts.

| People | CLEAR raw elapsed | CLEAR display | RESTRICTED raw elapsed | RESTRICTED display |
|---:|---|---|---|---|
| 2 | 5.868–11.736 | **5.5–12** | 8.118–16.236 | **8–16.5** |
| 4 | 2.934–11.736 | **2.5–12** | 4.059–16.236 | **4–16.5** |
| 8 | 1.467–11.736 | **1–12** | 2.0295–16.236 | **2–16.5** |

All crew sizes under BLOCKED retain null bounds. Access and crew changes compare raw elapsed hours separately from person-hours. Changes to unrelated facts/recipes/models are rejected as confounded comparisons.

## 5. Repair sequence, sectionalization and criticality

Upstream-first serial repair is a **prototype policy**, based on source ancestry. The fuse repair carries 1.728 repair person-hours and could clear the declared damage dependency for three paths. The transformer carries 10.008 person-hours and could clear the remaining one after the fuse. This is conditional on other assets intact, supply/materials available, access cleared and operational authorization. It is not an actual restoration schedule.

A fuse is a potential isolation boundary. Operating state, complete connections, backfeed, protection and switching authorization are unavailable. `sectionalization_restorable_customers` stays **null**. Do not relabel the 1,559 paths outside declared damage as customers actually restored by switching.

Facilities are source-derived **spatial criticality context**, not verified electrical dependencies. Regional inventory: hospitals 5, fire stations 37, ambulance locations 10. Within the bounding extent of exact circuit/alias/station-matched primary segments: 0 / 1 / 0 respectively, after CRS validation/conversion. The extent is not a service/outage polygon. A missing extent yields null counts. Identities and coordinates are not exported.

The nearby fire-station feature prompts a specific decision-support action: verify electrical attachment, outage and backup arrangements before dispatch prioritization. Affected critical facilities and priority weights/score remain null. The model recommends the fuse first because it is upstream and could release three declared dependencies; it does not invent an optimal ranking among independent jobs or a criticality multiplier.

## 6. Customer guidance, communication and AI

Optional medical, accessibility and critical-responsibility needs are **user-declared**, held only in page memory and request processing. None is the default. They add reviewed preparation and direct-support/phone guidance; they do not alter risk, labor, duration, infrastructure priority or facility counts. They are never inferred from `critical_c`, geography or AI, and are stripped from every provider context/cache. No enrollment/contact/delivery occurs.

Teammate `pipeline/guidance.py` remains authoritative for existing preparation/eligibility/message templates. The backend adapter applies the new elapsed bounds and preserves finite/null handling. Alert update rule is **prototype policy**: eligible customer plus absolute raw elapsed endpoint delta strictly greater than six hours, or finite/unavailable transition. Exactly six does not qualify. CLEAR→RESTRICTED at four people changes the upper endpoint by 4.5 hours and does **not** qualify; an update sample is still viewable. RESTRICTED eight→two people changes the lower endpoint by 6.0885 and qualifies with unchanged person-hours. Official AEP thresholds remain unavailable.

AI receives validated, minimized context and can only select approved references. Server templates render person-hours separately from elapsed hours, include unknown-efficiency caveats and expose missing switching evidence. Unsupported questions, extra fields, invented values, wrong IDs, stale revisions, timeouts or provider errors fall back/refuse safely. The LLM cannot calculate, infer needs, determine connectivity or dispatch priority. See [explanation contract](AI_EXPLANATIONS.md).

## 7. Contracts and verification

`backend/contracts.py` is the executable Pydantic source; OpenAPI generates frontend types. Evaluation schema 2.0 uses restoration model `person-hours-serial-envelope-v2` and assumptions `explicit-person-hour-envelope-v2`. Result IDs bind public results and source hashes; API recomputes prior scenarios rather than accepting client-calculated values. Declared guidance is separately bound to the same result/revision. Every important input/rule has one evidence class in the [ledger](AEP_REALIGNMENT.md); computed output provenance is not a substitute for classifying its ingredients.

Run the full tests, `python -m backend.demo`, type generation and frontend build using README commands. [DEMO_FREEZE.md](DEMO_FREEZE.md) records current browser/live evidence and remaining gaps. No operational accuracy or full regional reverse-join coverage is claimed.
