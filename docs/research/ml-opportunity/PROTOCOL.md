# ML opportunity audit plan · Issue #22

Baseline: `df7cb19f4df41bde0ede0f26bbe02710018f2871`, including merged PR #21.
This is an exploratory, retrospective audit, not another untouched final evaluation.
No historical training, tuning, selection, or evaluation command is reopened.

1. Independently aggregate archived per-episode metrics, verify identical paired
   exogenous draws, and compare with published summaries. Report stochastic cohorts
   separately. Use equal configuration weights and 2,000 paired configuration
   bootstrap replicates (Python random seed 2026110422). This independent RNG means
   intervals need not exactly reproduce the historical NumPy endpoints.
2. Reproduce the three-policy hindsight ceiling both as the mean of group-relative
   improvements and as the ratio of mean costs. These are different estimands.
   Preserve group-level calculations and clearly distinguish episode hindsight.
3. Audit every archived training label: decision counts, aliases, distinct-task ties,
   margins and WAIT. Reconstruct the frozen public features for collision diagnostics
   and compare frozen-student teacher-state errors with archived on-policy errors.
   Do not turn final labels into training examples. Quantify missing evidence.
4. Audit ML I's four-policy headroom from integer costs, train/development/final
   label support and feature ranges. Preserve its original outcome units.
5. Conduct a small exact, non-clairvoyant diagnostic: 12 fresh four-task configurations,
   two crew variants, low/high finite supports. Use seed 2026110422, authored forward
   DAGs and overlapping customer requirements, independent of algorithm performance.
   Exclude historical full-problem fingerprints; their 10+ task graphs cannot equal
   these four-task graphs. Exhaustively integrate public conditional transitions,
   cap each solve at 100,000 states, cross-check optimum with the existing Bellman
   verifier and fixed-policy expectations with complete duration-world enumeration.
   This tiny diagnostic is not a representative performance test or an ML pilot.
6. Rank A/B/C/D on input/target validity, empirical value, compute and generalization.
   A pilot requires all Issue #22 conditions, including evidence of an advantage
   against an appropriately priced strong comparator. A plausible loss function
   alone is insufficient. Distinguish a conditional future study from a GO now.

Practical economics for a future study: an improvement of 2% in configuration-mean
wait versus downstream at no more than 1 ms median full callback, or teacher-quality
within 2% at least 3× faster, would be worth testing. Neither is a utility-derived
threshold. Check critical/p95 upper degradation ≤max(0.25 h, 5% reference), zero
invalid actions, and worst configuration ratio ≤1.25. These prospective planning
thresholds do not replace any historical gate or determine a retrospective victory.
Use group-level observed SD for an approximate 80%-power, two-sided 5% normal sample
size; include sensitivity to doubled SD. This is budget planning, not a power guarantee.

If no opportunity clears the gate, fit zero new models and publish NO-GO for an
immediate pilot, with explicit conditions to reopen. If one clears it, commit a
separate bounded pilot protocol before generating/fitting new train/dev data.
No new final set will be opened in this issue.

Implementation uses standard-library statistics and JSON/gzip. Frozen feature/model
adapters reuse the existing pinned environment; no new dependencies. All analysis
runs inside the existing raw-data/network-denying guard. Output must be outside
historical directories. Hash every consumed artifact, preserve baseline tracked
files, test math against analytic examples, regenerate evidence twice, and run the
existing relevant source-free suites. One PR; no merge, release, tag or deployment.
