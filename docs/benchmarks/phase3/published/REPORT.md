# Phase 3 optimization comparison

Fixed comparator: `legacy-release-per-person-hour-adapter-v1`.
Cases: 278; failed/invalid: 0. Previously inspected synthetic benchmark; no blind-holdout claim.
Promotion target on published suite met: **False**.

| Metric | Comparator | Finite pairs | Median improvement % | Mean improvement % | Clustered 95% median interval | Wins / ties / regressions |
|---|---|---:|---:|---:|---|---|
| modeled_customer_outage_hours | fixed | 225 | 0.0 | 0.3510349569012278 | [0.0, 0.0] | 30 / 195 / 0 |
| modeled_customer_outage_hours | best-of-four | 225 | 0.0 | 0.1736351944465556 | [0.0, 0.0] | 27 / 198 / 0 |
| modeled_customer_outage_hours | fifo-v1 | 225 | 32.32830820770519 | 28.129900188360644 | [0.0, 39.3479871137657] | 180 / 45 / 0 |
| modeled_customer_outage_hours | customer-count-v1 | 225 | 8.014321123657394 | 8.902136301287069 | [0.0, 15.507159457230676] | 176 / 49 / 0 |
| modeled_customer_outage_hours | legacy-release-per-person-hour-adapter-v1 | 225 | 0.0 | 0.3510349569012278 | [0.0, 0.0] | 30 / 195 / 0 |
| modeled_customer_outage_hours | legacy-critical-proxy-first-adapter-v1 | 225 | 0.0 | 3.0239948054666286 | [0.0, 6.984924623115578] | 71 / 154 / 0 |
| restricted_horizon_customer_hours | fixed | 270 | 0.0 | 0.29253020985770056 | [0.0, 0.0] | 30 / 240 / 0 |
| restricted_horizon_customer_hours | best-of-four | 270 | 0.0 | 0.144697074478807 | [0.0, 0.0] | 27 / 243 / 0 |
| restricted_horizon_customer_hours | fifo-v1 | 270 | 25.325454913645963 | 21.37915045810373 | [0.0, 33.37516825204639] | 180 / 90 / 0 |
| restricted_horizon_customer_hours | customer-count-v1 | 270 | 5.21396957306005 | 7.299030554635249 | [0.0, 12.943262411347519] | 176 / 94 / 0 |
| restricted_horizon_customer_hours | legacy-release-per-person-hour-adapter-v1 | 270 | 0.0 | 0.29253020985770056 | [0.0, 0.0] | 30 / 240 / 0 |
| restricted_horizon_customer_hours | legacy-critical-proxy-first-adapter-v1 | 270 | 0.0 | 2.5598245122245773 | [0.0, 2.4051803885291396] | 71 / 199 / 0 |

## Breakdowns versus fixed comparator

| Metric / subset | Pairs | Mean % | Median % | Wins / ties / regressions |
|---|---:|---:|---:|---|
| modeled_customer_outage_hours / crews:1 | 75 | 0.08733827591219655 | 0.0 | 1 / 74 / 0 |
| modeled_customer_outage_hours / crews:2 | 75 | 0.31983435417741857 | 0.0 | 7 / 68 / 0 |
| modeled_customer_outage_hours / crews:4 | 75 | 0.6459322406140684 | 0.0 | 22 / 53 / 0 |
| modeled_customer_outage_hours / family:critical-tradeoffs | 45 | 0.06265909514307796 | 0.0 | 4 / 41 / 0 |
| modeled_customer_outage_hours / family:independent-branches | 45 | 0.06265909514307796 | 0.0 | 4 / 41 / 0 |
| modeled_customer_outage_hours / family:overlapping-dependencies | 45 | 1.5865899671670878 | 0.0 | 19 / 26 / 0 |
| modeled_customer_outage_hours / family:serial-chain | 45 | 0.0 | 0.0 | 0 / 45 / 0 |
| modeled_customer_outage_hours / family:upstream-bottleneck | 45 | 0.043266627052895565 | 0.0 | 3 / 42 / 0 |
| modeled_customer_outage_hours / tasks:10 | 75 | 0.663303260250162 | 0.0 | 20 / 55 / 0 |
| modeled_customer_outage_hours / tasks:100 | 75 | 0.006604616154413321 | 0.0 | 4 / 71 / 0 |
| modeled_customer_outage_hours / tasks:25 | 75 | 0.38319699429910825 | 0.0 | 6 / 69 / 0 |
| restricted_horizon_customer_hours / crews:1 | 90 | 0.07278189659349713 | 0.0 | 1 / 89 / 0 |
| restricted_horizon_customer_hours / crews:2 | 90 | 0.26652862848118214 | 0.0 | 7 / 83 / 0 |
| restricted_horizon_customer_hours / crews:4 | 90 | 0.5382801044984223 | 0.0 | 22 / 68 / 0 |
| restricted_horizon_customer_hours / family:blocked-prerequisites | 45 | 0.0 | 0.0 | 0 / 45 / 0 |
| restricted_horizon_customer_hours / family:critical-tradeoffs | 45 | 0.06265909514307796 | 0.0 | 4 / 41 / 0 |
| restricted_horizon_customer_hours / family:independent-branches | 45 | 0.06265909514307796 | 0.0 | 4 / 41 / 0 |
| restricted_horizon_customer_hours / family:overlapping-dependencies | 45 | 1.5865964418071516 | 0.0 | 19 / 26 / 0 |
| restricted_horizon_customer_hours / family:serial-chain | 45 | 0.0 | 0.0 | 0 / 45 / 0 |
| restricted_horizon_customer_hours / family:upstream-bottleneck | 45 | 0.043266627052895565 | 0.0 | 3 / 42 / 0 |
| restricted_horizon_customer_hours / tasks:10 | 90 | 0.5527527168751349 | 0.0 | 20 / 70 / 0 |
| restricted_horizon_customer_hours / tasks:100 | 90 | 0.005507084115376458 | 0.0 | 4 / 86 / 0 |
| restricted_horizon_customer_hours / tasks:25 | 90 | 0.3193308285825902 | 0.0 | 6 / 84 / 0 |

## Status and interpretation

Solver statuses: {'OPTIMAL': 52, 'FEASIBLE': 177, 'UNKNOWN': 3, 'NOT_RUN': 46}
Fallbacks: {'solver_unknown': 3, 'no_executable_tasks': 46}

Full per-case metrics, releases, critical/fairness tradeoffs, raw statuses, bounds, failures and rejected candidates are retained in results.jsonl.gz and report.json.
Intervals resample family and seed clusters, retaining all scale/crew variants. Only five seeds and five finite families: no population-valid confidence claim.
Restricted costs retain unknown customers at the horizon without assigning finite restoration. Completed costs exclude unavailable full outcomes with their counts disclosed.
Missing/failed cases prohibit promotion; all nulls, ties, negative results and budget-stopped searches remain visible. Runtime observations are separate.
