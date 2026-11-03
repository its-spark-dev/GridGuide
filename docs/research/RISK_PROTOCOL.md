# Phase 4 outage-risk protocol v1

Preregistered before model fitting on the Phase 4 branch from main
`976a67f68dfc55380ed7f157560e51cf73abf5e2`. This protocol follows the approved
roadmap and G1–G3 evidence. No model has been fitted. Initial metadata inspection
has already disclosed EAGLE-I's ambiguous omitted observations; this is a prospective
feasibility protocol, not a claim that source limitations were unknown.

## Target and population

Unit: county × daily issue time at 00:00 UTC, 2018–2022. Primary geography: all 88
Ohio counties (FIPS state prefix 39); Pennsylvania (prefix 42, 67 counties) is the
geographic holdout, never included in fitting or calibration. Verify county identities
against an authoritative versioned crosswalk before joining actual data. Do not infer
county identity from a NOAA forecast-zone code. No adaptive geographic selection.

Target: more than 100 reported customers without power for at least one hour within
the next 24 hours. Operationalize the 15-minute source as five successive observations
strictly >100 spanning 60 minutes, entirely in (issue, issue+24h]. This is a sampled
persistence target, not proof of uninterrupted service loss between samples. It is not
a household probability, equipment failure label, or outage-onset-only target.

Require all 96 future quarter-hour timestamps, each with explicit successful observation
and stable reporting scope, for either class. The previous 24h feature window is
(issue-24h, issue], also 96 complete observations. Missing/null/failed observations,
unknown reporting scope, duplicate county-time keys or off-grid times invalidate the
window; never fill with zero, forward-fill, interpolate or retain only easy positives.
An explicit observed count of zero is usable only with documented zero semantics.
Report exclusions and denominators by county/year; label missing windows null.

Coverage gate: at least 95% eligible daily windows in every year for at least 80% of
counties in EACH fixed geography (71 Ohio, 54 Pennsylvania), with stable county mapping
and independently documented successful-collection/zero semantics. This threshold is
an engineering inclusion rule, not proof of population representativeness. Stop rather
than change geography or threshold to obtain a model.

## Sources, rights and acquisition

- EAGLE-I DOI 10.13139/ORNLNCCS/1975202, 2014–2022 release (May 2023): outcome and
  lag-count candidate. Resolve exact payload versions, checksums, applicable research
  permission and county-time collection-quality evidence. Article CC BY terms are not
  automatically a grant for standalone data. Annual state/FEMA coverage is not a
  county-time validity mask. [Catalog](https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1),
  [descriptor](https://www.nature.com/articles/s41597-024-03095-5).
- NOAA Storm Events C00510: use pinned bulk details snapshots for 2018–2022, metadata,
  NCEI data policy and schema. Retrospective grouping/context only; narratives, severity,
  damage, event-end fields and revisions are excluded from predictors.
  [Bulk files](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/),
  [metadata](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html).
- DOE-417: optional major-event corroboration only. Verify any public payload's terms
  and schema; absence from reports is never evidence of no outage.
  [Program](https://doe417.energy.gov/).

Record access timestamps, final URLs, response types, byte counts and SHA-256 of actual
responses separately from observation-payload status. HTML/metadata/unauthorized responses
are not observations. Raw downloads stay under ignored data/external/phase4; derivatives
under data/prepared. Publish only aggregate audits, hashes and cited findings. No partner,
paid data, credential acquisition, or authentication bypass is required or authorized.
At most four engineering days of access/quality investigation; stop earlier when a
critical evidence gate cannot be met. Bounded public HTTP probes and representative
NOAA snapshot audits suffice when the outcome source has a decisive unresolved gate.
Do not claim the time cap elapsed merely because a decision was reached.

## Features and temporal availability

Allowed candidate predictors: UTC calendar month/day-of-week; previous-24h reported
count mean/max and count at issue time. Each source feature must record observation
end and actual available-at time, both <= issue. Future counts and all retrospective
storm information are prohibited predictors. Require a verified historical latency
policy or publication timestamps for as-of claims. If only retrospective counts exist,
a separate explicitly retrospective experiment may use observation-end times with its
availability assumption disclosed; it cannot claim operational forecasting. Unknown
latency never silently becomes zero latency. Training remains gated on valid labels.

## Split and event controls

Ohio train: 2018–2020; validation/calibration: 2021; final test: 2022. Geographic
assessment: Pennsylvania 2022, evaluated once alongside the Ohio final test; never fit
on Pennsylvania. Reserve all final labels from tuning. Purge rows whose feature/target
windows touch a split boundary or its 24h embargo on either side.

Before splitting, reconstruct retrospective episode membership across counties from
NOAA episode/event IDs (validated county/time conversions) plus outage intervals.
Combine overlapping episode intervals across geographies into connected event clusters;
retain at least 24h separation between clusters. Link any row whose feature or target
window intersects a cluster to that cluster; union clusters touched by the same row.
Background windows use UTC week blocks, unioned with intersecting event groups.
These conservative unions may reduce sample size: do not relax them to reach 30.
Purge all clusters crossing temporal boundaries from both sides. Ensure county-time
keys, dependency windows and cluster identities never overlap between temporal splits.
Same storms in Ohio and Pennsylvania are shared clusters; geographic results do not
add independent events to Ohio uncertainty. Verify preprocessing fit IDs are a subset
of training, calibration IDs a subset of validation, and neither intersects final IDs.

## Conditional experiment and promotion

All critical gates must pass: permitted research use, acquired/audited outcome payload,
zero/missing semantics, coverage, valid labels of both classes, reconstructed events,
features without leakage, defensible splits, >=30 independent final event clusters and
both final classes. Unknown evidence fails closed. Permission cannot be established by
an unaudited boolean alone: record source citation and exact reviewed scope.

Only after Go: seasonal/climatology baseline (training month prevalence with global
training prevalence for empty months); persistence baseline (past-24h sampled target,
probabilities smoothed from training). Regularized logistic regression C=1, L2; one
histogram gradient boosting classifier (100 iterations, depth 3, learning rate .1,
seed 20261103). No search over model families/hyperparameters. Standardize numeric
features from training only; no outcome imputation. Sigmoid calibration on validation
only; select the learned candidate by validation Brier, logistic regression on ties.
Freeze pipeline/software/model hashes before the single final evaluation. If compatible
libraries are needed, pin them before fitting; none is required for a No-Go.

Metrics: Brier, log loss (probabilities clipped to [1e-6,1-1e-6]), PR-AUC, prevalence,
10 equal-width reliability bins (empty bins explicit), precision/recall at threshold
selected on validation for maximum F1 (higher threshold on ties). Report by county,
state, coverage band and retrospective event severity. No severity predictors.
Use 2,000 paired event-cluster bootstrap draws, seed 20261103, keeping all county/window
rows per sampled cluster, percentile 95% intervals. Include geographic transfer results
separately. At least 30 clusters is a floor, not a guarantee of reliable inference.

Promotion: positive Brier skill relative to the stronger validation-selected fixed
baseline, with 95% paired event-bootstrap lower bound >0; final log loss no more than
0.01 above that baseline; expected calibration error <=0.05 with observed and predicted
bin rates reported. Both classes and minimum event count are mandatory. No test-driven
threshold changes, refitting, or repeated final evaluation. Preserve inconclusive and
negative results; cap conditional modeling at 6–10 engineering days. Product integration
requires separate approval regardless of research performance.

## No-Go deliverables and checks

If any critical gate is failed/unverified, do not fit models. Publish RISK_FINDINGS.md,
Phase 4/G4 review packet, machine-readable source/access/feasibility audit, and executable
validation primitives with adversarial tests for missing versus zero, full windows,
threshold duration, duplicate rows, county identity, permissions, event overlap,
embargoes, future features and preprocessing/calibration leakage. Artificial test inputs
are software fixtures only, never research observations or performance evidence.
Reproduce audit results from pinned cached responses without network; distinguish access
re-probing (upstream can change) from deterministic audit reproduction. Prior source,
application, benchmark and optimization artifacts remain unchanged. Stop at a G4 PR;
no merge, Phase 5, release or deployment.
