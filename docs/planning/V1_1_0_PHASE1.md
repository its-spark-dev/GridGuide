# v1.1.0 Phase 1 — G1 review packet

Implemented for owner review on November 3, 2026. **G1 approval is pending. Do not
merge this PR or begin Phase 2 without approval.** The [complete approved roadmap](V1_1_0_MASTER_ROADMAP.md)
contains all nine phases and the five controlling refinements. The public README
only changes the local launch command to select challenge-local explicitly.

## Implemented scope

- Versioned, reproducible dataset register and six target-level feasibility decisions.
- Fresh aggregate topology/damage audit with pinned source and implementation hashes.
- Six independently authored fictional scenarios: simple, branching, overlap, blocked,
  missing evidence and critical-service dependencies. No source sampling/anonymization.
- Strict centralized Pydantic contracts, regenerated TypeScript, immutable catalog
  preparation, revision/fingerprint metadata and an explicit startup mode selector.
- Read-only synthetic catalog/definition/health endpoints. No numerical evaluation,
  training, scheduler, Monte Carlo, new frontend, CI or hosting has been implemented.
- Catalog-only publication artifact checks with an exact allowlist, content manifest,
  symlink/extra-entry/tampering rejection and isolated extraction/startup tests.

Only the ordinal threshold function was moved, unchanged, to decouple public contracts
from private source configuration. `backend.config` re-exports it for compatibility.
The legacy engine, policies, golden values, source pins and teammate pipeline are unchanged.
The old `backend.api:app` remains an explicitly named challenge-only entrypoint;
`backend.runtime:app` is the canonical mode-selected entrypoint.

## G1 acceptance checklist

Implementation checks are distinct from owner acceptance:

- [x] Approved roadmap preserved with 5% target, deterministic/wall-time separation,
  restricted/completed hours distinction, provisional effort and licensing/coverage gates.
- [x] Every target records units, horizon/origin, observation process, inclusion rules,
  present decision, licensing/coverage gates and missing prerequisites.
- [x] Each important synthetic input binds exactly one evidence classification;
  incompatible source-observation claims and unbound evidence fail validation.
- [x] Synthetic startup succeeds with challenge files absent and no provider imports.
- [x] Fictional definitions have explicit origin; partial topology, actual efficiency,
  observed outages and restoration outcomes never acquire fabricated values.
- [x] Legacy Python/API, golden CLI, browser and build regressions pass.
- [x] Artifact inspection finds no challenge archives, processed tables, source locators,
  real geometry, Git history, research downloads, provider code or credentials.
- [x] v1.0.0 and main ancestry preserved; raw/processed data, teammate pipeline and
  third-party attribution remain unchanged.
- [ ] Owner accepts the evidence boundaries and catalog-only synthetic foundation.
- [ ] Owner authorizes merge. Phase 2 still requires explicit approval.

## Evidence and decisions

The [feasibility findings](../research/phase1/FEASIBILITY.md) explain the
[machine-readable register](../research/phase1/dataset_register.json).
Challenge data remains a no-go for premise outage probabilities, task-duration labels
and customer restoration outcomes. County-level prediction and aggregate recovery are
**conditional, not cleared**: no training or validation is authorized by metadata alone.
Public observation acquisition, exact payload terms, quality masks, event grouping and
as-of feature availability remain missing. Partner/private/paid data is not required.

The [source coverage report](../research/phase1/source_coverage.json) reproduces
117,599 indexed paths, 40,779 complete paths and 8,093 physical assets with complete
reverse membership (8,095 entries including two abstract terminals). It retains
rejection reasons and denominators; overlapping failures are not additive. Of 1,659
damage reports, 139 pass the spatial-candidate policy and 28 have complete reverse
membership. These remain hypotheses, not direct ARCOS identity or observed outages.
All 1,659 outage/incident identifiers are zero, all event labels are Default, and 76
unrepaired records nevertheless contain repair dates. No duration labels are derived.

The [artifact check](../research/phase1/artifact_check.json) records 12 allowlisted
archive entries, including the manifest. The [clean-install check](../research/phase1/clean_install_check.json)
records resolved dependencies and successful real loopback HTTP startup in a fresh
Python virtual environment, using only extracted files. No archive binary is committed
or publicly deployed; the builder reproduces it for review.

## Verification performed

Environment: macOS, Python 3.12.14, Node 26.5.0, npm 11.17.0; existing pinned application
dependencies. Checks use Standard explanations and do not contact model providers.

| Check | Observed result |
|---|---|
| Full Python discovery | **224 passed**, including the existing 194 and 30 new Phase 1 tests; 70.842 seconds |
| Playwright browser suite | **49 passed**; 55.4 seconds; existing prepared/fixture server, not the synthetic frontend |
| Strict TypeScript/Vite production build | Passed |
| OpenAPI/TypeScript regeneration | Generated bytes unchanged on rerun |
| Golden CLI | Passed; 11.736 repair person-hours; CLEAR 2.5–12 h, RESTRICTED 4–16.5 h, BLOCKED null |
| Full existing source audit | Completed; all four hashes match the pinned baseline |
| New source evidence reproduction | Exact checked-in JSON reproduced, including implementation hashes |
| Synthetic archive | Reproducible bytes, exact allowlist and contents; rejection tests passed |
| No-source/no-network subprocess | Passed with challenge file opens and outgoing socket connections forbidden |
| Fresh synthetic-only install | Dependency check and real HTTP health/catalog/missing-evidence responses passed |
| Existing environment dependency check | No broken requirements |
| Protected files/history | No changes to raw/processed data, pipeline or notices; v1.0.0 unchanged |

These times describe one local verification run, not benchmarks or response-time promises.
No CI workflow was added: Phase 8a is later work and has not been silently started.

Reproduction from the repository (source-dependent commands require authorized pinned files):

```sh
GRIDGUIDE_AI_PROVIDER=none .venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m backend.demo
.venv/bin/python scripts/audit_data.py --output /tmp/gridguide-g1-audit.json
.venv/bin/python scripts/phase1_evidence.py > /tmp/gridguide-g1-source-coverage.json
cmp /tmp/gridguide-g1-source-coverage.json docs/research/phase1/source_coverage.json
.venv/bin/python -m research.datasets > /tmp/gridguide-g1-datasets.json
cmp /tmp/gridguide-g1-datasets.json docs/research/phase1/dataset_register.json
npm --prefix frontend run types:generate
npm --prefix frontend run build
npm --prefix frontend test
```

Synthetic test selection (does not read challenge files; source-dependent suites are
**not executed**, not counted as passing, when this selection alone is used):

```sh
.venv/bin/python -m unittest discover -s tests -p test_phase1.py -v
```

Build into a new path; the builder intentionally refuses overwrite:

```sh
.venv/bin/python scripts/check_phase1_artifact.py --build /tmp/gridguide-g1-catalog.zip
.venv/bin/python scripts/check_phase1_artifact.py --inspect /tmp/gridguide-g1-catalog.zip
```

Follow the bundled [artifact instructions](../research/phase1/ARTIFACT_README.md)
for a fresh synthetic-only environment. `/api/v2/scenarios` lists capabilities and
`/api/v2/scenarios/syn-missing` demonstrates unavailable evidence. The existing browser
journey continues with `GRIDGUIDE_MODE=challenge-local ... backend.runtime:app`.

## Preserved history

Branch: `feat/v1.1-phase1-evidence-isolation`, based on current `origin/main`
`166c170e46bfd5f076d05a8bf08d3ab445d5b585`.
v1.0.0 remains `b324c1b355cda60035fb11fa32bcddf10931f649`. No tag, release or shared
history is rewritten. The branch adds new commits only; nothing is merged automatically.

## Limitations and review questions

1. **Public-data feasibility:** exact EAGLE-I payload terms and county-window coverage
   remain unvalidated. NOAA supports retrospective context subject to snapshot checks;
   DOE-417 remains a metadata lead. This phase does not conclude suitable public data
   cannot exist. Later research must pass acquisition and coverage gates before fitting.
2. **Synthetic scope:** is the explicit catalog-only G1 boundary accepted? Numerical v2
   routes and customer/operator integration remain later phases. Fixtures are examples,
   not the frozen performance evaluation suite and not utility observations.
3. **Distribution:** the isolated catalog package does not remediate existing repository
   exposure or grant licenses. Payload scans cannot establish operational safety. Full
   deployment packaging, dependency locking and security review remain later gates.
4. **Original authority:** missing original challenge/guide attachments and source
   redistribution permission remain unresolved; existing recorded excerpts and local
   authorization are retained without invented citations.
5. **Research disposition:** is a conditional county-research protocol with present
   no-go for training acceptable at G1? No ML outcome is made a release dependency.

These questions are review items, not requests to expand Phase 1 or acquire private data.

## Effort recalibration and stop point

Phase 1 was produced in an agent-assisted implementation/verification session; that is
not a measured human engineering-day sample. Scope and check runtimes are recorded
above; owner review and external rights clearance have no measured effort yet. The
original 6–8-day estimate is provisional, not a completion-time claim.

Reassessment after this phase retains **40–60 provisional engineering days** for the
remaining required roadmap work, plus **6–10 conditional modeling days** only if
feasible. No evidence justifies applying this session's automation speed to the remaining
work. In particular, benchmark normalization/independent validation and generic scheduling
are still unimplemented, while external observation acquisition remains uncertain.
Re-estimate each phase using its actual scope, tests, findings and review burden; no
calendar deadline or automatic phase transition follows from these numbers.

Stop here pending owner review. Do not implement Phase 2, merge, tag, publish a release,
or deploy the future demonstration under this Phase 1 authorization.
