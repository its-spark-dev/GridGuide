# Source and measurement audit

Audit version: `outage-source-audit-v1`. Acquisition date: 2026-11-04 UTC. Complete
receipts: [acquisition.json](evidence/acquisition.json). Every numeric finding below
is descriptive; no predictive outcome was evaluated.

## PNNL / DOE · primary source

Publisher: Pacific Northwest National Laboratory; authors Buxin She, Veronica Adetola,
Ji Young Yun. Catalog: [OEDI 6458](https://data.openei.org/submissions/6458).
The catalog labels the artifact **Outage Dataset v2** even though its basename is
`Outage_Dataset_R1.zip`. Pin the bytes, not an inferred version from the basename.
The download is **31,260,449 bytes**, SHA-256
`44557bae7a5c8e02c611a14f75fe9e123d81d286f700b9fd88ac538edd910fe7`.

The official v2 guidelines and disclaimer were read before data use and rendered for
inspection. Their hashes are in the acquisition record. The archive has 52 members:
one directory, 50 CSVs and a disclaimer identical to the separately downloaded one.
No processing code, license file or detailed coverage/censoring dictionary is embedded.
All member names, bytes, checksums and CSV schemas are in
[source-audit.json](evidence/source-audit.json).

| File family (ten yearly files each) | Unit | Actual columns / meaning |
|---|---|---|
| `_group.csv` | State/year/month aggregate; month 0 is annual | `state`, `year`, `month`, `outage_count`, `max_outage_duration` (hours), `customer_weighted_hours` |
| `_merged.csv` | Processed continuous county episode | `fips`, `state`, `county`, `start_time`, `duration` (hours), `min_customers`, `max_customers`, `mean_customers` |
| `with_events_YEAR.csv` | County episode–incident association, repeated | Merged fields plus `event_id`, `state_event`, `Datetime Event Began`, `Datetime Restoration`, `Event Type`, `end_time` |
| `_8_hours_lag.csv`, `_24_hours_lag.csv` | Alternative association windows | Event fields above **without `end_time`**; separate analyses, never pooled as independent observations |

FIPS values are source strings, often without a leading zero; the audit validates decimal
spelling and pads to five characters for comparisons. It does not infer utility connectivity.
Recorded timestamps have no offsets, and the guide gives no timezone. They remain naive.
The source's 15-minute underlying cadence does not establish instantaneous report arrival.

### Measured checks

- Merged files: **1,385,389** rows, no exact duplicate rows or repeated county/start keys
  within the audited files, no missing cells, positive durations on quarter-hour increments.
  Every recorded minimum customer count is at least **200**. This is an observed floor,
  **not an invented source threshold policy**; the guide does not explain it.
- The 2014 file begins **November 1**, not January 1. Its 13,516 rows must not be presented
  as a complete comparable year. Geographic label counts and represented county counts
  vary by year; absence of a row is not a reliable negative outage observation.
- **79** implied episode ends cross a year boundary; **274** rows begin January 1 at
  midnight; **4,180** implied ends fall on December 31 or January 1. These are boundary
  diagnostics, **not counts of proven censored events**. No censor flag is supplied.
- Unlagged links: **526,165** rows, **168,858** county/start keys counted within year,
  **357,307** repeated-key rows, including **273,291** exact duplicate rows. Repeated
  keys can represent duplicate joins or multiple incident associations; do not automatically
  call each additional row a separate outage or an erroneous observation.
- **29** year/event IDs map to multiple `(incident start, incident restoration, type,
  state_event)` definitions. County rows share incident identities and event IDs may be
  reused across years. Neither random row splitting nor `year:event_id` alone suffices.
- **67,482** unlagged rows attach to an incident whose restoration is not later than
  its start. **306,190** start after the attached restoration time. Source timestamp
  conventions and linkage code are unavailable here, so the audit flags inconsistencies
  without rewriting dates or declaring their real cause.
- All unlagged episode `end_time` values equal `start_time + duration`. This is an
  internal arithmetic check, not independently observed complete restoration.
- The **91,402** 8-hour rows and **114,610** 24-hour rows have **1,975** and **2,094**
  exact duplicates, respectively. Neither has an episode starting after its attached
  restoration time. They have **8,423** and **31,631** starts before incident start,
  consistent with the possibility of a lag window; causality is not established.

The descriptor DOI [10.1109/IEEEDATA.2025.3598229](https://doi.org/10.1109/IEEEDATA.2025.3598229)
was located via its author's publication page and Crossref. IEEE returned a browser check
or empty HTTP 202 response; its linked PDF endpoint returned HTTP 418. Its full methods
were **not** read. Do not treat that access limitation as proof that no further methods
exist. The actual downloaded guide and archive are the reviewed methodological evidence.

## Purdue · bounded alternative

[Official LASCI page](https://engineering.purdue.edu/LASCI/research-data/outages) links
`outage.xlsx`: **660,364 bytes**, SHA-256
`1d64b446ef131f39c99beea2b1380396f94cfaac1e56c722eba0693e13ee253a`.
The spreadsheet is accessible through direct HTTP even though the browsing tool followed
the relative link to a landing page. No third-party mirror was substituted.

The `Masterdata` worksheet has introductory rows, a header on Excel row 6, units on row 7,
and **1,534** observations. It states January 2000–July 2016 and single-state reported
events. There are 55 substantive variables plus `OBS`; the first `variables` column is
a label column. The full schema and per-field missingness are committed in the audit JSON.
`OUTAGE.DURATION` is in **minutes**, converted to hours only for aggregate statistics.
Excel serial dates/times are compared in minutes; no local zone or UTC offset is inferred.

The parser reads OOXML cached values, never formulas or external links. The workbook has
4,602 formulas in customer-percentage columns AJ/AK/AL; their cached values are not
recalculated. Source IDs remain strings. No source cell is changed.

There are **58** missing durations/restoration dates/restoration times, **9** missing
start dates/times, **78** zero durations, and **31** duration discrepancies greater than
one minute among 1,476 rows with all four timestamps and a duration. There are **31**
additional repeated state/start rows and no repeated `OBS` values. The discrepancy and
repeated-start sets need not be the same observations. Zero is not converted to missing;
no values are repaired or used as training targets.

An independent `openpyxl` read confirmed all 31 differences are exactly one hour:
14 are +60 minutes and 17 are −60 minutes (timestamp subtraction minus stated duration).
That pattern could reflect daylight-saving treatment; without a timezone convention it
must **not** be presented as 31 proven erroneous duration labels. The workbook's explicit
duration might be correct. The audit preserves both fields and this unresolved explanation.

The [authors' descriptor](https://pmc.ncbi.nlm.nih.gov/articles/PMC6141375/) describes
selected major outages and regional covariates, not a population-wide absence-of-outage
panel. Cause/customer totals and same-period economic or electricity summaries lack an
early-availability timestamp. Incident identity across related state records and censoring
are not established by `OBS`. Article licensing and workbook licensing are distinguished
in [SOURCES.md](SOURCES.md); that unresolved gate blocks training here.

## Zenodo · metadata and compact evidence only

[Record 22651795](https://zenodo.org/records/22651795), DOI
`10.5281/zenodo.22651795`, published September 8, 2026, modified September 30, 2026.
The API explicitly says CC BY 4.0. Advertised files include:

| Artifact | Advertised bytes | Publisher MD5 | Downloaded? |
|---|---:|---|---|
| `Eagle_I_US_2024_with_VTEC_Updated.csv` | 366,933,304 | `b47a454b0c7f2e8047e870d3167a157c` | No |
| `EAGLEI_Source_Record_Availability.csv` | 32,427,674 | `b1405e2de2cf47e5760ee054214ff7ff` | No |
| `NWS_WARNINGS_COMBINED_data_Updated.csv` | 832,283,249 | `523de61d8272fc76202270ea4c06dbd0` | No |
| Missing-data sensitivity | 232 | See acquisition receipt | Yes |
| Recovery-persistence sensitivity | 558 | See acquisition receipt | Yes |
| Temporal-aggregation sensitivity | 911 | See acquisition receipt | Yes |

Advertised hashes for unacquired files are **not independently verified**. No full-table
row count, duplicate rate, event count or eligible modeling denominator is claimed.
Downloaded compact files have both verified publisher MD5 and locally recorded SHA-256.
The descriptor was read through Europe PMC's full-text XML after the normal PMC view
was unavailable; [publisher DOI](https://doi.org/10.1038/s41597-026-08356-z).

The observation unit is a positive processed county-hour overlapping a warning. UTC is
documented here. County-local event IDs, duration, peak, warning types and source-record
availability accompany a maximum of trailing four-hour means. Missing source records are
computationally zero-filled, not verified no-outage intervals. Segmentation uses a county
75th percentile and can split at zero or absent reports. A county-local ID is not a
cross-county storm identity. The primary table omits unmatched hours, so its minimum and
maximum recorded `Hour` cannot safely reconstruct every complete physical outage.

The compact sensitivity file reports median relative differences of **0%, 18.75%, 43.75%,
75%** across descending source-availability tiers. Its denominator is processed windows,
not independent outage events. Recovery persistence is **17,060/17,060** complete-source
transitions. These are the authors' processing diagnostics, not GridGuide model errors.
They support a distinct processed-signal analysis, not a ready-made verified restoration
label. The bounded review stopped without downloading the ~1.3 GB release.
