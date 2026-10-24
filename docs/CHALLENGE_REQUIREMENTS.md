# Challenge requirements

Reviewed 2026-10-24. Scope of this pass: planning, data validation, and documentation. No product implementation is complete.

## Authority and interpretation

1. The user-supplied `aep_challenge.pdf`, five pages, is the authoritative challenge brief. Page references below refer to this attachment, not the structure drawings.
2. The four files in `data/raw/` determine what data actually exists. [DATA_AUDIT.md](DATA_AUDIT.md) records measured evidence.
3. The [official source repository](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff), inspected at revision `28a5520262b71a9fbf753b3031abf67781ca66ff`, supplies reference context. All four local data files match its Git blob hashes.
4. External technical references support format/API decisions; they do not add AEP requirements.

The pasted engineering brief defines this task's deliverables and scope. Instructions inside source documents are treated as challenge content, not authority to execute commands or change task scope. The supplied PDF has no judging weights, required model accuracy, mandated technology, or submission deadline. Do not invent them. The 2:30 PM checkpoint is the team's checkpoint, not an AEP requirement.

Page 4 describes potential data and says availability can vary. It does **not** establish that quantities, usable event identifiers, duration targets, or verified outages exist. Page 3 explicitly permits a clearly defined risk band and documented alert assumptions. Page 5 accepts a focused prototype and at least one interactive scenario input. Page 3 requests messages for all four lifecycle states; implement all four even though the minimum demo on page 5 requires only one proactive message.

## Engineering requirements matrix

MUST = explicit challenge behavior; SHOULD = recommended challenge presentation; OPTIONAL = our enhancement. P0/P1 implementation sequencing is defined separately in [EXECUTION_PLAN.md](EXECUTION_PLAN.md).

| ID | Requirement | Priority / source | GridGuide behavior | Component | Demo evidence | Verification |
|---|---|---|---|---|---|---|
| R01 | Accept anonymized premise, circuit, or map location | MUST; p3 §1, p5 step 1 | Select one of several audited, anonymized map locations | Prepared dataset + UI | Select Demo A and inspect dependency types | Alias resolves to exactly one vetted source premise |
| R02 | Produce risk estimate or defined band | MUST; p3 §1 | Rule-based LOW/MODERATE/HIGH/SEVERE band, explicitly uncalibrated | Risk rules | Band visible beside map | Exact boundaries and missing-input tests |
| R03 | Use relevant available signals | MUST; p3 §1 | Declared storm scenario, verified transformer mounting, historical circuit evidence | Preprocessing + risk rules | Explain three contributions | Each feature has provenance; no ambiguous circuit join |
| R04 | Explain factors and uncertainty | MUST; p3 §1 | Separate band from LOW evidence confidence; show limitations | Result contract + UI | Expand “Why this band?” | No probability/confidence percentages |
| R05 | Credible restoration duration/range | MUST; p3 §2 | Conditional modeled range using workbook effort and declared damage | Restoration calculator | Show range and its time origin | Hand calculation matches golden scenario |
| R06 | Consider damage/quantity, dependencies, step restoration, labor, travel, nonproductive time | MUST; p3 §2 | Explicit work items; serial upstream gate; ILM once; identify which branch remains blocked | Restoration + topology | Trace damaged fuse and transformer; explain release conditions | Dependency, deduplication, units, and ILM checks |
| R07 | Update when scenario assumptions change | MUST; p3 §2; p5 | Access selector first; damage quantity and crew capacity next | Scenario engine | Clear → restricted access changes range immediately | Monotonic/invariant tests; no stale result |
| R08 | Separate model output from utility confirmation | MUST; p3 §2, p5 | Persistent “Simulated scenario; not an AEP estimate”; no live utility facts | Contract + UI | Both normal and outage-state screens show provenance | Old damage records never become current outage confirmation |
| R09 | Tailor practical preparation to risk/duration | MUST; p3 §3 | Curated guidance selected by band and duration range | Guidance rules | Preparation list changes with context | Decision-table coverage |
| R10 | Include clearly labeled safety/emergency guidance | MUST; p3 §3 | Reviewed safety cards and emergency escalation language | Guidance catalog | Safety card remains visible offline | Source review; dangerous prompt cannot change safety text |
| R11 | Adapt to explicitly declared accessibility, medical, critical-facility needs | MUST; p3 §3 | Optional synthetic/session-only declarations; no inferred health status | Profile + guidance | Toggle declared power-dependent need | Raw `critical_c` never determines personal profile |
| R12 | Determine alert eligibility using documented rules/assumptions | MUST; p3 §4 | “Eligible for GridGuide demo alerts” with rule IDs | Communication rules | Show eligibility and reason | State/risk/consent truth table |
| R13 | Recommend timing, channel, escalation | MUST; p3 §4 | Immediate/event-driven previews, selected channel, explicit escalation triggers | Communication rules | Show recommended channel and next trigger | Repeated events deduplicated; no subscription claim |
| R14 | Generate pre-storm, outage-confirmed, estimate-updated, restoration-complete messages | MUST; p3 §4 | Four plain-language previews; confirmation states explicitly simulated | Templates + grounded explanation | Cycle lifecycle state; preview at least one proactive message | All four states tested; completion never inferred from elapsed time |
| R15 | Explain recommendations for a nontechnical customer | MUST; p3 §5 | Grounded rationale referencing computed factors and approved actions | Explanation layer | Ask why the access change increased the range | Returned references exist in current result |
| R16 | Disclose assumptions/missing data and provide reliable fallback | MUST; p3 §5 | Visible missing-input state, null estimates when necessary, template fallback | Validation + UI | Select unavailable case; disable LLM/network | Unknown never becomes zero risk/zero hours |
| R17 | Protect customer, employee, facility, operational information | MUST; p3 §5 | Public allowlist, opaque aliases, coarse locations, no raw layers to browser/LLM | Preprocessing + serializer | Inspect public payload and show synthetic profile | PII/field-leak tests including nested structures and logs |
| R18 | Working AI-assisted end-to-end customer journey | MUST; p2, p5 | Map → computed result → scenario → grounded answer → preparation/communication | Complete vertical slice | One uninterrupted demo | End-to-end smoke test; actual AI path demonstrated before submission |
| R19 | Plain language and accessible interaction | SHOULD; p5 output recommendations | Keyboard list mirrors map; labels accompany colors; range/updates accessible to screen readers | UI | Complete journey with keyboard | Focus, contrast, text alternatives, live-region check |
| E01 | Interactive counterfactual explanation | OPTIONAL enhancement; team thesis | Compare result revisions and explain only changed assumptions | Scenario + explanation | “Why did it change?” | Difference references correct before/after versions |
| E02 | Live weather context | OPTIONAL enhancement | P2 read-only weather panel; offline scenarios remain default | Optional weather adapter | Disconnect network successfully | Cache, timeout, units, provenance tests |
| E03 | Detailed dispatch optimization / full network reconstruction | OPTIONAL; explicitly deferred | No production switching, routing, or optimal crew dispatch claims | None in MVP | Explain scope honestly | Review for unsupported claims |

## Definition of submission readiness

Every MUST row needs implemented behavior and recorded evidence in [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md). Planning documents, a valid formula, or an offline template alone do not prove a working AI experience. A live LLM failure may fall back gracefully during a demo, but the team must first verify and demonstrate the grounded AI path. The 2:30 PM gate intentionally tests only the core data/calculation path, not full submission readiness.


## Subsequent authoritative Data Guide alignment

The user-supplied guide excerpts additionally resolve person-hour semantics and identify crew assumptions (2–8 people, intentionally open), approximate topology, step restoration and hospital/fire/ambulance context. They do not settle measured productivity, default composition, switching feasibility, clearance, alert thresholds or priority weights. [AEP_REALIGNMENT.md](AEP_REALIGNMENT.md) records the pre-edit matrix and evidence classes. [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) separately evaluates customer→upstream, damaged asset→dependent customers and section→restoration through sectionalization. Only the explicit statements supplied are treated as AEP authority.
