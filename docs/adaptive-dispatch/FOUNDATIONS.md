# Foundation audit and literature

## What is reusable

| Foundation | Reuse | Boundary |
|---|---|---|
| G2 `benchmarks/contracts.py` | Strict fictional DAG, disjoint customer memberships, crew availability, integer assignments | Fixed-schema provenance literals remain compatibility fields; new wrapper owns adaptive versions |
| G2 metrics and independent validation | Release after all required tasks, unresolved nulls, customer-hours, critical/branch/p95 waits | Validator assumes deterministic conditional durations; reconstruct those from sampled durations for each completed episode |
| G2 policies | Four fixed plans and their exact ranking definitions | A precomputed schedule is not a reactive policy; recalculating ranks must use only completed tasks |
| G3 `backend/optimization.py` | Feasible-incumbent discipline, independent candidate validation, bounded search principles | Deterministic CP-SAT cannot see actual future draws; no claim of optimal stochastic dispatch |
| G5 `backend/simulation.py` | Keyed per-task common random numbers; fixed crew/order replay; no double labor factor | Planned-start lower bounds prevent pulling future work forward; no adaptive action/state interface |
| ML I generator/contracts | Audited DAG mechanisms, configuration grouping, ID-invariant topology rejection | New configurations and fresh outcome/seed namespaces; do not reuse its revealed final cohort |
| ML I evaluation discipline | Train-only transforms, freeze/reveal separation, grouped uncertainty and guardrails | Its classifier chooses among four complete policies; this project selects tasks sequentially |
| ML II source audit | Evidence/availability and nonclaiming discipline | No observed-duration data is suitable or used to calibrate this fictional environment |

G3 failed its historical promotion target. G5's uncertainty profiles are authored assumptions
and retain numerical instability limitations. ML I's logistic selector failed promotion and
generalization. ML II stopped before fitting after its source review. Nothing here revises
those findings. The new use of finite independent duration supports is an explicit modeling
choice for exact verification, not a correction to or hidden reuse of G5's empirical claims
(G5 has no empirical calibration).

## Literature and design consequences

- Zhang et al. (2020), [Learning to Dispatch for Job Shop Scheduling via Deep Reinforcement
  Learning](https://proceedings.neurips.cc/paper/2020/hash/11958dfee29b6709f48a9ba0387a2431-Abstract.html),
  learns dispatching rules from graph state. This motivates task-level actions and action
  masks, not a policy-selection classifier. Its job-shop results do not establish benefit
  for customer dependency releases or stochastic repair durations here.
- Shuai et al. (2023), [Post-storm repair crew dispatch using stochastic Monte Carlo tree
  search and deep neural networks](https://doi.org/10.1016/j.ijepes.2022.108477), also available
  from [the authors' institution](https://curent.utk.edu/wp-content/uploads/2024/07/Shuai_Hang_UTK_Li_2_R0.pdf),
  combines lookahead and learning for uncertain repair-crew navigation. Its unknown damage
  locations, travel and grid physics are **not** transplanted into GridGuide. It motivates
  establishing an expensive non-clairvoyant teacher before proposing a learned surrogate.
- [Uncertainty in Stochastic Scheduling](https://cris.maastrichtuniversity.nl/en/publications/uncertainty-in-stochastic-scheduling/)
  distinguishes scheduling policies from fixed schedules and requires nonanticipation.
  Our observation contract reveals completion/elapsed time but hides realized remaining work.
- Ross, Gordon and Bagnell (2011), [A Reduction of Imitation Learning and Structured
  Prediction to No-Regret Online Learning](https://proceedings.mlr.press/v15/ross11a.html),
  addresses the distribution shift caused by a learned policy's own decisions. A pilot must
  evaluate full student rollouts on unseen configurations; high action-label accuracy alone
  is insufficient. Dataset aggregation or RL would be a later explicitly motivated study.

This is a focused review of relevant mechanisms, not a systematic literature review or a
claim to reproduce those papers' algorithms/results. The initial prototype uses bounded
root-action stochastic rollout, not AlphaZero, full MCTS, graph neural networks or RL.
