# Grounded explanations — v2

Flow: validated deterministic result → minimized approved clauses → optional provider reference selection → strict validation → server-rendered answer. Gemini never calculates person-hours, elapsed duration, risk, customer dependency, repair priority, alert eligibility or medical/accessibility needs.

## Context and privacy

`ExplanationContext` version v2 separates repair person-hours, total person-hours and nullable elapsed bounds; it includes selected crew size, approved source/dependency/priority clauses and classified assumptions. Labor answers show installation/removal/direct labor, one AEP 4.5 multiplier and the distinction between effort and elapsed outlook. Sequence answers distinguish conditional repair release, spatial criticality and unknown switching.

No raw source IDs, premise lists, exact/generalized coordinates, contact fields, source records or workbook cell references reach the provider. Declared-needs selections, tailored actions and eligibility reasons are replaced by the generic journey before context construction; the same generic context is used for every vendor and cache. Raw user questions are not sent: a bounded catalog maps exact supported questions to canonical intents. The browser has seven suggested questions, including labor and repair sequence, not general chat.

`/api/explain` recomputes current/previous location, access, crew and revisions. Result IDs must match; stale or forged inputs return sanitized 409. Extra calculation/credential fields are rejected. No explanation mutates the engine result.

## Restoration-plan scope

The context now carries `scope=customer|restoration_plan`. Three plan questions cover damage dependencies, why the recommended action is first, and crew-driven scheduling. `backend/plan_explanations.py` builds every count, recommendation, timing and caveat from the recomputed deterministic plan. No map positions, private IDs, source row locators or facility identity enter the provider. Gemini selects relevant approved references; it cannot alter the mandatory answer or author new priority reasons. Unknown complete duration under blocked work remains unavailable, while independent scheduled work can still be explained. Cross-scope and injected questions never reach the provider.

## Strict selection contract

The provider returns exactly `result_id`, `intent`, and one to three `supporting_refs`. It cannot supply an answer, numbers, operational status or uncertainty. Schema enums are request-specific. Independent validation rejects extra/duplicate keys, malformed/oversized output, stale IDs, wrong intent, duplicates, irrelevant references and finite-change answers omitting the deterministic comparison. Every displayed claim is rendered by the server from current result/policy templates.

The mandatory lead distinguishes **11.736 repair person-hours** from **2.5–12 conditional elapsed hours** at four-person CLEAR. BLOCKED duration stays null; no previous finite comparison can become a current ETA. Clearance, switching and measured efficiency remain unavailable. Unsupported/adversarial requests are refused without provider traffic.

## Providers, fallback and browser

Gemini is the default when a server-side key is present; OpenAI remains an explicit alternative. Missing/disabled credentials make no external request. Provider failure, 429, timeout, refusal, truncated or invalid output yields deterministic Standard explanation. Gemini transport deadline is seven seconds; overall async deadline eight, browser ten. No automatic paid/model/vendor failover. See [Gemini setup and current smoke evidence](GEMINI_PROVIDER.md).

The process-local validated-answer cache holds 64 entries with five-minute TTL. Keys bind full generic context and intent, including comparison/revision. Invalid answers are not cached; no raw response, declaration or credential persists. The frontend aborts old questions and discards wrong result/revision responses. Explanation-only failure retains the numerical journey and supports retry.

Tests cover both provider request schemas, numerical/operational injection, hidden needs, source privacy, missing credentials, timeouts/quota/errors, strict references, cache binding, BLOCKED and stale IDs. Browser/live outcomes are recorded in [DEMO_FREEZE.md](DEMO_FREEZE.md). Automated provider tests are mocked; live smoke is separately labeled.
