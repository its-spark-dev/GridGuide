# Phase 3 optimization comparison

Fixed comparator: `legacy-release-per-person-hour-adapter-v1`.
Cases: 80; failed/invalid: 0. Previously inspected synthetic benchmark; no blind-holdout claim.
Promotion target on published suite met: **False**.

| Metric | Comparator | Finite pairs | Median improvement % | Mean improvement % | Clustered 95% median interval | Wins / ties / regressions |
|---|---|---:|---:|---:|---|---|
| modeled_customer_outage_hours | fixed | 60 | 0.0 | 0.9040143065917591 | [0.0, 0.0] | 15 / 45 / 0 |
| modeled_customer_outage_hours | best-of-four | 60 | 0.0 | 0.3841016689878103 | [0.0, 0.0] | 13 / 47 / 0 |
| modeled_customer_outage_hours | fifo-v1 | 60 | 31.034104266899384 | 28.736878806192852 | [0.0, 39.732142857142854] | 48 / 12 / 0 |
| modeled_customer_outage_hours | customer-count-v1 | 60 | 7.797179999883704 | 8.669627137226925 | [0.0, 17.770290067389393] | 46 / 14 / 0 |
| modeled_customer_outage_hours | legacy-release-per-person-hour-adapter-v1 | 60 | 0.0 | 0.9040143065917591 | [0.0, 0.0] | 15 / 45 / 0 |
| modeled_customer_outage_hours | legacy-critical-proxy-first-adapter-v1 | 60 | 0.0 | 2.934874701802035 | [0.0, 4.034958523967071] | 25 / 35 / 0 |
| restricted_horizon_customer_hours | fixed | 72 | 0.0 | 0.7533452554931326 | [0.0, 0.0] | 15 / 57 / 0 |
| restricted_horizon_customer_hours | best-of-four | 72 | 0.0 | 0.32008472415650857 | [0.0, 0.0] | 13 / 59 / 0 |
| restricted_horizon_customer_hours | fifo-v1 | 72 | 29.167438981869086 | 23.938826766983137 | [0.0, 39.42217069456234] | 48 / 24 / 0 |
| restricted_horizon_customer_hours | customer-count-v1 | 72 | 5.047940740242031 | 7.225908467514575 | [0.0, 14.396709323583181] | 46 / 26 / 0 |
| restricted_horizon_customer_hours | legacy-release-per-person-hour-adapter-v1 | 72 | 0.0 | 0.7533452554931326 | [0.0, 0.0] | 15 / 57 / 0 |
| restricted_horizon_customer_hours | legacy-critical-proxy-first-adapter-v1 | 72 | 0.0 | 2.445847844552351 | [0.0, 1.2023418018864516] | 25 / 47 / 0 |

## Breakdowns versus fixed comparator

| Metric / subset | Pairs | Mean % | Median % | Wins / ties / regressions |
|---|---:|---:|---:|---|
| modeled_customer_outage_hours / crews:1 | 20 | 0.6353739387520987 | 0.0 | 2 / 18 / 0 |
| modeled_customer_outage_hours / crews:2 | 20 | 0.6145441244937857 | 0.0 | 3 / 17 / 0 |
| modeled_customer_outage_hours / crews:4 | 20 | 1.4621248565293927 | 0.029797377830750895 | 10 / 10 / 0 |
| modeled_customer_outage_hours / family:critical-tradeoffs | 12 | 0.09713940254108934 | 0.0 | 2 / 10 / 0 |
| modeled_customer_outage_hours / family:independent-branches | 12 | 0.09713940254108934 | 0.0 | 2 / 10 / 0 |
| modeled_customer_outage_hours / family:overlapping-dependencies | 12 | 4.234515501133317 | 1.7651532623856434 | 8 / 4 / 0 |
| modeled_customer_outage_hours / family:serial-chain | 12 | 0.0 | 0.0 | 0 / 12 / 0 |
| modeled_customer_outage_hours / family:upstream-bottleneck | 12 | 0.09127722674329924 | 0.0 | 3 / 9 / 0 |
| modeled_customer_outage_hours / tasks:10 | 30 | 1.7238349906577 | 0.0 | 13 / 17 / 0 |
| modeled_customer_outage_hours / tasks:25 | 30 | 0.08419362252581815 | 0.0 | 2 / 28 / 0 |
| restricted_horizon_customer_hours / crews:1 | 24 | 0.5294782822934155 | 0.0 | 2 / 22 / 0 |
| restricted_horizon_customer_hours / crews:2 | 24 | 0.5121201037448214 | 0.0 | 3 / 21 / 0 |
| restricted_horizon_customer_hours / crews:4 | 24 | 1.2184373804411606 | 0.0 | 10 / 14 / 0 |
| restricted_horizon_customer_hours / family:blocked-prerequisites | 12 | 0.0 | 0.0 | 0 / 12 / 0 |
| restricted_horizon_customer_hours / family:critical-tradeoffs | 12 | 0.09713940254108934 | 0.0 | 2 / 10 / 0 |
| restricted_horizon_customer_hours / family:independent-branches | 12 | 0.09713940254108934 | 0.0 | 2 / 10 / 0 |
| restricted_horizon_customer_hours / family:overlapping-dependencies | 12 | 4.234515501133317 | 1.7651532623856434 | 8 / 4 / 0 |
| restricted_horizon_customer_hours / family:serial-chain | 12 | 0.0 | 0.0 | 0 / 12 / 0 |
| restricted_horizon_customer_hours / family:upstream-bottleneck | 12 | 0.09127722674329924 | 0.0 | 3 / 9 / 0 |
| restricted_horizon_customer_hours / tasks:10 | 36 | 1.4365291588814166 | 0.0 | 13 / 23 / 0 |
| restricted_horizon_customer_hours / tasks:25 | 36 | 0.07016135210484846 | 0.0 | 2 / 34 / 0 |

## Status and interpretation

Solver statuses: {'OPTIMAL': 21, 'FEASIBLE': 46, 'NOT_RUN': 13}
Fallbacks: {'no_executable_tasks': 13}

Full per-case metrics, releases, critical/fairness tradeoffs, raw statuses, bounds, failures and rejected candidates are retained in results.jsonl.gz and report.json.
Intervals resample family and seed clusters, retaining all scale/crew variants. Only five seeds and five finite families: no population-valid confidence claim.
Restricted costs retain unknown customers at the horizon without assigning finite restoration. Completed costs exclude unavailable full outcomes with their counts disclosed.
Missing/failed cases prohibit promotion; all nulls, ties, negative results and budget-stopped searches remain visible. Runtime observations are separate.
