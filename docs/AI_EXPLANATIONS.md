# Constrained explanations — October 24, 2026

GREEN for local functionality, mocked-provider grounding and offline/no-key behavior. A live provider smoke test has **not** been performed: no API key is configured on this workstation. This does not change the unresolved labor-unit and calibration limits of the numerical model.

## Authority and scope

The flow is verified engine → allowlisted explanation context → optional model reference selection → server validation → server-rendered answer. The LLM neither calculates nor supplies factual prose. This implements the reference-selection design in [MODEL_SPEC §6](MODEL_SPEC.md#6-ai-output-and-grounded-rendering). It is deliberately more constrained than arbitrary generated answers.

`backend/explanations.py` defines the vendor-neutral async `ExplanationProvider.select(context, intent, allowed_refs)` interface. `backend/ai_provider.py` implements an optional OpenAI Responses adapter using the already installed `httpx`; no new Python or frontend dependency is needed for this slice. The UI displays “AI-assisted explanation” only after a successful validated model selection. All other supported answers display “Standard explanation.”

The model chooses and orders one to three supporting clauses for the chosen question. It cannot replace the mandatory answer, uncertainty statement, region disclosure or safety guidance. Every displayed sentence comes from the current validated result, the existing engine comparison, teammate-derived preparation, or reviewed templates. The engine, teammate pipelines, data files and existing safety copy are unchanged.

## Context, request and response contracts

`ExplanationContext` is an explicit Pydantic allowlist: opaque result ID and revision, anonymized label, Virginia challenge-data disclosure, risk band/confidence/null probability, restoration status/nullable display bounds, simulated access, verified topology types, demo alert eligibility/preview-only delivery, assumptions, limitations and approved clauses. Each clause has an ID, text and provenance type (`modeled`, `simulated`, `verified`, `mixed`).

No precise or generalized coordinates, raw premise/equipment/circuit identifiers, contact fields, medical/critical flags, shapefile attributes, workbook cell references or private source objects are included. Raw user question text is **not sent to the model**. A bounded exact-match question catalog resolves to a canonical intent on the server; anything outside it receives an insufficient-verified-information response without contacting a provider. The customer UI offers five suggested questions and no general-purpose chat input.

`POST /api/explain` accepts the existing validated location/access/revision selection and optional previous selection, plus current `result_id`, optional `previous_result_id` and a question of at most 240 characters. The server recomputes current/previous evaluations and the comparison with the unchanged engine. Both result IDs must match; mismatches return a sanitized 409. Client-supplied analysis, bounds, credentials or extra fields are rejected. The endpoint returns `ExplanationResponse`, not a modified `Evaluation`; the original `generated_explanation: null` field remains unchanged.

The only accepted model output is:

```json
{
  "result_id": "<current opaque result ID>",
  "intent": "change",
  "supporting_refs": ["comparison-summary", "access-detail"]
}
```

There are no model-authored `answer`, numeric or uncertainty fields. Strict JSON Schema constrains IDs/intent/references in the provider request. The server independently rejects extra/duplicate keys, malformed or oversized output, stale IDs, wrong intents, duplicate references, references outside the current intent and finite-change responses that omit the engine comparison. Choosing an irrelevant but otherwise valid global clause is rejected. A refusal or incomplete provider response is also rejected.

The customer response contains authoritative `answer`, `supporting_factors`, `uncertainty_note`, `dataset_note`, `source_type`, `mode`, safe `fallback_reason`, and result/revision binding. No raw provider response, reasoning, error details or credentials are returned or logged by application code.

## Fallback and BLOCKED behavior

- AI disabled/missing key: return the deterministic answer immediately, with no provider request.
- Transport failure, rate limit, timeout, refusal, malformed/unsupported output: return the same grounded standard answer and approved default references. No retry loop or model repair request.
- HTTP transport timeout: 4.5 seconds; overall async provider deadline: 6 seconds. Late browser answers are aborted/discarded on question or scenario changes.
- Unsupported question: say GridGuide lacks sufficient verified information; no external request.
- Explanation-endpoint/network failure: retain the existing deterministic comparison and primary customer journey, with an explanation-only retry. This is distinct from provider failure, which returns a complete standard answer with HTTP 200.

BLOCKED context retains null restoration bounds. Restoration/availability/change answers lead with unknown clearance time and the need to clear access before a credible modeled range is available. A blocked change cannot select a previous finite-range comparison clause. No replacement duration is synthesized. Preparation may still contain existing food-storage durations, clearly labeled as preparation rather than restoration estimates.

## Optional provider setup

The application defaults to `GRIDGUIDE_AI_PROVIDER=none`, even if another application has set `OPENAI_API_KEY`. To enable the adapter, set these **server-side** environment variables before starting FastAPI:

```sh
export GRIDGUIDE_AI_PROVIDER=openai
export GRIDGUIDE_AI_MODEL=gpt-4o-mini-2024-07-18
```

Supply `OPENAI_API_KEY` securely through the server environment; never place it in source, frontend/Vite variables, screenshots or shell commands saved in this repository. The root `.env` is already ignored, but the app does not automatically load it. Restart the backend after configuration changes. `GRIDGUIDE_AI_MODEL` is optional; the adapter defaults to the snapshot shown above. Model access must be checked on the actual account.

The fixed endpoint is `https://api.openai.com/v1/responses`. Requests use strict structured output, `store: false`, a bounded output budget and no tools, retrieval, browsing, conversations or external endpoints selected by the user/model. Only the sanitized context and canonical intent leave the server. Disabling AI restores fully local behavior. `store: false` is a request setting, not a blanket promise about a provider's retention policies.

Official implementation references: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) and [GPT-4o mini capabilities/snapshot](https://developers.openai.com/api/docs/models/gpt-4o-mini). Another vendor can implement the small provider interface without changing customer policy or the numerical engine.

## Browser experience and verification

“Ask GridGuide” sits after “Why the outlook changed,” before the map. Suggested questions and one answer panel preserve the AEP-derived shell; there is no conversation history or chatbot takeover. Scenario updates remove the old answer immediately. The component verifies result/revision identity, aborts superseded requests, supports keyboard selection and retains the primary page when explanations fail.

Baseline: 66 backend tests, frontend build and the existing browser journey passed before edits. Final: **89 backend tests pass**, including 23 explanation/provider tests. They cover context privacy, exact server rendering, all access states, unsupported/injected questions, stale/forged request binding, malformed/duplicate/irrelevant model output, every prohibited claim category, deadlines, no-key configuration, strict HTTP request shape, provider refusal/rate limit and transport failures. All provider tests use fakes or `httpx.MockTransport`; they make no real API calls.

Verification commands:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
npm --prefix frontend run types:generate
npm --prefix frontend run build
```

TypeScript/production build and golden CLI pass. This repository has no separate frontend unit-test runner; real-API Chrome automation provides the frontend behavior checks. The browser verification exercised:

1. CLEAR: “Why is restoration 11–18 hours?” explains the simulated scope, clear access, workbook allowance and crew-response time origin.
2. CLEAR → RESTRICTED: “Why did my estimate change?” shows 16–25 and the exact engine comparison, including two worksites. UI text matches the returned supporting clauses.
3. BLOCKED: “When will my power be restored?” says access must be cleared and provides no numeric restoration duration.
4. Risk: HIGH is an ordinal modeled concern band, not a probability; confidence remains LOW.
5. No-key standard answers and an isolated mocked-provider server exercising actual API validation/rendering and the “AI-assisted” UI state. No live provider performance claim is made.
6. Explanation failure/retry, forged result response rejection, delayed prior question suppression and scenario-change cancellation; zero uncaught browser errors.
7. Existing map/tile failures and retries, schematic, all lifecycle messages, preparation, alert previews, scenario/error/retry behavior and 390/768 px mobile/tablet layouts. Desktop/mobile explanation screenshots reviewed.

Raw source hashes remain unchanged. No teammate pipeline or raw/processed data changes; no commit or push. The previous geographic slice remains uncommitted alongside this work.

Immediate next task: run a small live-provider smoke test with a securely configured account, checking valid-reference selection, fallback rate and latency. Keep raw model prose disabled. Labor-unit interpretation and predictive calibration still need organizer/data clarification before any operational claim.
