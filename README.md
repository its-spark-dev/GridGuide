# GridGuide

**Inspect dependencies. Compare restoration policies. Prepare for an outage.**

GridGuide is an evidence-driven restoration decision-support portfolio project, originating
as a three-person **AEP AI Outage Concierge Challenge** entry at **HackOHI/O 2026**.
The **v1.1.0 release candidate** adds a self-contained fictional demonstration that runs
without challenge data, provider credentials or an internet connection after installation.
It is a research demonstration—not a utility service, dispatch tool or live outage feed.

![Integrated GridGuide overview using approved fictional inputs](docs/media/v1.1.0-integrated/01-overview.png)

[Demonstration](docs/media/v1.1.0-integrated/README.md) · [Quick start](#quick-start) ·
[Evidence report](docs/benchmarks/v1.1.0.md) · [Reproduce it](docs/REPRODUCING_V1_1.md) ·
[Release-candidate notes](docs/releases/v1.1.0.md)

## Product walkthrough

- **Start with your storm outlook.** The original dashboard layout connects Overview,
  Prepare & alerts and Grid insights. Select approved fictional scenarios and ask
  questions about their repair milestones. Household risk and geographic context
  remain explicitly unavailable in this source-free demonstration.
- **Understand a fictional power path.** Inspect declared dependencies and prepared repair
  milestones. Completed, blocked and unresolved states remain distinct; unknown completion
  never becomes a finite restoration estimate.
- **Compare policies fairly.** Eight operator examples compare FIFO, customer-count,
  release/person-hour and critical-proxy-first under identical assumptions. Python owns
  calculations; an independent validator checks schedules and customer release.
- **Review the tradeoff.** Add a bounded precedence constraint, inspect recomputed results,
  acknowledge limitations and export JSON plus a readable summary. Replay the JSON locally.
  Changed settings invalidate review. Checksums verify consistency, not reviewer identity.
- **Prepare offline.** Explicitly install generic safety guidance and save a non-sensitive
  fictional snapshot. It stays timestamped and historical. Browser restart without network
  is supported; operator calculation still requires Python. Storage can be evicted.

![Grid insights in the integrated release candidate](docs/media/v1.1.0-integrated/10-policies.png)

The public demo uses independently authored fictional inputs, not anonymized customer
records. The original challenge-local map, ordinal concern band, conditional labor model,
optional grounded explanations and communication previews remain preserved separately.
That original journey requires authorized pinned challenge sources; see the
[v1.0.0 release](https://github.com/its-spark-dev/GridGuide/releases/tag/v1.0.0).

## Engineering and research

One **FastAPI/Python** service owns numerical rules and validation; **React/TypeScript**
renders version-bound results. No database or browser numerical engine is required.
The source-free distribution uses an explicit allowlist, pinned dependency hashes,
nonroot container, production browser tests and public CI. Original data and external
AI are excluded. [Architecture](docs/ARCHITECTURE.md) · [Model specification](docs/MODEL_SPEC.md).

The strongest fixed **release/person-hour baseline remains the default**. Optional CP-SAT
is a validated frozen experiment: the preregistered **5% median promotion target failed**.
Combined best-of-four plus CP-SAT achieved 0.351% mean improvement versus fixed, while
incremental improvement beyond best-of-four was 0.174%; these are not additive. Secondary
critical-service and fairness regressions remain visible.

Prediction research concluded an evidence-bounded **No-Go**, not universal infeasibility.
No validated household outage probability was produced. Offline simulation reports
preserve **195 stable and 15 unstable** convergence combinations under synthetic assumptions;
no empirically calibrated restoration confidence or detailed simulation UI is claimed.
[Complete results, denominators and limitations](docs/benchmarks/v1.1.0.md).

## Quick start

Download the inspected ZIP from the successful candidate PR's **Synthetic verification**
CI artifact and verify its hash against the [candidate manifest](docs/media/v1.1.0-integrated/package.json).
This is a release candidate, not a published v1.1.0 Release. See the
[acquisition and inspection steps](docs/REPRODUCING_V1_1.md) for exact paths and build fallback.
From the **clean extracted package**, with Python 3.12 available:

```sh
python3.12 -m venv /tmp/gridguide-runtime
/tmp/gridguide-runtime/bin/pip install --require-hashes -r deploy/requirements.lock
PYTHONDONTWRITEBYTECODE=1 /tmp/gridguide-runtime/bin/python deploy/serve.py
```

Open **http://127.0.0.1:8000/**. Keep the environment and downloaded exports outside the
immutable package. Dependencies require network access to install; installed operation
needs no external service. A Docker path and fully tested reproduction commands are in
[the guide](docs/REPRODUCING_V1_1.md). Do not build the container from a broad repository copy.

## Scope and preservation

No real alerts, switching, field dispatch, arbitrary addresses, calibrated outage risk,
new interactive CP-SAT solves, accounts or utility-confirmed ETRs. Testing covers Chromium;
detailed manual VoiceOver observations and cross-browser behavior remain unverified.
Known dependency dispositions, unexecuted OS CVE scanning and offline trust limitations
are documented in the [release notes](docs/releases/v1.1.0.md). Public hosting requires a
separate current vulnerability assessment and host-security review; no deployment or
security certification is implied.

GridGuide was built collaboratively by **three teammates** at **HackOHI/O 2026,
October 24–25**. Original team achievements, guidance and pole-replacement work remain
attributed and preserved in the pipeline and [contributor history](https://github.com/its-spark-dev/GridGuide/graphs/contributors).
Individual roles are not inferred from commit counts. The last known hackathon checkpoint
is [`bb7c53c`](https://github.com/its-spark-dev/GridGuide/commit/bb7c53ce2e0733c6770c9de631a75df094407727);
the exact submission SHA is unconfirmed. Later v1.1 improvements are documented in their
phased PRs; they do not reassign original teammate work.

This is intended as the final major feature release, with reproducible artifacts preserved
for later review and no service/support SLA. No project-wide software license has been
selected, and challenge-data permissions remain unresolved. The source-free package does
not remediate original records in repository history. [Third-party notices](THIRD_PARTY_NOTICES.md).

[Documentation](docs/README.md) · [Reproduction](docs/REPRODUCING_V1_1.md) ·
[Requirements](docs/REQUIREMENTS_TRACEABILITY.md) · [Risk register](docs/RISK_REGISTER.md)
