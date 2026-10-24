# GridGuide

GridGuide is a working AEP HackOHI/O 2026 outage-concierge prototype: verified GIS and topology → declared damage on specific source assets → reverse customer dependencies → workbook repair effort → crew/access conditional duration → bounded repair priority → customer preparation, communication previews and grounded explanation.

The AEP Data Guide resolves **direct labor × 4.5 = total person-hours**, including travel, safety discussion and setup. Actual crew efficiency, default composition, switching feasibility, clearance time, official alert rules and priority weights remain open. The demo uses a transparent conditional elapsed-time envelope, not an official AEP ETR. Read [the model](docs/MODEL_SPEC.md), [requirement/evidence matrix](docs/AEP_REALIGNMENT.md) and [demo freeze](docs/DEMO_FREEZE.md).

## Run the browser

From the project root, Python 3.12 and Node 22.12+:

```sh
.venv/bin/python -m pip install -r requirements-web.txt
npm --prefix frontend ci
```

If no environment exists, first create it with `python3.12 -m venv .venv`. The separate engine-only dependencies are in `requirements-checkpoint.txt`; the teammate's `requirements.txt` is unchanged.

Terminal 1, deterministic/no external AI:

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```sh
npm --prefix frontend run dev
```

Open **http://127.0.0.1:5173/** after backend startup. Both ports must be available. For live Gemini, use the secure [local `.env` loader](docs/GEMINI_PROVIDER.md#local-credential-and-launch-setup) instead of the provider-disabled command. Never display a key or put it in frontend variables. Missing AI credentials/network/quota uses Standard explanation.

One vetted Virginia customer is selected automatically. The map shows generalized source geometry; the dependency schematic explains upstream relationships. Crew size, access and optional customer-declared needs are interactive. Refresh resets four-person CLEAR and removes declarations. No declarations are stored or sent to AI. No alerts are delivered and no enrollment occurs.

## Golden model

Declared replacement scope: one source-verified fuse cutout and one 100-kVA transformer unit. This is simulated damage, not an established ARCOS-to-these-assets match. Exact typed identities support a reverse dependency count of **4 fuse premises / 1 transformer premise / 4 in their union**. Actual ARCOS outage impact and customers restorable by switching remain unavailable.

Installation `1.28 + 0.256 = 1.536`; removal `0.944 + 0.128 = 1.072`; replacement direct labor **2.608**. Apply 4.5 once → **11.736 repair person-hours**. RESTRICTED adds two assumed site tasks at 0.5 direct hours each → **16.236 total person-hours**. BLOCKED retains known repair effort but complete effort and duration are null.

| Crew assumption | CLEAR conditional elapsed hours | RESTRICTED conditional elapsed hours | BLOCKED |
|---:|---|---|---|
| 2 people | 5.5–12 | 8–16.5 | unavailable |
| 4 people (demo default) | 2.5–12 | 4–16.5 | unavailable |
| 8 people | 1–12 | 2–16.5 | unavailable |

Prototype envelope: `[person-hours / selected people, person-hours / one effective worker]`, serial tasks, outward half-hour display rounding. Actual conversion efficiency is unknown; this is not a calibrated interval or guaranteed bound. Unknown delays may exceed it. Extra crews never divide serial work. Risk stays **HIGH**, score 4, LOW predictive confidence, probability null.

Repair sequence could clear three declared dependencies after the fuse and one after the transformer, conditional on all other scope/supply/safety assumptions. Actual sectionalization remains unverified. Hospital/fire/ambulance GIS contributes aggregate **spatial criticality context** and a need to verify electrical attachment before dispatch priority; proximity does not prove dependency.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
.venv/bin/python -m backend.demo --crew-size 2 --access NORMAL
.venv/bin/python -m backend.demo --crew-size 8 --access RESTRICTED
.venv/bin/python -m backend.demo --access BLOCKED
npm --prefix frontend run types:generate
npm --prefix frontend run build
```

`--json` returns structured scenarios; `--schema` returns the executable contract. Backend tests cover source identity/hashes, global reverse indexing, independent workbook arithmetic, crew/access invariants, nulls, needs/privacy, raw elapsed alert thresholds, GIS and provider faults. Browser evidence is in [DEMO_FREEZE.md](docs/DEMO_FREEZE.md). Generated TypeScript comes from OpenAPI; frontend code contains no independent numerical model.

API: `/api/locations`, `/api/map?location_alias=demo-a`, `/api/health`; `/api/evaluate` accepts location/access/crew size/declared needs/revision and optional previous access/crew/revision. `/api/explain` recomputes and binds result IDs before a model can select approved references. `/docs` is the local API reference.

## Engineering and data

- [AEP realignment and evidence classes](docs/AEP_REALIGNMENT.md)
- [Model formulas and complete golden derivation](docs/MODEL_SPEC.md)
- [Architecture and ownership](docs/ARCHITECTURE.md)
- [Requirements coverage](docs/REQUIREMENTS_TRACEABILITY.md) and [remaining risks](docs/RISK_REGISTER.md)
- [Customer declarations and alerts](docs/CUSTOMER_INTEGRATION.md)
- [Explanation contract](docs/AI_EXPLANATIONS.md) and [Gemini setup](docs/GEMINI_PROVIDER.md)
- [Geographic map](docs/GEOGRAPHIC_MAP.md), [data audit](docs/DATA_AUDIT.md), [exact field inventory](docs/DATA_SCHEMA.md)
- [Demo freeze](docs/DEMO_FREEZE.md), [execution handoff](docs/EXECUTION_PLAN.md), [agent instructions](AGENTS.md)

Raw files remain immutable under `data/raw/`, pinned to the [official source revision](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff). The independent read-only audit is `python scripts/audit_data.py --output /tmp/gridguide-audit.json` (Python 3.10+, pyshp, pyproj, shapely, openpyxl). Do not publicly serve raw GIS, private identifiers or precise facility/customer locations. Teammate pipelines and raw/processed data are preserved.
