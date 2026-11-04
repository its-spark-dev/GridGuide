# Synthetic dataset contract

ML Lab uses **independently authored fictional scheduling inputs**, not utility
measurements or challenge data. Its generator does not import the historical G2
generator, published results, or source loaders. All four policy implementations
and the numerical benchmark contracts remain unchanged.

## Lineage and units

`MLCase` (`ml-case-v1`) owns `ml-generator-v1`, partition, structural group,
generation configuration, topology hash, and the embedded `BenchmarkProblem`.
The inner contract retains `benchmark-generator-v1` and its legacy
`development`/`evaluation` compatibility fields because those literals belong to
the frozen contract. **They do not identify the new generator or define ML
partitions.** Only the outer lineage is authoritative for ML splitting.

Repair effort is independently sampled **total person-hours**, with four decimal
places and a 0.02 person-hour floor. It is not multiplied by AEP's 4.5 factor.
The benchmark's one-effective-worker conditional duration remains unchanged.
Crew availability is in integer seconds after the modeled response origin. All
crew variants retain four people per crew; crew count and people are distinct.
Inputs are scenario assumptions, duration/precedence conventions are prototype
policies, and unknown effort/dependencies/productivity are unavailable. No
synthetic observation is labeled AEP-specified or source-derived.

## Generation mechanisms

Every configuration samples a fresh graph, effort vector, customer membership,
critical-service flags and report order. It is a whole case family, not a row.
The only related variants are 1, 2 and 4 crews, sharing all those inputs and the
same prefix of the four sampled crew availability times.

| Mechanism | Graph construction | Partition role |
|---|---|---|
| Random ordered DAG | Independent edges from an earlier to a later topological index | Train / dev / final ID |
| Layered | Random level sizes; dense adjacent-level links and sparse skip links | Train / dev / final ID |
| Bottleneck | Sampled hub positions with denser outgoing and incoming dependencies | Train / dev / final ID |
| Modular | Dense connections within index-modulo modules with a sampled module count, sparse bridges | Train / dev / final ID |
| Preferential | Earlier nodes gain outgoing-link probability as their degree grows | Final structural shift |
| Deep sparse | High consecutive-edge probability with sparse longer-range links | Final structural shift |

Edges always respect a sampled construction order; the task identifiers are
independently shuffled afterward. Group release dependencies are a separate
relation from repair prerequisites. Customer groups enumerate unique, disjoint
customer IDs; overlap means multiple groups require the same repairs, never
duplicated customers.

The shifted cohort changes both graph mechanisms and scale (40–64 tasks versus
10–36 in ID), and expands crew-delay support (0–8 h versus 0–3 h). Therefore its
result measures a **combined structural/scale/availability shift**; it cannot
attribute a loss to one factor. These are declared synthetic mechanisms, not
samples from an electric network population.

## Parameter distributions

The exact realized parameters and random seed are in each group's manifest.
All ranges below are generator assumptions fixed before final evaluation.

| Parameter | Distribution / rule |
|---|---|
| ID task count | Discrete uniform 10–36 |
| Shift task count | Discrete uniform 40–64 |
| Base edge density | Uniform 0.06–0.32; mechanism-specific multipliers in source |
| Layer count / module count | Discrete uniform 3–8 / 2–5 |
| Effort family | Uniform choice: uniform, lognormal, mixture |
| Effort scale / log spread | Uniform 0.5–6 / 0.3–1.3 |
| Uniform effort | Scale × Uniform(0.2, 2) |
| Lognormal effort | Scale × LogNormal(0, spread) |
| Mixture effort | Scale × Uniform(0.1, 0.8) × multiplier; multiplier 1 with 75%, 8 with 25% |
| Groups per case | Discrete uniform 8–28 |
| Group size | Rounded Uniform(1,12) + skew × Exponential(mean 18), clamped 1–60; skew Uniform(0,1) |
| Dependency overlap | Uniform 0.05–0.8; shared hot repair pool plus independent extra dependencies |
| Critical prevalence | Uniform 0–0.4, then independent group Bernoulli draws |
| Report order | Uniform choice: random, ascending effort, descending raw membership |
| Availability | Four independent Uniform(0, configured delay cap) draws, rounded seconds |
| Incomplete mode | None 85%; blocked 5%; unknown effort 5%; unresolved customer dependency 5% |

Blocked and missing-effort modes deliberately affect a repair required by a
customer. Unresolved dependency affects a declared customer group. Unknown
clearance is never sampled into a finite release. Actual realized incomplete
counts, including chance variation from 15%, are recorded in the audit.

## Splitting and duplicate exclusion

The full dataset has **240 structural groups and 720 cases**:

| Partition | Groups | Cases | Role |
|---|---:|---:|---|
| Training | 30 per ID mechanism = 120 | 360 | Fit preprocessing and learned parameters; training-only baseline |
| Development | 10 per ID mechanism = 40 | 120 | Select declared model/hyperparameters |
| Final ID | 10 per ID mechanism = 40 | 120 | One-time held-out evaluation |
| Final shift | 20 per shifted mechanism = 40 | 120 | Separate one-time generalization evaluation |

The bounded smoke profile has 32 groups / 96 cases: 36 training, 24 development,
24 final ID and 12 shifted cases. Its distinct seeds come from the profile name;
it is engineering verification, not the final scientific cohort.

All related variants and the exact generation configuration remain in one
partition. A deterministic directed color-refinement hash ignores task names,
task order, effort and customer labels. Equal topology signatures are rejected
across *all* different groups, including within one partition. Thus isomorphic
repair DAGs cannot cross partitions; hash collisions conservatively reject some
non-isomorphic DAGs too. Rejection is capped at 100 attempts per group, with
every accepted attempt and seed recorded. No result-dependent rejection occurs.

This does **not** establish semantic independence of all near graphs, guarantee
a minimum graph edit distance, or prevent common motifs across independently
sampled graphs. Mechanisms share implementation and assumptions. ID holdout tests
new grouped realizations under those mechanisms; it is not transfer to unseen
mechanisms. Crew variants are correlated and must remain grouped in CV and
uncertainty calculations. Final inputs are visible and regenerable; outcome
isolation is procedural, not external blind-test custody.

## Frozen artifact format

`write_dataset` refuses an existing output directory and requires a full source
revision. It writes four deterministic `*.jsonl.gz` files and `manifest.json`.
The manifest records generator/source revision and source-file hashes, profile,
partition hashes (compressed and canonical uncompressed bytes), configurations,
case and problem fingerprints, topology hashes, support counts and split rules.
`dataset_hash` hashes the complete manifest before adding that field.

The input-only support audit computes executable prerequisite closure and
unresolved membership; it never schedules a policy or computes a future metric.
Known-later censoring requires schedule evaluation and is intentionally absent
from this input audit. The labeling stage owns its explicit eligibility rules.
Final policy labels and costs do not exist in these input artifacts.

`load_partition` verifies manifest and file hashes and reparses every contract.
The higher-level Stage A/B workflow restricts training access and binds the
frozen dataset to model and evaluator identities. File checksums detect changes;
they are not signatures or access control against a malicious repository owner.

```sh
.venv/bin/python -m unittest research.ml_lab.tests.test_dataset -v
```

Source-free checks cover determinism, grouped split isolation, ID-invariant graph
hashing, null scope, immutable writes, exact compressed replay, and forbidden
outcome/source dependencies. The complete workflow and evidence are linked from
the [ML Lab research page](README.md).
