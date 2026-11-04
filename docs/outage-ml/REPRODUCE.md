# Reproduce the source audit

Reference Python: **3.12.14**. Acquisition and auditing use only the standard library.
Figure rendering reuses the unchanged hash-pinned `requirements-ml.lock` environment
from ML Lab I (Matplotlib 3.10.7). No new runtime dependency is added to GridGuide.
Raw data is kept outside Git under the already ignored `data/external/` directory.

## Acquire the reviewed sources

Read the [official PNNL v2 guide](https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx)
and [disclaimer](https://data.openei.org/files/6458/Disclaimer.docx) before interpreting
the dataset. The original review did so before data use. Network access is needed only
for acquisition and dependency installation.

```sh
python3.12 -m research.outage_ml acquire \
  --cache data/external/outage-ml/audit-v1 \
  --output /tmp/outage-acquisition.json
```

This fetches four fixed artifacts, seven metadata/descriptor snapshots and three small
Zenodo sensitivity files. Fixed artifacts fail closed on changed bytes or SHA-256.
Metadata is bounded to 2 MB per resource; sensitivities to 10 KB. The PNNL archive limit
is its pinned 31,260,449 bytes; expansion is limited to 250 MB. The workbook is limited
to 660,364 downloaded bytes and 10 MB expanded XML. No whole Zenodo archive or large
observation file is downloaded. No formula, macro, external spreadsheet link or document
instruction is executed. Network failures are failures, not cached success claims.

Catalog pages and API metadata are mutable. A fresh download may have a different
receipt from the committed review; retain the new receipt and compare it. Reuse a cache
only when its per-file receipt validates. Do not replace source hashes to silence a change.

## Recompute every aggregate from original bytes

```sh
python3.12 -m research.outage_ml audit \
  --cache data/external/outage-ml/audit-v1 \
  --output /tmp/outage-source-audit.json
cmp docs/outage-ml/evidence/source-audit.json /tmp/outage-source-audit.json
```

The audit reads all 50 CSV members and the Purdue workbook. It does not extract ZIP
paths, repair source values, infer UTC, impute targets, construct negative examples or
fit anything. Quoted quantiles are **nearest-rank empirical** summaries. Exact duplicate
rows hash every parsed field; repeated episode keys use normalized FIPS plus source
start spelling within one file. Parent definitions contain incident start/end, type and
state; an event ID mapping to more than one definition is flagged. Alternative lag
tables are never stacked into a training dataset.

Metadata-dependent Zenodo inventory is read from the cached API snapshot. Later publisher
metadata changes can change that part of the report; the committed acquisition record
identifies the exact snapshot used. The original full replay compared byte-for-byte.

## Verify and regenerate without external data

```sh
python3.12 -m venv .venv-ml
.venv-ml/bin/pip install --require-hashes -r requirements-ml.lock
.venv-ml/bin/pip check
.venv-ml/bin/python -m unittest discover -s research/outage_ml/tests -v
.venv-ml/bin/python -m research.outage_ml verify \
  --output docs/outage-ml/presentation
.venv-ml/bin/python -m research.outage_ml report --output /tmp/outage-report-a
.venv-ml/bin/python -m research.outage_ml report --output /tmp/outage-report-b
diff -r /tmp/outage-report-a /tmp/outage-report-b
cmp docs/outage-ml/presentation/MEASURED.md /tmp/outage-report-a/MEASURED.md
```

Use the existing ML environment if installed; no need to recreate it. Figures bind to the
audit JSON hash and are deterministic within the pinned rendering environment. Linux and
macOS raster/font bytes can differ, so CI validates committed hashes and regenerates twice
on its own platform; it compares numeric Markdown across platforms. It does not pretend
to rerun the full source audit from aggregate evidence alone.

## Scope of verification

The dedicated workflow checks parsers, schema drift, missing-versus-zero semantics,
duplicate/incident identity diagnostics, year boundaries, nonfinite rejection, bounded
downloads, aggregate consistency and report integrity. Fixtures are fictional parser tests,
not training data. It deliberately has no `train` or `evaluate` command because the
feasibility gate is NO-GO. Model reproducibility, baselines, predictive split isolation and
held-out uncertainty tests are **not applicable**, not reported as passed.

Existing public/challenge/research and ML Lab I tests, frontend build and frozen evidence
verification are recorded in [VERIFICATION.md](VERIFICATION.md). No external raw inputs,
learned models, new service, interactive UI, tag or release are part of this delivery.
