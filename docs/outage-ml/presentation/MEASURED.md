# Measured source inventory

Generated from `evidence/source-audit.json`. Counts describe files, not independent storms.

| Year | Merged episodes | Linked rows (unlagged) | Distinct county/start keys | Repeated linked rows | Ambiguous year/event IDs |
|---|---:|---:|---:|---:|---:|
| 2014 | 13,516 | 805 | 805 | 0 | 0 |
| 2015 | 115,962 | 12,681 | 7,497 | 5,184 | 2 |
| 2016 | 116,438 | 22,097 | 7,819 | 14,278 | 1 |
| 2017 | 118,929 | 23,945 | 8,819 | 15,126 | 2 |
| 2018 | 153,442 | 36,563 | 18,694 | 17,869 | 4 |
| 2019 | 157,478 | 53,570 | 19,992 | 33,578 | 3 |
| 2020 | 166,183 | 84,875 | 28,219 | 56,656 | 6 |
| 2021 | 174,936 | 119,435 | 24,158 | 95,277 | 5 |
| 2022 | 189,149 | 94,853 | 30,954 | 63,899 | 4 |
| 2023 | 179,356 | 77,341 | 21,901 | 55,440 | 2 |

## Purdue workbook checks

| Check | Count |
|---|---:|
| Rows | 1,534 |
| Missing duration | 58 |
| duration_and_four_timestamps_present | 1,476 |
| duration_timestamp_mismatch_over_one_minute | 31 |
| nonpositive_duration_rows | 78 |
| restoration_before_start | 0 |
| Repeated state/start rows | 31 |

Missing durations are not zero durations. Timestamp agreement is an internal check, not external validation.

## Zenodo bounded inspection

Only metadata, the descriptor and three small sensitivity summaries were acquired. Full observation counts are unmeasured.

No train/development/test partition, fitted model, or held-out score exists. The feasibility gate stopped before training.
