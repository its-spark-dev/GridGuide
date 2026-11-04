# Independent implementation review

Independent coding subagents reviewed design/contracts and the feature, label,
model, metric and holdout implementation before full-data training. This is code
review by collaborating agents, **not externally independent scientific evaluation**.
Reviewers did not access scientific final policy outcomes.

Material findings addressed before the scientific input/model freeze:

- Preserve the frozen benchmark contract through an ML lineage wrapper.
- Compare labels in exact integer customer-seconds, retain all policy ties, and
  require complete task scope as well as known customer releases.
- Reject shortened predictions or eligible-case abstentions; paired comparisons
  must use every eligible case rather than dropping difficult rows.
- Require explicit training partition provenance for every baseline-fitting row.
- Inherit denied paths through nested isolation contexts.
- Refuse model selection after an evaluation receipt spends a scientific cohort.
- Create an exclusive receipt before final labels; changing output directories
  cannot bypass a spent-cohort check, including after a failed evaluation.
- Bind serialized model paths and hashes to the frozen inventory before loading;
  require matching Python and package versions for the scientific replay.

Tests exercise each guard, source/network denial, malicious artifact paths,
metric corruption, metadata leakage and missingness. Serialized model files are
trusted repository-owned artifacts. Hash verification establishes consistency;
it cannot make arbitrary third-party joblib files safe to load.
