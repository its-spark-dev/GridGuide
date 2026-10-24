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

## Live results and checks — AEP realignment

Model discovery was repeated on October 24, 2026: HTTP 200; `gemini-3.5-flash-lite` listed with `generateContent`. The official Standard pricing table was rechecked and lists Free Tier input/output at no charge. This does not independently verify project billing; billing disabled is user-declared. No billing/account changes, paid fallback or model change were made.

The following browser smoke calls used the current AEP person-hour model, actual local FastAPI service, configured key and existing strict validator. Times include browser interaction and visible response, not a service guarantee.

| Case | Mode | Observed seconds |
|---|---|---:|
| CLEAR | ai_assisted | 1.030 |
| CLEAR cached | ai_assisted | 0.049 |
| LABOR | ai_assisted | 0.928 |
| PRIORITY | ai_assisted | 0.962 |
| RISK | ai_assisted | 0.884 |
| RESTRICTED | ai_assisted | 0.848 |
| BLOCKED | ai_assisted | 0.806 |

CLEAR rendered 11.736 person-hours separately from 2.5–12 elapsed hours. RESTRICTED rendered 16.236 person-hours, 4–16.5 elapsed hours and exact comparison evidence. Labor rendered 2.608 direct hours and the single 4.5 multiplier. Priority explicitly retained the missing ARCOS join and unavailable actual sectionalization count. BLOCKED had no finite ETA. Risk remained ordinal HIGH/LOW confidence. All six uncached intents succeeded; the repeated identical CLEAR request used the validated cache. No secret or raw provider response was printed or persisted.

Full automated tests include mocked provider faults, strict references, privacy, declaration exclusion, numerical invariants and reverse joins. Standard-mode browser checks separately verified all scenarios, stale response suppression, failure/retry, map isolation and customer previews. See [current freeze evidence](DEMO_FREEZE.md) for counts, commands and boundaries. The provider adapter itself was not changed during this realignment.
