# AEP Data Guide realignment

Authority: the user supplied excerpts of **HackOHI/O 2026 — AEP AI Outage Concierge Data Guide** and explicitly designated them authoritative for this task. No separate original guide file was supplied; do not invent page citations or claim to have verified an original PDF. Only the statements actually supplied close assumptions. This note controls the implementation scope.

## Requirement matrix — recorded before implementation

| AEP question | Source data | Current implementation | Gap | Required fix |
|---|---|---|---|---|
| What is damaged? | ARCOS historical reports; equipment GIS; supplied guide | Historical circuit evidence plus simulated replacement of one fuse cutout and one 100-kVA transformer | No verified damage-record-to-these-assets match | Keep damage/quantity simulated; show the explicit repair scope, never promote circuit history to current failures |
| Which customers depend on it? | `matched_upstream.txt`, Customer/Transformer/Fuse GIS and exact typed joins | Verified Demo A path and separate geographic map | No aggregate affected-customer/step context | Count distinct source-matched customer paths through the selected equipment; report approximate dependencies and conditional restoration stages |
| What work is required? | Workbook install/removal cells, equipment phase specification, guide labor semantics | Correct replacement recipes but incorrect elapsed-time interpretation | Person-hours treated as crew elapsed hours | Separate installation, removal, access direct labor, total person-hours and conditional elapsed outlook; remove old conversion/upper multiplier |
| What first, with limited crews and criticality? | Dependency paths, three supplied facility layers, workbook effort; guide crew range | Serial path only; no facility context; no people-per-crew input | Missing people/crew distinction, criticality and bounded sequence explanation | Add 2/4/8-person assumption; dependency-first stages with conditional customer release; aggregate facilities in source-derived primary context; affected-facility/switching status remains unavailable; no invented ranking weights |

Also close the declared-needs customer journey with explicit session-only choices. Keep these separate from facility GIS. Preserve the Gemini reference-only boundary, privacy, map, safety, previews and stale-response guards.

## Evidence and classification ledger

| Input or rule | Classification | Known / open |
|---|---|---|
| Workbook labor-only semantics; 4.5 applied once produces total person-hours | AEP-specified | Resolved by supplied guide excerpts; includes travel, safety discussions and setup |
| Workbook cell values, GIS geometry, approximate upstream paths, facility inventory | source-derived | Source hashes and existing exact joins remain required |
| Primary-segment bounding extent chosen as a spatial context window | prototype policy | Not an electrical service polygon or outage boundary |
| LOW predictive confidence and ordinal risk thresholds | prototype policy | No calibrated confidence/probability is supplied |
| One fuse and one transformer replacement; quantities; storm/access; available supply | scenario assumption | Not directly ARCOS-derived current damage |
| Crew range 2–8 people; crew assumptions intentionally open | AEP-specified | Does not specify composition, productivity, or default |
| Four people per crew initially; one available crew | scenario assumption | Demo selection, not an AEP staffing rule |
| Actual productivity/parallelizability/skill mix | unavailable | No measured conversion efficiency supplied |
| Conditional elapsed envelope: each serial task spans ideal all-person contribution to one effective worker | prototype policy | An explicit what-if envelope, not calibrated operational bounds; unknown holds can exceed it |
| Half-hour outward display rounding; upstream-first serial task order; 50 m worksite grouping | prototype policy | Presentation/sequencing/grouping choices, not AEP standards |
| Restricted-access rate 0.5 direct hours | source-derived | Labor only work!D2 |
| One restricted-access task per modeled site | scenario assumption | Two-site application is not an AEP universal per-site rule |
| Clearance, dispatch queue, storm holds, actual switching feasibility, facility electrical attachment | unavailable | No invented delay, operation or affected-facility count |
| Strict >6 elapsed-hour endpoint change or availability transition; communication thresholds | prototype policy | Never compare person-hours to this threshold; not an AEP alert rule |
| Medical, accessibility or critical responsibility selection | user-declared | Explicit optional choices only; no persistence or facility-based inference |
| Priority weights and actual operational priority | unavailable | No numeric rank; show dependency/customer/effort evidence and missing criticality confirmation |

## Source checks and derivation to preserve

Workbook installation values are transformer C25 **1.28** and fuse A90 **0.256**: **1.536 direct labor hours → 6.912 person-hours** for installation alone. The existing scenario is replacement, also requiring transformer removal D25 **0.944** and fuse removal B90 **0.128**. Full replacement direct labor is **2.608 hours**, yielding **11.736 person-hours**, not elapsed hours. Removing those removal tasks merely to match the installation-only example would change the scenario silently.

Read-only audit of the selected circuit found **1,563** source-matched customer paths, **4** through the selected fuse and **1** through the selected transformer. Three fuse-dependent paths bypass that transformer; their possible earlier release is conditional on all other scope/supply/safety assumptions. This does not establish switching feasibility.

The supplied facility inventory contains **5 hospital**, **37 fire-station**, and **10 ambulance** point features. The bounding extent of primary segments matched by the verified circuit code/alias/station contains **0 hospitals, 1 fire station, 0 ambulance features** after CRS conversion. This is geographic context only, not an outage area or electrical connection. Facility identities and coordinates stay private; affected facility count stays null.

Final formulas and the full crew/access table are in [MODEL_SPEC.md](MODEL_SPEC.md). Current verification and rehearsal evidence is in [DEMO_FREEZE.md](DEMO_FREEZE.md). The superseded numerical model is not a compatibility target.

## Damage-centric evidence chain — separate coverage claims

| Link | Evidence / result | Classification | Status |
|---|---|---|---|
| ARCOS report → selected pole/equipment/section | No verified equipment-ID or pole-location field for these repairs; NEAR_FID source identity unresolved; poles/lines are not topology tokens | unavailable | Observed impact stays null; nearest-pole association would not by itself close pole→topology identity |
| Declared damage → selected asset | Work item explicitly names the verified fuse/transformer alias; declaration attaches to exact source identity, not an arbitrary simulated component | scenario assumption | Supported simulated damage scope, not observed ARCOS damage |
| Asset → topology identity | Entity+ID, type/location metadata, circuit/station/parent all verified against GIS | source-derived | Exact supported identities |
| Asset → all dependent premises | Global `premises_by_asset` index across every supplied path, then independent customer/first-transformer GIS checks; no prefilter hides conflicts | source-derived | Fuse 4 / transformer 1 / union 4; incomplete joins withhold full counts |
| Asset repair → cleared declared dependencies | Upstream-first serial policy, all selected damaged dependencies completed | prototype policy | Three could clear after fuse; one after transformer; supply/other-damage/authorization assumptions still required |
| Section isolation → actual restorable customers | No complete switching feasibility/state/protection evidence | unavailable | Explicit null; not the same as conditional repair release |
| Facility inventory/primary extent | Source CRS and exact circuit-matched primary extent; aggregate 0 hospital / 1 fire / 0 ambulance nearby | source-derived | Spatial criticality context only, not service/outage polygon |
| Facility → damaged section electrical dependency | No facility/premise/equipment crosswalk | unavailable | Affected count stays null; verify supply/outage/backup before dispatch priority |
| Risk thresholds and preparation/communication decision rules | Transparent existing rules, no AEP calibration or official thresholds supplied | prototype policy | Disclosed, tested; not inferred from the guide |

Coverage is separately **GREEN for customer→upstream**, **GREEN for declared damaged source asset→dependent customers**, and **YELLOW for section→restoration through sectionalization**. The overall observed ARCOS→asset→impact chain remains **YELLOW** at its first join. The forward schematic is never used as a substitute for the reverse-index evidence.

## Final verification and exact change manifest

118 backend tests passed; golden CLI, generated-type consistency and production build passed. Chrome regressions passed crew/access/declarations, reverse impact, privacy, keyboard/mobile, stale responses and map/explanation failures. Six live Gemini intents and one cache repeat passed; the normal port-8000 live service was restarted and checked after final changes. No provider/raw-key logging. Detailed timing and judge Q&A are in DEMO_FREEZE.

All four pinned raw source hashes verified. No teammate pipeline or raw/processed data changes. `.env` remains ignored, mode 0600, absent from staged/untracked changes. No credential-shaped values or workstation paths found in changed files. Git whitespace and local documentation links passed. Main is 0 ahead / 0 behind origin/main after fetch; no new commit, staging or push. Starting/current HEAD: `d9d6677b8f7335b9890c6a1414292f5ff0a2245b`.

Exact repository-relative paths in this pass:

| State | File |
|---|---|
| Modified | `AGENTS.md` |
| Modified | `README.md` |
| Modified | `backend/api.py` |
| Modified | `backend/config.py` |
| Modified | `backend/contracts.py` |
| Modified | `backend/customer.py` |
| Modified | `backend/data.py` |
| Modified | `backend/demo.py` |
| Modified | `backend/engine.py` |
| Modified | `backend/explanations.py` |
| Modified | `docs/AI_EXPLANATIONS.md` |
| Modified | `docs/ARCHITECTURE.md` |
| Modified | `docs/CHALLENGE_REQUIREMENTS.md` |
| Modified | `docs/CUSTOMER_INTEGRATION.md` |
| Modified | `docs/DATA_AUDIT.md` |
| Modified | `docs/DEMO_FREEZE.md` |
| Modified | `docs/EXECUTION_PLAN.md` |
| Modified | `docs/GEMINI_PROVIDER.md` |
| Modified | `docs/GEOGRAPHIC_MAP.md` |
| Modified | `docs/MODEL_SPEC.md` |
| Modified | `docs/REQUIREMENTS_TRACEABILITY.md` |
| Modified | `docs/RISK_REGISTER.md` |
| Modified | `frontend/src/App.tsx` |
| Modified | `frontend/src/AskGridGuide.tsx` |
| Modified | `frontend/src/CustomerJourney.tsx` |
| Modified | `frontend/src/api.generated.ts` |
| Modified | `frontend/src/api.ts` |
| Modified | `frontend/src/styles.css` |
| Modified | `tests/test_checkpoint.py` |
| Modified | `tests/test_customer.py` |
| Modified | `tests/test_explanations.py` |
| Modified | `tests/test_gemini.py` |
| New, untracked | `backend/impact.py` |
| New, untracked | `docs/AEP_REALIGNMENT.md` |
| New, untracked | `frontend/src/RestorationEvidence.tsx` |
| New, untracked | `tests/test_aep_model.py` |
