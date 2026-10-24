# GridGuide model specification — customer v2 / restoration-plan v1

Authority: the user supplied authoritative excerpts from the HackOHI/O 2026 AEP AI Outage Concierge Data Guide. They resolve direct-labor × 4.5 → total person-hours, including travel, safety discussions and setup. They do not specify actual conversion efficiency, default crew composition, switching feasibility, alert thresholds, clearance duration or priority weights. See [evidence ledger and requirement matrix](AEP_REALIGNMENT.md). No original guide PDF or page references are claimed.

## 1. Source, damage and dependency identity

Pinned source hashes and snapshot live in `backend/config.py`. `prepare_context()` verifies them before reading. Demo A is anchored by 1-based Customer_Clip row 1077 in that exact snapshot. Identifiers stay strings. Exact `(entity, id)` topology keys must match GIS `id`, type, location, circuit and parent relationships; circuit aliases must be unique in both directions. Unknown IDs never receive a guessed location match.

The source path is Customer → Distribution transformer → Fuse → abstract Circuit Breaker terminal. The transformer contains a 100-kVA phase specification. The scenario explicitly declares one replacement unit on that verified transformer and one cutout replacement on that verified fuse. Their identity is source-derived; damage and quantity are **scenario assumptions**. Historical same-circuit ARCOS evidence does not establish failure of either asset.

The ARCOS schema has no verified equipment ID/pole-location key for these repairs. `NEAR_FID` refers to a historical nearest-primary-line operation (verified XML metadata), not an equipment key or a stable current-layer row ordinal. Poles and primary segments are absent from the upstream token identities. A nearest-pole hypothesis permitted by the guide would still need a defensible pole-to-equipment/section join; none is silently added. ARCOS-observed affected-customer count for these two golden repairs remains **null**. The independent planning catalog below adds a qualified historical spatial replay on a different fuse.

`TopologyIndex.premises_by_asset` reverses ALL supplied paths to private premise sets. For each declared asset, the engine checks every indexed premise against unique customer GIS, first-transformer typed identity/location, circuit/station, supported downstream path and terminal. It does not first filter away contradictory memberships. Any unresolved membership withholds the complete dependent count. Unknown asset identity is unavailable, never zero. Premise identities remain private.

The golden fuse has **4** dependent premises; the transformer has **1**, contained in those four. Union impact is **4**, not five. There are **1,563** source-matched circuit paths, **1,559** outside this declared damage scope. These are approximate source dependencies under declared damage, not live outage counts or claims of complete regional electrical modeling.

## 1A. Generalized reverse evidence and bounded planning catalog

`backend/network.py` indexes 117,599 paths, 32,600 assets and 490,090 memberships. Full GIS/customer/circuit/station/parent validation supports 40,779 complete paths. Complete reverse membership exists for 6,103 transformers and 1,990 fuses, plus two abstract terminals. An asset with any unresolved member returns unavailable. O(1) prepared asset lookup retains private sets; unions and release groups deduplicate premises. Source syntax alone is not verified connectivity.

`backend/damage.py` examines all 1,659 ARCOS rows. No direct equipment identifier is established. The prototype spatial policy requires same type/circuit/station, nearest device and nearest pole each ≤25 m with ≥10 m runner-up gap, unique pole-location label bridge and exact typed GIS/topology identity. 139 observations qualify spatially; 28 additionally have complete reverse memberships. Repeated observations never establish replacement quantity. Metadata explains NEAR_FID/NEAR_DIST as nearest-primary processing; neither is used as an equipment key or metric distance.

`restoration-plan-v1` compares four curated candidates: golden fuse (4 dependent premises, 1.728 repair person-hours), golden transformer (1, 10.008), historical fuse replay (23, 1.728), and declared critical-context fuse (1, 1.728). Union 28, summed memberships 29, one duplicate. Three branches are independent within the verified source paths; transformer follows golden fuse under conservative prototype policy. One cutout per fuse bank and one transformer unit are replacement-scope assumptions, not source damage quantities.

Facility policy: nearest premise ≤50 m with ≥10 m runner-up gap; then validate that premise's whole path. Across 52 facilities, 21 geometric proxies exist, four with valid paths. The selected fire-station proxy is 14.759 m from its nearest premise (runner-up 50.999 m), on the one-premise critical fuse branch. Its electrical attachment is always unknown. The golden-extent fire feature is ambiguous (13.287/16.590 m), on a different unresolved branch, and is not assigned to golden repairs.

## 1B. Prototype priority, crews and planning time

Ranking is lexicographic, not an AEP weighted score: exclude blocked/incomplete work and its dependents; require selected upstream predecessors; optional supported spatial-criticality preference (including prerequisites); then maximize marginal release / total person-hours including access; tie-break by greater release, lower total effort and stable alias. The default first candidate is the critical-context fuse (one premise); disabling proxy priority favors historical fuse replay (23 premises). Show this tradeoff explicitly.

One or two available crews determine independent task concurrency. Two through eight people per crew determine only the ideal time boundary. Each task has duration `[P/N, P]`, with P = `(replacement direct labor + declared access direct work) × 4.5` once. A restricted worksite adds 2.25 person-hours; four curated locations are separate sites. Blocked work has no duration and defers its dependent tasks while independent work may proceed. Unknown complete duration stays null; scheduled subset duration is separate.

For each selected task, choose the crew with earliest conservative upper completion (stable crew-number tie). Its lower/upper start is the respective maximum of that crew's availability and all selected upstream predecessor finishes. Add task duration endpoint-wise. This produces two conditional ideal/single-effective-worker schedules, not probabilistic windows. Milestones group equal endpoint pairs and compute set-based release after completed tasks. Uncertain real-world finish windows may overlap; the modeled order is not an observed execution sequence.

Default four-person CLEAR total: **15.192 person-hours**. One crew: critical fuse → historical fuse → golden fuse → transformer; release increments **1, 23, 3, 1**; raw completion **3.798–15.192 h**. Two crews start critical/historical independently; then golden fuse; then transformer. Milestones **24, 27, 28** cumulative; raw completion **3.366–13.464 h**. Planning display rounds outward to **quarter hours**: **3.75–15.25 / 3.25–13.5**. This separate display policy preserves useful short-task detail; the customer-v2 outlook below retains half-hour rounding.

All important rules/inputs carry exactly one six-class evidence label in the public plan ledger. Full investigation, source row locators, sensitivity, remaining unknowns and validation are in [Q2_Q4_DECISION_SUPPORT.md](Q2_Q4_DECISION_SUPPORT.md). Actual switching-restorable premises, measured efficiency, verified facility electrical dependencies and current damage confirmation remain null.

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

The nearby fire-station feature prompts a specific decision-support action: verify electrical attachment, outage and backup arrangements before dispatch prioritization. Affected critical facilities and priority weights/score remain null. The model recommends the fuse first because it is upstream and could release three declared dependencies; it does not claim an operational optimum or criticality multiplier. The separate restoration-plan-v1 comparison above implements disclosed independent-job ranking and spatial-proxy preference.

## 6. Customer guidance, communication and AI

Optional medical, accessibility and critical-responsibility needs are **user-declared**, held only in page memory and request processing. None is the default. They add reviewed preparation and direct-support/phone guidance; they do not alter risk, labor, duration, infrastructure priority or facility counts. They are never inferred from `critical_c`, geography or AI, and are stripped from every provider context/cache. No enrollment/contact/delivery occurs.

Teammate `pipeline/guidance.py` remains authoritative for existing preparation/eligibility/message templates. The backend adapter applies the new elapsed bounds and preserves finite/null handling. Alert update rule is **prototype policy**: eligible customer plus absolute raw elapsed endpoint delta strictly greater than six hours, or finite/unavailable transition. Exactly six does not qualify. CLEAR→RESTRICTED at four people changes the upper endpoint by 4.5 hours and does **not** qualify; an update sample is still viewable. RESTRICTED eight→two people changes the lower endpoint by 6.0885 and qualifies with unchanged person-hours. Official AEP thresholds remain unavailable.

AI receives validated, minimized context and can only select approved references. Server templates render person-hours separately from elapsed hours, include unknown-efficiency caveats and expose missing switching evidence. Unsupported questions, extra fields, invented values, wrong IDs, stale revisions, timeouts or provider errors fall back/refuse safely. The LLM cannot calculate, infer needs, determine connectivity or dispatch priority. See [explanation contract](AI_EXPLANATIONS.md).

## 7. Contracts and verification

`backend/contracts.py` is the executable Pydantic source; OpenAPI generates frontend types. Evaluation schema 2.0 uses restoration model `person-hours-serial-envelope-v2` and assumptions `explicit-person-hour-envelope-v2`. Result IDs bind public results and source hashes; API recomputes prior scenarios rather than accepting client-calculated values. Declared guidance is separately bound to the same result/revision. Every important input/rule has one evidence class in the [ledger](AEP_REALIGNMENT.md); computed output provenance is not a substitute for classifying its ingredients.

Run the full tests, `python -m backend.demo`, type generation and frontend build using README commands. [DEMO_FREEZE.md](DEMO_FREEZE.md) records current browser/live evidence and remaining gaps. No operational accuracy or full regional reverse-join coverage is claimed.
