# Execution plan

Planning baseline: 2026-10-24, America/New_York. First GO/NO-GO checkpoint: **Saturday, October 24, 2026 at 2:30 PM EDT**. No official submission deadline was supplied; confirm that separately before allocating the final hours. **Engine checkpoint: executable gate passed; overall status YELLOW.** Actual AEP data supports the limited customer-facing simulation. Workbook-hour semantics and predictive calibration do not support a validated operational ETR. The user's implementation request narrowed this checkpoint to a CLI/backend proof; UI, API, AI, guidance and alerts remain later work.

## Executable checkpoint evidence — October 24

- Re-ran the full read-only audit before implementation. Golden customer remained `demo-a`, pinned `Customer_Clip` DBF record 1077 (1-based); no replacement or synthetic path was needed. Typed IDs, locations, circuit crosswalk, upstream parents and terminal sentinel reconcile to the raw sources.
- Implemented actual customer → Distribution transformer → Fuse → Circuit Breaker terminal. Public aliases and approximate positions are separated from private IDs/exact geometry. The terminal is abstract, with no supplied geometry.
- Golden simulation: storm level 2, one available reference crew, one fuse cutout and one 100-kVA transformer replacement, two worksites, supply available. Risk is HIGH (4 = 2 + 1 + 1), LOW predictive confidence, probability null.
- Clear access: raw 11.736–17.604, displayed 11–18 provisional hours. Restricted: raw 16.236–24.354, displayed 16–25. Blocked: pending clearance, null range. Restricted access adds 0.5 source hours per worksite; ILM 4.5 applies once. Risk remains unchanged. Extra crews plateau on this serial path.
- Official challenge wording, all workbook sheets/labels and workbook metadata still do not establish person-hour versus crew-hour semantics. Conversion 1 reference-crew hour per source labor hour is centralized in `backend/config.py`; the illustrative upper multiplier remains 1.5. Both assumptions are included in every result. No model formula or golden selection had to change.
- `.venv/bin/python -m unittest discover -s tests -v`: **36 tests passed in 5.373 seconds** on this workstation. Covers independent workbook arithmetic, actual-source path joins, all risk combinations, missing/invalid inputs, monotonic access/quantity behavior, crew plateau, source tampering rejection, immutable raw files, serialization privacy, comparison causality and separate-process repeatability. Synthetic cases are explicitly test-only.
- After tests passed, manually ran the complete `.venv/bin/python -m backend.demo` and each of `--access NORMAL`, `--access RESTRICTED`, `--access BLOCKED`. Results match above. `--json` exposes structured results and causal comparisons; `--schema` exports the current contract.
- Local measurement: source preparation 1.674 seconds excluding interpreter/import startup; 100 reused-context evaluations median 0.089 ms, maximum 0.514 ms; compact result 8,698 bytes. No disk cache or database was needed. These are engine timings with uncontrolled filesystem cache, not browser latency.
- No frontend, endpoint, AI adapter, database, weather call or messaging integration was added. No commit or push was performed. Next: clarify source labor units with AEP, then build a thin API/customer view that consumes this contract without duplicating formulas.

## Team and integration contract

Three people can work concurrently after agreeing on MODEL_SPEC's v1 types. Assign one owner per path to preserve teammate work; these are team workstreams, not authorization for autonomous agents to create separate chats.

| Owner | Primary paths to create in the implementation pass | Integration responsibility |
|---|---|---|
| A: data/calculation | `backend/data/`, `backend/models/`, `backend/engines/`, `scripts/prepare_data.py` | Verified fixture, numerical contracts, model tests |
| B: customer journey | `frontend/` | Map/list selection, result panels, controls, accessibility, state revisions |
| C: experience integration | `backend/api/`, `backend/explanations/`, `backend/guidance/`, `tests/e2e/`, startup scripts | API wiring, communication rules, AI adapter, offline demo |

Before parallel work: A publishes shared schema and one sanitized fixture; C owns API wiring; B consumes fixture through the agreed client interface. A owns model definitions to avoid duplicate schemas. C changes model contracts only with A; B never copies formulas into UI code. A single integrator handles shared dependency/config files. The table's folders remain proposed ownership boundaries; the checkpoint keeps the same responsibilities in small `backend/*.py` modules, avoiding unnecessary package scaffolding.

## P0: finish the core customer journey

| Slice | Outcome visible to a customer/judge | Work / dependency | Completion evidence |
|---|---|---|---|
| P0.1 Verified location | Choose Demo A; see approximate location and transformer → fuse → supply trace | A prepares pinned row-1077 fixture with strict identity/circuit/privacy checks; B creates selection/map shell; C validates contract | Alias has one private source anchor; required nodes resolve; no raw private attributes reach browser |
| P0.2 Trustworthy result | See HIGH concern, LOW confidence, contributing factors and 11–18 modeled hours | A implements `scenario-risk-v1` and `serial-path-v1`; C adds evaluation route; B binds result cards | Formula independently matches golden values; unavailable state rendered; time origin and assumptions visible |
| P0.3 Counterfactual | Clear → restricted access yields 16–25 hours; ask what changed | A adds access inputs/delta; C serves versioned results; B prevents stale responses | Band unchanged; endpoints nondecreasing; reset restores original result; blocked access removes finite range |
| P0.4 Prepared and informed | Preparation adapts to risk/duration and declared need; preview alert eligibility and communication | C implements reviewed rule tables and all four lifecycle templates; B adds profile and preview panel | No inferred needs or subscription claim; at least one proactive message shown |
| P0.5 AI explanation | Customer asks why; AI selects correct computed factors; rendered answer contains authoritative values | C adds constrained adapter and fallback after stable contract; B links question to current revision | Live AI path demonstrated; invalid output/key failure uses labeled standard explanation |
| P0.6 Reliable demo | Cold-start offline numerical journey, clear errors, keyboard alternative, rehearsal | All; C owns startup/runbook | Restart and disconnect-network rehearsal succeeds; privacy checks pass; no setup improvisation |

P0.1–P0.3 are the checkpoint gate. P0.4–P0.6 remain required before submission; “P0” does not mean all must be done by 2:30 PM. AI templates can unblock early UI work but must not be presented as a verified live AI integration.

## Checkpoint schedule

Original full-journey targets below are retained for team context. The latest authorized checkpoint scope supersedes their UI/API milestones with the executable engine evidence above; these are not claims that frontend work is complete:

| By EDT on Oct 24 | Evidence |
|---|---|
| 12:45 PM | Pin schema, private/public fixture split, source hashes and recipe-cell mappings; ask AEP mentor about labor units and optional recloser/circuit inconsistencies |
| 1:15 PM | Executable fixture → risk → restoration tests pass; B renders static sanitized fixture; no weather/LLM dependency |
| 1:45 PM | Local evaluation route connects to map/list selection and cards |
| 2:15 PM | Access counterfactual works end-to-end, plus blocked/missing state; 15-minute integration buffer remains |
| 2:30 PM | GO/NO-GO review using the four checks below |

### GO criteria

1. **Location → grid:** select Demo A using public alias; show the verified static transformer/fuse/circuit-type path. Source hashes and private joins must be reproducible. Approximate coordinates and abstract supply node are labeled.
2. **Risk:** return score 4/HIGH and LOW predictive confidence with three traceable contributions. No percentage. Unsupported selection returns insufficient data.
3. **Restoration:** two declared replacement tasks produce raw `[11.736, 17.604]`, display `[11,18]`, using source ILM once. State conditional time origin and unit assumption.
4. **Scenario:** restricted access produces raw `[16.236,24.354]`, display `[16,25]`; resetting returns the original; blocked access withdraws duration. Explain why risk is unchanged.

All four must execute through the same real-data preparation and calculation path; a hand calculation or screenshots of separate mockups do not pass. The authorized checkpoint accepts the reproducible CLI and tests above; a frontend, endpoint or screen recording is not required for this gate. Full customer-view integration remains later work.

**NO-GO / scope change:** if the audited fixture cannot be reproduced, data identity is ambiguous, rates/units are concealed, or access behavior violates invariants, stop feature expansion and repair the core. Do not replace source-backed grid relationships with a silently synthetic graph. If elapsed-hour interpretation is rejected by the organizer and no conversion is available, show a labeled labor-effort scenario and explicitly mark the challenge's restoration-duration requirement unmet until resolved. Current evidence supports the limited fixture; broad network reconstruction is already out of scope.

## Remaining hackathon work

After the checkpoint, connect the P0.1–P0.3 customer view/API to the engine contract, then finish P0.4–P0.6. Reserve the last 3–4 hours before the actual submission deadline for cold-start rehearsal, documentation, presentation, bug fixing and recording. Plan the story around a two-minute sequence:

1. Select approximate Demo A and view its grid dependencies.
2. Explain HIGH concern with LOW confidence and historical/contextual evidence.
3. Show 11–18 modeled hours and the declared repair scope.
4. Restrict access; show 16–25 hours and the changed factor.
5. Ask why; receive a grounded explanation.
6. Declare a power-dependent need; show preparation and demo alert eligibility.
7. Preview an estimate-update message; show privacy and unavailable-state handling.

### P1 — polish and differentiation after all P0 behavior

- Damage quantity selector with the 21–33 hour two-transformer-unit regression case.
- Side-by-side before/after explanation with exact revision and source labels.
- Two additional fully vetted locations, including an insufficient-data fixture, without implying all premises are supported.
- Step-restoration illustration on two verified customer branches; verify shared work is counted once. Only add a new crew scheduling model if a concrete independent-work fixture demonstrates both benefit and monotonicity. In v1, extra crews legitimately plateau.
- Better accessible map/list navigation, readable uncertainty/assumption panel, loading/error states, and concise communication wording.

### P2 — only with substantial time remaining

- Optional NWS context panel with cache/failure tests and frozen scenario isolation.
- Reconcile location/type candidates for missing reclosers with organizer confirmation and strict ambiguity checks.
- Additional verified component recipes or generalized circuit geometry.

Do not attempt supervised outage probability, historical restoration regression, Monte Carlo percentiles, optimal dispatch, real messaging delivery, account eligibility, exact critical-facility maps, or full power-flow/switching simulation during this hackathon.

## Test plan for implementation

| Boundary | Required evidence |
|---|---|
| Source/parse | Hash-pinned sources; all ZIP integrity checks; exact schema/cell mappings; leading-zero premise fixture; malformed-token rejection |
| Topology | Golden exact ID/location/circuit joins; multi-parent/cycle/repeated-node fixtures rejected; terminal `CIRCUIT` sentinel recognized; duplicate location labels never first-matched; 14 circuit alias conflicts rejected |
| Geospatial | WGS84/customer extent sanity; 3857 facility transform roundtrip; axis order; metric distance near 140.266 m for golden worksites; no degree-distance use |
| Risk | Enumerate 4 storm × 2 mounting × 2 history cases; check band cutoffs; each missing required input; no uplift from duplicate historical rows; storm monotonic; crew/access invariance |
| Labor/restoration | Hand-calculated golden values; one ILM; install/remove scope; quantity vs CU-count distinction; per-worksite access deduplication; serial order and no impossible parallelism |
| Scenarios | Access monotonicity; quantity monotonicity; crew plateau/zero-crews; blocked access null range; input reset; identical-input repeatability; no stale result after rapid changes |
| Guidance/alerts | All four lifecycle states; opt-in separate from eligibility; declared-need adaptations; no completion from time expiry; duplicate event suppression; unsupported channel rejected |
| API | Invalid aliases/types/NaN/negative quantities return validation errors; unavailable data is a typed result; version/hash mismatch fails readiness; private data never returned in errors |
| AI | Valid reference-only output; reject forged factor/action IDs, numbers/extra properties, wrong revision and prompt-injection requests; no key/timeout fallbacks; live grounded path demonstrated |
| Privacy/accessibility | Recursive allowlist tests for precise coordinates, source IDs, `road_name`, `anno_strin`, `critical_c`, contacts and facilities; keyboard journey; text labels for risk colors; focus and update announcements |
| Demo | Cold start from documented commands; offline assets and explanations; one complete golden flow; recover after server/LLM failure; measure payload and local latency targets |

The matrix describes the full submission target. The engine subset is now covered by `tests/test_checkpoint.py` and the manual CLI runs above. Endpoint, UI, accessibility, guidance, alerts and AI checks remain unexecuted because those integrations are not built.
