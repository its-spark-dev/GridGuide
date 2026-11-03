# Post-release editorial review — November 3, 2026

Local review record for `docs/post-release-portfolio-editorial`, based on the verified latest `main` at `b324c1b355cda60035fb11fa32bcddf10931f649`. This is documentation work, not a new product release. The proposed [release body](v1.0.0.md) is ready for review; the published GitHub body has not been edited. Publishing this branch or changing GitHub metadata requires separate authorization.

## Editorial assessment

Before: the README mixed the customer journey with six implementation/coverage rows, repeated caveats, detailed intermediate arithmetic, and release-approval navigation. The release body described owner decisions and execution steps. Several deeper records used “current,” “uncommitted,” or “pending” for already-completed work.

After: the README leads with problem, solution, authentic UI, and four things to explore. A short walkthrough leads into architecture and three verified achievements. Setup and concise limitations remain visible. The index groups technical references by reader question and places historical/process navigation in one collapsed section. The release body focuses on implemented behavior, evidence, verification, and prototype boundaries.

The README is reduced from **1,841 to 1204 whitespace-delimited words** (including code and diagram text); the proposed release body is **365 words**. The top narrative is designed for a 60–90-second scan, not a claim of measured recruiter usability. Detailed evidence is reachable directly from each summary.

## Document classification and changes

Classification describes the material, not its importance. PORTFOLIO is for first-time visitors; TECHNICAL supports engineering review; HISTORICAL preserves provenance; INTERNAL records execution/approval work; REDUNDANT identifies repeated summaries, not evidence to discard.

| Document | Classification | Change / disposition |
| --- | --- | --- |
| [Root README](../../README.md) | PORTFOLIO; selected TECHNICAL; REDUNDANT detail | Rewrite around the journey; retain architecture, setup, limitations, and team acknowledgment. Detailed denominators and arithmetic remain in model/evidence references. |
| [Documentation index](../README.md) | PORTFOLIO navigation | Curate Architecture, Data, Models, Verification, and Development; collapse historical navigation. |
| [Release body source](v1.0.0.md) | PORTFOLIO; REDUNDANT process commentary | Prepare concise replacement prose, remove duplicate title and owner-checklist link. Public links distinguish maintained documentation from the immutable snapshot. |
| [Release checklist](CHECKLIST.md) | INTERNAL / HISTORICAL | Retain in place; add completed milestones and collapse the original checklist. Remove from primary navigation. |
| [Original PR body](PR_BODY.md) | INTERNAL / HISTORICAL | Retain verbatim beneath a new historical introduction linked to merged PR #1. Not a reusable current PR template. |
| [Publication assessment](PUBLIC_RELEASE_AUDIT.md) | TECHNICAL findings; HISTORICAL decisions; INTERNAL recommendations | Preserve findings table and original decision. Clarify that publication-gate recommendations were superseded, while data/privacy/permission findings were not resolved. Keep a direct Data & Evidence link. |
| [Release verification](VERIFICATION.md) | TECHNICAL / HISTORICAL | Keep results, environment, and claim references. Date the scope and record completed GitHub presentation checks. |
| [Screenshot provenance](../media/v1.0.0/README.md) | TECHNICAL / HISTORICAL | Unchanged. Capture settings, genuine online basemap evidence, dates, and hashes remain authoritative. |
| [Contributing](../../CONTRIBUTING.md) | TECHNICAL | Remove obsolete release-branch instructions; retain evidence standards, privacy precautions, and contribution-rights boundary. |
| [Third-party notices](../../THIRD_PARTY_NOTICES.md) | TECHNICAL | State current license status and retained materials neutrally. Preserve findings/decision link; remove a speculative license suggestion. |
| [Architecture](../ARCHITECTURE.md) | TECHNICAL | Clarify runtime privacy versus tracked data; point to release verification and dated live checks. Module boundaries unchanged. |
| [Model specification](../MODEL_SPEC.md) | TECHNICAL | Replace “current freeze” test pointer with release verification. Formulas, assumptions, and golden values unchanged. |
| [Decision support](../Q2_Q4_DECISION_SUPPORT.md) | TECHNICAL; HISTORICAL / INTERNAL later sections | Retain all source investigation, counts, sensitivity, examples, and handoff. Add dated context and current walkthrough link. |
| [AI explanations](../AI_EXPLANATIONS.md) | TECHNICAL | Label provider smoke evidence as dated; contracts and fallback unchanged. |
| [Customer integration](../CUSTOMER_INTEGRATION.md) | TECHNICAL | Unchanged; explicit needs, preparation policies, and communication limitations remain. |
| [Geographic map](../GEOGRAPHIC_MAP.md) | TECHNICAL / HISTORICAL verification | Clarify current contract and dated checks; correct stale claims that labor units were unresolved and the explanation adapter was still future work. |
| [Data audit](../DATA_AUDIT.md) | TECHNICAL / HISTORICAL investigation | Add chronological context; all source findings and later follow-ups retained. No new data audit. |
| [Schema inventory](../DATA_SCHEMA.md) | TECHNICAL | Unchanged; retain exact fields and coverage. |
| [AEP interpretation ledger](../AEP_REALIGNMENT.md) | TECHNICAL ledger; HISTORICAL / INTERNAL plan and manifest | Link directly to the ledger in primary navigation; label earlier status/implementation instructions as historical. |
| [Requirements coverage](../REQUIREMENTS_TRACEABILITY.md) | TECHNICAL | Date coverage review and fix “no public raw data” to explicitly mean no raw records in public API outputs; link tracked-data findings. |
| [Risk register](../RISK_REGISTER.md) | TECHNICAL | Keep unresolved model/runtime risks; link the separate tracked-data exposure record. |
| [Challenge requirements](../CHALLENGE_REQUIREMENTS.md) | HISTORICAL | Retain original brief/planning interpretation; label initial “no implementation” statement as historical. |
| [Execution plan](../EXECUTION_PLAN.md) | INTERNAL / HISTORICAL | Unchanged; existing historical banner is sufficient. Accessible only in the history navigation. |
| [Demo freeze](../DEMO_FREEZE.md) | HISTORICAL / INTERNAL | Unchanged; retain dated live checks and original sequence. Existing banner separates them from released behavior. |
| [Judge UX notes](../JUDGE_UX_HARDENING.md) | HISTORICAL / INTERNAL | Unchanged; preserve original exercise results and demo script behind history navigation. |
| [Customer product redesign](../CUSTOMER_PRODUCT_REDESIGN.md) | HISTORICAL / TECHNICAL | Add a historical banner; preserve design reasoning and frontend regression evidence. |
| [Gemini provider](../GEMINI_PROVIDER.md) | TECHNICAL setup; HISTORICAL discovery/results | Keep direct setup anchor; label model/pricing/latency observations as dated rather than current guarantees. |
| [Frontend visual research](../../frontend/AEP_UI_REFERENCE.md) | HISTORICAL | Add supersession banner for old ranges and UI order; preserve original observations. |
| [Browser harness guide](../../frontend/tests/README.md) | TECHNICAL | Unchanged; remains the reproducibility reference. |
| [Engineering instructions](../../AGENTS.md) | INTERNAL | Reviewed, unchanged; not promoted as a project overview. |
| This review | INTERNAL / HISTORICAL | New review artifact under existing release records; only linked from collapsed history navigation. |
| [Published GitHub Release](https://github.com/its-spark-dev/GridGuide/releases/tag/v1.0.0) | PORTFOLIO with INTERNAL / REDUNDANT material | Read and compared to the original source file. Proposed replacement is local only. |

## Removed, relocated, and consolidated information

No existing file is deleted or moved. No screenshot, scientific result, attribution, or original audit finding is removed.

| Removed from the main reading path | Where the necessary information remains |
| --- | --- |
| Intermediate path/node/asset denominators and labor arithmetic in README | [MODEL_SPEC §1A–4](../MODEL_SPEC.md#1a-generalized-reverse-evidence-and-bounded-planning-catalog), [decision-support investigation](../Q2_Q4_DECISION_SUPPORT.md), and [verification claim map](VERIFICATION.md#claim-review). |
| Repeated engineering-principle list and long limitation explanations | Concise architecture/limitations in README; [architecture](../ARCHITECTURE.md), [model](../MODEL_SPEC.md), [AI contract](../AI_EXPLANATIONS.md), and [risk register](../RISK_REGISTER.md) retain detail. |
| Release checklist / approval sequence in public navigation | [Publication record](CHECKLIST.md), original [PR body](PR_BODY.md), and collapsed history index. Completed milestones are now explicit. |
| Owner data-retention/process narrative in README and release body | [Original decision and findings](PUBLIC_RELEASE_AUDIT.md); concise data/privacy pointer remains in README setup and the main evidence index. |
| Repeated source-control SHA discussion in release body | [Publication record](CHECKLIST.md), README background, and the linked immutable snapshot. Exact submission SHA remains unconfirmed. |
| Detailed environment and provider non-retest commentary in release body | [Verification scope](VERIFICATION.md) retains environment, fresh-install limit, offline checks, and absence of new live-provider testing. |
| Speculative v1.1.0 directions and possible MIT license suggestion | Original [tagged README](https://github.com/its-spark-dev/GridGuide/blob/v1.0.0/README.md) and [tagged notices](https://github.com/its-spark-dev/GridGuide/blob/v1.0.0/THIRD_PARTY_NOTICES.md). No feature commitment or license selection is implied. |
| Pending owner-approved-credit wording in the README | No identities or roles invented. Three-person acknowledgment and Git attribution remain; missing preferences/consent remain recorded in the [publication record](CHECKLIST.md). |

For CHECKLIST, PR_BODY, DEMO_FREEZE, EXECUTION_PLAN, and JUDGE_UX_HARDENING, retain-in-place plus removal from primary navigation is sufficient; no archive directory or consolidation is needed. PUBLIC_RELEASE_AUDIT also stays in place, with its findings directly accessible in primary technical navigation. This preserves evidence without treating accepted release decisions as new publication blockers.

## GitHub About and topics — suggestion only

The current About text describes an “AI-powered outage intelligence platform” focused partly on “risk prediction.” That wording is broader than the implemented ordinal scenario model. No remote metadata changes were made.

Suggested About: **Explainable storm outage scenarios, dependency-aware repair planning, and customer guidance. Independent HackOHI/O 2026 prototype.**

Suggested topics: `hackohio`, `hackathon`, `outage-management`, `decision-support`, `explainable-ai`, `geospatial`, `fastapi`, `react`, `typescript`, `python`. GitHub currently has no topics configured. These suggestions align with the README and release draft without claiming calibrated predictions or operational use.

## Verification for this editorial pass

- Reviewed the complete diff: **23 Markdown files** changed, including this new review. No existing document was moved or deleted. All **92 tracked non-Markdown files** are byte-identical to the release commit, including application code, dependencies, datasets, tests, and images.
- Checked **245 local links/anchors across 31 Markdown files**, image references, code fences, and Git whitespace: no failures.
- All **five revised-release links** returned HTTP 200. The walkthrough and documentation links intentionally follow `main`; verification and the original snapshot remain pinned to `v1.0.0`. The maintained pages will show this editorial revision only after a separately approved merge.
- Checked **29 distinct HTTPS destinations** in the Markdown corpus: 27 returned HTTP 200 directly. The existing [Ohio EMA reference](https://ema.ohio.gov/prepare-respond/preparedness-resources/power-outages) returned **404** in both direct HTTP and Chrome checks; it remains an unresolved external-link issue in the customer-integration reference, retained as the original citation rather than replaced with an unverified equivalent. [FoodSafety.gov](https://www.foodsafety.gov/keep-food-safe/food-safety-in-disaster-or-emergency) returned **403** to those clients, but the web reader retrieved the page. This is a reachability limitation, not evidence that the source is absent. No safety copy or application behavior changed.
- The Mermaid source is byte-identical to the released README. Opened that source on GitHub and verified the rendered SVG with **nine nodes**. Reviewed the local README preview at desktop and mobile widths; all five images load and the 390-pixel view has no horizontal page overflow. The preview is a local rendering, not a published branch preview.
- All five original PNG SHA-256 hashes and **1440×1000** dimensions match the provenance record. The evidence image still shows the genuine street basemap, generalized cells, marker, evidence, and attribution. No screenshots were recaptured or altered.
- Rechecked claims against model/architecture references and existing network, planning, and explanation assertions. The original PR body remains intact beneath its historical introduction; every publication-audit findings-table row remains unchanged.
- Read-only GitHub checks confirm the release body, title, tag target, publication flags, and update timestamp are unchanged. Local and remote `main` and the `v1.0.0` tag still resolve to their recorded SHAs.

The previous **194 Python / 49 Chrome** results, production build, generated-type check, and golden CLI checks are reused from the dated [release verification](VERIFICATION.md); the application suite is not rerun for prose/navigation changes.

The existing annotated tag object is `c2b2d37aaf5e74a03190746c12badacc6bc86369`; its target is `b324c1b355cda60035fb11fa32bcddf10931f649`. The new editorial commit is separate from that immutable snapshot. No push, PR, merge, tag update, visibility change, or release-body publication is part of this pass.
