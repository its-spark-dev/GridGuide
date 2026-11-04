# v1.1.0 product continuity correction

Base: `ae6d9c482c4e55d5db483338bad34d1415b99ec5`. This is a correction to the
release candidate, not another research phase. No release or deployment is authorized.

## Integration proposal

Restore the original dashboard as the public product's primary UX foundation:
Overview → Prepare & alerts → Grid insights. Reuse the unchanged original Barlow
typography, design tokens, header, cards, icon library, responsive layout and
progressive explanation pattern. A shared public shell gives all three entries the
same navigation and identity. The original challenge application remains separate
at build time and unchanged; it is not imported into the public bundle.

The public Overview renders the already approved G6 fictional frames after mode,
catalog and content verification. Scenario selection and milestone playback select
Python-produced results, never calculate them in TypeScript. Dependency inspection
uses the existing PowerPath. Ask GridGuide provides deterministic, frame-bound
explanations of the displayed evidence. No provider or new prediction API is needed.
Links to preparedness carry only an allowlisted fictional scenario/milestone; the
eight-case operator catalog is explicitly a separate exercise, never an implied
continuation of the customer's network. G7's request/review bindings remain intact.

Geographic coordinates, household risk and elapsed-time confidence are unavailable
in these approved public inputs. Preserve those questions in the dashboard with
honest explanations. Crew counts/access are fixed by the selected definitions;
use approved blocked/missing cases instead of inventing free-form recalculation.
The authorized challenge version retains its original risk, map, crew/access,
needs, communication preview and Standard explanation flows.

Preparedness keeps its exact `/preparedness/` worker scope, explicit save/open,
strict snapshot schema and historical labeling. The root dashboard and operator
page remain uncached. Only shared static presentation resources and the generic
kit may enter the offline shell; no API responses, scenario files or new storage.
Package root HTML and the four existing self-hosted font files through an explicit
allowlist, with their existing OFL and source notices. Continue exact-tree checks.

## Review evidence to complete

- Feature-level comparison of v1.0.0, pre-correction distribution and corrected UX.
- Authentic matched 1440×1000 and 390×844 browser screenshots, with commit provenance.
- Original challenge journey; integrated public controls, navigation and scenario binding.
- Existing G6/G7 offline, privacy, review invalidation and export/replay verification.
- Strict build/types, Python lanes, production package/container checks and frozen hashes.

No numerical rule, catalog, frozen research result, model default, original attribution
or historical tag changes are in scope. Previous G9 screenshots remain historical
evidence; correction screenshots are stored separately. Unavailable public features
are intentional differences, not claims of complete functional equivalence.

## Feature-level comparison

“Source-only” means preserved and functioning in authorized challenge-local mode,
but omitted from the pre-correction public package. “Alternative” is deliberately
not equivalence of numerical models or datasets. The v1.0.0 tag was checked out
separately and its real frontend/API passed the original 49 browser tests. The
current challenge-local application independently passed those same 49 tests.

| Feature / original flow | Before correction: public package at base main | Integrated public candidate / intentional difference | Evidence |
|---|---|---|---|
| Branding, Barlow typography, red/blue palette, card hierarchy | Source-only; replaced by minimal Arial preparedness styling | Original visual system reused across all three screens | Unchanged `styles.css`/`Icon.tsx`; `PublicShell`; matched screenshots |
| Overview landing and three-page navigation | **Broken product continuity**: `/` redirected to `/preparedness/`; no Overview | `/` serves real Overview; Overview / Prepare & alerts / Grid insights shared navigation | `public_app.py`; production route/browser tests |
| Desktop/mobile hierarchy and keyboard navigation | Original responsive dashboard source-only; alternative G6/G7 responsive pages | Original responsive rules plus scoped new controls; native keyboard controls and skip link | Original 49-test suites; public 1440/390/320px and G6/G7 browser tests |
| Anonymous service location selector | Source-only, intentionally absent public source data | Six independently authored scenario choices; no address/location claim | G1 catalog + verified G6 frames; all-18-frame browser comparison |
| Geographic context, generalized asset/line map, optional tiles, recenter/selection, textual equivalent | Source-only; intentionally unavailable publicly | Geographic-context disclosure plus interactive declared dependency schematic; no coordinates or map-library bundle | `GeographicContext.tsx` preserved; `PublicDashboard`/`PowerPath`; exact package manifest |
| HIGH ordinal concern band, factors, score, missing evidence | Source-only; no fictional risk contract | Same dashboard question with explicit unavailable state and explanation; no invented band or probability | `App.tsx`/engine unchanged; public risk disclosure and Standard answer test |
| Conditional restoration envelope, shared-scale counterfactual | Source-only; alternative G6 deterministic milestone output elsewhere | Original timing-card intent with conditional modeled completion; **not** the challenge envelope, empirical interval or G5 simulation | Exact frame completion displayed; blocked/missing values stay unavailable |
| Access clear/restricted/blocked; 2/4/8-person customer controls | Source-only; unsupported in public contracts | Explained fixed staffing/access; working selection of approved blocked/missing examples. No fake sliders | Original interaction tests; G6 nulls; explicit control-limits disclosure |
| Scenario updates and repair timeline | Source-only original comparison; G6 alternate playback | 18 server-prepared milestones, accessible timeline buttons and dependency state changes | Frame equality, scope-binding and null-state tests |
| Source power path, abstract supply, inspection | Source-only; G6 fictional alternative already accessible | G6 component integrated into Overview and preparedness, preserving unresolved links/unlocated terminal | Existing path tests + all-18-frame production tests |
| Repair effort, sequence, source provenance and assumptions | Source-only; public versions/provenance in G6/G7 | Approved frame fingerprints, assumption disclosures and G7 task effort/assignment details; no workbook rates | `offline.ts` trust checks; `review.py` unchanged; original evidence flows preserved |
| Ask GridGuide, contextual questions and Standard fallback | Source-only; original provider/server explanation routes excluded | Standard questions render only reviewed text and approved frame values/reasons; answers reset on selection. No provider/free-text box or new calculations | `FrameExplanation`; invalid-artifact, selection/reset and blocked explanation tests |
| Next action / Prepare now | Source-only original next action; generic safety alternative | Dashboard action transfers exact approved scenario/milestone into preparedness | Real navigation → snapshot fingerprint equality test |
| Scenario-tailored checklist and optional medical/accessibility declarations | Source-only; intentionally no public tailored guidance inputs | Generic reviewed kit, print/download; explicit unavailable tailored-declarations disclosure. No new sensitive input | Original customer journey unchanged; G6 storage/privacy tests |
| Alert eligibility, channel/escalation policy, four communication previews | Source-only; not implemented in approved synthetic contracts | Prepare & alerts preserves navigation intent and explicitly says previews require challenge-local inputs; no invented eligibility/messages | Original four-stage tests; public disclosure; no messaging routes |
| Grid insights: four curated repairs, source evidence, proxy priority, crew scheduling, impact map, explanation ledger | Source-only; replaced by separate G7 minimal operator page | G7 eight-case exercise within Grid insights; four baselines, finite/restricted metrics, task evidence, precedence, tradeoffs | G7 browser tests and independent export/replay; explicit separate-catalog notice |
| Experimental CP-SAT, review and export | G7 accessible alternative | Retained in shared visual system; fixed baseline default, optional frozen CP-SAT, five acknowledgements, settings invalidate review | Unchanged G7 request logic/API; browser invalidation and replay |
| G5 uncertainty visualization | Intentionally unsupported; deferred in accepted G7 | Still unsupported; no quantiles, calibration or resolved ETR invention; 15 failures retained | Original artifacts unchanged; on-screen limits |
| Historical snapshots, save/open/delete, storage reset | Accessible G6 addition | Same strict schema, explicit actions, historical status; exact selection handoff added | Browser restart, schema compatibility, cross-tab, quota and stale-save tests |
| Offline generic kit, printable/downloadable fallback | Accessible G6 addition | Same `/preparedness/` scope/allowlist semantics. Root/operator/API/frames/fonts stay uncached; offline typography falls back | Worker unchanged; cache exclusion tests and real process restart |
| Loading/retry, subsystem isolation and stale results | Source-only originals + accessible G6/G7 protections | Original protections retained; Overview withdraws invalid/offline results and retries without source fallback | Original, G6/G7 and new tampered-artifact/mode tests |
| Version/evidence disclosure and contributor attribution | Accessible documents; source original UI preserved | Frozen versions, original files, Git history and notices retained; font OFL/source notice explicitly packaged | Preservation manifest, Git diff and recursive package inspection |

No original source feature was removed. The confirmed regression was distribution-level
product continuity. The corrected public flow still cannot equal the source-backed
model/map/communication capabilities without new evidence and an independently reviewed
contract. It does not conceal those differences or relabel the synthetic output as AEP data.

## Implemented boundary and review findings

- One FastAPI service and three public React entries; root is now the dashboard.
  Legacy `index.html`/`App` remain the challenge-local build, never a public import.
- Only `backend/public_app.py` changes on the server: root static routing and
  same-origin font CSP. No new numerical route or schema; no generated-type edit.
- Package adds one exact HTML entry, compiled dependencies, four original WOFF2
  files and OFL/source notices. Startup still checks every byte and rejects extra files.
- The original `styles.css` and icon set are reused without edits. G6/G7 logic remains
  intact except the approved-frame link selection at preparedness startup.
- An automated accessibility regression found the brand's explicit accessible name
  did not match its visible text. The shared link now derives its name from visible
  content. This was corrected, not waived. Automated checks are not manual VoiceOver.
- No new public-data research, solver experiment, simulation or statistical analysis.
  G2/G3, G4 No-Go and all G5 convergence findings remain historical frozen evidence.

Detailed verification, package checksums and screenshot provenance accompany the PR.
Existing Chromium-only coverage, missing detailed VoiceOver observations, storage
limits, same-origin compromise and non-authenticating hashes remain limitations.
Historical G9 captures and recording are not overwritten or presented as the updated UI.
Public hosting, licensing/security prerequisites, merge and publication still need
separate authorization.

## Verification commands and results

See [verification evidence](../verification/continuity/README.md) and [matched
screenshots](../media/continuity/README.md). The operator landing also surfaces
Python-owned completed/restricted customer-hours, critical latency and unresolved /
censored counts in summary cards; detailed comparison, all tradeoffs and experimental
limitations remain available below. No derived metric is computed by the UI.
