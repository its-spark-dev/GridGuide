# Learned dispatch implementation ledger

New prospective study, based on merged PR #20 at `740e7ec03c618b9bcb73f0c11a7ccc63a5eb5de9`.
Branch: `feat/learned-dispatch-v1`. The new owner brief makes real training and working
learned inference mandatory, independently of scientific promotion.

| Phase | Evidence / next verification | Status |
|---|---|---|
| 0: baseline and protocol | PR #20 merge verified; prior adaptive/ML I/ML II findings reviewed; new protocol | Registered before new data/fitting |
| 1: inputs and seal | 112 fresh groups / 224 variants; 48/16/24/24 split; 276 historical topology signatures excluded | Sealed at `4825e5d` before scientific fitting |
| 2: teacher data | 480 validated trajectories, 12,980 visits, 5,352 unique discretionary states, 24,240 action rows | Complete; exact state/visit lineage retained |
| 3: fitted models | Three Ridge + two random-forest candidates; actual learned JSON exports | Complete; all five exact repeat-fit exports; zero dev export-parity error |
| 4: inference | Validated public state, action masks, hash-verified loader, safe fallback | Scientific development: no invalid actions or fallback |
| 5: development/freeze | 1,440 method-episodes; forest-depth4 champion, ridge-alpha10 linear winner | Selection committed `230f0f4`; freeze committed `7161a86` before reveal |
| 6: final ID/shift | One spent-cohort receipt, 5,184 held-out method-episodes, paired draws, no retuning | Complete; promotion FAIL in both cohorts |
| 7: showcase | Trained artifacts, model card, runnable example, four PNG/SVG figures and measured report | Complete; independently regenerated twice, all 12 presentation files identical |
| 8: delivery | 460 local tests; full scientific audit; 691 old files and 115 frozen artifacts verified | Local checks complete; final PR-head CI required |

Reused numerical code remains in its historical packages. The new package may call it
but may not modify PR #20's frozen protocol, source or evidence. The previous no-training
conclusion stays intact; this study intentionally asks a separate distillation question.

## Pre-scientific implementation verification

- 18 new tests passed, including real fits/export parity/repeat fitting, hand-valued features,
  future interventions, identity invariance, exact teacher costs, crew-alias equivalence,
  complete trajectories, hash/structure corruption, development selection and final resumption.
- Separate `smoke` run fitted all five candidates on 1,010 action rows; independently audited
  108 development, 72 final-ID and 72 shifted method-episodes. These are engineering fixtures,
  not scientific performance evidence. Output: ignored `artifacts/learned-dispatch-smoke-1`.
- Input identity: `6b8cac24a1d8c2910b5bdb9ddded365d5d904df7163ff737becae0373cadaf7b`.
  Final scientific inputs contain no outcomes and remain unopened by modeling commands.
- Tiny constant-column weighted-scaler smoke fits emitted scikit-learn's roundoff variance
  warning; its constant-feature handling returned finite scales and all export/fit checks
  passed. No warning was hidden and no model result was substituted.

## Scientific training and development

Scientific collection took 23.373 s summed over configuration shards. The fitting pipeline,
including repeat fits and development export-parity probes, took 24.444 s with 278.0 MiB
peak RSS. Development evaluation took 136.674 s across four measured batch invocations.

Development stochastic configuration-mean waiting: forest-depth4 14.363986 h,
forest-depth8 14.494520 h, ridge-alpha10 14.553853 h, ridge-alpha1 14.614378 h,
ridge-alpha0.1 14.666755 h. Median teacher: 13.871175 h; reactive downstream:
14.414876 h. The champion is therefore forest-depth4 under the preregistered full-rollout
selection rule, despite its higher training error than the deeper forest. These development
findings do not establish held-out promotion; no feature/model/threshold was changed.

## Frozen final findings

Each final cohort contains 24 configurations, 48 variants and 432 episodes per method;
384 stochastic episodes per method form the primary estimand. Six methods produce 2,592
method-episodes per cohort. The same frozen champion and criteria were used throughout.

| Champion / median teacher | Final ID | Shift |
|---|---:|---:|
| Mean-wait ratio | 1.032246 [1.022555, 1.042162] | 1.046580 [1.032165, 1.062510] |
| Teacher/student configuration-median speed ratio | 3.846970 [3.245973, 4.485699] | 7.823368 [6.451530, 9.377698] |
| Mean wait minus reactive (h) | −0.079361 [−0.342699, 0.153734] | 0.564734 [0.135028, 1.019432] |
| Failed guards | Teacher quality | Teacher quality; reactive noninferiority |
| Invalid actions / fallback | 0 / 0 | 0 / 0 |

Brackets are 95% paired configuration-bootstrap intervals. Critical, p95, support and
catastrophe screens pass, but the full conjunction fails. **No scientific promotion.**
Both model families, including all fitted candidates, remain retained and runnable.
Final ID took 272.437 s and shift 872.460 s over six measured batch invocations each.

## Final local verification

Machine-readable record: [verification.json](evidence/verification.json).

- 21 new learned-dispatch tests, including exact replay of all 12,055 retained public-state
  teacher labels and real learned inference from approved model artifacts.
- 29 unchanged adaptive environment tests; 44 ML I and 17 ML II regression tests. These
  preserve earlier studies; their scientific evaluations were not reopened or reinterpreted.
- Existing lanes: 102 public, 196 challenge-local, 51 research tests. All passed without skips.
- All 6,624 development/final method-episodes independently audited for exact coverage,
  paired exogenous draws, schedules, metrics and online trajectories; summaries regenerated.
- 691 baseline file hashes unchanged, plus exact root README preservation after removing
  the marked additive section. Raw/other data directories have no diff. Original tag objects
  remain recorded in `PRESERVATION.json`. Existing frozen checker verifies 115 artifacts.
- New authored example: SHA-verified forest returns `syn-independent` / `syn-crew1`, and
  a complete five-task stochastic episode passes independent validation with zero fallback.
- Four source-bound PNG/SVG figures visually inspected. Two independent report regenerations
  match across all 12 files. Actual coefficients/impurity importance, interval definitions,
  action imbalance, worst episodes and negative findings are explicit.

Added `.github/workflows/learned-dispatch.yml` for source-free Linux tests, genuine smoke
fitting and both final paths, committed scientific audits, actual-model inference, historical
preservation and report replay. The existing synthetic CI lane remains untouched and must
also pass on the final PR head. Local evidence is not reported as remote CI success.
