# Reproduce ML Lab

Run from the repository root with Python **3.12.14**. CPU only. Install-time package
retrieval needs network access; generation, fitting, evaluation, replay and rendering
run offline without AEP files. Dependencies are separate from the v1.1.0 runtime.
The reference environment is macOS arm64; CI also checks Linux. Timing is measured,
not a portable SLA. Never load unrelated or untrusted joblib model files.

## Install and verify the committed result

```sh
python3.12 -m venv .venv-ml
.venv-ml/bin/pip install --require-hashes -r requirements-ml.lock
.venv-ml/bin/pip check
.venv-ml/bin/python -m unittest discover -s research/ml_lab/tests -v
.venv-ml/bin/python -m research.ml_lab audit \
  --dataset docs/ml-lab/evidence/dataset \
  --training docs/ml-lab/evidence/training \
  --freeze docs/ml-lab/evidence/selection-freeze.json \
  --final docs/ml-lab/evidence/final
```

`audit` recomputes all 240 final cases using the already-frozen artifacts. It checks
all schedules/metrics, predictions, grouped summaries and hashes. It writes no final
results, fits no model and makes no new selection. This is verification of a spent
holdout. Add `--hash-only` for integrity inspection without numerical replay.

## Exercise the complete workflow with separate smoke data

```sh
.venv-ml/bin/python -m research.ml_lab smoke --output /tmp/gridguide-ml-smoke
```

Choose a fresh output directory. Smoke uses 96 cases / 32 groups and performs real
supervised fitting of all eight configurations, grouped validation, repeat-fit checks,
a freeze, one test evaluation and replay. It never reads the scientific final cohort.
Its outputs are engineering checks, not additional evidence for the reported result.

## Regenerate the presentation

```sh
.venv-ml/bin/python -m research.ml_lab report \
  --training docs/ml-lab/evidence/training \
  --final docs/ml-lab/evidence/final \
  --output /tmp/gridguide-ml-presentation
```

This validates completed evidence, then regenerates Markdown, PNG and SVG figures.
It does not fit, predict, schedule or change results. Each output manifest binds the
source evidence and generated files. Repeated runs in the same environment are byte
identical; font/raster libraries may change rendered bytes across platforms. Relative
Markdown links depend on output location; CI recreates the same sibling evidence layout.

## Reproduce the original training without reopening model selection

The pre-reveal commit `6d4b906` contains the committed inputs, training evidence and
selection freeze, but no scientific final receipt. Use a separate source-free checkout
of that historical implementation to verify the exact original computation. This is
an audit of a frozen recipe, **not permission to tune on the published final results**.
The final model and result in this branch stay unchanged.

```sh
ML_PYTHON="$PWD/.venv-ml/bin/python"
git worktree add --detach --no-checkout /tmp/gridguide-ml-prereveal 6d4b906
cd /tmp/gridguide-ml-prereveal
git sparse-checkout set backend benchmarks research docs/ml-lab docs/planning
git checkout
test ! -e data/raw
"$ML_PYTHON" -m research.ml_lab train \
  --dataset docs/ml-lab/evidence/dataset \
  --output /tmp/gridguide-ml-training-replay
"$ML_PYTHON" - <<'PY'
from pathlib import Path
from research.ml_lab.artifacts import file_hash, read_json
original = Path('docs/ml-lab/evidence/training')
replay = Path('/tmp/gridguide-ml-training-replay')
a, b = read_json(original/'training.json'), read_json(replay/'training.json')
for key in ('candidates', 'baselines', 'family_winners', 'best_ml', 'champion', 'class_counts', 'cv_folds'):
    assert a[key] == b[key], key
for path in (original/'models').glob('*.joblib'):
    assert file_hash(path) == file_hash(replay/'models'/path.name), path.name
print('All eight model artifacts and selection evidence reproduced')
PY
```

Source revision, hardware and timing metadata legitimately differ between invocations;
the learned artifacts and scientific training/development values are compared directly.
The reference machine also executed this full reproduction in a sparse checkout.
Other platforms may yield tiny fitted-parameter differences; the committed model replay
is checked separately from any claim of cross-platform retraining byte identity.

## Scientific sequence already executed

The following is the recorded original sequence, **not a script to rerun against the
spent cohort**. Every destination refuses overwrite. Full-data input and model seals
must be committed before the next scientific stage.

```sh
# Inputs committed at fa3c9cc before fitting.
python -m research.ml_lab prepare --output docs/ml-lab/evidence/dataset
# Training committed at 501152d.
python -m research.ml_lab train --dataset docs/ml-lab/evidence/dataset \
  --output docs/ml-lab/evidence/training
# Selection freeze committed at 6d4b906 before final labels.
python -m research.ml_lab freeze --dataset docs/ml-lab/evidence/dataset \
  --training docs/ml-lab/evidence/training \
  --output docs/ml-lab/evidence/selection-freeze.json
# Exactly one scientific invocation; receipt belongs to the dataset seal.
python -m research.ml_lab evaluate --dataset docs/ml-lab/evidence/dataset \
  --training docs/ml-lab/evidence/training \
  --freeze docs/ml-lab/evidence/selection-freeze.json \
  --output docs/ml-lab/evidence/final
```

A spent receipt prohibits another training-selection run in that scientific workspace
and another evaluation even with a different output directory. Failed attempts preserve
the receipt. Any future modeling on published final data is post-hoc research and needs
a separately preregistered new final cohort for a fresh claim.

## Artifact inventory

| Artifact | Contents |
|---|---|
| `evidence/dataset/manifest.json` | Version, revision, generator hashes, configuration seeds, graph signatures, split membership, input eligibility and partition hashes |
| `evidence/dataset/*.jsonl.gz` | Deterministic compressed fictional inputs; no policy outcomes |
| `evidence/training/{train,dev}-labels.jsonl.gz` | Four complete schedules/metric objects, labels, ties, features and lineage |
| `evidence/training/training.json` | Baselines, class counts, grouped folds, all candidate predictions/summaries, coefficients/importances and model hashes |
| `evidence/training/models/*.joblib` | Eight trusted fitted pipeline artifacts; no untrusted deserialization endpoint |
| `evidence/selection-freeze.json` | Committed model, features, environment, acceptance criteria, source and artifact hashes |
| `evidence/dataset/evaluation-receipt.json` | Exclusive final invocation, pre-label timestamp, revision and seal bindings |
| `evidence/final/cases.jsonl.gz` | Every final case, schedule, metric, prediction and abstention |
| `evidence/final/{results,completion}.json` | All comparisons, subgroup support, promotion failures and exact result hashes |
| `evidence/{training,final}/runtime.json` | Measured timing/memory and machine metadata, separate from numerical hashes |
| `presentation/` | Reproducible report, four PNG/SVG figures and output manifest |
| `evidence/phase-ledger.json` | Actually executed gates, commands, tests and remaining limitations |

Historical checks remain available through `scripts/check_frozen_artifacts.py` and the
existing public/challenge/research test lanes. The independent ML CI lane installs only
the pinned ML environment, omits all challenge data, and checks smoke/replay/presentation.
It does not retrain the full scientific suite on every pull request.
