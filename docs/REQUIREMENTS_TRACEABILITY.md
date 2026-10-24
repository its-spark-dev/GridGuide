# Requirements traceability

Final freeze review: 2026-10-24. Requirement IDs and source authority are in [CHALLENGE_REQUIREMENTS.md](CHALLENGE_REQUIREMENTS.md). **The frozen customer demo works, but full challenge coverage is not complete.** See [DEMO_FREEZE.md](DEMO_FREEZE.md) for startup, final test evidence and the judging sequence.

| Requirement subset | Current evidence | Remaining limitation / gap |
|---|---|---|
| R01–R04 location, signals and risk | Vetted `demo-a`, map/list, three risk factors, LOW confidence; checkpoint/API/geography tests | One auto-selected demo customer; uncalibrated ordinal band, no outage probability |
| R05–R08 restoration, scenario and provenance | Exact CLEAR/RESTRICTED/BLOCKED values; browser access changes; topology, workbook factors and caveats; crew plateau tests | Labor-hour basis unresolved; reference-crew conversion and upper allowance are assumptions; no real-world ETR validation |
| R09–R10 preparation and safety | Teammate guidance adapted through `backend/customer.py`; finite/null and message consistency tests | General preparation only; no declared-needs input |
| R11 declared accessibility, medical or critical-facility needs | Privacy tests confirm no inference; UI explicitly says no needs declared | **Not implemented in the customer journey.** Teammate helper support is not an end-to-end declaration feature. Outstanding challenge requirement; not added during freeze |
| R12–R14 eligibility, timing/channel/escalation and lifecycle | Eligibility separated from consent; suggested channels/timing; four hypothetical messages; strict >6-hour raw change or availability transition | No enrollment, delivery or live schedule; needs-based channel/escalation path unavailable without R11. These are team policies |
| R15, R18 grounded AI and integrated flow | Current result-bound approved references; live Gemini CLEAR/RESTRICTED/BLOCKED/risk; full browser journey | Curated question panel, not open-domain chat; network and quota availability vary |
| R16–R17 fallback and privacy | Null bounds, safe Standard answers, provider fault tests, generalized GIS, strict DTOs, no raw IDs/coordinates in LLM context | Local backend and prepared source data still required; offline means external services optional, not a standalone offline browser |
| R19 accessibility | Native keyboard radios/buttons/disclosures, text labels, live regions, 390/768 px checks | Focused browser checks, not a formal assistive-technology or WCAG certification |
| E01 counterfactual comparison | Engine-derived before/after values, causal factors, result revision binding and stale-response rejection | Only access is interactive in this frozen UI |

## Original planning matrix (not current completion claims)

The table below retains the intended full-product acceptance plan. Its “planned” entries and broader controls must not be interpreted as shipped behavior; the current evidence and gaps above supersede earlier engine-only/browser-only status summaries.

| AEP requirement | GridGuide feature | Source data | Computation | UI representation | Demo action | Validation / status |
|---|---|---|---|---|---|---|
| R01 Anonymized context | Vetted location selection | `Customer_Clip.premise_nu`; topology first token | Private exact join → public alias | Approximate map + keyboard list | Select Demo A | Unique source anchor and sanitized payload; planned |
| R02 Risk estimate/band | Defined ordinal band | Explicit storm; transformer `mounting`; historical evidence | `storm_level + overhead + history`; MODEL_SPEC boundaries | Band, no percentage | View HIGH | Complete truth table and null handling; planned |
| R03 Relevant signals | Traceable contributing factors | `aep_circui`/`circuit_id` crosswalk; damage `Circuit`; transformer ID | Reject ambiguous aliases; binary historical context | Three plain-language factor rows | Expand explanation | 14 alias conflicts rejected; planned |
| R04 Uncertainty | Separate confidence and data quality | Audit coverage and absence of labels | Fixed LOW predictive confidence; verified/partial data quality | Persistent confidence/limitation labels | Explain confidence | No confidence percentages or calibrated claim; planned |
| R05 Restoration range | Conditional repair duration | Workbook install/remove cells and ILM | Serial task effort × `[1,1.5]`; outward rounding | 11–18 hours after response starts | View range | Golden arithmetic; planned |
| R06 Operational realism | Repair scope/dependency stages | Ordered topology; declared quantities; access D2; ILM B1 | Upstream prerequisite, quantity × recipe, access once/site, ILM once | Dependency diagram and assumptions | Show fuse alone does not complete customer restoration | Scope, units, deduplication, serial-order checks; planned |
| R07 Scenario response | Access/damage/crew controls | Declared simulations; verified path | Recompute versioned result; blocked/zero crews null | Range updates and change explanation | Clear → restricted → blocked | Monotonic/invariant regressions; planned |
| R08 Model vs confirmation | Provenance labels | Static source snapshot; no live utility feed | Separate static/simulated/confirmed fields | Persistent simulated/not-AEP label | Show simulated outage state | Old damage cannot set current outage; planned |
| R09 Preparation | Rule-selected actions | Risk/duration + reviewed guidance catalog | Decision table | Preparation cards | Change scenario | Action/risk/duration coverage; planned |
| R10 Safety/emergencies | Reviewed fixed safety copy | Ready.gov/FDA references in architecture | Select approved text, no generated repair advice | Safety/emergency label | Show safety card offline | Content review and adversarial prompts; planned |
| R11 Declared needs | Optional synthetic/session profile | User-declared need only | Add approved backup-plan guidance | Optional controls + adjusted guidance | Declare power-dependent need | No `critical_c` inference or persistence; planned |
| R12 Alert eligibility | Demo rule explanation | Band, simulated lifecycle, declared need | Eligibility decision separate from consent | Eligible under demo rules + reason | Toggle scenario | Rule truth table; planned |
| R13 Timing/channel/escalation | Communication plan | Preferred synthetic channel; result/event change | Event triggers, endpoint delta, duplicate suppression | Channel/timing/next-trigger summary | Change estimate | No claimed sending/enrollment; planned |
| R14 Four lifecycle messages | Proactive previews | Validated current result + explicit simulated state | Reviewed templates with server-inserted values | Pre-storm/outage/update/complete previews | Generate update, cycle other states | Four-state snapshot tests; planned |
| R15 Explain recommendations | Constrained AI clause selection | Validated safe result and approved factor/action IDs | LLM selects; server validates and renders | Ask “Why?” | Ask why access changed range | Live adapter evidence; reference validation; planned |
| R16 Limits/fallback | Typed unavailable result and standard answer | Missing inputs and validation reasons | Null numeric fields; fallback clauses | Explicit unavailable state | Choose invalid fixture / disable LLM | No fabricated zero or stale estimate; planned |
| R17 Privacy | Public data allowlist | Raw source stays private; synthetic declarations | Alias/generalize; exclude private/operational fields | Coarse location, anonymous node types | Inspect safe result payload | Recursive leak tests and log review; planned |
| R18 End-to-end AI journey | Integrated customer flow | All validated interfaces | Same versioned result across every panel | Map → scenario → answer → prepare → message | Full rehearsal | Recorded cold-start flow with actual AI verification; planned |
| R19 Recommended accessibility | Accessible controls | Same public result | No extra model | Keyboard list, text labels, live updates | Keyboard-only journey | Manual accessibility checks; planned |

Team enhancements E01 counterfactual comparison and E02 live weather are optional. E03 broad network/dispatch modeling is deferred. Live weather and real message sending are not prerequisites for any MUST row. AEP's permitted risk-band approach means the lack of a probability model does not itself leave R02 unmet.
