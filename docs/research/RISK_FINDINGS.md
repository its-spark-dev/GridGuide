# Phase 4 findings: No-Go for the preregistered predictive experiment

**Decision: No-Go on the evidence acquired in this bounded investigation. Modeling was
not authorized: zero models fitted, no predictive metrics, no probability-model promotion.**
This is not a claim that all public outage prediction research is impossible. It records
specific missing prerequisites for the Ohio/Pennsylvania county-day task in the
[committed protocol](RISK_PROTOCOL.md), preregistration commit `bf56ca9`.

The [machine-readable decision](phase4/feasibility.json) records every failed/unverified
gate, with file hashes. The [source audit](phase4/source_audit.json) records actual HTTP
responses and NOAA payload measurements. The [review ledger](phase4/evidence_review.json)
separates measured access from reviewed permissions and unavailable observations.
No challenge damage record or synthetic test fixture became a predictive label.

## Rights and access

All requests were anonymous, with a 25-second response timeout and 30 MB response cap.
The cached evidence was acquired on November 3, 2026. Every successful response has a
byte count and SHA-256; an HTTP 200 does not itself establish a usable dataset.

| Candidate | Actual retrieval | Research permission disposition | Role and limit |
|---|---|---|---|
| EAGLE-I 2014–2022 | Catalog and DataCite JSON returned 200; Globus UI returned HTML; tested listing route returned 404 with unknown-resource response; no outage CSV acquired | Unverified: DataCite rightsList is empty; catalog review did not establish a payload-specific grant | Candidate outcome/lag counts; no usable outcome panel established |
| NOAA Storm Events | 2018 c20260323 and 2022 c20260625 gzip CSVs returned 200, decompressed and schema-audited | Federal NWS/NOAA aggregate research audit accepted with citation; no blanket third-party narrative redistribution grant asserted | Retrospective storm context only; not outage labels or negatives |
| DOE-417 | Program and tested annual-summary route each returned the same 481-byte JavaScript shell | Exact report-payload terms unverified | Optional corroboration; no report table acquired |

Sources: [ORNL catalog](https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1),
[DataCite record](https://api.datacite.org/dois/10.13139/ORNLNCCS/1975202),
[NOAA bulk directory](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/),
[NOAA metadata](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html),
[NCEI policy, section 4](https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf),
[DOE program](https://doe417.energy.gov/).

An empty rights field is not a prohibition; it is insufficient clearance for this gate.
The failed listing request establishes failure of that tested route, not that Globus is
universally inaccessible or that authentication necessarily resolves it. No credentials
were requested and no access controls were bypassed. Article licensing was not substituted
for data licensing. The raw downloaded files remain ignored and are not distributed.

## Observation process and measured coverage

The [EAGLE-I descriptor, Data Records section](https://www.nature.com/articles/s41597-024-03095-5#Sec3)
explains that zero-count records are omitted and absence conflates zero with collection
failure. Its state/year coverage and FEMA/year quality summaries do not establish a
county-quarter-hour success mask. Therefore this investigation cannot validate omitted
slots as negatives. Fully observed low-count windows could in principle support negatives;
no acquired outage payload permits measuring how many qualify here.

**County-time outage coverage, positive/negative label counts and independent final
outage-cluster counts are unknown (null), not measured zeros.** We did not infer them
from NOAA reports. The sampled-hour target is five successive >100 readings spanning
60 minutes, not evidence of continuous service loss between readings. Both class labels
require the complete feature and outcome windows under the same eligibility rule.

Actual NOAA measurements from the two pinned payloads:

| Measurement | 2018 | 2022 |
|---|---:|---:|
| All report rows | 62,699 | 69,887 |
| Duplicate EVENT_ID values | 0 | 0 |
| Missing required audit fields | 0 | 0 |
| County-type rows nationally | 35,755 | 32,927 |
| Forecast-zone-type rows nationally | 26,944 | 36,960 |
| Ohio county / zone rows | 982 / 350 | 1,076 / 489 |
| Pennsylvania county / zone rows | 1,163 / 393 | 888 / 639 |
| Distinct reported Ohio county codes | 85 | 88 |
| Distinct reported Pennsylvania county codes | 67 | 66 |
| Ohio episode IDs in county rows | 172 | 129 |
| Pennsylvania episode IDs in county rows | 158 | 107 |

Selected-state timestamps carry EST-5 in both snapshots. This is a schema audit, not
validated UTC conversion or a geographic crosswalk. Zone codes are not county codes.
A county absent from the report list is not known to have no storm or no outage. Episode
counts are not independent outage event clusters. Even large episode counts cannot pass
the 30-cluster gate without compatible outcomes and the preregistered grouping/purging.
NOAA metadata describes delayed retrospective publication; these records were never
admitted as as-of predictors. Revised 2026 snapshots do not establish what was known in
2018–2022. Full timezone, crosswalk and five-year event reconstruction remain unexecuted.

## Gate disposition and stop

Two gates fail on acquired evidence: outcome payload and zero/missing resolution.
Seven are unverified: outcome research permission, county-time coverage, labels of both
classes, event reconstruction, predictor availability, split integrity and final event
count. All nine block training. No mandatory gate is bypassed by a useful auxiliary file.

Stop reached after bounded public requests, rights review and two real NOAA payload
audits; the three–four engineering-day allowance was not exhausted or claimed as elapsed.
Downloading additional NOAA years or gigabytes of ambiguous outcome data would not resolve
the current rights/collection-mask prerequisites. No partners, paid data or private access
are needed to finish G4. No learned model libraries or training pipeline were added.

Reopening the experiment would require: a permitted pinned outage payload, documented
zero/failed-collection distinction and stable reporting scope; audited fixed-geography
coverage; prediction-time or explicitly retrospective feature provenance; verified county
and timezone mapping; reconstructable event clusters and embargoed partitions with both
classes and sufficient final events. Record new evidence and seek the applicable review;
do not reinterpret this No-Go as a passing dataset or reuse a final set for tuning.

## Executable checks and reproduction

`research/risk/validation.py` implements strict window eligibility, sampled-hour labels,
calendar denominators, feature availability, event/split embargo and fit/calibration
leakage guards, plus the evidence decision. These are validation primitives, not a
complete real-data importer, event-cluster reconstruction or an ML training pipeline.
Tests use clearly artificial records to check failure behavior; they are not research
observations, synthetic model evaluations or proof of real-data split integrity.

From repository root with existing Python dependencies:

```sh
# Decision replay needs only committed evidence, no raw sources or network.
.venv/bin/python scripts/evaluate_risk_feasibility.py --output /tmp/gridguide-risk-decision.json
cmp docs/research/phase4/feasibility.json /tmp/gridguide-risk-decision.json
.venv/bin/python -m unittest discover -s tests -p test_risk_research.py -v
# Re-audit original cached bytes (if retained locally).
.venv/bin/python scripts/audit_risk_sources.py --cache data/external/phase4/probe-20261103 --output /tmp/gridguide-risk-audit.json
cmp docs/research/phase4/source_audit.json /tmp/gridguide-risk-audit.json
# Fresh access investigation: upstream responses may differ; never overwrite old evidence.
.venv/bin/python scripts/probe_risk_sources.py --output data/external/phase4/new-probe
```

Commands refuse output overwrites. Cached replay verifies all response hashes before
parsing; a fresh probe's timestamps/HTML/revisions can change. Compare payload hashes
before attributing aggregate differences to code. Public records preserve the audit and
source URLs but do not redistribute raw responses or guarantee future upstream access.
The decision ledger requires human review; citations/booleans alone do not certify rights.

The original concern band and null outage probability remain unchanged. The accepted G3
finding also stands: combined policy mean gain 0.351%, incremental beyond best-of-four
0.174%, failed 5% median target, fixed baseline default. This No-Go neither compensates
for that result nor starts simulation, integration, release or deployment.
