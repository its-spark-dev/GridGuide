# GridGuide demo freeze — 2026-10-24

**Local demo: GREEN. Overall challenge readiness: YELLOW.** The verified flow works with live Gemini or Standard explanations. Do not claim full challenge completion: explicit customer-needs declarations (R11) are absent, related escalation (R13) is partial, and workbook labor-hour semantics remain unresolved. No runtime blocker was found. See [current requirement evidence](REQUIREMENTS_TRACEABILITY.md).

## Recover the exact demo

Run from the repository root. Prerequisites: the existing Python 3.12 `.venv`, installed frontend dependencies, and the pinned challenge files in `data/raw/`. If a teammate needs dependency setup, follow README; do not upgrade dependencies just before judging. Ports 8000 and 5173 must be free. Stop only processes you own.

Terminal 1, live Gemini using the existing ignored local `.env`:

```sh
git check-ignore .env
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

The loader accepts simple single-line settings, never executes `.env` as shell code and never prints values. The application does not load `.env` implicitly. Environment names: `GEMINI_API_KEY`, `GRIDGUIDE_AI_PROVIDER`, optional `GRIDGUIDE_AI_MODEL`; `OPENAI_API_KEY` belongs to the retained explicitly selected alternative. Keep the verified Gemini model default; see [provider configuration](GEMINI_PROVIDER.md). Free Tier intent/billing-disabled status was supplied by the user; generation success does not independently verify project billing.

Wait for “Application startup complete.” Terminal 2:

```sh
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173/`. Demo location A is automatically selected; this is a single vetted customer, not arbitrary address lookup. A refresh starts at CLEAR and clears session comparisons/questions.

For a provider-independent rehearsal, stop the backend with Ctrl-C and use this **instead of** the live command, then refresh the browser:

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

This command does not read `.env`. The page shows **Standard explanation**. Disable **Street map** for a no-tile demo. Keep the local backend/frontend running: “offline” means no external AI/tiles required, not a standalone browser application.

## Frozen scenario and exact outputs

Alias `demo-a`: anonymized Demo location A; verified Virginia challenge geography. Dependency order: Customer → Distribution transformer → Fuse → abstract Circuit Breaker terminal. The terminal has no supplied geometry and must stay schematic-only.

Simulated inputs: storm level 2, one reference crew, one fuse-cutout replacement, one 100-kVA transformer replacement, available circuit supply. Only access is interactive. These are declared repairs, not observed failed equipment.

| Access | Risk / confidence | Raw modeled hours | Displayed provisional hours |
|---|---|---|---|
| CLEAR / NORMAL | HIGH / LOW | 11.736–17.604 | **11–18** |
| RESTRICTED | HIGH / LOW | 16.236–24.354 | **16–25** |
| BLOCKED | HIGH / LOW | **null** | **Unavailable — pending access clearance** |

Risk score 4 = storm 2 + overhead transformer 1 + historical circuit evidence 1. It is an ordinal concern band, never an outage probability. Access does not change risk. Two work sites receive the restricted-access adder; ILM 4.5 applies once. Extra crews never divide serial repair duration. The range begins when an assigned crew starts its response, excluding unknown dispatch queues, storm holds and unlisted work. Workbook-hour conversion and the 1.5 upper allowance are provisional team assumptions, not official AEP ETR semantics.

## A 2–3 minute judge sequence

1. **0:00–0:25:** Identify Demo A and Virginia challenge data. Show HIGH, LOW confidence and 11–18 provisional hours; expand the three risk factors. State that no outage probability or live utility status is claimed.
2. **0:25–0:55:** Use **Grid context**. Show customer/transformer and fuse areas; select the Circuit Breaker row to demonstrate missing geometry. Contrast the generalized map with the verified dependency schematic.
3. **0:55–1:25:** Select RESTRICTED. Point to **11–18 → 16–25 hours** and the two-worksite access cause. Ask why the estimate changed; AI selects approved evidence, the engine owns the values.
4. **1:25–1:45:** Select BLOCKED. Show unavailable/null and ask when power will be restored. No replacement ETA appears; access clearance is required. The comparison can retain a clearly labeled previous range, never a current estimate.
5. **1:45–2:20:** Open **Alerts & preparation**. Show general preparation, safety, eligibility distinct from opt-in, and the four hypothetical message stages. No notification is sent.
6. **2:20–2:45:** Explain Standard fallback and optional street tiles. Return to CLEAR if time permits. Use the prepared provider-disabled run if external service is unavailable; never pretend a Standard answer was AI-generated.

## Policies, failures and limits

- **Alert update:** eligible customer plus either absolute raw endpoint delta **>6 hours**, or a finite/unavailable transition. Exactly 6 does not qualify; CLEAR → RESTRICTED qualifies via upper delta 6.75. The availability trigger is an adapter extension. A viewable update sample is not necessarily an eligible alert. The old one-displayed-hour planning rule is retired. All thresholds and timing are prototype policies, not confirmed AEP rules.
- **AI:** curated questions; no general chat. Raw user questions, identities and coordinates are not sent to Gemini. The model returns allowed reference IDs; the server rejects extra claims, wrong results, unsupported references and invalid output, then renders approved text. Nine judge adversarial prompts across all three states are refused without a provider call. The supported BLOCKED restoration question returns no finite range.
- **Provider failure:** missing key, timeout, invalid output, HTTP/auth/quota errors use deterministic Standard explanations. Overall provider deadline is eight seconds; the browser allows ten. Cache is process-local, 64 validated answers, five-minute TTL, context/question bound. Simultaneous cold calls may consume separate requests. No persistent cache or paid-provider failover.
- **GIS:** 0.01° generalized cells, two displayed marker groups for three located assets, 165 generalized primary-line parts. No precise premise positions, secondary-service inference, fabricated terminal position, routing or inferred connectivity. Map tiles are optional. Map API failure leaves the schematic and analytical journey intact.
- **Recovery:** analysis/location/map/explanation retries are separate. Scenario and question revisions reject stale results. During failed/pending analysis, old restoration, comparison, preparation and alert output is withheld. Refresh returns to CLEAR.
- **Operational boundary:** no live outage, weather, dispatch, crew-position, enrollment, notification or restoration-confirmation integration. Safety/preparation comes from the teammate rules; no inferred medical status.

## Final evidence and severity

99 backend tests pass, including the 98-test baseline plus 27 adversarial question/state cases in one new regression test. Golden CLI, generated OpenAPI/TypeScript consistency, TypeScript check and Vite production build pass. Browser checks cover three access states, exact API/UI values, risk invariance, four message stages, preparation, GIS/schematic, map/tile failure and retry, stale questions/scenarios, analysis/initial-load/explanation retries, response binding and refresh. Provider fault tests use mocks; live verification is a separate small smoke sample.

Keyboard checks cover skip link, access/lifecycle radios, question buttons, asset list, map toggle and disclosures. Layout checks pass at 320/390/768 px. Primary text colors measure 5.39:1 or higher against the secondary surface. Desktop/mobile screenshots were reviewed. This is focused accessibility QA, not formal WCAG or screen-reader certification.

Both services were restarted from the commands above. The live rehearsal passed CLEAR, risk, RESTRICTED and BLOCKED with `AI-assisted explanation`, then repeated the exact CLEAR request through the validated cache. The backend was restarted with AI disabled and the complete sequence passed with `Standard explanation`. Browser refresh reset the session correctly. Measurements below are local single-run observations after backend readiness, not a performance guarantee.

| Interaction | Live Gemini run | AI-disabled run |
|---|---:|---:|
| New browser page to CLEAR result | 134 ms | 202 ms |
| Location evaluation HTTP | 3.1 ms | 2.8 ms |
| CLEAR → RESTRICTED visible update | 54 ms | 55 ms |
| RESTRICTED → BLOCKED visible update | 58 ms | 60 ms |
| First explanation HTTP / visible | 4,725 / 4,772 ms | 2.4 / 59 ms |
| Repeated exact explanation HTTP / visible | 3.6 / 42 ms (cached AI) | 3.0 / 48 ms (Standard) |

Other uncached live calls: risk 4.09 s, RESTRICTED 4.93 s, BLOCKED 5.66 s HTTP. This is slower than the earlier 0.9–1.3 s sample and will be noticeable during judging. No timeout or invalid live response occurred in this final sample. Narrate the already-visible calculation while the contextual answer loads; do not promise subsecond AI. Standard answers took 48–59 ms to display. External-failure tests confirmed the core journey remains available.

| Severity | Finding | Freeze disposition |
|---|---|---|
| BLOCKER | None in the verified local demo | Runtime GREEN |
| HIGH | R11 declared accessibility/medical/critical-facility needs not implemented end to end | Disclose incomplete challenge coverage; do not add a feature during freeze |
| MEDIUM | Workbook-hour semantics unresolved; no calibrated restoration accuracy | Keep persistent provisional/time-origin/assumption labels; seek mentor clarification after the freeze review |
| MEDIUM | R13 needs-based escalation incomplete without declarations | Suggested general channels and timing only; no operational claim |
| MEDIUM | Final uncached Gemini calls took 4.1–5.7 seconds | Show pending state and explain validated result while waiting; bounded Standard fallback remains available |
| MEDIUM, resolved | Older architecture claimed a one-hour update rule | Documentation now matches strict >6 raw hours plus availability change; existing boundary tests pass |
| LOW | One auto-selected customer; provider quota varies; no assistive-technology certification | Bounded demo scope, honest fallback, focused accessibility checks |
| POLISH, resolved | Probability meaning, geography, preview/enrollment and map limitations needed quicker comprehension | Concise visible labels, expandable map detail, numbered stages, access-change and BLOCKED explanations |

## Freeze rules

Do not change golden selection, source pins, raw/processed data, teammate pipelines, numerical engine, labor recipes, ILM, upper allowance, risk rules, privacy generalization or result-binding validation. No new features, providers, weather, RAG, authentication or real delivery. Keep `.env` ignored and local; never print or commit values. Fix only a reproduced regression with targeted verification. Rehearse both live and Standard paths after any approved change.

Recheck commands:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
npm --prefix frontend run types:generate
git diff --exit-code -- frontend/src/api.generated.ts
npm --prefix frontend run build
```

Gemini checkpoint: `4c57b7b` (`feat: integrate validated Gemini outage explanations`), pushed with preceding `3ac13b8` to `origin/main`. Final polish/freeze is a separate reviewed commit. No source data, teammate pipeline, numerical engine, API contract or credential is part of the final polish patch.
