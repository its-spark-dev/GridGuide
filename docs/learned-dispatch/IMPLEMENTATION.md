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
| 5: development/freeze | 1,440 method-episodes; forest-depth4 champion, ridge-alpha10 linear winner | Selection complete; commit and freeze before reveal |
| 6: final ID/shift | One spent-cohort receipt, paired same-draw evaluation, no retuning | Pending |
| 7: showcase | Trained artifacts, coefficients/importances, runnable example, verified figures | Pending |
| 8: delivery | Local/source-free CI, previous-artifact preservation, one unmerged PR | Pending |

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
peak RSS. Development evaluation took 136.674 s across four measured commands.

Development stochastic configuration-mean waiting: forest-depth4 14.363986 h,
forest-depth8 14.494520 h, ridge-alpha10 14.553853 h, ridge-alpha1 14.614378 h,
ridge-alpha0.1 14.666755 h. Median teacher: 13.871175 h; reactive downstream:
14.414876 h. The champion is therefore forest-depth4 under the preregistered full-rollout
selection rule, despite its lower training fit than the deeper forest. These development
findings do not establish held-out promotion; no feature/model/threshold was changed.
