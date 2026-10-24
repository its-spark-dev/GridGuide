# GridGuide

GridGuide is a planned map-centered customer experience for the AEP HackOHI/O 2026 AI Outage Concierge challenge. It will connect an anonymized location to verified grid dependencies, explain a scenario-based outage-risk band, estimate a conditional restoration range, and show how access or damage assumptions change that result. Preparation guidance and communication previews will use validated results and explicitly declared customer needs.

Proposed architecture: React/TypeScript and Leaflet, one Python/FastAPI service, preprocessed local data, deterministic risk/restoration rules, and a constrained AI explanation layer with a standard offline fallback. No trained probability model or live utility integration is supported by the current data.

**Browser slice: GREEN for the demonstrated local flow; model credibility remains YELLOW.** The React dashboard calls FastAPI and the unchanged validated engine for customer → topology → risk → restoration → access change → causal explanation → preparation and alert previews. A Leaflet map shows verified, privacy-generalized AEP geography. “Ask GridGuide” adds constrained AI-assisted reference selection with deterministic fallback. Gemini Flash-Lite passed the four live smoke cases; see [provider setup and evidence](docs/GEMINI_PROVIDER.md). Labor-unit interpretation and predictive calibration remain unresolved; output remains a conditional simulation.

## Run the browser dashboard

From the repository root, with the existing Python 3.12 environment and Node 22.12+:

```sh
.venv/bin/python -m pip install -r requirements-web.txt
npm --prefix frontend ci
```

Start the backend in one terminal:

```sh
.venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```sh
npm --prefix frontend run dev
```

Open **http://127.0.0.1:5173/**. The frontend proxies `/api` to port 8000. Both ports must be available; the frontend fails explicitly rather than silently selecting another port. Wait for backend startup to finish, or use the dashboard's retry button. Initial preparation verifies the AEP sources once; scenario changes reuse that context.

Select **Clear → Restricted → Blocked → Clear**. The browser displays API-provided ranges, stable HIGH risk and the engine's calculated explanation. Blocked access has null bounds and a pending-clearance message. During requests or failures, the previous restoration range is hidden. Aborted and superseded responses cannot replace a newer selection. Controls support keyboard navigation, and the layout adapts to mobile screens.

Grid context now pairs a **Leaflet geographic map** with the authoritative **dependency schematic**. The golden customer/transformer area, fuse area and 165 generalized primary-line parts come from verified AEP GIS. The Circuit Breaker terminal has no supplied geometry and stays schematic-only. Locations and lines use the existing 0.01° privacy grid; they are unsuitable for routing or distance measurement. The source geography is Virginia, despite the AEP Ohio-derived UI style. Optional attributed OpenStreetMap tiles can be disabled; tile or map failure preserves the analytical journey and schematic. See [map audit, privacy and verification](docs/GEOGRAPHIC_MAP.md).

Expand “What this scenario assumes” for declared repair scope, workbook references, unit conversion, upper allowance and limitations. No external map, font, weather or AI service is required for numerical results.

API: `GET /api/locations` returns safe location/path data; `GET /api/map?location_alias=demo-a` returns the separately prepared geographic contract. `POST /api/evaluate` accepts `location_alias`, `access`, `scenario_revision` and optional `previous: {access, scenario_revision}`. It returns `{result, comparison, customer_journey}`. Previous revisions are recomputed on the server from the same immutable context, not accepted as client-calculated results. `GET /api/health` reports readiness; `/docs` provides the local API reference.

Checks and generated frontend types:

```sh
.venv/bin/python -m unittest discover -s tests -v
npm --prefix frontend run types:generate
npm --prefix frontend run build
```

All **98 backend tests** pass (89 existing + 9 Gemini/cache tests). TypeScript and the production build pass. Chrome verification covered the complete live-API flow, preparation and previews, verified map, keyboard/mobile behavior, stale responses and failure/retry handling, plus no-key and AI-assisted explanations. Automated provider tests remain mocked. Generated TypeScript types come from FastAPI's OpenAPI schema; numerical formulas remain solely in the engine. See [map verification](docs/GEOGRAPHIC_MAP.md#verification-and-rehearsal) and [Gemini verification](docs/GEMINI_PROVIDER.md#live-results-and-checks).

## Run the checkpoint

From the repository root, using the prepared local environment:

```sh
.venv/bin/python -m backend.demo
.venv/bin/python -m backend.demo --access NORMAL
.venv/bin/python -m backend.demo --access RESTRICTED
.venv/bin/python -m backend.demo --access BLOCKED
.venv/bin/python -m backend.demo --json
.venv/bin/python -m backend.demo --schema
.venv/bin/python -m unittest discover -s tests -v
```

For a fresh environment, use Python 3.12 and the small, pinned engine dependency file. This leaves the teammate's existing `requirements.txt` unchanged:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-checkpoint.txt
```

The current workstation's environment was created with Codex's bundled Python 3.12; `python3.12` above is the fresh-machine prerequisite, not a promise that this executable is on every machine's PATH. After dependencies are installed, the engine needs no network connection.

Golden selection: alias **demo-a**, pinned `Data1.zip` → `Customer_Clip` **1-based DBF row 1077**. Private identifiers are derived and checked at load time. Actual path: customer → **Distribution transformer → Fuse → Circuit Breaker terminal**. The terminal is abstract, with no invented geometry. Public positions are labeled approximate 0.01° cell centers.

The scenario declares storm level 2, one available reference crew, replacement of one fuse cutout and one 100-kVA transformer unit, and available circuit supply. Damage and supply availability are simulated; topology, mounting, historical context and labor rates come from AEP files.

| Output | Computed result |
|---|---|
| Risk | **HIGH**, score 4: storm 2 + overhead 1 + verified historical circuit evidence 1; LOW predictive confidence; no probability |
| NORMAL / `clear` | **11–18 provisional hours**, raw 11.736–17.604 |
| `restricted` | **16–25 provisional hours**, raw 16.236–24.354 |
| `blocked` | **Unavailable / pending clearance**, null bounds |

Restricted access adds 0.5 workbook labor hours at each of two verified worksites, 140.266 m apart. Applying ILM 4.5 once adds 4.5 modeled hours to the lower bound and 6.75 to the upper bound. Blocked clearance time is unknown, so the engine withdraws the finite estimate. Access does not change the risk band.

Workbook labels, sheet context, metadata and the official challenge still do not resolve person-hours versus crew-hours. [Central assumptions](backend/config.py) explicitly use one reference-crew hour per workbook hour and an illustrative upper multiplier of 1.5. The range begins when an assigned crew starts its response; unknown dispatch/storm holds and unlisted damage are excluded. Extra crews do not divide serial repair time.

The [Pydantic contract](backend/contracts.py) separates source facts, simulated inputs, computed results and assumptions. Results include immutable revisions, deterministic IDs, factors, repair stages, workbook-cell references, missing-data reasons and causal comparisons. Both values inside `confirmed_utility` and `generated_explanation` remain null. Treat the `--schema` output as the executable contract; no UI or LLM needs to recompute numbers.

Validation: **36 tests passed**, including independent workbook recomputation, real topology joins, risk truth table, monotonicity, crew plateau, source tampering rejection, privacy serialization, null transitions and repeated CLI runs. All four raw source hashes remain unchanged. See [checkpoint evidence and next work](docs/EXECUTION_PLAN.md).

## Engineering handoff

- [Challenge requirements](docs/CHALLENGE_REQUIREMENTS.md)
- [Data audit and feasibility findings](docs/DATA_AUDIT.md)
- [Verified geographic map, privacy and fallbacks](docs/GEOGRAPHIC_MAP.md)
- [Constrained AI explanations and optional provider setup](docs/AI_EXPLANATIONS.md)
- [Exact GIS field inventory](docs/DATA_SCHEMA.md)
- [Architecture and fallbacks](docs/ARCHITECTURE.md)
- [Model rules, golden scenario and JSON contracts](docs/MODEL_SPEC.md)
- [Execution plan and validation gates](docs/EXECUTION_PLAN.md)
- [Requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md)
- [Risk register](docs/RISK_REGISTER.md)
- [Instructions for coding agents](AGENTS.md)

## Data inspection

The original inputs are immutable under `data/raw/`. Their hashes match the [official AEP source repository](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff). Some identifying and internal attributes remain; raw files must not be served publicly or passed to an LLM.

The read-only [inspection utility](scripts/audit_data.py) requires Python 3.10+ with `pyshp`, `pyproj`, `shapely`, and `openpyxl`:

```sh
python scripts/audit_data.py --output /tmp/gridguide-audit.json
```

See DATA_AUDIT for setup context and limitations. The audit has its own `shapely` dependency; the checkpoint does not require it. The API/customer view is implemented. Clarifying the workbook's labor basis with AEP remains an unresolved modeling task.

### Preparation and communication previews

The browser now consumes teammate preparation, alert eligibility and lifecycle messages through the API. CLEAR → RESTRICTED selects an estimate-update preview; BLOCKED preserves unavailable bounds. No messages are sent and no customer needs are inferred. See [integration ownership, assumptions and rehearsal](docs/CUSTOMER_INTEGRATION.md).

### Ask GridGuide

Choose a suggested question beneath “Why the outlook changed.” `/api/explain` uses only the current server-validated scenario. The optional model selects approved explanation references; the server supplies all facts, numbers and caveats. Unsupported questions, malformed responses, timeouts and unavailable credentials never create new estimates. BLOCKED stays unavailable pending access clearance.

No key is required for the local “Standard explanation” path. Gemini is the default live provider when server-side `GEMINI_API_KEY` is present, using `gemini-3.5-flash-lite`. `GRIDGUIDE_AI_MODEL` overrides the model; `GRIDGUIDE_AI_PROVIDER=none` disables AI, and `openai` explicitly selects the retained OpenAI alternative with `OPENAI_API_KEY`. Never use frontend environment variables for credentials. See [secure .env launch instructions and live verification](docs/GEMINI_PROVIDER.md#local-credential-and-launch-setup). The UI is intentionally a small question panel, not general chat.
