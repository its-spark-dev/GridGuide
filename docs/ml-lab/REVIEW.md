# Independent implementation review

Independent coding subagents reviewed design/contracts and the feature, label,
model, metric and holdout implementation before full-data training. This is code
review by collaborating agents, **not externally independent scientific evaluation**.
Pre-freeze reviewers did not access scientific final policy outcomes.

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

## Review after the one-time final reveal

An independent coding subagent then inspected the spent final evidence. It recomputed
training fixed-policy totals, CV membership, final denominators and exact-cost regret;
verified source/model/input hashes and seal chronology; and confirmed the correct
interpretation of both failed promotion gates. It executed 41 ML tests and the complete
240-case read-only numerical replay successfully. No frozen numerical source change was
requested. The static renderer was additionally hardened to verify completed evidence
before presenting it. Code review is not independent utility outcome validation.
