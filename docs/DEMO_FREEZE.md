# GridGuide AEP-aligned demo freeze — October 24, 2026

**Overall evidence chain: YELLOW. Local implemented flow: GREEN.** AEP labor semantics are resolved, reverse dependencies for declared damage on source-verified assets are implemented, and explicit customer needs work. The observed ARCOS→specific equipment/section join, actual sectionalization, measured conversion efficiency and operational priority remain unavailable. Do not claim these are resolved by the guide or by passing tests. See [separate coverage matrix](REQUIREMENTS_TRACEABILITY.md).

## Recover the demo

Run from the project root with Python 3.12 `.venv`, installed frontend dependencies and pinned raw source files. Use README setup commands if necessary. Ports 8000 and 5173 must be free; stop only processes you own. Sources prepare in memory at startup.

Terminal 1, live Gemini from the ignored local `.env`. First verify `git check-ignore .env`; never print the file or key:

```sh
.venv/bin/python - <<'PY'
import os
from pathlib import Path
import uvicorn
allowed = {'GEMINI_API_KEY', 'OPENAI_API_KEY', 'GRIDGUIDE_AI_PROVIDER', 'GRIDGUIDE_AI_MODEL'}
for line in Path('.env').read_text().splitlines():
    name, separator, value = line.strip().removeprefix('export ').partition('=')
    if separator and name.strip() in allowed:
        os.environ[name.strip()] = value.strip().strip('"\'')
uvicorn.run('backend.api:app', host='127.0.0.1', port=8000)
PY
```

The loader reads simple single-line values without executing shell syntax. Free Tier/billing-disabled intent is user-declared; successful generation does not verify billing configuration. See [provider evidence](GEMINI_PROVIDER.md).

Terminal 2:

```sh
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173/ after “Application startup complete.” One vetted Virginia customer is selected. Refresh resets CLEAR, four people, no declarations, comparison or answer.

For deterministic recovery, use this backend command instead of the live loader, then refresh:

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Disable Street map if tiles fail. Offline means the local services still run with external AI/tiles optional. Standard explanation is labeled honestly; numerical results and customer guidance remain local.

## Frozen numerical and dependency evidence

Declared scope: one 100-kVA transformer unit replacement plus one fuse cutout replacement on exact verified source assets. Source topology is Customer → transformer → fuse → abstract Circuit Breaker terminal. Historical ARCOS circuit context does not establish those failures.

Direct installation `1.28 + 0.256 = 1.536`; removal `0.944 + 0.128 = 1.072`; replacement `2.608 × 4.5 = 11.736 person-hours`. Installation-only would be 6.912, not the complete replacement scenario. Restricted two-site direct access work adds 1.0; `(2.608 + 1.0) × 4.5 = 16.236 person-hours`. No additional travel/setup time.

| Crew people | CLEAR raw → displayed elapsed hours | RESTRICTED raw → displayed elapsed hours | BLOCKED |
|---:|---|---|---|
| 2 | 5.868–11.736 → **5.5–12** | 8.118–16.236 → **8–16.5** | null |
| 4, default scenario | 2.934–11.736 → **2.5–12** | 4.059–16.236 → **4–16.5** | null |
| 8 | 1.467–11.736 → **1–12** | 2.0295–16.236 → **2–16.5** | null |

The prototype envelope spans ideal all-person contribution to one effective worker, serial tasks, half-hour outward rounding. It is neither a measured efficiency nor a guaranteed duration bound. Real productivity, crew composition and unknown holds remain open. Extra available crews do not divide this path. Risk stays score 4/HIGH, LOW predictive confidence, probability null.

Reverse index: all global paths containing the exact fuse identity yield four unique GIS-matched premises; transformer identity yields one, already in those four. Their union is four, not five. Three paths could clear declared damage after fuse repair; one after transformer repair. There are 1,559 other source circuit paths outside the declared damage. These are conditional dependency facts, not observed outages/restorations.

Actual sectionalization-restorable customers, ARCOS-observed affected customers and affected critical facilities remain null. The source regional facility inventory is hospital/fire/ambulance 5/37/10; within matched primary geographic extent 0/1/0. This is **spatial criticality context only**, prompting electrical/outage/backup verification before prioritization.

## A 2–3 minute AEP judge sequence

1. **0:00–0:20:** Demo A, HIGH/LOW confidence, four-person CLEAR 2.5–12 conditional elapsed hours. Say damage is declared on verified source assets; no official ETR.
2. **0:20–0:45:** Expand labor derivation: installation + removal = 2.608 direct labor; AEP ×4.5 = 11.736 person-hours. Effort is not duration; travel/setup already included.
3. **0:45–1:05:** Select two, eight, then four people. Effort/risk stay fixed; only the ideal elapsed boundary moves. Actual crew efficiency is unknown.
4. **1:05–1:25:** RESTRICTED shows 16.236 person-hours and 4–16.5 elapsed hours. Ask why it changed while narrating the source-derived access rate and assumed two-site application.
5. **1:25–1:45:** BLOCKED withdraws finite duration. Unknown clearance is not guessed.
6. **1:45–2:15:** Show damage-centric reverse counts: fuse four, transformer one, union four; conditional release three then one. State actual switching restoration is unavailable. The nearby fire-station context requires electrical verification, not an assumed connection.
7. **2:15–2:40:** Declare medical/accessibility need, show tailored preparation and phone/direct-support suggestion. No inference, AI disclosure, enrollment or sending. Clear declarations. Explain Standard fallback if Gemini is unavailable.

## Verified behavior and prototype policy

Four lifecycle messages remain hypothetical previews. Eligible updates require absolute **raw elapsed** endpoint change >6 hours or finite/unavailable transition. Four-person CLEAR→RESTRICTED does not qualify (upper delta 4.5), though its sample is viewable. Restricted eight→two qualifies (lower delta 6.0885), with unchanged person-hours. Exactly six does not qualify. Official AEP thresholds, timing and escalation rules remain open.

Needs are explicit enum selections, held only in page memory/request processing; no source attribute inference, storage or provider exposure. Provider contexts/cache are generic. AI returns reference IDs only; the server inserts every fact and value. Unsupported questions never contact the provider. Invalid output, quota/network/auth failure or timeout yields Standard explanation. Gemini deadline seven seconds, overall eight; browser ten. Cache 64 validated answers / five minutes. No paid fallback.

The map retains generalized geometry, two marker groups/three located assets and 165 primary parts. Missing terminal geometry stays missing. GIS/tile failure does not affect the schematic, calculations, preparation or messages. Pending/error analysis hides old effort, range, impact and guidance. Fast crew/access/needs changes preserve the latest combined selection; forged/mismatched responses are rejected.

## Verification record

Full suite: **118 backend tests**; provider unit tests are mocked. Golden CLI verifies NORMAL/CLEAR, RESTRICTED and BLOCKED, all crew sizes, deterministic risk, nulls and unchanged pinned source hashes. OpenAPI generation, strict TypeScript and Vite production build pass.

Headless Chrome against the real local API passed crew/access matrices, exact API/UI equality, reverse counts and unknown ARCOS/switching labels, all three declarations/clearing/refresh, no browser storage, no declarations in explanation requests, all four previews, raw elapsed eligibility, keyboard radios, 320/390/768 layouts, combined delayed selections, analysis failure/retry and wrong-crew result rejection. Separate regressions passed map/tile failure/retry, source geometry/schematic, explanation failure/retry, stale question/scenario suppression and wrong-result rejection. No uncaught page errors. Desktop/mobile result, effort, impact, controls, needs and AI screenshots were inspected. These are focused accessibility checks, not formal WCAG certification.

Live Gemini model discovery HTTP 200; selected model supports generateContent. Six uncached browser intents (CLEAR, labor, priority, risk, RESTRICTED, BLOCKED) all returned validated AI-assisted explanations in **0.806–1.030 seconds**; identical CLEAR repeat **0.049 seconds**. These local smoke observations do not promise provider latency. No key/raw provider output was exposed. [Full live table](GEMINI_PROVIDER.md#live-results-and-checks--aep-realignment).

## Recheck and freeze boundaries

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
npm --prefix frontend run types:generate
npm --prefix frontend run build
git diff --check
```

Compare generated types before/after generation for drift; an uncommitted contract change naturally differs from HEAD. Do not force it back to the prior schema. Preserve source hashes, teammate pipelines/data, credential exclusion, identity/privacy checks, reference validation and explicit unknowns. No new weather/RAG/auth/SMS/ML/power-flow scope. Only repair reproduced defects with targeted verification.

This realignment started from clean checkpoint `d9d6677b8f7335b9890c6a1414292f5ff0a2245b` (`chore: freeze judge-ready GridGuide demo`). No new commit or push is part of this pass. Current changes are intentionally reviewable in the working tree. The previous freeze's operational assumptions do not override the AEP guide or the user's evidence constraints.

## Ten judge questions

1. **Are labor values elapsed time?** Direct workbook labor ×4.5 is total person-hours; elapsed time is a separately labeled conditional crew model.
2. **How is the range calculated?** For four-person CLEAR, 11.736/4 to 11.736/1 gives raw 2.934–11.736; outward half-hour display is 2.5–12. Actual efficiency is unavailable.
3. **Why not four times faster with eight people?** Only the ideal boundary scales; serial dependencies, unknown skill mix and operational holds prevent a guaranteed proportional speedup.
4. **Why does access worsen it; is travel counted twice?** Two assumed access tasks add 1.0 direct hour before the single 4.5 multiplier. Travel/setup already sit inside it; no second adder exists.
5. **How do you know who depends on the damaged asset?** Reverse all exact typed asset memberships in matched_upstream, then validate every premise/customer/transformer/circuit join. Fuse four, transformer one, union four. Damage is declared on those verified identities.
6. **Did ARCOS identify these damaged assets?** No. The equipment/section identity join is missing; observed ARCOS impact remains null. Historical circuit evidence is separate.
7. **Why repair the fuse first; does it prove switching feasibility?** Upstream-first policy could release three declared dependencies before the remaining transformer path. Actual isolation operations and sectionalization-restorable counts are unavailable.
8. **Are critical facilities actually supplied and electrically affected?** The three layers are supplied; one fire-station feature falls in the geographic context. Electrical attachment/outage/backup is unverified, so affected count and weights stay null.
9. **Are medical needs inferred or sent to Gemini?** No. Explicit optional selections affect reviewed guidance only, remain session-only and are stripped from provider context/cache.
10. **Does AI calculate this or fail dangerously when offline?** The engine owns all numbers, policy and dependencies. AI selects approved references only; failure yields the same server-grounded Standard explanation, with BLOCKED still null.
