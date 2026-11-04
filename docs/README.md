# GridGuide documentation

Start with the [project walkthrough](../README.md#product-walkthrough) or [local setup](../README.md#getting-started). For a technical review, read the architecture, model specification, and verification record in that order.

## Architecture & system design

| Reference | What it explains |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | Service boundaries, API routes, startup preparation, public outputs, and request lifecycle. |
| [Grounded explanations](AI_EXPLANATIONS.md) | Deterministic calculations, constrained AI reference selection, result binding, and fallback. |
| [Customer guidance](CUSTOMER_INTEGRATION.md) | Session-only declarations, preparation rules, and preview-only communication. |
| [Geographic map](GEOGRAPHIC_MAP.md) | Generalized map contracts, coordinate systems, offline vectors, and tile attribution. |

## Data & evidence

| Reference | What it explains |
| --- | --- |
| [Source audit](DATA_AUDIT.md) | Pinned source provenance, joins, missing data, and the progression from initial inspection to validation. |
| [Schema inventory](DATA_SCHEMA.md) | Exact field names, types, missing counts, and snapshot coverage. |
| [AEP interpretation ledger](AEP_REALIGNMENT.md#evidence-and-classification-ledger) | Which rules are supplied by AEP, source-derived, assumed, or unavailable. Earlier implementation plans remain historical. |
| [Data distribution findings](releases/PUBLIC_RELEASE_AUDIT.md#findings) | Recorded identifier, coordinate, inferred-field, metadata, and permission concerns. Retaining the data did not resolve these findings or add a license grant. |
| [Third-party materials](../THIRD_PARTY_NOTICES.md) | Source, dependency, font, and map notices; project license status. |

## Models & scenarios

| Reference | What it explains |
| --- | --- |
| [Model specification](MODEL_SPEC.md) | Authoritative risk interpretation, labor units, elapsed-time assumptions, formulas, and golden values. |
| [Repair decisions and crew scenarios](Q2_Q4_DECISION_SUPPORT.md) | Reverse dependencies, spatial hypotheses, priority tradeoffs, overlap removal, and scheduling. |

## Verification & limitations

| Reference | What it establishes |
| --- | --- |
| [v1.0.0 verification](releases/VERIFICATION.md) | November 3 test/build results, environment, and claim-to-source references. |
| [Requirements coverage](REQUIREMENTS_TRACEABILITY.md) | Implemented behavior and unresolved evidence for each challenge requirement. |
| [Risk register](RISK_REGISTER.md) | Limits on prediction, operational validity, source interpretation, and runtime privacy. |
| [Browser test harness](../frontend/tests/README.md) | Reproducible fixtures, ports, offline checks, and accessibility test scope. |
| [Screenshot provenance](media/v1.0.0/README.md) | Authentic capture states, OpenStreetMap loading checks, and image hashes. |

## Development

[Install and run](../README.md#getting-started) · [Optional Gemini configuration](GEMINI_PROVIDER.md#local-credential-and-launch-setup) · [Contributing](../CONTRIBUTING.md) · [Published v1.0.0 release](https://github.com/its-spark-dev/GridGuide/releases/tag/v1.0.0)

## v1.1.0 phased work

The [approved master roadmap](planning/V1_1_0_MASTER_ROADMAP.md) preserves the full scope and controlling refinements. G1 is approved and merged. The original Phase 1 evidence is in the [G1 checklist](planning/V1_1_0_PHASE1.md), [feasibility findings](research/phase1/FEASIBILITY.md), and [isolated catalog instructions](research/phase1/ARTIFACT_README.md). Later phases require their review gates; this is not a v1.1.0 release announcement.

## Historical development records

The original plans, checkpoints, and release records remain at their existing paths. Their test totals, working-tree status, demo scripts, and provider observations describe their dates, not pending work or current service guarantees.

<details>
<summary>Browse development and release history</summary>

| Record | Historical purpose |
| --- | --- |
| [Challenge requirements](CHALLENGE_REQUIREMENTS.md) | Original brief interpretation and pre-implementation plan. |
| [Execution and handoff](EXECUTION_PLAN.md) | Implementation ownership and integration gates. |
| [Demo freeze](DEMO_FREEZE.md) | Successive checkpoints and dated live-provider checks. |
| [Judge-facing UX](JUDGE_UX_HARDENING.md) | Competition demo script and explanation exercises. |
| [Customer product redesign](CUSTOMER_PRODUCT_REDESIGN.md) | Journey design, frontend changes, and their verification. |
| [Gemini provider observations](GEMINI_PROVIDER.md) | October 24 discovery and live checks, alongside reusable setup instructions. |
| [Frontend visual research](../frontend/AEP_UI_REFERENCE.md) | Original design references and superseded UI/model snapshots. |
| [Release checklist](releases/CHECKLIST.md) | Completed publication milestones and the original approval record. |
| [Original PR body](releases/PR_BODY.md) | Preserved description for merged PR #1. |
| [Publication assessment](releases/PUBLIC_RELEASE_AUDIT.md) | Original findings and the subsequent data-retention decision; findings remain disclosed above. |
| [Release body source](releases/v1.0.0.md) | Repository copy of release prose; edits here do not update GitHub automatically. |
| [Editorial review](releases/EDITORIAL_REVIEW.md) | Post-release classification, information-retention map, and local verification. |

</details>

The [v1.0.0 snapshot](https://github.com/its-spark-dev/GridGuide/tree/v1.0.0) preserves the first release. The last known hackathon-period checkpoint is [`bb7c53c`](https://github.com/its-spark-dev/GridGuide/commit/bb7c53ce2e0733c6770c9de631a75df094407727); the exact submitted SHA is unconfirmed.

Phase 2 review: [benchmark specification](benchmarks/PHASE2_SPEC.md),
[G2 evidence and acceptance checklist](planning/V1_1_0_PHASE2.md), and
[complete baseline report](benchmarks/phase2/standard/REPORT.md). That phase introduced no optimizer.

Phase 3 review: [model](research/phase3/MODEL.md), [preregistered evaluation](research/phase3/EVALUATION_PROTOCOL.md),
[complete comparison report](benchmarks/phase3/published/REPORT.md), and
[G3 review packet](planning/V1_1_0_PHASE3.md). The optional optimizer is verified on the
synthetic suite; its 5% median promotion target was not met. Application defaults are unchanged.

Phase 4 review: [risk protocol](research/RISK_PROTOCOL.md), [No-Go findings](research/RISK_FINDINGS.md),
[recorded feasibility](research/phase4/feasibility.json), and [G4 review packet](planning/V1_1_0_PHASE4.md).
No predictive model was fitted or promoted; application behavior remains unchanged.

Phase 5 review: [simulation protocol](research/phase5/SIMULATION_PROTOCOL.md),
[complete artifact/reproduction instructions](research/phase5/ARTIFACTS.md), and
[G5 evidence and acceptance questions](planning/V1_1_0_PHASE5.md). Fixed schedules are
replayed under declared synthetic duration profiles; failed convergence checks and
paired policy regressions remain visible. No empirical calibration or default promotion
is claimed, and no API/UI integration is included.

## Customer preparedness review

[Phase 6 / G6 packet](planning/V1_1_0_PHASE6.md) covers fictional power paths, strict
snapshot storage, scoped offline caching, reproduction commands and accessibility limits.

- [Phase 7 operator review packet](planning/V1_1_0_PHASE7.md): fictional comparisons,
  structured overrides, review/export and replay; implementation awaits independent G7 approval.
