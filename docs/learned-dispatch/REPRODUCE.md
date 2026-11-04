# Reproduce learned dispatch

This is source-free, CPU-only research. Nothing connects to a grid, sends a message or
changes the application's default policies. Commands run from the repository root with
Python 3.12.14 and the existing hash-pinned `requirements-ml.lock`.

```sh
python3.12 -m venv .venv-ml
.venv-ml/bin/pip install --require-hashes -r requirements-ml.lock
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
.venv-ml/bin/python -m unittest discover -s research/learned_dispatch/tests -t . -v
.venv-ml/bin/python -m research.learned_dispatch smoke --output artifacts/learned-smoke-new
```

Smoke genuinely collects teacher trajectories, fits all five models twice, validates JSON
exports, selects by complete development rollouts, freezes and evaluates separate smoke-ID
and smoke-shift groups. Its namespace is separate and it supports no performance claim.
Use a new output path for each smoke run. No GPU, model API or original AEP data is needed.

## Load the actual trained champion

The selected depth-4 forest contains 64 fitted trees. Its artifact is 211,281 bytes;
SHA-256 `8280d3929a316c61bd5f93ef15610d891e0bf2e6cc80b8d9fb262f66cc097e52`.
This command scores a new authored example with one active task, an idle crew, multiple
ready tasks and legal WAIT. The example is outside the scientific dataset.

```sh
.venv-ml/bin/python -m research.learned_dispatch infer \
  --model docs/learned-dispatch/evidence/training/models/forest-depth4.json \
  --sha256 8280d3929a316c61bd5f93ef15610d891e0bf2e6cc80b8d9fb262f66cc097e52 \
  --state docs/learned-dispatch/example-state.json

.venv-ml/bin/python -m research.learned_dispatch episode \
  --model docs/learned-dispatch/evidence/training/models/forest-depth4.json \
  --sha256 8280d3929a316c61bd5f93ef15610d891e0bf2e6cc80b8d9fb262f66cc097e52 \
  --problem docs/learned-dispatch/example-problem.json --profile high --seed 0
```

Python integration uses the same strict boundary:

```python
from pathlib import Path
from research.learned_dispatch.models import LearnedPolicy, load_model
from research.learned_dispatch.public import from_public_dict
from research.ml_lab.artifacts import read_json

model, load_ns = load_model(
    Path("docs/learned-dispatch/evidence/training/models/forest-depth4.json"),
    "8280d3929a316c61bd5f93ef15610d891e0bf2e6cc80b8d9fb262f66cc097e52",
)
policy = LearnedPolicy(model)
state = from_public_dict(read_json(Path("docs/learned-dispatch/example-state.json")))
action = policy(state)
print(action, policy.score(state, action), policy.fallbacks)
```

Higher `score` means lower predicted teacher regret. It is not a probability or calibrated
restoration estimate. Corrupt/unapproved artifacts fail loading. Valid unsupported states
use an explicitly recorded deterministic reactive fallback; malformed states are rejected.
The [interface document](INTERFACES.md) defines limits and units.

## Audit already revealed evidence

These commands independently recompute schedule metrics and trajectory legality, verify
every expected method/episode/configuration, and regenerate the exact grouped summaries.
They do not refit, select, open a new scientific reveal or overwrite evidence.

```sh
for stage in dev final_id final_shift; do
  .venv-ml/bin/python -m research.learned_dispatch audit \
    --dataset docs/learned-dispatch/evidence/dataset \
    --training docs/learned-dispatch/evidence/training \
    --output "docs/learned-dispatch/evidence/$stage"
done
.venv-ml/bin/python -m research.learned_dispatch report \
  --evidence docs/learned-dispatch/evidence \
  --output artifacts/learned-presentation-replay
```

Reports read approved models and audited outcomes. PNG and SVG figures are generated from
those sources; exact figure bytes are expected only in the same rendering environment.
The presentation manifest binds both source evidence and output files. Numerical summaries
and the Markdown report must agree independently of font/raster differences.

## Full teacher-data and model reproduction

The published scientific dataset is spent: `collect`, `fit` and development execution reject
it after the final receipt. Do not delete that receipt or overwrite old artifacts. To reproduce
training, use a disposable worktree/branch and a **new** directory such as
`docs/learned-dispatch/reproduction/run-1`. This reproduces an already published experiment;
it is not a new blind test or permission to retune on its final outcomes.

```sh
RUN=docs/learned-dispatch/reproduction/run-1
.venv-ml/bin/python -m research.learned_dispatch prepare --profile full --output "$RUN/dataset"
git add "$RUN/dataset"
git commit -m 'reproduction: seal identical published learned-dispatch inputs'
for batch in 1 2 3 4 5 6 7 8 9 10 11 12; do
  .venv-ml/bin/python -m research.learned_dispatch collect \
    --dataset "$RUN/dataset" --output "$RUN/teacher" --max-groups 4
done
.venv-ml/bin/python -m research.learned_dispatch fit \
  --dataset "$RUN/dataset" --teacher "$RUN/teacher" --output "$RUN/training"
```

Input fingerprints, numerical teacher-shard bytes and fitted JSON parameters should match
the pinned implementation. Timing, commit/environment metadata and local paths need not.
Training JSON binds the actual teacher shards and source hashes. `training_matrix_identity`
binds features, targets, weights and grouping. Every fit repeats and compares exports and
predictions. Recorded training/development/final metrics remain authoritative historical
evidence; reproduction does not create another independent observation.

## Original scientific execution order

The implementation ledger records the actual sealed input, model-selection and reveal commits.
The original sequence was `prepare` → commit inputs/schema → `collect` → `fit` → development
`evaluate` → commit models/development → `freeze` → commit freeze → final `evaluate` in
immutable four-configuration shards → read-only `audit`. Scientific calls used 48/16/24/24
configuration groups. Both crew variants, all profiles and visited states stay within their group.

For an authorized future protocol with fresh inputs, `evaluate --partition dev` takes
`--dataset`, `--training`, `--output` and `--max-groups 4`; `freeze` additionally takes
`--development`. Final evaluation requires `--partition final_id` or `final_shift` and a
committed `--freeze`. Repeating an unfinished call processes pending shards only; repeating
a completed evaluation fails. The exclusive dataset receipt binds both final cohorts to the
same freeze and output root. Failures are retained. No final reselection is allowed.

Resource bounds are one numerical thread, <2 GiB RSS and <30 minutes per bounded command.
Model fitting dependencies are isolated from the frozen v1.1 distribution. The learned policy
is optional research code; no production integration, release, deployment or RL is included.
