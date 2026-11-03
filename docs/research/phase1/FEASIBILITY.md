# G1 evidence and data-use feasibility

Reviewed November 3, 2026. The machine-readable [register](dataset_register.json)
is reproduced by `python -m research.datasets`. It records versions, checksums,
acquisition state, units, observation process, coverage, missingness, licensing,
permitted claims and separate target-level decisions. **Metadata review is not
observation validation, license clearance, or approval to train.**

## Decisions

| Target | Present decision | What is missing |
|---|---|---|
| Premise outage probability | No-go on current data | Verified outage positives, observed non-outage controls, exposure windows and as-of features |
| County reported-outage risk | Conditional, not cleared | Exact permitted EAGLE-I files, quality masks, missing/zero semantics, event grouping, sufficient held-out events |
| Repair-task duration | No-go on current data | Task start/finish, scope, staffing, interruptions and censoring |
| Customer restoration duration | No-go on current data | Premise-level outage onset and confirmed restoration, identity linkage and observation coverage |
| Aggregate outage recovery | Conditional, not cleared | Audited county time series with stable reporting, event origin and censoring rules |
| Fictional contract/isolation checks | Go, synthetic only | No real-world validity is claimed; Phase 2 benchmark design remains unstarted |

The proposed county target remains **more than 100 reported customers without power
for at least one hour in the next 24 hours**. Its unit, horizon and observation
requirements are a proposed research specification, not a labeled dataset. Neither
synthetic outcomes nor absent reports can supply the missing negative examples.
No model was fitted, calibrated or evaluated; no prediction/performance metric exists.

## Source licensing, coverage and use are distinct gates

### Challenge files

All four pinned hashes are checked before source analysis. The [coverage report](source_coverage.json)
reproduces the current validators, not just topology syntax. It contains aggregate
counts/rejection reasons and implementation hashes, not source rows or identities.
The existing [publication assessment](../../releases/PUBLIC_RELEASE_AUDIT.md) records
retention authorization and unresolved permissions/exposure; neither is rewritten.
No explicit redistribution grant was established, and all challenge files and processed
customer tables are excluded from the new catalog artifact. Existing local analysis
continues under the owner's established authorization.

Observations remain unsuitable for learned outcomes: all 1,659 outage/incident IDs are
zero; event labels are `Default`; date-only reports do not identify storms or elapsed
outage durations; all 76 unrepaired flags still have repair dates. Complete reverse
membership is not observed outage membership. Spatial damage/facility matches remain
hypotheses. Rejection categories overlap and must not be summed.

### ORNL EAGLE-I

The [ORNL landing page](https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1)
identifies the 2014–2022 release, county/time/count fields, 15-minute granularity and
Globus distribution. It describes collection from utility outage maps. It does not,
by itself, establish the terms for a selected downloadable payload, complete county
coverage, zero-versus-missing semantics, or a premise/task outcome crosswalk.

This pass reviewed metadata, not observation files. No observation checksum is
invented. The [paper](https://doi.org/10.1038/s41597-024-03095-5) was accessible during
the master-plan review but a new direct fetch encountered an identity/cookie redirect;
the [DataCite endpoint](https://api.datacite.org/dois/10.13139/ORNLNCCS/1975202) could not
be retrieved through the research tool. No authentication was bypassed. Article terms
are not assumed to license its underlying dataset. The exact release's payload terms
and locally measured county-window completeness remain open. This is a promising
research lead, not a conclusion that suitable public data cannot exist.

### NOAA Storm Events

The [dataset metadata](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html)
requires citation, warns of potentially unverified information from multiple sources,
and describes delayed retrospective publication. The [bulk format](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf)
provides event/episode keys. `CZ_TYPE` distinguishes county, forecast-zone and marine
areas; a forecast-zone code must not silently become a county FIPS code. Timezone and
revision semantics require validation before joining.

The [NCEI open-data policy](https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf)
distinguishes federal public-domain data from third-party material with retained
rights. Exact downloaded snapshots still need attribution/terms review. No observation
snapshot has been acquired or joined. Storm reports can support retrospective grouping;
they cannot independently establish an outage label or a feature known before prediction.

### DOE-417

The [reporting-program site](https://doe417.energy.gov/) identifies incident/emergency
reporting context. Its rendered page provided no readable report table in this review.
No report file, exact schema, observation coverage or payload terms were validated.
The program is a candidate for corroboration, not an exposed non-outage denominator.
Missing reports must not become negatives. It remains optional and excluded from artifacts.

## Optional partner-data specification

No partner relationship, supplied data or permission is claimed. A future review needs:

- Written research/training/display/redistribution permissions, retention rules and restrictions.
- Stable event, asset and premise keys with permitted private crosswalks and topology version.
- Observed outage onset and restoration timestamps, timezone, timestamp provenance and publication latency.
- Complete observation windows and explicit non-outage controls; collection gaps separate from zero.
- Task scope/start/end, crew assignment/composition, pauses, holds and unfinished work.
- Stable reporting population, event grouping, censoring rules and source-quality indicators.

Partner data is not required for this release. Any acquisition or modeling proceeds
only in an approved later phase; downloads belong in ignored `data/external/`, and
private derived files in ignored `data/prepared/`, never in `data/raw/` or a public artifact.

## Evidence classification and unknowns

Existing six-class authority is unchanged: AEP-specified, source-derived, scenario
assumption, prototype policy, user-declared, unavailable. Dataset metadata is source
evidence about that dataset, not permission to turn every possible join into a fact.
The fictional catalog permits only consistent synthetic-definition/scenario-assumption,
prototype-rule/prototype-policy, and missing-evidence/unavailable pairs. No source
fact or AEP policy is attributed to fictional labor, customer identities or topology.
Each important fixture field binds one evidence entry; unused, missing or misclassified
references fail schema validation. Customer declarations are not accepted by this API.

The absent original challenge PDF/Data Guide attachments remain absent; this work uses
existing recorded excerpts and does not invent new page citations or policies.

## Later metric boundaries, fixed now but not implemented

Completed modeled customer-outage hours require known release for the full scope.
Restricted-horizon customer-hours integrate waiting only to the fixed horizon. Record
known releases beyond that horizon as censored for the horizon analysis; record unknown
release separately as unresolved. Both remain in denominators. An unresolved full-scope
completion is null, not the horizon and not the sum for a convenient complete subset.

The 5% optimization improvement remains a preregistered target, never a mandatory result
or permission to alter evaluation scenarios. Reproducibility uses deterministic work
budgets; wall-clock latency is a separate operational check and may interrupt a solver.
These rules are preserved in the [approved roadmap](../../planning/V1_1_0_MASTER_ROADMAP.md).

## Research stop and review disposition

Phase 1 reaches a bounded metadata/coverage decision without downloading large datasets,
installing ML libraries, acquiring accounts or requesting partner access. It does not
claim that the four-day research cap was exhausted. The unresolved payload terms and
observation coverage are concrete future prerequisites; they are not blockers to the
synthetic engineering foundation. G1 acceptance is an owner review of these boundaries.
No Phase 2 benchmark, optimizer, simulation, training or hosting has begun.
