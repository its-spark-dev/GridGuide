# GridGuide Q2/Q4 feature-freeze evidence — October 24, 2026

**Local implementation: GREEN. Operational evidence: bounded / YELLOW.** Q2 supports complete reverse dependencies for verified source assets and a qualified historical ARCOS spatial replay. It does not establish direct ARCOS identity or current outages. Q4 supports an explicit four-candidate prototype priority policy, spatial critical-premise context, one/two-crew scheduling and conditional time. It is not AEP dispatch policy. Actual switching, facility electrical attachment, measured efficiency and clearance duration remain unavailable.

Detailed source investigation, coverage denominators, six-class evidence ledger, candidate comparison, ten hostile judge questions and the current 2–3 minute demo: [Q2_Q4_DECISION_SUPPORT.md](Q2_Q4_DECISION_SUPPORT.md). Formulas: [MODEL_SPEC.md](MODEL_SPEC.md). Requirement matrix: [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md).

## Recover the demo

Use Python 3.12 `.venv`, installed frontend dependencies and the four pinned raw files. Sources prepare once in memory; the larger planning inventory adds startup work. Wait for application startup before opening the UI. Stop only local processes you own.

For deterministic operation without external AI:

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

For the existing Gemini configuration, first verify `git check-ignore .env`. Never print the file or key:

```sh
.venv/bin/python - <<'PY'
import os
from pathlib import Path
import uvicorn
allowed = {'GEMINI_API_KEY', 'GRIDGUIDE_AI_PROVIDER', 'GRIDGUIDE_AI_MODEL'}
for line in Path('.env').read_text().splitlines():
    name, separator, value = line.strip().removeprefix('export ').partition('=')
    if separator and name.strip() in allowed:
        os.environ[name.strip()] = value.strip().strip('"\'')
uvicorn.run('backend.api:app', host='127.0.0.1', port=8000)
PY
```

Free Tier/billing-disabled intent is user-declared; successful generation does not verify billing configuration. No paid-provider failover is configured. The verified model remains `gemini-3.5-flash-lite`.

In another terminal:

```sh
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173/. The restoration decision panel appears first. Refresh resets one crew, four people, clear access and spatial-proxy preference enabled. The customer outlook below remains a separate golden scenario. The planning map uses generalized source cells without external tiles; customer map tiles and AI are optional. Local services and pinned source files remain necessary offline.

## Frozen scenario facts

| Candidate | Damage evidence | Dependent premises | Repair person-hours | Default incremental release |
|---|---|---:|---:|---:|
| Critical-context fuse | Declared; fire-station/premise spatial proxy | 1 | 1.728 | 1 |
| Historical fuse replay | Qualified ARCOS pole/device spatial hypothesis | 23 | 1.728 | 23 |
| Golden upstream fuse | Declared on exact source asset | 4 | 1.728 | 3 |
| Golden transformer | Declared 100-kVA replacement | 1 | 10.008 | 1 |

Union **28** premises, sum **29**, overlap **1**. Clear total **15.192 person-hours**. Four people/one crew: raw **3.798–15.192 h**, displayed **3.75–15.25**. Two crews: raw **3.366–13.464 h**, displayed **3.25–13.5**; first milestone releases 24 dependencies concurrently. Quarter-hour display rounding belongs to planning-v1. Extra crews do not divide the serial fuse→transformer branch.

Restricted access adds **2.25 person-hours per declared separate worksite**. Blocking the golden fuse defers the transformer, leaves 24 independent premise releases potentially executable, and withholds full completion. Blocking every candidate gives no tasks, no recommendation and no duration. These are dependency releases under the declared damage set, not confirmed energized premises.

The original customer-v2 golden scenario remains **11.736 repair person-hours**; four-person clear **2.5–12 h**, restricted **16.236 person-hours / 4–16.5 h**, blocked null. Risk remains score 4 / HIGH, predictive confidence LOW, probability null. Customer declarations stay session-only and outside AI/infrastructure priority. Communications remain previews; no delivery occurs.

## Executed validation

- Full `.venv/bin/python -m unittest discover -s tests -v`: **171 tests passed**, final run 55.885 s. Includes all 118 baseline tests plus source matching, spatial ambiguity, generalized reverse sets, candidate scheduling, null evidence, privacy and grounded-plan checks.
- Golden `backend.demo`, RESTRICTED and BLOCKED commands succeeded. Source hashes checked throughout; no raw mutation.
- Generated API types reproduced byte-for-byte. Strict TypeScript and production Vite build passed.
- Isolated Chrome: **15 browser check groups passed**. Default union/recommendation; two-crew milestone; separate people control; proxy preference; restricted effort; blocked descendants; all three offline Standard questions; selected-candidate map; keyboard controls/disclosures/questions; customer regression; 390/320 px mobile with no page overflow; plan failure/retry; explanation failure/retry; rapid stale-response rejection; no browser runtime errors.
- Native select keyboard checks used type-ahead plus Tab on macOS Chrome; checkbox/candidate/disclosure/explanation controls used Space/Enter. Focused QA is not formal assistive-technology certification.
- Live Gemini plan smoke: dependency question **2,769 ms**, priority **2,470 ms**, crew schedule **2,294 ms**; all `ai_assisted`, no fallback, valid bound IDs/references. Browser showed the bound AI-assisted priority answer. Numerical results were already available independently of the provider.
- Final desktop and mobile decision screenshots were visually inspected. Reproduced missing-evidence copy and excessive decimal formatting defects were fixed and rechecked.
- Git index remains empty. `.env`, IDE metadata, schema intermediates and build output remain ignored. No pipeline/raw/processed-data changes. No commit or push was made in this Q2/Q4 pass.

Transient test logs, browser scripts and screenshots are under `/tmp/gridguide-q2q4-*`; they are not project artifacts or runtime dependencies. Source fixtures and committed baseline history make numerical tests reproducible without them.

## Freeze recommendation and boundaries

**Ready for a bounded prototype feature freeze after review of this uncommitted diff.** Prior realignment is already committed at `8d6f7ee`; this pass deliberately creates no commit. Focus remaining effort on rehearsing the evidence chain and preserving the fallback path.

Do not add weather, RAG, training, authentication, messaging, power flow or more candidate recipes in this freeze. Actual operational use needs authoritative damage identity, positional accuracy/service attachment, full topology reconciliation, measured productivity/concurrency, qualified crew composition, dispatch/clearance/material timing, switching state/protection/capacity and utility priority/alert policy. Preserve these as unavailable rather than choosing defaults.
