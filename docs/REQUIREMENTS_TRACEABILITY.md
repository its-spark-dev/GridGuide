# Requirements traceability

## v1.1 Phase 1 review scope

| Requirement | Evidence | Remaining limit |
|---|---|---|
| Preserve roadmap and refinements | [Master plan](planning/V1_1_0_MASTER_ROADMAP.md) | Later phases need approval |
| Licensing, coverage, target feasibility | [Findings and register](research/phase1/FEASIBILITY.md), reproducible aggregate audit | External payloads/coverage unvalidated; no new outcome labels |
| Independent synthetic startup | Six-case pinned catalog, strict contracts, lazy mode selection, extracted tests | Catalog-only API; browser remains challenge-local |
| Publication boundary | Exact allowlist, checksum/content checks, rejection tests | No history remediation, new license or hosted release |
| Baseline preservation | Source pins, golden/API/browser regressions, v1.0.0 identity | Source-dependent tests still require authorized files |

Evidence and owner review status are in [G1](planning/V1_1_0_PHASE1.md).

## Preserved challenge requirements

Coverage review: dedicated Q2/Q4 pass, October 24, 2026. Later test/build checks are recorded in [release verification](releases/VERIFICATION.md). Detailed audit: [Q2/Q4 decision support](Q2_Q4_DECISION_SUPPORT.md). Source authority and original requirement IDs: [CHALLENGE_REQUIREMENTS.md](CHALLENGE_REQUIREMENTS.md). The pre-implementation matrix and evidence classes are in [AEP_REALIGNMENT.md](AEP_REALIGNMENT.md). Operational correctness beyond the supplied evidence is not implied by passing prototype tests.

| Requirement | Implemented evidence | Coverage / remaining limit |
|---|---|---|
| Customer → upstream dependencies | Exact typed GIS ID, location/circuit/station/parent and terminal validation | GREEN for 40,779 complete source paths; 76,820 unresolved paths explicitly withheld |
| Damaged asset → dependent customers | Reusable reverse index: 8,093 physical assets with complete membership evidence. Four candidates: 4/1/23/1 premises, union 28 | GREEN for declared source assets; CONDITIONAL for historical ARCOS spatial replay with explicit pole/device hypothesis. Direct ARCOS identity and current damage remain unavailable |
| Damaged section → potentially restorable customers through sectionalization | Set-based release only when every selected damaged dependency is repaired; overlap deduplicated; schedule milestones | YELLOW: topology-conditional repair release implemented. Actual switching feasibility and sectionalization-restorable count remain null |
| AEP damage → structure/material/labor chain | Phase-supported transformer/fuse recipes, explicit replacement quantities, workbook cells | YELLOW: 28 complete historical spatial observations support conditional asset impact; replacement quantity is declared. No direct ARCOS identity or automatic structure-drawing bill of materials |
| R01–R04 location, signals, risk/uncertainty | One vetted customer; source mounting/history and simulated storm; HIGH/LOW confidence/null probability | GREEN bounded demo; no arbitrary address coverage or calibrated probability |
| R05–R08 restoration/scenarios/provenance | AEP labor semantics; person-hours separate from elapsed; 2/4/8 people; CLEAR/RESTRICTED/BLOCKED; classification ledger | GREEN conditional model implementation; actual efficiency/default composition/delays are unavailable, not AEP-confirmed |
| Q4: limited crews, criticality, priority and time | Four source-backed repair alternatives; disclosed fire-station/premise proxy; lexicographic ranking; 1/2-crew dependency schedule; separate 2–8 people control | GREEN as bounded GridGuide prototype decision support. YELLOW operational validity: facility attachment, actual productivity/dispatch, AEP weights and switching remain unavailable |
| R09–R11 preparation, safety, declared needs | Reviewed actions; explicit medical/accessibility/critical responsibility, None/clear, session-only adaptation | GREEN bounded journey; no inference, clinical advice, enrollment or persistence |
| R12–R14 eligibility, timing, escalation, lifecycle | Teammate policy adapter; declared-needs phone/direct-support guidance; four previews; strict >6 raw elapsed hours or availability change | GREEN prototype behavior; official AEP rules, real consent/subscription/sending absent |
| R15/R18 grounded AI and integrated flow | Server-computed labor/duration/impact/priority clauses; constrained reference selection; Standard fallback | Curated questions; live results recorded in freeze/provider notes; no independent AI decisions |
| R16/R17 fallback and privacy | Nulls, safe errors, source pins, private reverse sets, generalized map, no needs/credentials in model context | Local services and pinned data required; no raw records in public API outputs. Tracked-data exposures are documented [separately](releases/PUBLIC_RELEASE_AUDIT.md#findings) |
| R19 accessibility | Native controls/disclosures, live regions, keyboard/map list, mobile regression | Focused QA; not formal WCAG/assistive-technology certification |

“Which customers depend on it?” is satisfied for **declared damage on verified assets**, because item 2 is implemented; the customer-upstream schematic alone is not counted as evidence. The observed ARCOS→pole/device→topology→impact chain is implemented as a conditional spatial hypothesis for qualified observations; it is not an exact-identity or confirmed-outage claim. Any unsupported identity or incomplete reverse membership suppresses impact rather than publishing a partial count.

## Phase 2 / G2 additions

| Requirement | Evidence | Limit |
|---|---|---|
| Identical validated scheduling inputs | Versioned offline contracts and per-case fingerprints | Fictional assumptions only |
| Four fair baselines | Stable ranks and shared availability/duration semantics | Normalized legacy adapters, no improved optimizer |
| Independent verification | Corrupted-schedule/metric tests, separate exhaustive enumeration | Eight tasks / 250,000 nodes; interrupted search is not optimal |
| Frozen reproducible evaluation | 270-case hash manifest, separate development seeds, deterministic result artifact | Structural examples, not utility population samples |
| Baseline preservation | Separate 24-case source regression lane and existing suites | Missing source tests are unexecuted, not passed |

See [G2 acceptance and results](planning/V1_1_0_PHASE2.md).

## Phase 3 / G3 additions

| Requirement | Evidence | Limit |
|---|---|---|
| Integer dependency-aware optimization | CP-SAT interval/assignment/release model | Synthetic conditional durations; no operational constraints inferred |
| Correctness and safe failure | Unchanged G2 validator, exhaustive micro-oracle and fault tests | Only proof-bearing accepted candidates labeled optimal |
| Fair comparison | Preregistered fixed baseline, separate best-of-four, paired crossed clusters | Public suite, no blind holdout; 5% median target missed |
| Reproducibility | Full source-free hash match, version/settings manifest | Wall timing is separate |
| Human tradeoff visibility | Critical/fairness regressions and fallback metadata retained | Operator integration is future work |

[G3 review packet](planning/V1_1_0_PHASE3.md) records results and owner approval.

## Phase 4 / G4 additions

| Requirement | Evidence | Limit |
|---|---|---|
| Preregistered county risk task | Risk protocol committed before modeling | No model authorized by current evidence |
| Actual access and rights review | Pinned HTTP audit, two NOAA payload audits, evidence ledger | No outage payload/permission or county-time validity mask established |
| Leakage and label safeguards | 20 research tests and deterministic decision replay | Artificial tests do not establish real-data validity |
| Research disposition | [G4 No-Go packet](planning/V1_1_0_PHASE4.md) | Independent G4 approval pending; no customer-risk integration |
