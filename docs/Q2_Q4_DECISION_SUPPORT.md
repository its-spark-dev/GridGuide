# Q2/Q4 decision support: engineering evidence and demonstration

Audit date: 2026-10-24. This document records the source investigation, bounded implementation, and claims that can be defended for damaged-asset impact and restoration prioritization. It supplements [MODEL_SPEC](MODEL_SPEC.md), [DATA_AUDIT](DATA_AUDIT.md), and [AEP_REALIGNMENT](AEP_REALIGNMENT.md). It does not redefine current outage status, electrical switching capability, or AEP operating policy.

The source investigations and integrated implementation are locally verified: **171 tests passed**, generated types reproduce byte-for-byte, strict TypeScript/production build passes, 15 desktop/mobile/keyboard/failure browser check groups pass, and all three live Gemini plan questions returned validated AI-assisted answers (2.3–2.8 seconds). Raw-source pins and teammate pipelines/data remain unchanged; credentials and generated artifacts remain excluded. No commit or push was made. See [executed freeze evidence](DEMO_FREEZE.md). Q2 historical matching remains conditional and Q4 remains prototype decision support, not operational confirmation.

## 1. What the prototype now supports

A complete private reverse index is constructed from all supplied upstream records before any circuit or display filtering. Every candidate asset retains all source premise memberships. Publishing a complete dependent count requires validating every membership, including customer existence, exact typed equipment identity, type/location metadata, circuit/station agreement, unambiguous parentage, and each GIS upstream relationship. A valid path alone cannot make an incomplete asset reverse set valid.

ARCOS observations are historical evidence. A narrow, explicit spatial policy can propose a source asset for an observation. That candidate is separately checked against the complete reverse index. The result can support a **historical replay scenario**, not a statement that these customers were actually out during that historical event or are out now.

The visible comparison contains four curated repair candidates. It demonstrates overlap removal, upstream dependencies, a branch with historical spatial evidence, a distinct branch with facility proximity context, a transparent priority policy, and conditional scheduling across one or two crews. It is not an optimal dispatch plan across the entire territory.

## 2. Evidence classes

Use exactly these six classes. A derived output does not erase the classification of each ingredient.

| Input or rule | Single evidence class | Meaning and boundary |
|---|---|---|
| Direct labor × 4.5 gives total person-hours, including travel/setup | AEP-specified | Apply once. This does not itself produce elapsed time. |
| Guide permits a reasonable nearest-pole assumption and spatial critical-location relationships | AEP-specified | The supplied excerpts do not specify accuracy, distance thresholds, or guaranteed electrical attachment. No invented page citations. |
| GIS geometry, topology tokens, historical report fields, workbook rates | source-derived | Read from pinned sources; preserve their dates, units, and unresolved cases. |
| Exact GIS↔topology identity and verified reverse memberships | source-derived | String typed IDs and all-membership checks; no inferred edges from line crossings. |
| Historical ARCOS geometry/type/circuit/station and computed candidate distances | source-derived | Measurements are evidence about a proposed association, not a direct ARCOS equipment ID. |
| Treat selected historical damage and three declared assets as simultaneous repair work | scenario assumption | A replay comparison; does not reconstruct a historical incident or assert current failures. |
| One fuse cutout per selected bank; one 100-kVA transformer replacement | scenario assumption | Bank, phase, and material metadata do not establish damaged-unit quantity. |
| Clear access, one available crew, four people per crew by default | scenario assumption | Controls may change these values; actual staffing is not known. |
| Apply the workbook's 0.5 direct-hour restricted-access task at a selected worksite | scenario assumption | The rate is source-derived; whether/how often that work is needed is declared. |
| Damage distance ≤25 m and runner-up gap ≥10 m, for both device and pole | prototype policy | Reject ties and insufficient separation; no probability or accuracy percentage. |
| Facility nearest-premise distance ≤50 m and runner-up gap ≥10 m | prototype policy | A spatial proxy requiring complete premise-path validation, not proven service. |
| Optional critical-proxy preference, marginal release/person-hour ranking, upstream-first scheduling | prototype policy | A transparent comparison policy; no AEP weighting or operational optimization claim. |
| Per-task elapsed envelope from person-hours/people through person-hours/one effective worker | prototype policy | Propagate crew and ancestry constraints; no chosen efficiency factor. |
| Outward quarter-hour display for the planning timeline | prototype policy | Existing customer-outlook half-hour display remains a separate documented policy. |
| Optional medical/accessibility/critical-responsibility declarations | user-declared | These remain separate from infrastructure priority and provider context. |
| Actual productivity, skill mix, dispatch availability, clearance duration, switching feasibility, priority weights | unavailable | Null or explicit limitation; never substitute a convenient constant. |

## 3. ARCOS investigation

### 3.1 Historical observations and explicit identifiers

There are 1,659 ARCOS records: 704 primary, 355 pole, 280 fuse-bank, 156 secondary, 74 transformer, 58 recloser-bank, 19 switch, six capacitor-bank, five light, one step-transformer, and one blank asset type. No explicit quantity or verified pole/equipment identifier appears in the ARCOS schema. Circuit and station labels can restrict candidates but do not identify an individual asset.

`Outage_Num` and `Incident_W` are zero throughout; `Event` is `Default`. Report dates span multiple years. Of 76 records marked unrepaired, all still contain a repair date. Neither report/repair dates nor flags establish current outages, elapsed restoration time, or negative outage examples. Twenty-five rows duplicate all DBF attributes; repeated observations must not become damaged-unit quantities.

### 3.2 New evidence for `NEAR_FID` and `NEAR_DIST`

The ARCOS `.shp.xml` processing history contains this command, dated 20261005:

```text
Near arcos_prod_damage_09_28_Clip Primary_ExportFeatures "200 Feet" NO_LOCATION NO_ANGLE PLANAR "NEAR_FID NEAR_FID #;NEAR_DIST NEAR_DIST #" # #
```

This identifies the target of that operation as **primary line features**, not poles. Recomputing planar nearest-primary distance in the stored WGS84 coordinates reproduces all 1,659 `NEAR_DIST` values within 1e-11 native degrees; maximum absolute discrepancy was approximately 1.62e-14. These fields are therefore not meter-valued pole distances.

`NEAR_FID` must not be treated as the current primary row number or equipment ID. Its maximum, 63,094, exceeds the current 62,788 primary features. Only 628 observations point to a current nearest feature if interpreted as a one-based ordinal, and only four if interpreted as zero-based. Among observations with one nearest primary, differences between the FID and current zero-based nearest row cluster at 1, 11, 309, 313, and 326. This is evidence of a different feature-numbering namespace, consistent with an earlier export or row changes; the supplied files do not prove the exact transformation. Do not invent an offset conversion.

The currently nearest primary has the ARCOS circuit alias in 1,571 observations and station in 1,590. Sixty-two observations tie between two nearest primary features. This further rules out interpreting the Near result as verified electrical attachment. `backend/damage.py` records the metadata evidence but does not use either Near field to establish identity or metric distance.

### 3.3 Stronger spatial and shared-label evidence

Distances below were recomputed in EPSG:32617, using longitude/latitude axis order and validated source CRS. Facility layers use a different source CRS and are separately transformed.

| Source device layer | Rows | Exact device `location_n` → unique pole `location_n` matches | Geometric evidence |
|---|---:|---:|---|
| Transformer | 26,959 | 20,301 | 20,298 within 1 m of the label-matched pole; maximum 37.268 m |
| Fuse bank | 7,616 | 7,616 | Median offset 4.664 m; 7,615 within 25 m; one 67.581 m outlier |
| Recloser bank | 331 | 331 | Median offset 6.394 m; one beyond 25 m |
| Switch | 900 | 896 | All label-matched devices within 25 m |

The pole label is unique in the pole layer. Device labels can be repeated: multiple devices at a pole must remain multiple candidates. This is why label matching alone, or choosing the first device at a pole, is insufficient.

Of 125,576 possible primary endpoint-label entries, 110,383 match pole labels, covering 53,073 distinct poles. For 110,209 entries the corresponding pole is within 25 m of either line endpoint. This is useful section-incidence context. It does not establish endpoint orientation, phase continuity, normal switching state, or a directed pole/line-to-customer network. The complete pole-damage affected count remains unavailable.

For same-type, same-circuit/station nearest devices, 67 of 74 transformer observations and 260 of 280 fuse observations fall within 0.01 m of a device. These coincidences are stronger evidence than a distant nearest neighbor, but remain spatial associations because ARCOS provides no direct shared equipment key. There are also mismatches beyond a kilometer, ambiguous nearby devices, inconsistent circuit mappings, and unresolved topology IDs.

### 3.4 Implemented matching gates and coverage

`backend/damage.py` prepares all 1,659 records in memory. The policy requires:

1. A supported source device type on the same circuit alias and station.
2. The nearest device within 25 m and at least a 10 m gap to the second nearest device, using the whole eligible inventory before filtering by radius.
3. The nearest pole within 25 m and at least a 10 m gap to its second nearest pole.
4. Exactly one pole with the device's location label, equal to the selected nearest pole, with compatible device-to-pole geometry.
5. A circuit-code/alias mapping unique in both directions across all relevant line and device layers.
6. A unique exact typed GIS ID present in topology, with matching type and location metadata.

The resulting `asset_key` is private and exists only when every gate passes. Status is still `spatial_candidate`. No complete customer count is supplied by this matching layer; `backend/network.py` must validate the full reverse set independently.

| Funnel | Count | Denominator and interpretation |
|---|---:|---|
| All historical observations examined | 1,659 | Entire ARCOS layer |
| Observations in the four supported device categories | 431 | Transformer, fuse, recloser, switch; 1,228 other/blank types remain unavailable |
| Strict spatial candidates | 139 | 102 fuse observations and 37 transformer observations |
| Distinct candidate equipment identities | 131 | Repeated observations are deduplicated here, not interpreted as repair quantities |
| Candidates also having a complete validated reverse set | 28 | Observation count, after the independent all-membership check |
| All unavailable observation associations | 1,520 | Includes unsupported types, distance/ambiguity, circuit conflicts, and unresolved IDs |

Overlapping rejection reasons include 165 circuit-crosswalk conflicts, 109 unresolved typed equipment identities, 72 device-ambiguity cases, 29 out-of-distance device cases, 30 missing/conflicting pole bridges, 20 pole-ambiguity cases, six out-of-distance pole cases, and three missing same-type/circuit/station groups. These reason counts are not disjoint and must not be added to obtain the unavailable total.

An exploratory audit found 33 close observations with complete reverse sets before applying all runner-up/pole gates. The implemented policy reduces that to 28. Do not report 33 as production eligibility.

### 3.5 Selected historical fixture and rejected alternatives

Engineering locators are one-based DBF record numbers in the pinned snapshot. They are not public aliases or runtime identity substitutes.

ARCOS row **933** describes a historical fuse-bank damage observation dated 2025-02-13. Its candidate is Fuse_Bank row **6271**, with:

- Device distance **0.000 m**, second same-type/circuit/station device **53.640 m** away.
- Nearest Pole row **69624** at **5.765 m**, next pole **31.378 m** away.
- Exact shared device/pole location label, unambiguous circuit mapping, and exact typed GIS/topology identity.
- **23** complete reverse dependencies, independently checked without dropping inconvenient memberships.
- A populated single C-phase fuse specification; one cutout replacement remains a declared work scope, not an observed count.

No historical spatial assignment is available for the golden Transformer row **24215** or Fuse row **6096**. Their nearest same-type/circuit/station observations are approximately 1,221 m and 649 m away. They retain explicit declared damage. None of the nearest same-type/circuit/station transformer candidates in the historical audit had a 100-kVA specification; do not force the golden 100-kVA recipe onto another observation.

Fuse row **2557**, used for criticality context, has no ARCOS fuse-bank observation on its circuit/station. It likewise uses declared damage, with source-verified asset identity and reverse membership.

## 4. Generalized reverse-index audit

`backend/network.py` retains the global index and the reasons a node, path, or complete asset set cannot be validated. A source membership is retained even if it fails validation. Unknown asset identity or any unresolved membership yields null complete impact, not zero and not a filtered partial count.

| Measurement | Count | Exact scope |
|---|---:|---|
| Customer GIS rows / unique premises | 117,642 | Same count; identifiers retained as strings |
| Supplied topology paths | 117,599 | Headerless source records |
| Unique typed topology nodes | 32,600 | Includes 110 abstract circuit terminals |
| Directed source edges | 32,551 | Union of source paths; not inferred GIS connectivity |
| Asset/premise memberships | 490,090 | Memberships, not unique customers |
| Customer rows without a topology path | 47 | Unknown dependency |
| Topology premises missing customer GIS | 4 | Fail complete membership checks |
| Paths with all nonterminal GIS IDs resolved | 52,322 | Topology-record denominator; less strict than full validation |
| Fully validated paths | 40,779 | Out of 117,599; requires all additional consistency checks |
| Unresolved/inconsistent paths | 76,820 | Out of 117,599; not discarded from membership evidence |
| Assets with a fully validated complete reverse set | 8,095 | Includes two abstract circuit terminals |
| Supported physical assets with a complete reverse set | 8,093 | 6,103 Distribution + 1,990 Fuse |
| Distribution nodes indexed | 25,302 | Denominator for the 6,103 complete Distribution assets |
| Fuse nodes indexed | 6,757 | Denominator for the 1,990 complete Fuse assets |

The prior audit's 52,321 fully ID-resolved **customer rows** and this audit's 52,322 fully ID-resolved **topology records** have different denominators. Neither is the complete-validation count. The reverse audit's union across complete physical asset sets contains 40,766 unique premises; do not confuse this aggregate with the 40,779 independently valid paths. The remaining 13 otherwise-valid paths have no physical asset whose entire reverse set validates, because another membership invalidates each shared asset's complete count.

All 322 recloser topology IDs remain unresolved against the supplied GIS IDs. There are also unresolved step transformers, sectionalizer, fuse, and distribution identities. Location-only candidates do not repair these failures. Circuit-code/alias contradictions affect 14 aliases/codes; adding station does not resolve those contradictions.

For any selected damage set, affected premises are a **set union**. A premise becomes conditionally released only after every selected damaged dependency on its source path is complete. Upstream ancestry comes from supplied paths. No line crossing, nearest line, or geometric coincidence creates a new edge.

## 5. Facility context with explicit uncertainty

All **52** facilities were inspected: five hospital, 37 fire-station, and ten ambulance features. Exact facility names, addresses, and coordinates remain private. Distances were computed after appropriate CRS conversion against the complete customer inventory, with a second-nearest comparison before radius filtering.

At the implemented 50 m maximum and 10 m runner-up gap, **21/52** features qualify geometrically; **4/52** also have a completely validated nearest-premise path. These counts are spatial-proxy coverage, not affected facilities. The four fully validated cases are fire-station features. A wider radius creates more geometric candidates without necessarily improving validated electrical evidence.

The curated example is Fire_Stations row **25** → Customer row **82367**. The nearest premise is **14.759 m** away; the second nearest is **50.999 m** away, giving a **36.240 m** gap. The selected premise's Distribution → Fuse → Circuit path is fully validated. Fuse_Bank row **2557** has one globally indexed premise and that one membership passes every check.

This does not prove the fire station is supplied by that premise, is without power, lacks backup, or should receive an AEP operational priority. The prototype's optional preference asks the reviewer to see how a disclosed critical-location proxy changes ranking, while making electrical attachment verification an explicit next action. No affected-facility count or invented numeric criticality multiplier is produced.

The fire-station feature inside the original golden circuit bounding extent fails the needed trace validation because its nearest premise path includes an unresolved recloser. A bounding-box count is not enough to include it in the verified comparison.

## 6. Four-candidate comparison and arithmetic

| Candidate label | Private engineering locator | Damage basis | Complete dependent premises | Repair person-hours |
|---|---|---|---:|---:|
| Golden upstream fuse | Fuse_Bank row 6096 | Declared on source-verified asset | 4 | 1.728 |
| Golden transformer | Transformer row 24215 | Declared one 100-kVA unit | 1 | 10.008 |
| Historical fuse replay | ARCOS row 933 → Fuse_Bank row 6271 | Strict spatial historical association, replayed | 23 | 1.728 |
| Critical-context fuse | Fuse_Bank row 2557 | Declared; separate facility spatial proxy | 1 | 1.728 |

The transformer's one premise is contained in the golden fuse's four. The historical branch and critical-context branch are disjoint from those and each other. The raw membership sum is **29**, the overlap is **1**, and the unique union is **28**. Restoring the golden fuse can release three declared dependencies while its transformer premise remains dependent on both selected repairs.

The workbook supplies fuse cutout installation/removal at `Labor time material related!A90:B90` and 100-kVA transformer installation/removal at `C25:D25`. A fuse replacement is `(0.256 + 0.128) × 4.5 = 1.728 person-hours`; a transformer replacement is `(1.28 + 0.944) × 4.5 = 10.008 person-hours`. All four repairs total **15.192 person-hours**. Phase specifications support the recipe's size but do not prove how many phases/units failed. The 4.5 multiplier already includes travel/setup; no second generic travel adder is applied.

The policy first excludes blocked or insufficient-evidence work and defers dependents, respects selected upstream prerequisites, optionally prefers critical-proxy work/prerequisites, then compares additional dependency release per total person-hour. Ties use release count, effort, and stable alias. Crew assignment uses earliest conservative availability. This is a deterministic heuristic over four curated tasks, with disclosed tradeoffs, not an optimizer or measured utility procedure.

With clear access and the critical-proxy preference enabled, the default order is critical-context fuse → historical replay fuse → golden fuse → golden transformer. Incremental releases are **1, 23, 3, 1**, with cumulative counts **1, 24, 27, 28**. Disabling the proxy preference allows the 23-premise historical branch to lead on release/person-hour. The optional preference is a prototype choice, not a fact derived from AEP priority weights.

| Clear-access scenario | Exact modeled completion envelope, elapsed hours | Outward quarter-hour display | Total effort |
|---|---:|---:|---:|
| One crew, four people per crew | **3.798–15.192** | **3.75–15.25** | **15.192 person-hours** |
| Two crews, four people per crew | **3.366–13.464** | **3.25–13.5** | **15.192 person-hours** |

The two crews begin the critical-context and historical tasks concurrently. Crew 1 then handles the golden fuse. Crew 2, selected by earliest conservative availability, waits for that upstream fuse before handling the transformer. The modeled completion chain is the first fuse slot → golden fuse → transformer: `1.728 + 1.728 + 10.008 = 13.464` at the single-effective-worker endpoint and `13.464 / 4 = 3.366` at ideal contribution. This chain is not one crew’s total labor: Crew 1 has 3.456 person-hours of work; Crew 2 has 11.736 plus a dependency wait. Extra crews do not reduce total effort or divide a task.

These endpoints represent ideal contribution by the selected crew size versus one effective worker per available crew. They are not a calibrated confidence interval, guaranteed completion bound, or AEP ETR. Actual inefficiency, storm holds, dispatch queues, material shortages, unlisted damage, and clearance can exceed the modeled upper endpoint. Actual efficiency remains null.

Restricted access uses source rate 0.5 direct hours ×4.5 = **2.25 additional person-hours** for each declared restricted worksite. Scope/count is a scenario assumption. Blocked access has unknown clearance; the affected task is excluded and dependent tasks deferred. Full-scope completion must be null while work remains blocked. Known repair effort and executable independent work may still be shown, without implying all 28 premises can be released.

Actual isolation, switching-restorable customers, alternate-feed capability, protection coordination, and authorized energization remain **null/unavailable**. Repair completion and dependency release do not confirm electrical restoration.

## 7. Implementation and verification responsibilities

- `backend/network.py`: private reusable all-path index, complete reverse validation, overlap and conditional-release sets.
- `backend/spatial.py`: deterministic metric nearest/runner-up indexing, finite coordinates, CRS conversion, ties and policy classification.
- `backend/damage.py`: all-record historical spatial assignment audit and aggregate allowlist; no reverse-count authority.
- `backend/criticality.py`: facility/premise spatial proxies with independent path validation; no facility service claim.
- `backend/planning.py`: curated candidates, access/staffing comparison, transparent ranking, person-hours, scheduling, public planning DTOs.
- Existing contracts/API/explanation/frontend layers: consume server results, bind current revisions, display nulls and caveats, and expose no private source records.

The damage test suite validates exact observed row 933, absent golden/proxy historical matches, same-type/circuit/station gates, missing/mismatched topology identities, crosswalk conflicts, duplicate/coincident devices, ambiguous poles, duplicate pole labels, a runner-up just outside the maximum radius, metadata interpretation, public aggregate allowlisting, offline execution, and immutable raw bytes. It passed **12/12** tests at this checkpoint.

Independent audit scripts/results were created in `/tmp` only and are disposable engineering evidence. The checked-in modules and pinned source locators reproduce the selected fixtures without those files. Executed integration evidence is recorded in DEMO_FREEZE.md. Tests cannot close the unresolved operational evidence gaps.

## 8. Forty evidence claims

These concise claims provide the factual basis for the final engineering report. Their evidence and limits are expanded above.

1. The four input files retain their pinned source hashes; no raw data was edited.
2. ARCOS contributes 1,659 historical observations, not a current outage feed.
3. No direct ARCOS equipment or pole key was established.
4. Metadata proves the Near operation targeted primary line features.
5. All 1,659 stored Near distances reproduce as planar native-degree distances.
6. `NEAR_FID` is not the present primary row ordinal or a stable asset identifier.
7. Geometry is reprojected to meters before applying distance policies.
8. Type, circuit, and station jointly restrict eligible equipment candidates.
9. Nearest and second-nearest candidates are retained before any radius filtering.
10. The damage policy requires 25 m proximity and a 10 m separation gap for both device and pole.
11. Exact unique pole-location labels provide an additional source bridge.
12. Duplicate device locations are retained and ambiguity is rejected.
13. Exact GIS↔topology typed identity is required after spatial candidate selection.
14. The matcher yields 139 candidate observations on 131 distinct assets.
15. Only 28 observations additionally have complete validated reverse dependencies.
16. No candidate count is interpreted as damaged-unit quantity.
17. All 117,599 source paths enter the private reverse index.
18. The index retains 490,090 asset/premise memberships.
19. Complete validation passes 40,779 paths; unresolved paths remain explicit.
20. Complete reverse sets are available for 6,103 Distribution and 1,990 Fuse assets.
21. Four topology premises missing customer GIS and 47 customer rows missing paths remain unresolved.
22. Recloser identity and other missing equipment are not repaired through location guesses.
23. Impact is a set union, never a sum of overlapping asset counts.
24. The curated four candidates sum to 29 memberships but only 28 unique premises.
25. Golden fuse and transformer damage remains explicitly declared.
26. Historical ARCOS row 933 has a strong disclosed spatial association to the alternative fuse.
27. Critical-context fuse damage remains declared because no matching historical observation exists.
28. All 52 supplied facilities are inspected with the proper CRS.
29. Twenty-one facility features pass geometric proxy gates; four also pass full premise-path checks.
30. Facility proximity does not establish electrical attachment or an affected facility.
31. Replacement scope is explicitly one cutout per selected fuse and one 100-kVA transformer unit.
32. Source installation and removal labor are both included.
33. The 4.5 multiplier produces person-hours and is applied exactly once.
34. The four selected repairs require 15.192 repair person-hours under that declared scope.
35. Four people is a scenario default; actual conversion efficiency remains unavailable.
36. One crew gives a modeled 3.798–15.192 elapsed-hour envelope under clear access.
37. Two crews give 3.366–13.464 by working independent branches concurrently, without dividing the serial golden dependency.
38. Priority is an explained prototype heuristic, and the critical-proxy preference can be compared explicitly.
39. Blocked clearance withholds full-scope completion and defers dependent work; switching-restorable counts stay null.
40. Privacy, revision binding, server-rendered claims, offline fallback, and executed integration evidence are required before submission claims.

## 9. Ten hostile judge questions and defensible answers

| Judge question | Answer |
|---|---|
| “You still cannot identify the ARCOS asset. Isn't the result fabricated?” | We separate the historical observation, a measured spatial candidate, and the exact GIS/topology identity. The selected observation is coincident with the same-type/circuit/station fuse, has a well-separated runner-up and a unique pole-label bridge. The association remains a disclosed hypothesis; the dependency set is independently verified. |
| “Why didn't you just join `NEAR_FID`?” | Source processing metadata identifies a primary-line Near operation. Distances reproduce in native degrees and feature numbering differs from current ordinals. Joining that field as a pole/device ID would assert evidence the source does not provide. |
| “Are these 28 customers actually out?” | No. They are the unique source-dependent premises under the four selected replay/declared repairs. We have no current outage feed or verified historical premise restoration outcomes. |
| “Your coverage is only a subset. Did you filter failures away?” | All paths and all reverse memberships are indexed first. Any failed membership withholds that asset's complete count. The UI can show explicit coverage denominators and unavailable reasons. The four comparison candidates are curated from fully validated sets. |
| “Why does four plus one plus 23 plus one not equal your total?” | The transformer's one premise is already among the golden fuse's four. We union private premise sets, giving 28 unique premises from 29 memberships. |
| “Why put a one-customer repair before a 23-customer repair?” | Only when the optional critical-location proxy preference is enabled. That is a disclosed prototype tradeoff, not an AEP priority weight. Turning it off demonstrates the release/person-hour alternative. Facility attachment still needs verification. |
| “You claimed a fire station is served by this fuse.” | We do not claim that. The facility is close to a premise with a verified source trace; the relationship is a spatial proxy. We keep affected-facility and confirmed service-attachment claims unavailable. |
| “Did you divide person-hours by crew count and call that restoration time?” | No. People determine the ideal per-task boundary; crew count permits concurrency only between independent tasks. The fuse→transformer dependency remains serial. Total effort stays 15.192 person-hours for either crew-count scenario. |
| “What if access is blocked or an unknown recloser is upstream?” | Unknown clearance excludes the blocked task and defers dependents. Incomplete topology withholds complete impact and scheduling. Unknown values never become zero duration or zero affected customers. |
| “Can your AI switch the network or promise an ETR?” | No. The numerical service owns the calculation and validated clauses. AI can select approved references; it cannot infer edges, operate switches, determine utility priority, or invent time guarantees. Actual switching/restoration needs utility evidence and authorization. |

## 10. Two-to-three-minute demonstration

| Time | Action | Statement supported by the demo |
|---|---|---|
| 0:00–0:25 | Start at the restoration decision panel; keep the anonymous customer outlook below separate. | “This is a replay/declared scenario using pinned source paths. These are dependency counts, not live outage reports.” |
| 0:25–0:50 | Inspect the four candidate cards and overlap total. | “The raw memberships sum to 29, but the union is 28 because the transformer premise also depends on the upstream fuse.” |
| 0:50–1:15 | Select the historical fuse and inspect its evidence. | “The historical observation is spatially coincident with the candidate; the next eligible fuse is 53.6 m away, and the pole-label bridge agrees. The association is still approximate; all 23 reverse memberships pass separately.” |
| 1:15–1:40 | Toggle critical-proxy preference and inspect recommendation reasons. | “This optional policy can prefer a verified premise path near a fire-station feature. It does not establish that the station is electrically attached. Without the preference, release/person-hour changes the ordering.” |
| 1:40–2:05 | Change one crew to two, holding four people and clear access fixed. | “Effort stays 15.192 person-hours. Independent branches overlap, while the golden fuse→transformer chain remains serial. The exact modeled envelope changes from 3.798–15.192 to 3.366–13.464 hours.” |
| 2:05–2:30 | Block access to an upstream selected task. | “Clearance is unknown, so full-scope completion is withheld and downstream work is deferred. Other independent work can still be inspected.” |
| 2:30–2:50 | Ask for the reason using the grounded explanation path, then show limitations. | “The server supplies the claims and the AI selects approved references. Switching feasibility and actual restoration remain unknown; a standard explanation works without external AI.” |

If time is limited, omit the optional explanation step rather than hiding the historical/declared distinction, overlap, or unavailable state. The controls, Standard fallback and live Gemini path were exercised; evidence is recorded in DEMO_FREEZE.md.


## 11. Final handoff and freeze recommendation

Question 2 is GREEN for declared damage on complete source-validated assets, CONDITIONAL for qualified historical spatial replay, and unavailable for exact ARCOS identity/current outage confirmation. Question 4 is GREEN as a bounded prototype comparison and schedule, YELLOW for operational dispatch validity. Actual sectionalization-restorable customer count remains null.

Recommend feature freeze after this uncommitted diff is reviewed. The product now demonstrates damage evidence → complete reverse dependency → overlap/release → transparent priority tradeoff → limited-crew schedule → conditional time → grounded explanation. Additional operational evidence would improve validity; new unrelated features would not resolve those missing facts.


## 12. Exact changed-file manifest

This Q2/Q4 pass leaves 32 intended source/documentation/test files uncommitted: 17 modified tracked files and 15 new files. The index is empty. `main` is 0 ahead / 0 behind the local `origin/main` reference at `8d6f7ee`; no fetch, commit or push was performed in this implementation pass. No teammate pipeline, raw/processed data, IDE, credential or temporary files are included.

```text
AGENTS.md
README.md
backend/ai_provider.py
backend/api.py
backend/contracts.py
backend/criticality.py
backend/damage.py
backend/explanations.py
backend/network.py
backend/plan_explanations.py
backend/planning.py
backend/spatial.py
docs/AI_EXPLANATIONS.md
docs/ARCHITECTURE.md
docs/DATA_AUDIT.md
docs/DEMO_FREEZE.md
docs/EXECUTION_PLAN.md
docs/MODEL_SPEC.md
docs/Q2_Q4_DECISION_SUPPORT.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/RISK_REGISTER.md
frontend/src/App.tsx
frontend/src/RestorationDecision.css
frontend/src/RestorationDecision.tsx
frontend/src/api.generated.ts
tests/test_criticality.py
tests/test_damage.py
tests/test_explanations.py
tests/test_network.py
tests/test_plan_api.py
tests/test_planning.py
tests/test_spatial.py
```
