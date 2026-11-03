# GridGuide documentation

Start with the [project overview and walkthrough](../README.md). This index separates implementation references from dated development records; it does not replace source code or the model specification.

## Understand the implementation

| Document | Read it for |
| --- | --- |
| [Architecture](ARCHITECTURE.md) | Service boundaries, modules, privacy, startup preparation, and request flow. |
| [Model specification](MODEL_SPEC.md) | Authoritative formulas, evidence classes, units, scenario assumptions, golden values, and unavailable operational facts. |
| [Q2/Q4 decision support](Q2_Q4_DECISION_SUPPORT.md) | Source validation, reverse membership, four-candidate ranking, spatial hypotheses, and crew scheduling. Its checkpoint counts and handoff notes are historical. |
| [AI explanations](AI_EXPLANATIONS.md) | Approved references, result binding, server-rendered claims, and deterministic fallback. |
| [Customer integration](CUSTOMER_INTEGRATION.md) | Preparation, optional declarations, communication lifecycle, and preview eligibility. |
| [Geographic map](GEOGRAPHIC_MAP.md) | Generalized map contract, CRS checks, offline vectors, and tile attribution. |

## Inspect the evidence

- [Data audit](DATA_AUDIT.md) and [schema inventory](DATA_SCHEMA.md): pinned source provenance and coverage limits. The audit describes the initial inspection; later complete-path counts are in the model specification.
- [AEP interpretation ledger](AEP_REALIGNMENT.md): what the supplied guide explicitly establishes and what remains an assumption.
- [Requirements traceability](REQUIREMENTS_TRACEABILITY.md) and [risk register](RISK_REGISTER.md): implemented scope and unresolved evidence.
- [November 3 portfolio verification](releases/VERIFICATION.md): current test/build results and claim-to-source references.

## Run, review, and release

- [Local setup](../README.md#getting-started), [optional Gemini configuration](GEMINI_PROVIDER.md#local-credential-and-launch-setup), and [browser test harness](../frontend/tests/README.md).
- [Contributing](../CONTRIBUTING.md) and [third-party materials](../THIRD_PARTY_NOTICES.md).
- [v1.0.0 release draft](releases/v1.0.0.md), [owner checklist](releases/CHECKLIST.md), and [data/history audit](releases/PUBLIC_RELEASE_AUDIT.md).
- [Authentic screenshots and provenance](media/v1.0.0/README.md).

## Historical development records

These retain the team's original investigation, decisions, and checkpoint evidence. References to uncommitted work, old test totals, screen order, temporary files, or provider latency describe the time of writing, not the current checkout.

| Record | Historical purpose |
| --- | --- |
| [Challenge requirements](CHALLENGE_REQUIREMENTS.md) | Original brief interpretation and pre-implementation planning. |
| [Execution and handoff](EXECUTION_PLAN.md) | Ownership, integration gates, and remaining evidence work. |
| [Demo freeze](DEMO_FREEZE.md) | Successive implementation checkpoints and dated live-provider results. |
| [Judge-facing UX checks](JUDGE_UX_HARDENING.md) | Competition demo script, wording checks, and hostile-question exercises. |
| [Customer product redesign](CUSTOMER_PRODUCT_REDESIGN.md) | Customer journey design and implementation verification. |
| [Gemini provider notes](GEMINI_PROVIDER.md) | Provider configuration plus October 24 discovery, pricing observations, and live checks; current availability is not guaranteed by those observations. |
| [Frontend visual reference](../frontend/AEP_UI_REFERENCE.md) | Historical visual research, not endorsement or permission to use AEP branding. |

The last known hackathon-period checkpoint is `bb7c53ce2e0733c6770c9de631a75df094407727`; the exact submitted SHA is unconfirmed. The v1.0.0 documentation pass does not implement future v1.1.0 work or include a private competitive retrospective.
