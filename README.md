# GridGuide

**Understand the outlook. Prepare for an outage. Inspect the decisions.**

GridGuide connects customer preparedness with explainable restoration planning in one
outage concierge: **Overview → Prepare & alerts → Grid insights**. Explore what a repair
scenario means, follow the dependencies behind it, and see how different priorities
change a restoration plan.

![GridGuide Overview with fictional scenario selection, conditional repair timing and links to preparedness and grid insights](docs/media/v1.1.0-integrated/01-overview.png)

[Watch the 4:44 demo](docs/media/v1.1.0-integrated/README.md) ·
[Explore the product](#product-walkthrough) · [Run locally](#getting-started) ·
[Architecture](#architecture) · [Research evidence](docs/benchmarks/v1.1.0.md)

Built for the **AEP AI Outage Concierge Challenge at HackOHI/O 2026**, then extended into
a reproducible portfolio project. The current **v1.1.0 release candidate** offers a
self-contained fictional demonstration without utility data or AI credentials.
It is not a live outage service or a utility-confirmed restoration forecast.

## From uncertainty to a practical next step

An outage raises connected questions: *What could happen? What is holding up restoration?
How should I prepare? Why would one repair come before another?* GridGuide brings those
questions into a shared experience, with the evidence and assumptions visible alongside
the answer.

The original challenge-local application explores a vetted anonymous location using
pinned challenge sources. The public fictional demo makes the dependency, preparedness
and decision-review workflows accessible without those records. It explicitly leaves
household risk and geographic context unavailable where the evidence cannot support them.

## Product walkthrough

### Overview — understand the scenario

Start with a fictional service scenario and explore its prepared repair milestones.
Inspect the power path to see which dependencies are complete, blocked or unresolved.
**Ask GridGuide** explains the selected result using deterministic, result-bound answers.
Unknown completion stays unknown rather than becoming a finite restoration estimate.

![Overview power-path inspection showing a completed fictional transformer, its upstream dependencies and the evidence behind its state](docs/media/v1.1.0-integrated/03-completed.png)

The timing card shows conditional modeled completion, not a utility ETR or calibrated
confidence interval. **Prepare now** carries the selected scenario and milestone into
preparedness, so the customer can continue from the same example.

### Prepare & alerts — keep useful guidance close

Read, print or download the generic safety kit. Explicitly enable offline access and
save a non-sensitive fictional snapshot to revisit later—even after a browser restart
without network access. Saved snapshots show their timestamp and historical status;
users can open, delete or reset them.

![Prepare & alerts page with the generic preparedness kit, print and download actions, and page navigation](docs/media/readme/preparedness-desktop.png)

The offline experience is limited to preparedness and saved snapshots; it does not
recalculate results or show live outage information. Browser storage can be evicted.
Despite the navigation label, the public demo sends no alerts: tailored guidance and
communication previews belong to authorized challenge-local mode.

### Grid insights — compare, question and review

Move from the customer journey into a **separate fictional operator exercise**. Compare
FIFO, customer-count, release/person-hour and critical-proxy-first policies under the
same assumptions. See how repair order affects modeled customer waiting, critical-service
latency and fairness. Completed customer-hours and restricted-horizon customer-hours
remain distinct, with unresolved and censored outcomes visible.

![Grid insights comparing four repair policies, including customer-hours, critical-service latency, fairness and unresolved outcomes](docs/media/v1.1.0-integrated/10-policies.png)

Add a supported precedence constraint, inspect the Python-recomputed plan, acknowledge
its limitations and export JSON plus a readable summary. Changed settings invalidate
review. The export can be replayed locally; checksums establish consistency, not reviewer
identity or a tamper-proof audit trail. Nothing dispatches crews or confirms restoration.

[Captioned walkthrough and screenshot provenance](docs/media/v1.1.0-integrated/README.md) ·
[Additional preparedness capture](docs/media/readme/README.md) ·
[Mobile view](docs/media/v1.1.0-integrated/mobile-preparedness.png)

## From HackOHI/O to v1.1.0

The three-person HackOHI/O project established the connected customer and operator
journey: geographic context, an explainable ordinal concern band, conditional restoration
ranges, crew/access scenarios, preparation and communication previews. Those features
remain in the original application; v1.1.0 preserves its visual identity and navigation
while adding independently authored fictional examples, offline preparedness, validated
policy comparisons and reproducible review exports.

**The two modes have different evidence and capabilities:**

| Product area | Public fictional demonstration | Authorized challenge-local application |
| --- | --- | --- |
| Overview | Prepared milestones, declared power paths and deterministic explanations | Generalized geographic context, source-validated dependencies, ordinal concern band and conditional labor-based range |
| Scenario controls | Approved examples, including blocked and missing-evidence cases | Crew-size and access changes; separate crew-count controls in repair planning |
| Prepare & alerts | Generic kit, offline access and explicitly saved fictional snapshots | Scenario-tailored preparation, optional session-only declarations and four communication previews; nothing is sent |
| Grid insights | Eight fictional cases, four baselines, bounded precedence overrides and review/export | Four curated repair candidates, two prototype priority policies, source evidence and conditional crew scheduling |

Challenge-local mode requires permission to use the pinned source files. Its concern
band is not an outage probability, and its restoration envelope is not a guaranteed
completion time. The fictional demo does not reproduce source-backed maps, risk scores,
arbitrary crew/access recalculation or tailored communications with invented inputs.

[Original v1.0.0 release](https://github.com/its-spark-dev/GridGuide/releases/tag/v1.0.0) ·
[Original product screenshots](docs/media/v1.0.0/README.md) ·
[Detailed feature comparison](docs/planning/V1_1_0_CONTINUITY.md#feature-level-comparison)

## Architecture

**React/TypeScript presents the experience; one FastAPI/Python service owns numerical
rules and validation.** Prepared immutable inputs and versioned contracts connect the
two. There is no database or browser copy of the numerical engine.

- **Explain validated results.** Public Standard explanations use approved frame values
  and reviewed text. The preserved challenge-local AI adapter can select approved
  references; it cannot calculate risk or restoration times. Standard answers work
  without an external model.
- **Validate schedules independently.** Check prerequisites, crew conflicts and customer
  release before presenting a comparison. Keep assumptions, nulls and tradeoffs visible.
- **Bind review to the result.** Scenario revisions and fingerprints reject stale or
  mismatched responses and make exported fictional cases reproducible.
- **Distribute only approved inputs.** An explicit allowlist packages fictional data,
  compiled UI and the Python runtime code without challenge records, credentials or
  Git history. Scoped offline caching excludes API responses and sensitive declarations.
- **Verify the real application.** Public CI exercises the extracted package and container,
  browser journeys, export replay and preserved evidence hashes. Source-dependent tests
  are reported unavailable when their data is absent, never counted as passed.

[Architecture and API boundaries](docs/ARCHITECTURE.md) ·
[Model specification](docs/MODEL_SPEC.md) · [Explanation design](docs/AI_EXPLANATIONS.md)

## Research findings and reproducibility

Frozen scenarios, independent validation and reproducible reports make unsuccessful
experiments as inspectable as successful ones:

- **Optimization:** the preregistered 5% median promotion target failed. The strongest
  fixed release/person-hour baseline remains the default; CP-SAT is optional and
  experimental, with only frozen validated results exposed in the public comparison.
- **Outage prediction:** the acquired evidence led to a No-Go for supervised modeling.
  No trained predictor or validated outage probability is claimed. This is an evidence
  limit, not a conclusion that all public-data research is infeasible.
- **Restoration uncertainty:** assumption-based fixed-timetable simulation retains all
  15 unstable convergence findings. It is not empirically calibrated restoration
  confidence, and detailed uncertainty visualization is not integrated into the product.

The [complete evidence report](docs/benchmarks/v1.1.0.md) retains numerical results,
denominators, regressions, timeouts and limitations. The
[reproduction guide](docs/REPRODUCING_V1_1.md) connects each result to its inputs and commands.

<a id="quick-start"></a>

## Getting started

**Try the fictional package first.** Follow the [acquisition and inspection guide](docs/REPRODUCING_V1_1.md#acquire-and-inspect-the-standalone-package)
to download the standalone ZIP from a successful **Synthetic verification** CI artifact
and verify it against the [reviewed package manifest](docs/media/v1.1.0-integrated/package.json).
CI artifacts expire; the guide includes a source-free build fallback. There is no
published v1.1.0 GitHub Release or hosted service yet.

From the **clean extracted package**, with Python 3.12:

```sh
python3.12 -m venv /tmp/gridguide-runtime
/tmp/gridguide-runtime/bin/pip install --require-hashes -r deploy/requirements.lock
PYTHONDONTWRITEBYTECODE=1 /tmp/gridguide-runtime/bin/python deploy/serve.py
```

Open **http://127.0.0.1:8000/**. Keep the environment and downloaded exports outside the
immutable package. Installation needs network access; installed local operation needs
no external service. [Docker instructions](docs/REPRODUCING_V1_1.md#container-path) use the
same inspected extraction, never a broad repository copy.

For the preserved original application, use the
[v1.0.0 setup instructions](https://github.com/its-spark-dev/GridGuide/blob/v1.0.0/README.md#getting-started)
with authorized pinned challenge sources. That mode is separate from the fictional package.

<a id="verify"></a>

**Explore further:** [verification and replay commands](docs/REPRODUCING_V1_1.md) ·
[documentation guide](docs/README.md) · [release-candidate notes](docs/releases/v1.1.0.md) ·
[contributing](CONTRIBUTING.md).

## Contributors, attribution and scope

GridGuide was built collaboratively by **three teammates** at **HackOHI/O 2026,
October 24–25**. Original team achievements, pipeline guidance and pole-replacement work
remain preserved. [Contributor history](https://github.com/its-spark-dev/GridGuide/graphs/contributors)
records the work; individual roles are not inferred from commit counts. The last known
hackathon checkpoint is [`bb7c53c`](https://github.com/its-spark-dev/GridGuide/commit/bb7c53ce2e0733c6770c9de631a75df094407727);
the exact submission SHA is unconfirmed. Later independent v1.1.0 improvements are
traceable through [reviewed pull requests](https://github.com/its-spark-dev/GridGuide/pulls?q=is%3Apr+is%3Amerged)
and do not reassign original teammate contributions.

This is an independent portfolio project with no AEP endorsement or utility deployment
claim. It provides no real alerts, arbitrary-address lookup, field dispatch, switching
advice or operational safety certification. Testing covers Chromium; detailed manual
VoiceOver observations and cross-browser behavior remain unverified. Offline storage
and same-origin trust limitations, retained dependency advisories and unexecuted OS CVE
scanning are documented in the [release limitations](docs/releases/v1.1.0.md#security-privacy-and-scope).
Future public hosting requires a current vulnerability assessment and host-security review.

No project-wide software license has been selected, and challenge-data permissions remain
unresolved. The source-free package does not remove historical repository exposure or
grant redistribution rights. See the [publication audit](docs/releases/PUBLIC_RELEASE_AUDIT.md#findings)
and [third-party notices](THIRD_PARTY_NOTICES.md).

v1.1.0 is intended as the final major feature release, with reproducible artifacts
preserved for later review. No service/support SLA or ongoing maintenance is promised.
[Requirements coverage](docs/REQUIREMENTS_TRACEABILITY.md) · [Risk register](docs/RISK_REGISTER.md).
