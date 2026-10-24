# Requirements traceability

Current review: AEP Data Guide realignment, October 24, 2026. Source authority and original requirement IDs: [CHALLENGE_REQUIREMENTS.md](CHALLENGE_REQUIREMENTS.md). The pre-implementation matrix and evidence classes are in [AEP_REALIGNMENT.md](AEP_REALIGNMENT.md). Operational correctness beyond the supplied evidence is not implied by passing prototype tests.

| Requirement | Implemented evidence | Coverage / remaining limit |
|---|---|---|
| Customer → upstream dependencies | Exact typed ID, location/circuit/parent checks; map separate from schematic | GREEN for vetted Demo A; incomplete regional topology remains open |
| Damaged asset → dependent customers | Global reverse index; all containing paths checked against GIS; fuse 4, transformer 1, union 4 | GREEN for simulated damage explicitly declared on those verified source assets. ARCOS-observed damage→these assets is unavailable; no claim of an end-to-end observed damage join |
| Damaged section → potentially restorable customers through sectionalization | Conditional repair release 3 then 1; 1,559 paths outside declared damage | YELLOW: bounded reasoning only. Actual switching feasibility and sectionalization-restorable count remain null |
| AEP damage → structure/material/labor chain | Phase-supported transformer/fuse recipes, explicit replacement quantities, workbook cells | YELLOW: declared damage scope; no verified ARCOS→pole/equipment/section join or automatic structure-drawing bill of materials |
| R01–R04 location, signals, risk/uncertainty | One vetted customer; source mounting/history and simulated storm; HIGH/LOW confidence/null probability | GREEN bounded demo; no arbitrary address coverage or calibrated probability |
| R05–R08 restoration/scenarios/provenance | AEP labor semantics; person-hours separate from elapsed; 2/4/8 people; CLEAR/RESTRICTED/BLOCKED; classification ledger | GREEN conditional model implementation; actual efficiency/default composition/delays are unavailable, not AEP-confirmed |
| Critical facilities and priority | Three source layers, CRS checks and aggregate spatial context; verify electrical supply before priority; dependency-first sequence | YELLOW operational priority: affected facilities, weights, independent job ranking and switching unavailable |
| R09–R11 preparation, safety, declared needs | Reviewed actions; explicit medical/accessibility/critical responsibility, None/clear, session-only adaptation | GREEN bounded journey; no inference, clinical advice, enrollment or persistence |
| R12–R14 eligibility, timing, escalation, lifecycle | Teammate policy adapter; declared-needs phone/direct-support guidance; four previews; strict >6 raw elapsed hours or availability change | GREEN prototype behavior; official AEP rules, real consent/subscription/sending absent |
| R15/R18 grounded AI and integrated flow | Server-computed labor/duration/impact/priority clauses; constrained reference selection; Standard fallback | Curated questions; live results recorded in freeze/provider notes; no independent AI decisions |
| R16/R17 fallback and privacy | Nulls, safe errors, source pins, private reverse sets, generalized map, no needs/credentials in model context | Local services and pinned data required; no public raw data |
| R19 accessibility | Native controls/disclosures, live regions, keyboard/map list, mobile regression | Focused QA; not formal WCAG/assistive-technology certification |

“Which customers depend on it?” is satisfied for **declared damage on verified assets**, because item 2 is implemented; the customer-upstream schematic alone is not counted as evidence. The complete observed ARCOS→asset→impact chain remains YELLOW at its first join. Any unsupported identity or incomplete reverse membership suppresses impact rather than publishing a partial count.
