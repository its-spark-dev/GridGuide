# Verification and preservation

Executed locally on 2026-11-04; scientific disposition is independently **NO-GO**.

| Check | Executed result |
|---|---|
| New audit contract/evidence tests | 17 passed |
| Full source audit replay | All 50 PNNL CSVs plus Purdue workbook; byte-identical JSON replay |
| Independent PNNL check | Separate pandas reader reproduced 526,165 rows, 273,291 exact duplicates, 357,307 repeated county/start rows and 306,190 after-restoration starts |
| Independent Purdue check | Separate openpyxl reader confirmed 31 one-hour timestamp discrepancies: 14 positive, 17 negative |
| Presentation | Two PNG figures visually inspected; two regenerations byte-identical in pinned environment; source hash and measured Markdown verified |
| Existing public lane | 102 passed, zero skipped/unavailable |
| Existing challenge lane | 196 passed, zero skipped/unavailable; authorized local sources present |
| Existing research lane | 51 passed, zero skipped/unavailable |
| Preserved ML Lab I | 44 passed |
| Frontend production build | Passed |
| Frozen evidence checker | 20 G2/G3 + 66 G5 + 10 G6 + 19 G7 files passed |

The independent pandas check used the bundled analysis environment because pandas is
not installed in the ML Lab I environment; no dependency was installed or added. The
first attempt there failed with `ModuleNotFoundError`, and was not counted as a pass.
The first workbook audit deliberately rejected formulas; inspection found cached formulas
only in customer-percentage fields. The parser was corrected to read cached values without
evaluating formulas, with a dedicated regression test. No data was changed to make it pass.

Commands for existing lanes:

```sh
.venv/bin/python scripts/run_test_lane.py --lane public --report artifacts/outage-ml/public.json
.venv/bin/python scripts/run_test_lane.py --lane challenge --report artifacts/outage-ml/challenge.json
.venv/bin/python scripts/run_test_lane.py --lane research --report artifacts/outage-ml/research.json
.venv-ml/bin/python -m unittest discover -s research/ml_lab/tests -v
.venv/bin/python scripts/check_frozen_artifacts.py
npm --prefix frontend run build
```

The scoped new CI lane runs without original or external outage data, uses the unchanged
hash-pinned research environment and checks audit contracts, committed integrity and two
report regenerations. It does **not** claim a full raw-source replay or model evaluation.
Existing workflows are unchanged. Final PR head checks are the delivery authority.

Preservation review: only new `research/outage_ml/`, `docs/outage-ml/`, the new CI lane and
a 13-line additive README section are in scope. Existing models, synthetic datasets,
frozen research, backend/frontend behavior, raw data, release assets, tags, license,
contributor attribution and original screenshots/maps remain unchanged. No merge, tag,
release, deployment or messaging action is part of this delivery.

Limitations: the source review was performed by the development agent, with independent
parser implementations for selected measurements, not an independent external scientific
review. A protocol/gate judgment cannot be validated by unit tests. Source metadata can
change, the IEEE descriptor was inaccessible, Purdue workbook rights remain unresolved,
and the large Zenodo tables were not inspected. These limitations are retained explicitly.
