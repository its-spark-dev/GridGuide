# Phase 5 paired comparisons and profile sensitivity

Generated from the complete standard report by `scripts/package_simulation_review.py`.
Case means are descriptive summaries of the published synthetic matrix. They are not
independent population samples. No confidence intervals, significance claim or promotion follows.
Microcases are retained in the full report but excluded from the following matrix aggregates.

## Paired policy differences

Candidate minus reference; negative customer-hours means lower modeled waiting.
Completed customer-hours use 225 finite cases (45 unresolved cases remain unavailable).
Restricted 168-hour customer-hours use all 270 cases and retain unresolved mass.
Every tie and positive difference is retained. Each cell is a mean of paired case means,
not a percentage improvement and not a replacement for G3 metrics.

| Profile | Candidate | Reference | Completed customer-hours difference | Restricted customer-hours difference | Completed case means better / tied / worse |
|---|---|---|---:|---:|---|
| deterministic-v1 | cpsat | fixed | -20.679809 | -17.233174 | 30 / 195 / 0 |
| deterministic-v1 | fifo | fixed | 25586.582222 | 9884.625926 | 0 / 45 / 180 |
| deterministic-v1 | customer-count | fixed | 6670.017778 | 3763.633333 | 9 / 46 / 170 |
| deterministic-v1 | best-of-four | fixed | -14.884444 | -12.403704 | 9 / 216 / 0 |
| deterministic-v1 | cpsat | best-of-four | -5.795364 | -4.829470 | 27 / 198 / 0 |
| independent-025-v1 | cpsat | fixed | -22.011005 | -18.314679 | 33 / 192 / 0 |
| independent-025-v1 | fifo | fixed | 26825.393696 | 10014.039680 | 0 / 45 / 180 |
| independent-025-v1 | customer-count | fixed | 7094.426840 | 3896.511523 | 12 / 45 / 168 |
| independent-025-v1 | best-of-four | fixed | -16.726418 | -13.909032 | 10 / 215 / 0 |
| independent-025-v1 | cpsat | best-of-four | -5.284587 | -4.405648 | 28 / 196 / 1 |
| independent-050-v1 | cpsat | fixed | -25.537992 | -20.800534 | 27 / 192 / 6 |
| independent-050-v1 | fifo | fixed | 29549.604534 | 10068.286030 | 0 / 45 / 180 |
| independent-050-v1 | customer-count | fixed | 7845.221311 | 4032.474213 | 13 / 45 / 167 |
| independent-050-v1 | best-of-four | fixed | -21.009181 | -17.015149 | 10 / 215 / 0 |
| independent-050-v1 | cpsat | best-of-four | -4.528810 | -3.785385 | 21 / 196 / 8 |
| shared-025-v1 | cpsat | fixed | -22.069756 | -18.129925 | 32 / 192 / 1 |
| shared-025-v1 | fifo | fixed | 27940.631758 | 9988.639731 | 0 / 45 / 180 |
| shared-025-v1 | customer-count | fixed | 7304.244691 | 3893.915986 | 11 / 45 / 169 |
| shared-025-v1 | best-of-four | fixed | -16.489973 | -13.474532 | 10 / 215 / 0 |
| shared-025-v1 | cpsat | best-of-four | -5.579783 | -4.655392 | 27 / 196 / 2 |
| shared-050-v1 | cpsat | fixed | -25.451043 | -19.566963 | 29 / 192 / 4 |
| shared-050-v1 | fifo | fixed | 31495.080964 | 9916.381785 | 0 / 45 / 180 |
| shared-050-v1 | customer-count | fixed | 8212.368587 | 3987.585486 | 12 / 45 / 168 |
| shared-050-v1 | best-of-four | fixed | -20.280121 | -15.302673 | 10 / 215 / 0 |
| shared-050-v1 | cpsat | best-of-four | -5.170922 | -4.264290 | 24 / 196 / 5 |
| storm-hold-v1 | cpsat | fixed | -24.993730 | -19.181092 | 29 / 192 / 4 |
| storm-hold-v1 | fifo | fixed | 31527.125801 | 9804.038142 | 0 / 45 / 180 |
| storm-hold-v1 | customer-count | fixed | 8230.976481 | 3958.835123 | 12 / 45 / 168 |
| storm-hold-v1 | best-of-four | fixed | -19.892953 | -14.888471 | 10 / 215 / 0 |
| storm-hold-v1 | cpsat | best-of-four | -5.100777 | -4.292620 | 24 / 196 / 5 |
| uniform-sensitivity-v1 | cpsat | fixed | -21.590159 | -17.973000 | 30 / 192 / 3 |
| uniform-sensitivity-v1 | fifo | fixed | 26411.755538 | 9999.468276 | 0 / 45 / 180 |
| uniform-sensitivity-v1 | customer-count | fixed | 6998.474637 | 3889.587523 | 11 / 45 / 169 |
| uniform-sensitivity-v1 | best-of-four | fixed | -16.579057 | -13.801256 | 10 / 215 / 0 |
| uniform-sensitivity-v1 | cpsat | best-of-four | -5.011102 | -4.171744 | 26 / 196 / 3 |

`cpsat` is the frozen protected combined best-of-four + CP-SAT result. `best-of-four`
is selected on deterministic inputs before sampling, not a hindsight trial winner.
Full paired p10/p50/p90, batch numerical diagnostics, better/tie/worse trial counts,
critical-service and fairness differences are in `standard/report.json.gz`.

## Fixed-baseline sensitivity

Means of finite case means / case quantiles are equally weighted across scenarios, not
customer-pooled population quantiles. Higher sigma increases the median-one lognormal mean.
Uniform multipliers have mean one and are not variance matched. Profiles have different
random streams; common draws pair policies within a profile, not different profiles.

| Profile | Mean completed customer-hours (225) | Mean restricted customer-hours (270) | Mean completion time (225), h | Mean case p90 completion, h | Mean case p90–p10 width, h |
|---|---:|---:|---:|---:|---:|
| deterministic-v1 | 63560.968889 | 45778.774074 | 197.795556 | 197.795556 | 0.000000 |
| independent-025-v1 | 66814.377037 | 46696.031643 | 208.526973 | 218.508390 | 18.841590 |
| independent-050-v1 | 73741.528262 | 48229.236610 | 232.546298 | 257.921062 | 48.076405 |
| shared-025-v1 | 69336.637872 | 46959.989102 | 216.150496 | 254.218058 | 58.628356 |
| shared-050-v1 | 78223.285351 | 48333.870362 | 245.101830 | 337.031156 | 142.868302 |
| storm-hold-v1 | 79180.991118 | 48849.596375 | 247.286395 | 339.631790 | 143.572180 |
| uniform-sensitivity-v1 | 65899.822391 | 46533.361084 | 205.490961 | 214.439011 | 16.635451 |

These are fixed-timetable sensitivity findings, not estimates of observed restoration.
Convergence failures remain disclosed in the G5 packet; no finite-scope result fills in unknown clearance.
