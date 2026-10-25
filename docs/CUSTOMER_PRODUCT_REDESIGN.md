# Customer product redesign — frontend freeze review

Implemented against backend freeze `a4a457b60dc61d50fd65477b2c0692f320622f04`.
This pass changes presentation, browser session state and frontend verification.
It does not change API contracts, generated types, numerical rules, AI grounding,
source relationships, teammate pipelines or data. The standalone pole module
remains a validated, inactive extension.

**Decision: FREEZE.** The intended frontend implementation and verification are
complete. Changes remain uncommitted for review; no commit or push was made.

## Product structure

The long planner-first page is replaced by three hash-navigation views:

- **Overview:** verified anonymous location, ordinal risk and low confidence,
  disconnected live status, conditional restoration range, first preparation
  action and explicit notification-delivery status.
- **Prepare & alerts:** exact server-ordered checklist actions, optional declared
  needs and server guidance, always-readable safety advice, separate eligibility,
  channels and triggers, and four communication previews. Nothing is sent.
- **Grid insights:** live policy comparison, candidate inspection with generalized
  map and evidence chain, then ordinal crew lanes and deduplicated release stages.

Customer and planning scenarios retain independent settings, revisions,
cancellation and explanation bindings. Planning loads on first visit. Browser
Back/Forward preserves session state; refresh clears declarations and checklist
completion. Checklist checks use exact action strings and never enter API or AI
requests. Confirming the same location does not reset results.

The customer range rail uses server `display_hours` and only transforms numbers
for graphical placement. Previous/current rails share a visual scale. Time starts
at crew response, not the current clock. Actual completion may take longer.
BLOCKED and insufficient-risk states retain unavailable values and access to
valid guidance. No midpoint, probability, countdown or utility ETA is invented.

Risk inputs retain their six evidence classifications, contribution points and
source references in the nearby disclosure. The assumption ledger and detailed
labor derivation remain available. The historical repair candidate remains a
qualified spatial hypothesis; nearby facilities are not asserted to be electrically
attached. Map geometry comes only from the existing public contracts.

Policy comparison uses both actual server responses under the same conditions.
Changing policy follows the new recommendation; changing crews/access retains a
valid inspection selection. An alternative-policy failure has an independent
retry. The 1 versus 23 comparison and equal repair effort are response values,
not UI constants. Crew cards show order, dependency waits and server finish
intervals; their widths do not encode elapsed duration.

## Frontend organization and visual system

`useCustomerAnalysis` owns customer requests and confirmed predecessors.
`useRestorationPlan` owns the separate plan, opposite-policy response, inspection
selection and plan explanations. Contextual customer explanations use the
existing canonical questions, empty declared-needs payload and bound results.
Standard and AI-assisted responses use the same presentation quality.

The existing React, TypeScript, Vite and Leaflet stack is retained. No router,
UI framework, chart or animation dependency was added. Playwright 1.64.1 is a
pinned development-only dependency, using installed Google Chrome.

Barlow Regular/Semibold and Barlow Semi Condensed Semibold/Bold are local WOFF2
assets with their OFL license and pinned source revision. There is no runtime
font CDN. Icons are a small local SVG set. White surfaces, blue actions and a
limited red identity replace repeated red banners and dense badges.

Mobile uses a continuous outlook summary and local Map / Evidence / Crew plan
tabs. Native controls, unique headings, a skip link, map list alternatives,
keyboard tabs/radios and short status announcements are provided. Navigation
moves focus to its destination. Declaration updates preserve keyboard position
unless the user has moved elsewhere. Reduced motion disables transitions.

## Verification

Reproducible commands from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
npm --prefix frontend run build
npm --prefix frontend test
```

Type reproduction was checked by saving the existing generated file, running
`npm --prefix frontend run types:generate`, and comparing bytes. No generated
contract change resulted. Browser fixture details and ports are documented in
[`frontend/tests/README.md`](../frontend/tests/README.md).

Verified in this pass:

- All **194 backend tests** pass. The golden demo retains CLEAR 2.5–12 hours,
  RESTRICTED 4–16.5 hours and BLOCKED unavailable at four people.
- Strict TypeScript and production build pass. Generated types are byte-identical.
- **37/37 browser tests pass** with fresh isolated server startup and automatic
  cleanup. The final location-selector focus assertion also passed independently.
- Frozen snapshots match for **9 customer evaluations, 9 AI public contexts and
  324 planning combinations**, including four pinned raw-source hashes.
- Protected backend, scripts, existing Python tests, raw/processed data inventory
  and hashes, pipelines and pole code match the pre-edit baseline.
- The browser suite uses real production API factories with a disabled provider.
  Its second isolated app changes only in-memory risk evidence to exercise B2.
  No product test switch, endpoint, provider call or data-file change is added.
- B1 directional, unchanged, mixed and unavailable transitions; B2 partial risk;
  declaration privacy; exact lifecycle messages; stale responses; independent
  customer/planner settings; comparison failure/retry; blocked descendants;
  offline maps/Standard explanations; keyboard and browser history are covered.
- Six widths—1440, 1280, 1024, 768, 390 and 320—cover normal, loading, failure,
  BLOCKED and insufficient-risk states. Actual Leaflet SVG/path dimensions are
  checked, rather than accepting a visible empty map container.
- Initial-view assertions cover all core answers at 1440×900 and 1280×800 and the
  first preparation CTA at 390×844. No horizontal overflow was found, including
  a 200% CSS zoom simulation. Local fonts load with external requests blocked.
- Measured palette contrast: body 13.11:1, secondary text 6.40:1, blue actions
  7.24:1, amber concern 5.97:1, safety text 6.43:1. Core select and outlined AI
  control borders exceed 3:1. Focus remains visible in keyboard task checks.

These are browser task simulations, visual inspection and heuristic accessibility
checks, not independent participant research or formal accessibility certification.
Live Gemini was not called by this frontend verification pass; grounded Standard
fallback and existing backend provider tests cover the unchanged contract.

## Before/after critique and remaining limits

Previously, operational planning pushed the customer outlook and preparation far
down one page. The new Overview exposes the customer's first answer and action
before deeper analysis. Technical depth remains reachable from the top navigation,
with explicit spatial evidence and crew dependencies instead of a long default
report. The map shows useful generalized areas without pretending to be an outage
boundary or exact service location.

The larger interpretation risks remain visible: no connected live outage service,
no official ETR or dispatch rule, uncertain actual efficiency and clearance,
unverified facility electrical attachment and no notification delivery. The
prototype is still bounded to supplied, verified scenario data.

An already-running demo API was found to have older code loaded. It was preserved;
verification used dedicated current-source processes. Before a final live demo,
restart the backend in its existing terminal using the documented command so it
loads the frozen source. The redesign does not change the launch commands:

```sh
.venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173/#overview` in Chrome. Walk through Overview → Prepare &
alerts → Grid insights; compare the policies, inspect historical evidence, change
to two crews, block the upstream candidate, and open a grounded explanation.

Screenshots, traces, build outputs and caches are local/ignored artifacts. Secrets
remain ignored and unstaged. No commit or push is part of this implementation.
