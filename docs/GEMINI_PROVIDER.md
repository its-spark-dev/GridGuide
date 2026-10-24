# Gemini provider and live verification — October 24, 2026

GREEN: the Gemini Developer API completed all four required live explanation cases with the existing strict server validator. Deterministic calculations, customer guidance and UI design are unchanged.

Final freeze rehearsal also passed all four live cases, but uncached HTTP latency was 4.1–5.7 seconds; the exact repeated answer took 3.6 ms from cache. Do not assume the earlier subsecond sample below is typical. The provider-disabled browser rehearsal also passed. See [final measurements and remaining risks](DEMO_FREEZE.md#final-evidence-and-severity).

## Checkpoint and provider choice

The previously verified GIS + AI work was committed together as `3ac13b8` (`feat: add verified GIS and grounded outage explanations`). Shared contracts/API/UI files made one coherent checkpoint safer than partial staging. Its 21 files exclude raw/processed data, teammate pipelines, credentials, caches and temporary outputs. Gemini was subsequently committed as `4c57b7b` (`feat: integrate validated Gemini outage explanations`) after rechecking all 98 baseline tests, CLI and build. Both commits were pushed to `origin/main` during the authorized final integration. See [the final freeze note](DEMO_FREEZE.md) for later rehearsal results.

`GeminiExplanationProvider` implements the same async provider interface as the retained OpenAI adapter, using existing `httpx` and the official `v1beta/models/{model}:generateContent` endpoint. The default configured provider is now **gemini**. `GRIDGUIDE_AI_PROVIDER=none` disables external AI; `openai` explicitly selects the existing alternative. Missing credentials always use Standard explanation. There is no automatic switch to a paid model or another vendor.

Selected model: **`gemini-3.5-flash-lite`**, centralized in `GEMINI_DEFAULT_MODEL` and overridable with `GRIDGUIDE_AI_MODEL`. The supplied key's model-list endpoint returned HTTP 200 and listed this model with `generateContent` support. Google's [Standard pricing table](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) lists free input/output for its Free Tier. The user stated the project is intended for Free Tier with billing disabled. Successful generation verifies access; the generation/models APIs do not independently prove the project's billing configuration.

The newer listed `gemini-3.8-flash` timed out at the original 4.5-second deadline. Flash-Lite fits this small reference-selection workload without deep reasoning. It uses minimal thinking; other supported Gemini 3 Flash overrides use low thinking, and Gemini 2.5 Flash overrides disable thinking. No arbitrary model URL or Pro model can be selected by the adapter. The user must independently verify tier availability when overriding the model.

## Contract and minimization

Gemini receives only the opaque result ID, canonical intent, restoration status, dataset disclosure and the approved clauses relevant to that question. It receives no raw user question, location label, coordinates, source records, customer identity or repository documents. The API key travels only in the server-side `x-goog-api-key` header, never the URL or browser DTO.

Native JSON output uses a schema requiring exactly `result_id`, `intent`, and one to three `supporting_refs`. Result/intent/reference enums are specific to the current request. The existing independent validator still rejects extra fields, duplicate keys, unsupported references, stale IDs, wrong intents and missing comparison evidence. Server templates alone supply the answer, numbers, uncertainty and safety copy. See [the explanation contract](AI_EXPLANATIONS.md).

Gemini returned a text part with an opaque `thoughtSignature` in an otherwise completed response. The adapter discards this transport metadata and passes only JSON text to the unchanged validator. It rejects thought text, tool calls, truncated responses, blocked responses and ambiguous candidates. Signatures and raw responses are never returned, logged or persisted. See Google's [structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output) and [thinking documentation](https://ai.google.dev/gemini-api/docs/generate-content/thinking).

## Local credential and launch setup

The project-root `.env` is ignored by the existing `.gitignore` rule and has owner-only permissions. It contains `GRIDGUIDE_AI_PROVIDER=gemini` and the locally entered `GEMINI_API_KEY`. The key was not displayed or committed. Do not copy it into chat, frontend variables, DTOs or diagnostic logs.

The application reads process environment variables; it does not implicitly evaluate `.env` as shell code. To start the backend from the project root using the local file without echoing secrets:

```sh
.venv/bin/python - <<'PY'
import os
from pathlib import Path
import uvicorn
allowed = {'GEMINI_API_KEY', 'OPENAI_API_KEY', 'GRIDGUIDE_AI_PROVIDER', 'GRIDGUIDE_AI_MODEL'}
for line in Path('.env').read_text().splitlines():
    name, separator, value = line.strip().removeprefix('export ').partition('=')
    if separator and name.strip() in allowed:
        os.environ[name.strip()] = value.strip().strip('"\'')
uvicorn.run('backend.api:app', host='127.0.0.1', port=8000)
PY
```

This accepts simple single-line settings; it does not execute shell syntax or interpolate variables. Start the frontend with `npm --prefix frontend run dev`. No model override is needed for the verified default. Set `GRIDGUIDE_AI_PROVIDER=none` in the local configuration for a fully deterministic demo. Keys remain server-side even when responses are shown in the browser.

## Deadlines, cache and fallback

Gemini has a seven-second transport timeout and an eight-second overall async provider deadline, below the browser's ten-second limit. OpenAI keeps its 4.5-second transport timeout. Timeout, exhausted quota/429, authentication/provider errors, malformed output or failed validation returns Standard explanation without a retry loop. Initial live timeouts exercised this fallback successfully. Successful latencies below are a small smoke sample, not a service-level guarantee.

A process-local LRU cache holds at most 64 **validated AI-assisted answers**, expiring after five minutes. Its key hashes the full allowlisted context and canonical intent, including revision, comparison text and policy version. It cannot reuse a prior comparison just because the current result ID matches. No raw questions, secrets or responses are stored. Failed/unsupported answers are not cached. Sequential identical questions reuse the answer; simultaneous cold requests can still produce separate calls. No persistence or background prefetching was added.

## Live results and checks

| Case | Mode | Observed seconds | Validated behavior |
|---|---|---:|---|
| CLEAR | AI-assisted | 0.970 | 11–18 provisional hours after crew response begins; approved repair, serial-work and labor clauses |
| RESTRICTED | AI-assisted | 0.931 | 16–25 provisional hours; required exact engine comparison and access detail |
| BLOCKED | AI-assisted | 0.877 | Null bounds; access clearance required, no numeric restoration estimate |
| HIGH risk | AI-assisted | 1.269 | Ordinal modeled concern band, not outage probability; LOW confidence retained |

All calls used the configured key and the same minimized context and validator used by the service. An initial signature-envelope rejection and deadline failures produced safe standard answers; no fabricated values reached the UI.

**98 automated backend tests pass**, all provider calls mocked. Added tests cover Gemini request schema, credential placement/non-echo, minimized context, response parsing, opaque signature handling, 4xx/5xx/429/timeout, malformed JSON/schema, unsupported references, stale IDs, four scenarios, no-key configuration, cache bounds/expiry/context binding and invalid-response non-caching. Existing OpenAI tests still pass. Tests do not load the local secret file or require live quota.

The golden CLI and frontend TypeScript/build pass. Chrome regression checks cover map/tiles/fallback, schematic, preparation, alert lifecycle, scenario changes, retries, stale responses and mobile/tablet layout. A separate local API instance loaded the secret only into its server environment: the browser displayed a successful live Gemini-backed AI-assisted answer. Repeating that exact result/question returned HTTP 200 from the validated cache in about 0.0015 seconds. No numerical engine, teammate pipeline or raw/processed data was changed. Keep Free Tier quota monitoring and Standard explanation available during the demo.
