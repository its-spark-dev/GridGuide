# GridGuide

GridGuide is a planned map-centered customer experience for the AEP HackOHI/O 2026 AI Outage Concierge challenge. It will connect an anonymized location to verified grid dependencies, explain a scenario-based outage-risk band, estimate a conditional restoration range, and show how access or damage assumptions change that result. Preparation guidance and communication previews will use validated results and explicitly declared customer needs.

Proposed architecture: React/TypeScript and Leaflet, one Python/FastAPI service, preprocessed local data, deterministic risk/restoration rules, and a constrained AI explanation layer with a standard offline fallback. No trained probability model or live utility integration is supported by the current data.

**Status: executable engine checkpoint passes; overall credibility remains YELLOW.** The real-data customer → topology → risk → restoration → access-change flow works. Labor-unit interpretation and predictive calibration remain unresolved; the output is a conditional simulation, not a utility ETR. Frontend, API and AI integration remain future work.

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

See DATA_AUDIT for setup context and limitations. The audit has its own `shapely` dependency; the checkpoint does not require it. Next: clarify the workbook's labor basis with AEP and connect a thin API/customer view to the validated engine contract.
