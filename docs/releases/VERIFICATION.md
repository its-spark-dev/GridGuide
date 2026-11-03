# v1.0.0 portfolio verification

Date: **November 3, 2026**. Implementation baseline: `bb7c53ce2e0733c6770c9de631a75df094407727`, the last known hackathon-period checkpoint; exact submitted SHA unconfirmed. Scope: documentation and media preparation, with the existing application unchanged.

## Executed checks

| Check | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` with external AI disabled | **194 passed**, 71.057 seconds. No preexisting failures observed. |
| `npm --prefix frontend test` | **49 passed**, 57.1 seconds; installed Chrome, isolated production API fixtures, external browser requests blocked. |
| `npm --prefix frontend run build` | Passed strict TypeScript and Vite production build; no runtime edits made to obtain a pass. |
| `npm --prefix frontend run types:generate` followed by generated-file diff | Passed; `frontend/src/api.generated.ts` unchanged. No API contract changes. |
| `.venv/bin/python -m backend.demo` | Passed CLEAR, RESTRICTED, and BLOCKED golden scenarios: 11.736 repair person-hours; 16.236 restricted total person-hours; blocked complete effort/time unavailable. |
| `.venv/bin/python -m pip check` | No broken requirements found. |
| Documented backend/frontend startup | Launched the exact README commands on 8000/5173. Health endpoint, real Vite API proxy, customer 2.5–12 hour outlook, and Grid Insights comparison passed with external browser requests blocked. |
| Source hashes / validation | Existing tests and CLI verify all four pinned source hashes and source-dependent joins. No raw or processed data changed. |
| Repository/history inspection | 28 reachable commits, 371 objects, 242 unique blobs before this pass; no credential-pattern/local-key matches within the bounded scan. Sensitive-data findings remain open. [Audit](PUBLIC_RELEASE_AUDIT.md). |

Environment: macOS, Python **3.12.14**, Node **26.5.0**, npm **11.17.0**. The README recommends Python 3.12 and Node 22.12+; Vite's installed engine declaration supports Node `^20.19.0 || >=22.12.0`. The existing environment and dependencies were reused; no new dependency, framework, service, or runtime feature was introduced. A fresh install on another machine was not performed.

The browser harness uses the production `create_app` and pinned preparation. Its second in-memory fixture deliberately tests insufficient risk evidence. Portfolio screenshots use only its normal, unmodified-data fixture, with no external provider. See [browser fixture documentation](../../frontend/tests/README.md).

Live Gemini was not called during this review, and the ignored local credential was not printed or staged. Historical provider latency/pricing/model-discovery notes describe October 24 observations, not current guarantees. No calibrated prediction benchmark, real dispatch test, human usability study, or formal accessibility certification is claimed.

## Claim review

| README / release claim | Source of truth |
| --- | --- |
| 117,599 paths; 40,779 complete; 8,093 physical reverse assets | [MODEL_SPEC §1A](../MODEL_SPEC.md#1a-generalized-reverse-evidence-and-bounded-planning-catalog), [network regression](../../tests/test_network.py), [network implementation](../../backend/network.py). |
| Four candidates, 28 unique premises, one overlap | [Planning regression](../../tests/test_planning.py), [planning implementation](../../backend/planning.py), MODEL_SPEC §1A. |
| One versus 23, both 1.728 person-hours, spatial criticality caveat | [Judge explanation assertions](../../tests/test_judge_explanations.py), [planning rules](../MODEL_SPEC.md#1b-prototype-priority-crews-and-planning-time). |
| Direct labor × 4.5 once; person-hours distinct from elapsed | [MODEL_SPEC §3–4](../MODEL_SPEC.md#3-direct-labor-and-person-hours), [AEP model tests](../../tests/test_aep_model.py). |
| Blocked access and incomplete memberships withhold results | [Checkpoint](../../tests/test_checkpoint.py), [network](../../tests/test_network.py), and [planning](../../tests/test_planning.py) tests. |
| One/two crews separate from people per crew | [Planning regression](../../tests/test_planning.py) and [browser product tests](../../frontend/tests/product.spec.ts). |
| AI only selects references; server renders numerical claims | [Explanation boundary](../AI_EXPLANATIONS.md), [provider](../../backend/ai_provider.py), [explanation service](../../backend/explanations.py), [plan explanations](../../backend/plan_explanations.py). |
| Declarations are session-only and excluded from AI | [Customer integration](../CUSTOMER_INTEGRATION.md), [customer tests](../../tests/test_customer.py), browser product tests. |
| Generalized public maps and offline vectors | [Map contract](../GEOGRAPHIC_MAP.md), [geography tests](../../tests/test_geography.py), browser product tests. |
| No product changes or v1.1.0 implementation | Final branch diff restricted to documentation/media; runtime trees, dependencies, tests, data, and teammate pipeline remain byte-for-byte unchanged against the baseline. |

## Documentation and asset review

Checked **186 local links/anchors across 29 Markdown files**, fenced blocks, image paths, whitespace, and the full diff before the local commit. Fixed one preexisting broken Gemini-to-freeze anchor. A local HTML README preview loaded all five images and was visually reviewed. The Mermaid data flow was compared with `backend/api.py` and the architecture document; no Mermaid renderer was installed for this pass. The diagram is embedded as GitHub-supported Mermaid, with final GitHub rendering reserved for owner review after an authorized push.

Five 1440×1000 application PNGs are visually inspected for readability and privacy. Capture conditions and file hashes are recorded with the [media](../media/v1.0.0/README.md). No image-generation model, UI/DOM text replacement, numerical alteration, or image retouching is used. Screenshots show anonymous aliases, generalized cells, no declared needs, and no raw identifiers or exact customer/facility locations.

This record supplements, rather than overwrites, historical freeze/test notes. Current results do not retroactively change what was verified or submitted during the hackathon. The owner has accepted the existing challenge data; remaining publication approvals are tracked in the [current checklist](CHECKLIST.md).
