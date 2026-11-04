# Adaptive dispatch implementation ledger

Active research branch: `feat/adaptive-dispatch`, based on merged ML II PR #19.
ML I PR #18 and ML II PR #19 are completed separate studies, not tasks to repeat.

| Phase | Current evidence | Disposition |
|---|---|---|
| Foundation audit | `FOUNDATIONS.md`, reviewed G2 contracts/validation, G3 optimization, G5 fixed replay, ML I generator and ML II feasibility | Complete |
| Prospective protocol | First committed at `ed57372`; arithmetic and median-comparator clarifications recorded before scientific outcomes | Complete |
| Event environment | Public-only policy callback, conditional stochastic supports, independent trace/G2 validation | 29 unit tests passing |
| Exact verification | Expected serial cost, parallel maximum, crew arrival, deliberate wait, bounded finite-support recursion | Passing tiny fixtures |
| Benchmark engineering | Fresh grouped generator, 15 comparators, common draws, staged selection, grouped intervals, immutable receipts and audit | 720 smoke method-episodes and full policy replay pass |
| Scientific opportunity | 12 discovery + 24 confirmation configurations; both crew variants; prescribed episode counts | Not run |
| Learning pilot | Conditional on confirmation opportunity gate | Not started; no model claim |
| Final delivery | Research report, figures, CI, preservation audit, one PR | Pending |

Executed in the isolated pinned `.venv-ml` environment:

```sh
.venv-ml/bin/python -m unittest discover -s research/adaptive_dispatch/tests -v
```

The first exact expectation test caught a pre-benchmark high-distribution mean error.
The recorded correction restores the intended mean-one distribution; all 29 current
tests pass. No scientific inputs or outcomes existed at that correction.

Smoke inputs use a distinct namespace and do not support scientific conclusions.
The v1 smoke exercised 360 method-episodes. The v2 discovery and confirmation
workflow completed 360 method-episodes each; both full independent read-only policy
replays passed with identical numerical identities. These small engineering cohorts
are not the scientific opportunity gate and cannot authorize learning. Historical files and prior evidence remain unchanged.
