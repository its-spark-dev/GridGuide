# Reproduce adaptive dispatch research

Use Python 3.12.14 and the existing isolated ML dependency lock. No new training
dependency set, GPU, utility dataset, hosted endpoint or network during experiments
is needed. Package installation requires network unless wheels are cached.

```sh
python3.12 -m venv .venv-ml
.venv-ml/bin/pip install --require-hashes -r requirements-ml.lock
.venv-ml/bin/pip check
.venv-ml/bin/python -m unittest discover -s research/adaptive_dispatch/tests -v
```

Run from the repository root. CLI commands deny access to challenge data paths and
network connections through the reused process-local isolation guard. This guard
protects accidental access, not malicious repository code. The GitHub verification
lane additionally uses a sparse checkout that contains no challenge data.

## Separate engineering smoke

Use fresh destinations; commands reject existing output directories.

```sh
.venv-ml/bin/python -m research.adaptive_dispatch prepare \
  --profile smoke --output /tmp/adaptive-inputs
.venv-ml/bin/python -m research.adaptive_dispatch run \
  --dataset /tmp/adaptive-inputs --output /tmp/adaptive-discovery --partition discovery
.venv-ml/bin/python -m research.adaptive_dispatch run \
  --dataset /tmp/adaptive-inputs --output /tmp/adaptive-confirmation --partition confirmation \
  --discovery /tmp/adaptive-discovery
.venv-ml/bin/python -m research.adaptive_dispatch audit \
  --dataset /tmp/adaptive-inputs --results /tmp/adaptive-discovery --replay
.venv-ml/bin/python -m research.adaptive_dispatch audit \
  --dataset /tmp/adaptive-inputs --results /tmp/adaptive-confirmation \
  --discovery /tmp/adaptive-discovery --replay
```

Smoke has four discovery and four confirmation configurations, two crew variants,
one deterministic and one episode per stochastic profile, and all 15 methods:
720 method-episodes across both stages. Its independent seed namespace and tiny
denominators make it an engineering check, not evidence for the learning gate.

## Audit the committed scientific evidence

These read-only commands check the completed scientific stages' source/input
hashes, complete cohort/method coverage, keyed duration draws, every assignment and
metric independently, and exact regeneration of grouped comparisons and gates.
They do not fit a model, change a comparator or spend a new evaluation cohort.

```sh
.venv-ml/bin/python -m research.adaptive_dispatch audit \
  --dataset docs/adaptive-dispatch/evidence/dataset \
  --results docs/adaptive-dispatch/evidence/discovery
.venv-ml/bin/python -m research.adaptive_dispatch audit \
  --dataset docs/adaptive-dispatch/evidence/dataset \
  --results docs/adaptive-dispatch/evidence/confirmation \
  --discovery docs/adaptive-dispatch/evidence/discovery
```

Add `--replay` to recompute all original policy decisions and verify exact numerical
equality. Timing may differ and is intentionally outside numerical identity hashes.
Routine CI performs full schedule/metric/grouped-result audits and all policy decisions
on smoke; full scientific policy replay remains a separately reproducible check.

## Regenerate the scientific presentation

```sh
.venv-ml/bin/python -m research.adaptive_dispatch report \
  --dataset docs/adaptive-dispatch/evidence/dataset \
  --discovery docs/adaptive-dispatch/evidence/discovery \
  --confirmation docs/adaptive-dispatch/evidence/confirmation \
  --output /tmp/adaptive-presentation
```

The renderer audits every episode and timing aggregate before writing the report or
three PNG/SVG figures. Same-environment regeneration is byte-identical. Raster/font
libraries can change bytes across platforms, so CI verifies its own repeated renders,
exact report text, committed artifact hashes and unchanged source-evidence identities.

Executed local preservation checks: 29 adaptive tests; 102 public, 196 challenge and
51 research tests; 115 frozen artifact hashes; exact full input regeneration; full
independent scientific schedule/metric audits; 720 smoke policy replays; and identical
report/figure regeneration. Challenge tests used authorized local sources, which are
not included in the new public evidence or source-free CI checkout.

## Scientific chronology and artifact contracts

The protocol was committed at `ed57372`. Engine and pre-benchmark corrections were
committed at `4acbdd7`. Scientific input generation was then sealed at `ed89a1b`,
before any scientific policy outcomes. Discovery must finish and its selection be
committed before confirmation can run. The eventual report records these identities.

| Artifact | Meaning |
|---|---|
| `dataset/manifest.json` | New adapter/version, generator revision/source hashes, configurations, seeds, topology and partition identities |
| `dataset/cases.jsonl.gz` | 72 immutable input variants / 36 complete-scope groups; no policy outcomes |
| `{discovery,confirmation}/receipt.json` | Invocation, source/input identities, environment and comparator inventory before execution |
| `{discovery,confirmation}/episodes.jsonl.gz` | Every policy schedule, common duration map, independent-validated metrics and configuration membership |
| `{discovery,confirmation}/summary.json` | Discovery selections, all comparator outcomes, paired configuration-bootstrap intervals, guardrails and gate |
| `{discovery,confirmation}/timings.jsonl.gz` | Every measured callback or fixed planning time, separate from outcomes |
| `{discovery,confirmation}/runtime.json` | Timing distributions, machine/environment, command wall time and peak RSS |
| `{discovery,confirmation}/completion.json` | Completed numerical identities and artifact hashes |
| `failure.json`, if present | Preserved failed command receipt; never overwrite to hide a failed attempt |

The generator adapts ML I's audited DAG mechanisms with fresh seeds, 10–14 tasks,
8–16 customer groups and explicit complete scope. Effort distributions, dependency
overlap, report order, critical flags, group-size skew and crew availability vary under
the committed configurations. Related 2/3-crew variants share their configuration and
remain together for uncertainty; their complete problem fingerprints key separate
duration maps. Policy comparisons **within** each variant use identical duration maps.
This study does not estimate the causal effect of adding a crew under matched durations.

Signatures reject cross-group topological duplicates conservatively; they cannot prove
that independently generated graphs have no semantic similarity. This is a small authored
scenario distribution, not an externally sampled or utility-representative population.
