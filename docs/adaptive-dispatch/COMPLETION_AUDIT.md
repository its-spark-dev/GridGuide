# Adaptive dispatch requirement audit

Scientific and implementation requirements are verified below. Final-head GitHub checks on [PR #20](https://github.com/its-spark-dev/GridGuide/pull/20) are additionally required before owner handoff. This matrix tracks the original research brief,
including its conditional learning requirement; a negative gate is not permission
to omit the environment, baselines, measurements, verification or final PR.

| Requirement | Authoritative evidence | Current disposition |
|---|---|---|
| Audit G2/G3/G5 and both prior ML studies | `FOUNDATIONS.md`, source review; historical studies treated separately | Complete |
| Review online/event-driven learning and stochastic crew-dispatch literature | Primary-source links and design consequences in `FOUNDATIONS.md` | Complete |
| New isolated event environment | `environment.py`; no application imports of adaptive research | Implemented, tests pass |
| Current time, completed/active work, crews, prerequisites, remaining dependencies, known characteristics | Frozen `Observation` / `PublicProblem`; elapsed time and remaining dependency sets derivable without future data | Implemented, tests pass |
| Valid task/crew action or wait, hidden future | Strict `step`, frozen public-only callback, future-intervention invariance tests | Implemented, tests pass |
| Reproducible declared stochastic assumptions and paired streams | Independent keyed durations, corrected pre-benchmark distribution, episode namespace tests | Implemented, tests pass |
| Prerequisites/capacity/no overlaps/nonpreemption/blocked scope/release accounting | Independent trajectory checker and G2 complete schedule/metric validation | All 29,880 scientific episodes pass full independent schedule/metric audit |
| Six required comparator categories | Eight fixed controls, five reactive rules, two online searches | All 15 executed on both complete scientific cohorts |
| Small-instance exhaustive verification | Rational Bellman recursion; exact expected serial/parallel/arrival and deliberate-wait fixtures | Complete for bounded tiny fixtures |
| Real adaptive value and learning headroom, not weak baselines | Discovery-selected fixed/reactive/cheap-search comparators; frozen confirmation gate | Complete: adaptive-value gate passes; teacher-headroom gate fails |
| Runtime, outcome, failure and generalization analysis | Immutable episodes/timings, grouped report renderer, explicit untested regimes | Complete: report, three figures, family/worst-case failures, local resources |
| Bounded genuine learned policy if opportunity passes | Protocol defines contextual action-cost models, train/dev/final isolation and rollout guards | Not applicable after failed opportunity gate; no model or learned-benefit claim |
| Stop before expensive learning if no opportunity | Immutable gate and required negative-result documentation | Complete: no model fitting; explicit recommendation against full RL |
| Reproduction and CI | `REPRODUCE.md`, new scoped source-free workflow, real smoke/replay | Source-free Linux smoke, complete numerical audit and figure regeneration passed on implementation head; final PR checks authoritative |
| Preserve all previous research, application behavior, permissions and releases | Diff restricted to adaptive additions; final historical hashes/tests and remote state | 115 frozen hashes pass; protected paths unchanged; 29 adaptive + 349 existing tests and 115 frozen hashes pass; Synthetic verification passes |
| One reviewable PR; no merge/tag/release/deployment | Dedicated branch `feat/adaptive-dispatch` | PR #20 open and unmerged; no tag/release/deployment |

Executed initial hardening: 29 adaptive tests pass; separate engineering smoke ran
720 method-episodes and reproduced every policy outcome exactly. Scientific discovery
ran 6,120 method-episodes and passed full independent schedule/metric/grouped-summary
audit. Discovery selections were committed at `c14d108` before confirmation started.
No scientific conclusion is inferred from smoke or from discovery alone.

Confirmation completed 23,760 method-episodes and passed the full independent audit.
The learning gate fails because the teacher improvement is 0.112838% with an interval
crossing zero, below the predeclared >=1% positive-interval requirement. Training,
student feature/model selection, final student/shift cohorts and RL are intentionally
not invoked under the original conditional scope; their absence is not claimed as
a trained-model result. PR #20 is open and both implementation-head workflows passed. Final documentation-head checks are verified on the PR before owner handoff.

Implementation-head CI evidence: [Adaptive dispatch](https://github.com/its-spark-dev/GridGuide/actions/runs/41871356203)
and [Synthetic verification](https://github.com/its-spark-dev/GridGuide/actions/runs/41871356053),
both success at `eb89e35b646989660950efc79a6742959485f2eb`. The final changes clarify
runtime denominators and record delivery evidence; they do not change numerical code,
inputs, decisions, outcomes, comparator selection or acceptance criteria.
