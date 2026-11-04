# ML Lab features, labels and baselines

This is a synthetic **policy-selection** task. Features describe one fictional scheduling
problem before any candidate policy runs. Labels measure outcomes of the unchanged four
benchmark policies, independently checked by `benchmarks.validation.validate`; they are
not utility observations or optimal dispatch labels.

## Static prediction contract

`extract_features(BenchmarkProblem)` reparses the input contract and emits the ordered
41-float schema `ml-static-features-v1`. It never imports a scheduler, metric calculator,
or label module. IDs are used only to resolve explicit graph/membership relations; IDs,
case family, random seed, split and fingerprints are absent from predictive features.
The features do not consume schedules, future completion times, candidate costs or labels.

All inputs are scenario assumptions. Feature aggregation is prototype policy. Missing
effort/access/dependency evidence remains unavailable. Zero-valued summaries for an empty
known-effort set are accompanied by an explicit missing fraction. The prediction support
check abstains for any unknown effort, blocked/unresolved task access, or unresolved
customer dependency. These diagnostic feature values do not authorize incomplete-case
predictions or invented targets. Invalid contracts raise instead of returning a policy.

| Feature | Unit | Pre-decision derivation |
|---|---|---|
| `task_count` | count | len(tasks) |
| `crew_count` | count | len(crews) |
| `people_per_crew` | people | crews[0].people; separate from crew count |
| `ideal_all_people` | indicator | duration_assumption equals ideal_all_people |
| `effort_mean` | person-hours | mean of known task effort |
| `effort_std` | person-hours | population SD of known task effort |
| `effort_q25` | person-hours | linear 25th percentile of known effort |
| `effort_median` | person-hours | linear median of known effort |
| `effort_q75` | person-hours | linear 75th percentile of known effort |
| `effort_max` | person-hours | maximum known effort |
| `effort_sum` | person-hours | sum of known effort; missingness separate |
| `effort_missing_fraction` | fraction | tasks with null effort / task count |
| `blocked_fraction` | fraction | tasks with access other than clear / task count |
| `dag_depth` | edges | longest prerequisite path |
| `dag_level_width` | tasks | largest longest-path-level population; not exact antichain width |
| `dag_edge_density` | fraction | prerequisite edges / n(n-1)/2 |
| `indegree_mean` | edges | mean prerequisite count |
| `indegree_max` | edges | maximum prerequisite count |
| `outdegree_max` | edges | maximum direct successor count |
| `root_fraction` | fraction | tasks without prerequisite / task count |
| `leaf_fraction` | fraction | tasks without successor / task count |
| `bottleneck_fraction` | fraction | tasks with at least ceil(n/2) strict descendants / n |
| `ancestor_mean` | tasks | mean distinct prerequisite ancestor count |
| `group_count` | count | len(groups) |
| `customer_count` | count | sum of disjoint group membership sizes |
| `group_size_mean` | customers | mean group membership size |
| `group_size_std` | customers | population SD of group membership size |
| `group_size_max` | customers | maximum group membership size |
| `small_group_fraction` | fraction | groups with <=5 customers / group count |
| `requirements_mean` | tasks | mean direct customer-group required-task count |
| `requirements_max` | tasks | maximum direct customer-group required-task count |
| `dependency_overlap` | fraction | mean pairwise required-task Jaccard; empty/empty defined zero |
| `task_group_membership_max` | groups | maximum groups directly requiring a task |
| `critical_group_fraction` | fraction | explicit critical-service groups / group count |
| `unresolved_group_fraction` | fraction | groups with unresolved_dependency / group count |
| `branch_count` | count | number of distinct branch equivalence classes; no branch label |
| `crew_available_mean` | hours | mean declared crew availability / 3600 |
| `crew_available_std` | hours | population SD declared crew availability / 3600 |
| `crew_available_max` | hours | maximum declared crew availability / 3600 |
| `report_effort_correlation` | correlation | Pearson declared report-order / known effort; constant defined zero |
| `report_customer_correlation` | correlation | Pearson declared report-order / direct customer membership; constant defined zero |

Quantiles use linear interpolation at `(n-1)q`; standard deviations are population SDs.
Correlation with fewer than two observations or zero variance is defined as zero.
The DAG width feature is the largest population at a longest-path level, **not** the
maximum antichain. Bottlenecks have at least `ceil(task_count/2)` strict descendants.
Pairwise overlap averages Jaccard over every unordered group pair; empty/empty pairs
contribute zero. These are compact structural summaries, not complete graph embeddings.

## Independently validated targets

`evaluate_problem` runs the four unchanged policies on exactly the same input. Every
schedule and its complete metric dictionary must pass the independent validator before
any target can be returned. A validator error fails the experiment; it is not silently
excluded. Exact integer customer-seconds are calculated as
`sum(len(group.customer_ids) * validated_release_tick[group.id])`.
The target is the policy with minimum exact cost, with lexicographic policy-ID tie-breaking;
all equal-cost policies remain in `ties` for tie-aware accuracy. Customer-hours are the
same integer objective divided by 3600. Floating-point closeness never decides labels.

Training eligibility requires **all declared tasks scheduled and all group releases known**
under all four policies. This conservatively excludes a case with an unrelated blocked
task even if its customer-only total happens to be finite. Ineligible rows retain their
four validated outcomes, reasons, null label and empty ties. Unknown release costs stay
null. Known completion after 168 hours remains finite and eligible for the full-completion
task; the distinct censored count and restricted-horizon metric remain visible. No 168-hour
surrogate becomes a full-completion label. There is no separate restricted-horizon ML task.

The best-of-four hindsight oracle is the minimum of these four costs, never the global
schedule optimum and never an inference-time option. The bounded exhaustive optimizer
in `benchmarks/oracle.py` is not used for this label.

## Baseline definitions fixed before final evaluation

- **Best fixed:** smallest total exact customer-seconds across eligible training cases,
  breaking ties lexicographically. Since every policy uses identical cases, this also
  minimizes mean absolute regret. No development/final outcome selects this baseline.
- **Majority:** most frequent deterministic training label, breaking count ties
  lexicographically. Its dominant class can reflect the label tie convention; tie-aware
  accuracy and tie frequency must accompany exact accuracy.
- **Structural heuristic:** choose `customer-count-v1` when the mean number of direct
  customer-group required tasks is strictly greater than 1.5; otherwise choose
  `legacy-release-per-person-hour-adapter-v1`. This simple threshold is declared before
  experiments and never fitted using policy outcomes. Incomplete inputs abstain.
- **Hindsight oracle:** per-case minimum of all four already measured costs, reported
  only as an unattainable-at-prediction-time reference.

`fit_baselines` requires every row to explicitly declare `partition="train"`, rejects
missing or non-training partition metadata (including ineligible rows), and checks targets
against exact costs. The workflow owns authenticated dataset loading, so a caller cannot
establish training provenance merely by rewriting a partition field. Standalone Python
functions are not a security boundary against an investigator deliberately bypassing the
protocol. No frozen G2/G3/G4/G5 input, policy, metric or result is changed.

## Executed checks

`python -m unittest research.ml_lab.tests.test_features_labels -v` checks hand-computed
features and labels, DAG/overlap summaries, schema order, identifier and metadata invariance,
absence of outcome imports, rejection of injected outcomes, missingness and support,
revalidation of unchecked model copies, the structural heuristic, exact ties, unresolved
nulls, known-later censoring, conservative blocked scope, corrupted metric rejection,
training-only baseline fitting and differing fixed/majority objectives.
