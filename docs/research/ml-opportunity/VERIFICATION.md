# Opportunity audit verification ledger

Baseline: main `df7cb19f4df41bde0ede0f26bbe02710018f2871`; PR #21 merge verified through
GitHub and the fetched main history. Work is on `research/ml-opportunity-audit`.

| Checkpoint | Evidence | Disposition |
|---|---|---|
| Baseline and scope | Issue #22, PR21 merge, historical reports; protocol committed at `e86e29d` | PASS; no historical study reopened |
| Independent numerical audit | Schedule-derived costs, critical, p95, branch outcomes; paired duration/coverage checks; independent grouped aggregation | PASS across PR20 confirmation and PR21 dev/ID/shift |
| Restricted ceilings | Explicit policy class, all group winners/costs; both percentage estimands; independent tests | PASS: 1.85945% / 1.30358% ratio-of-means gains reproduced |
| Signal and static-task diagnostics | Every retained training label, frozen feature/model inference, static integer policy costs, archived trajectory overlaps | PASS; rare-WAIT, ties, mismatch and missing causal evidence reported |
| Fresh exact diagnostic | 12 configurations × 2 crews × 2 profiles; rational expectations; independent solver and full-world policy checks | PASS: all 48 exact expectations; not a model pilot |
| A/B/C/D gate | Ranked report, identifiable inputs/targets, observed headroom, cost and validity constraints | NO-GO for immediate training; A/B conditional future investigations; C/D NO-GO |
| Numerical reproduction | Two independent complete invocations with `--exact`; recursive directory comparison | PASS: `audit.json`, `exact.json`, `sources.json` byte-identical |
| Presentation reproduction | Two renders from independent audit outputs; recursive comparison | PASS: Markdown and PNG/SVG byte-identical; chart visually inspected |
| Previous work | New baseline preservation plus both existing preservation checkers | PASS: 1,062 baseline files, 10 Git-only data identities, 691 prior learned-study preservation entries, 115 historical frozen artifacts |
| Local tests | Counts and commands below | PASS: 280 tests; zero failures/skips |
| Final PR CI | New source-free audit lane and unchanged synthetic verification lane | Required on final PR head; authoritative run links/status recorded in the PR description |

## Executed test suites

| Suite | Interpreter / command | Executed / passed |
|---|---|---:|
| New opportunity audit | `.venv-ml/bin/python -m unittest discover -s research/ml_opportunity/tests -t . -v` | 16 / 16 |
| Learned dispatch | `.venv-ml/bin/python -m unittest discover -s research/learned_dispatch/tests -t . -v` | 21 / 21 |
| Adaptive environment | `.venv-ml/bin/python -m unittest discover -s research/adaptive_dispatch/tests -v` | 29 / 29 |
| ML I | `.venv-ml/bin/python -m unittest discover -s research/ml_lab/tests -v` | 44 / 44 |
| ML II source contracts | `.venv-ml/bin/python -m unittest discover -s research/outage_ml/tests -v` | 17 / 17 |
| Public synthetic | `.venv/bin/python scripts/run_test_lane.py --lane public --report /tmp/opportunity-public-tests.json` | 102 / 102 |
| Existing research | `.venv/bin/python scripts/run_test_lane.py --lane research --report /tmp/opportunity-research-tests.json` | 51 / 51 |

The existing learned/ML I suites execute real **temporary smoke fits** and fixture
evaluation. Those verification fixtures are separate from scientific training/evaluation
and do not reopen spent historical datasets. The new opportunity analysis itself fits
zero models. Source-dependent challenge tests are intentionally unexecuted: this task
forbids use of AEP raw data, and no challenge/product behavior changed.

Two initial ML I/II test invocations supplied `-t .` to directories without package
initializers and failed discovery before running tests. Corrected to the existing suite
commands above; all 61 tests then executed and passed. During development, an empty fixed
callback population and the historical loader's `(model, timing)` return contract were
corrected. No historical numerical definition or fixture was changed to obtain success.

## Review and limits

Evidence classification: archived measurements, recomputed statistics and preserved
file identities are **source-derived** (from fictional experiments). Fresh task graphs,
customer weights, duration supports and crew scenarios are **scenario assumptions**.
Comparator algorithms, feature rules, bootstrap choices, state caps and proposed
economic/gate thresholds are **prototype policy**. Field productivity, actual-outage
targets and incremental model-memory measurements are **unavailable**. This audit
introduces no new AEP-specified facts or customer declarations.

- Reviewed schedule-derived denominators, pairing, null handling, alias collapse,
  exact-state overlap interpretation, independent bootstrap units and the distinction
  between mean-relative and ratio-of-means ceilings.
- Exact solver chooses before public successor events are revealed; complete duration
  enumeration checks only fixed-policy expectations and is never passed into a policy.
- Reviewed the full additive diff, generated tables, figure labels and relative links.
  The chart shows point cost/latency tradeoffs; uncertainty is in paired report tables.
- Read requirements traceability and risk register; no application scope or safety
  interpretation changes. No subagent review or external blind evaluation is claimed.
- v1.0.0 remains `c2b2d37aaf5e74a03190746c12badacc6bc86369`; v1.1.0 remains
  `9b255f1c2218702f5fd07bf181582a5c7ef9e797`. No release/tag/merge/deploy action performed.
- New raw-data guard/source allowlist tests fail before opening forbidden files. The
  preservation checker inspects data Git object identities, not raw working-tree bytes.

The report records scientific limitations and conditions for a later registered study.
CI completion belongs to the exact final PR head; a green local suite alone is not
represented as a green remote run.
