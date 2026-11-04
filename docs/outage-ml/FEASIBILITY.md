# Feasibility decision · outage-source-audit-v1

**NO-GO for training under the reviewed evidence, 2026-11-04.**
This decision follows actual file inspection. It is not a performance gate failure:
there has been no model fitting, development selection or final evaluation.

The brief permits a source-audit PR when target integrity, incident identity or required
rights cannot be established. That branch of the work is used here. PNNL was investigated
first; Purdue was the bounded data-bearing alternative. Zenodo was screened through its
official metadata, descriptor and three small sensitivity files, without its large data files.

| Candidate task | Valid input-time concept | Unresolved gate | Decision |
|---|---|---|---|
| A: total restoration hours at first outage report | Reported geography and calendar at first report; never eventual minima/maxima/means | PNNL contains retrospective county episodes, no first-report timestamp, coverage mask or censoring status. Its guide does not specify the observed 200-customer floor or enough segmentation logic to verify restoration endpoints. Unlagged incident membership has substantial chronology and identity defects | NO-GO |
| B: duration above a fixed threshold at first report | Same as A | Thresholding an unverified endpoint cannot repair censoring, report-time uncertainty or incident membership. No threshold was selected from target distributions | NO-GO |
| C: retrospective event-level target | Explicitly offline catalog analysis could use final information with a separate estimand | A model of recorded PNNL duration would estimate an incompletely documented processed quantity, with unvalidated independent incident groups. Predicting calendar/location from themselves or duration from its endpoint is circular. No nontrivial alternative satisfying the brief was demonstrated | NO-GO within this review |
| Purdue A/B/C | Geography/calendar could support a bounded retrospective duration study; cause and annual aggregates cannot simply be called onset-time inputs | The article is CC BY 4.0, but the linked workbook has no embedded grant and its landing page has no dataset license. Artifact-specific rights are unresolved; chronology, zero-duration and repeated-start semantics also require decisions | NO-GO pending rights and data clarification |
| Zenodo A/B | A specified completed hour, not the start of that hour, could permit a trailing signal | The primary file keeps only positive, warning-overlapping observations. Segmentation uses county empirical percentiles; source absence is computationally zero-filled and recovery is smoothed. The released schema does not expose all native endpoint observations or a cross-county storm identity | Not advanced to full acquisition/training |

### Why LIMITED-GO was not used

There are real, potentially useful observations here. PNNL's county/start keys are unique
in its merged files, and Purdue has 1,476 numeric durations. A restrictive processed-duration
study might eventually be defensible. This review does **not** prove that every such study
is impossible. It declines to certify a prediction target and independent-event test before
their definitions are established. A calendar-only regression would still require a clear
outcome, ascertainment population and evaluation unit; model simplicity does not remove
those requirements.

The PNNL 8/24-hour variants contain fewer chronology problems than the unlagged file.
They cannot be dismissed on the unlagged counts alone. Nevertheless, changing matching
windows does not supply source coverage, censoring flags or verified restoration endpoints.
An association window is not confirmation that a storm caused an episode. Deduplicating
rows and concatenating `year:event_id` would also leave 29 ambiguous unlagged IDs.

### Information cutoff and leakage ledger

| Source fields | Proposed role | Availability conclusion |
|---|---|---|
| PNNL `fips`, `state`, `county` | Geographic covariates / identity | Geographic values could be known at report; county is not a premise |
| `start_time` | Calendar candidate | Retrospectively recorded start, not a measured first-report arrival; timezone unspecified |
| `duration`, `end_time` | Candidate label and consistency check | Never predictors; arithmetic consistency is not proof of complete restoration |
| `min_customers`, `max_customers`, `mean_customers` | Whole-episode summaries | Excluded from onset predictors; no initial customer-count field supplied |
| `event_id`, `state_event`, incident start/end, `Event Type` | Audit/group candidates | Retrospective correlation; no verified global storm identity or as-of classification time |
| Grouped monthly/yearly counts, maximum duration, weighted hours | Descriptive summaries | Future information for events inside the summarized period; not event labels |
| Purdue state, postal/climate region, start date/time | Static/calendar candidates | No timezone/report-arrival metadata; identifiers stay strings |
| Purdue `OUTAGE.DURATION`, restoration date/time | Target/check only | Preserve missing and zero separately; do not silently replace discrepancies |
| Purdue cause/detail/hurricane, demand loss, customers affected | Final incident descriptors | Availability at early cutoff not established; hurricane name could help retrospective grouping only |
| Purdue monthly economic/electricity, annual population/GSP, climate anomaly fields | Context | Publication lag and vintage absent; same-period aggregates can contain future information |
| Zenodo `Hour`, `max_rolling_avg`, `source_completeness_pct` | Potential end-of-hour observations | An hourly maximum includes observations within that hour; not available at its beginning |
| Zenodo `evDur_Hr`, `evDur_day`, `Max_outage`, event completeness | Final target / summaries | Duration/day relationship is deterministic; peak and event completeness use future records |
| Zenodo `median_sum`, `new_event_no` | Segmentation threshold / local event ID | Full-record empirical segmentation is not a demonstrated train-only prospective transform |
| Zenodo warning codes/count/WFO | Co-occurrence | Matched phenomenon codes are not a unique incident identity or causal attribution |

### No experimental claims

Training/development/final samples: **not constructed**. Independent storm count:
**unverified**, not equated with row count. Models fitted: **0**. Final evaluations: **0**.
No acceptance metric, model champion, confidence interval or calibration score was fabricated.
The aggregate duration distribution is a source-quality measurement, not a blind holdout.
Future research must register a new protocol and acknowledge that these marginal summaries
have already been inspected.

### Evidence needed to reopen

For PNNL: versioned segmentation/filter code, timezone treatment, gap and year-boundary
rules, source availability, censored-versus-complete endpoint evidence, and a validated
incident crosswalk. For Purdue: an explicit workbook grant (or an author-confirmed binding
to the article's grant), resolved timestamp discrepancies and documented grouping/censoring.
For Zenodo: justify the processed estimand, recover full event boundaries, reconstruct
storm groups and prevent future-dependent segmentation from crossing evaluation boundaries.
Native EAGLE-I reconstruction is a different acquisition/preparation project, not an
implicit extension of this bounded review.

If reopened, use event-aware chronological training/development/final partitions, purge
cross-boundary incidents, fit preprocessing on training only, choose a primary metric and
freeze the evaluator before final reveal. A seasonal/regional baseline and a training median
would precede regression models; forecasting probabilities would additionally need valid
negative observations. None of those prerequisites is waived by this audit.
