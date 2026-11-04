# Phase 5 artifact layout and reproduction

Full numerical execution writes a new output directory and refuses overwrite. Each
case/profile/policy metadata record binds its exact problem, precomputed schedule,
seed, profile hash, numerical implementation and output digest. G3 schedules are loaded
from the unchanged published artifact; the simulator never invokes a solver.

The NPZ files retain **lossless sufficient statistics**, not quantile-only summaries:
`group_release_ticks[trial,group]` (int64; -1 is unknown) and `makespan_hours[trial]`
(float64; NaN is unknown). The manifest fixes group order, disjoint membership, branches,
critical flags and horizon. Those arrays reconstruct every customer metric and release
milestone exactly. Shared NPZ filenames represent identical outputs, not omitted runs.
All per-policy metadata and trial pairing remain explicit. The renderer verifies the
reconstructed full-array digest before emitting summaries. Do not load NPZ pickle objects.

The complete generated standard/convergence NPZ directories are retained locally under
ignored `artifacts/phase5/standard/` and `artifacts/phase5/convergence/`. The PR retains
compressed manifests and complete reports, timing records, convergence outcomes and
checksums. Large regenerable trial caches are not added to Git history. To independently
inspect or rerender raw trials from a fresh clone, run the commands below; no utility
files, provider keys, network, credentials or optimization search are required after
installing the pinned dependencies. This distinction is explicit: committed reports
are summaries; the local NPZ files are the lossless trial evidence.

```sh
.venv/bin/python -m pip install -r requirements-simulation.txt
.venv/bin/python scripts/run_simulation.py --suite smoke --output /tmp/gridguide-g5-smoke
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-smoke
.venv/bin/python scripts/run_simulation.py --suite standard --output /tmp/gridguide-g5-standard
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-standard
.venv/bin/python scripts/run_simulation.py --suite convergence --output /tmp/gridguide-g5-convergence
.venv/bin/python scripts/report_simulation.py /tmp/gridguide-g5-convergence
.venv/bin/python scripts/check_simulation_reproduction.py --reference /tmp/gridguide-g5-standard --output /tmp/gridguide-g5-reproduction.json
.venv/bin/python scripts/package_simulation_review.py --standard /tmp/gridguide-g5-standard --convergence /tmp/gridguide-g5-convergence --output /tmp/gridguide-g5-review
```

Compare regenerated manifest `numerical_sha256` to the committed manifest's value.
Canonical hashes bind ordered array names, dtypes, shapes and uncompressed bytes;
container compression/mtime and wall timings are not numerical outcomes. Pinned Python,
NumPy and host details are in each run. Cross-platform floating-transform bit equality
has not been established. Source-free reproduction tests a fresh extracted code tree
in the same installed numerical environment, not a newly provisioned operating system.

Original execution manifests retain their measured implementation hashes. A final
customer-weighted offset range guard only rejects extreme inputs; it does not change
the published scenarios. The `final_*_reproduction.json` records retain both original
and final-code implementation hashes and verify the full numerical results unchanged.
Do not rewrite original manifests to imply execution with a later implementation.

`report.json.gz` and `manifest.json.gz` in this directory's suite subfolders are ordinary
JSON compressed with gzip (zero timestamp). `REPORT.md` provides a readable overview.
The report includes **all** per-run quantiles, paired differences, critical/branch/small-
group metrics, null counts and failures. It is not a calibrated utility prediction.

The committed `demo/presets.json` contains all 56 fixed-baseline microcase/profile
summaries, exact inputs/schedules and explicit convergence flags for future integration
review. Its companion NPZ files retain those cases' lossless trial statistics in Git.
No preset is a live utility observation or an API endpoint. Flagged unstable estimates
must not be presented as converged results. G5 acceptance and future integration remain
owner decisions. `CHECKSUMS.json` covers the packaged reports, summary and demo files;
reproduction/verification documents have their own numerical bindings.

[Paired comparison tables](COMPARISONS.md) explain both completed and restricted
denominators. `summary.json` contains the same unrounded descriptive aggregates. Full
reports retain every per-run/paired metric; summary tables do not select winning cases.
