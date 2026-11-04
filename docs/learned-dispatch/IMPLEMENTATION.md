# Learned dispatch implementation ledger

New prospective study, based on merged PR #20 at `740e7ec03c618b9bcb73f0c11a7ccc63a5eb5de9`.
Branch: `feat/learned-dispatch-v1`. The new owner brief makes real training and working
learned inference mandatory, independently of scientific promotion.

| Phase | Evidence / next verification | Status |
|---|---|---|
| 0: baseline and protocol | PR #20 merge verified; prior adaptive/ML I/ML II findings reviewed; new protocol | Registered before new data/fitting |
| 1: inputs and seal | 112 fresh groups / 224 variants; 48/16/24/24 split; 276 historical topology signatures excluded | Generated and input-validated before scientific fitting |
| 2: teacher data | Genuine median-root action costs; pure/mixed training trajectories | Smoke verified; scientific collection next |
| 3: fitted models | Three Ridge + two random-forest candidates; actual learned JSON exports | All five genuinely fitted in smoke; scientific fitting next |
| 4: inference | Validated public state, action masks, hash-verified loader, safe fallback | Complete stochastic smoke rollouts pass |
| 5: development/freeze | Complete rollouts, family winners/champion, committed identities | Pending |
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
