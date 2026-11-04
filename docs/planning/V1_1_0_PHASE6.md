# v1.1.0 Phase 6 — G6 customer and offline review packet

**Owner conditionally approves the implemented Phase 6 scope; prior reported passes are preserved and targeted manual accessibility retesting is required. Do not merge, start Phase 7,
publish a release or deploy without separate approval.** Base main is
`98756a9e33da0ef6c9ed38bda177b7cb910c7855` (G5 merge); branch is
`feat/v1.1-phase6-customer-offline`.

This phase adds a fictional dependency learning experience and generic offline kit.
It preserves the challenge customer journey and scientific results. The implementation
uses six existing authored scenarios and 18 Python-prepared milestones, not additional
utility observations, a prediction model or a simulation endpoint.

## 1. Customer journey and evidence

The original preparation page links to `/preparedness/`. The dedicated React entry
starts with generic safety guidance, explicit cache controls and fictional examples.
Select a scenario and prepared milestone, inspect a component and its affected customer
paths, explicitly save an eligible frame, then explicitly reopen that historical snapshot.
The source-backed map and original numerical controls remain unchanged. Selection is
shared across repeated components within the new view; there is no attempted identity
mapping between fictional assets and challenge customers.

Authentic production-browser screenshots (fictional data only):

- [Selected dependency on desktop](../research/phase6/power-path-desktop.png).
- [Mobile unresolved power path](../research/phase6/power-path-mobile-unresolved.png).
- [Historical snapshot with networking disabled](../research/phase6/offline-snapshot.png).
- [Reviewed generic kit](../research/phase6/generic-kit.png).

The schematic is itself a semantic ordered list of native buttons; it is both the
visual and keyboard/text representation, avoiding two inconsistent graph renderings.
The [implementation design](PHASE6_DESIGN.md) records boundaries and choices.

## 2. Exact power-path semantics

| State | Meaning |
|---|---|
| Assumed intact | Fictional supply/equipment without a declared repair; not an observation of health |
| Declared damage | Listed repair has not finished at the selected prepared milestone |
| Blocked access | Authored access restriction; clearance time is unknown |
| Blocked by prerequisite | A required repair cannot currently be scheduled |
| Completed in this fictional milestone | Python's validated fixed schedule completed this task by this milestone |
| Unresolved evidence | Asset identity/connection or repair effort is unknown; never silently treated as intact |
| Unknown connection | An explicitly unresolved link; no inferred completion of the graph |
| Waiting / dependencies released / release unresolved | Customer-specific conjunction of declared damaged dependencies, with unknowns retained |

Paths follow their authored customer-to-supply order. Direction labels, state text and
selection outlines do not rely on color. Supply terminals are abstract and unlocated.
Selecting a component shows its assumptions, repair prerequisites and affected paths.
No map proximity, line crossing, facility label or incomplete source join creates an edge.
A milestone's elapsed time is distinct from full-scope modeled completion; blocked and
unknown scenarios preserve null full completion even when independent work finishes.

## 3. Provenance and unavailable results

`prepare_customer_paths.py` reuses the G1 catalog, G2 fixed baseline, metrics and independent
validator. Inputs are authored total person-hours; no AEP 4.5 multiplier is added.
The one-effective-worker assumption is explicit. The UI selects immutable frames and
validates their fingerprints; it does not calculate scheduling, restoration or risk.
Public frame schemas are centralized in `backend/contracts.py`, with generated TS types.
They are static artifact contracts, not new numerical API routes.

Each frame binds its G1 scenario/revision/input fingerprint, model version
`conditional-dependency-playback-v1`, policy `legacy-release-per-person-hour-adapter-v1`
and exact result content digest. `MODEL_SPEC.md` records evidence classifications.
Online selection requires a ready synthetic service and matching catalog. Save rechecks
the service and exact scenario metadata. Missing service, changed provenance, invalid
artifact and unknown mode disable saving. A saved view is never silently substituted
for a failed request. Refresh cancels outstanding requests/saves and clears old results.

G3's 5% median promotion target failed; CP-SAT remains optional/experimental and is not
used here. G4 remains an evidence-bounded No-Go, not universal public-data infeasibility;
no trained model or outage probability is introduced. G5 remains fixed-timetable delay
propagation, with 195 stable and 15 unstable combinations, not adaptive dispatch or
empirical calibration. **No G5 quantiles are displayed in this phase** because existing
application contracts do not provide a vetted simulation presentation interface.

## 4. Offline caching architecture

The Vite production build traverses only the preparedness entry's compiled dependencies.
It emits `/preparedness/service-worker.js` and an inspectable cache manifest with exact
SHA256 entries: preparedness HTML (including the slash URL alias), one JS entry, its
shared React/Icon chunk, one CSS asset and `kit.txt`. There are six URL entries.
The worker's content version binds the allowlist and worker implementation.

Install requires successful same-origin fetches, no redirects, matching content hashes
and a complete verification pass. Failed installs remove the incomplete cache. Fetch
handling accepts only GET, exact listed paths, no query string and the same origin.
Cache responses are checked before use. Missing/corrupt bytes fall back to the network
without silently populating new entries. Readiness is shown only after worker verification.

Generic content is derived from the reviewed [American Red Cross outage guidance](https://www.redcross.org/get-help/how-to-prepare-for-emergencies/types-of-emergencies/power-outage.html),
reviewed November 3, 2026 (local date). It is generic reference, not tailored emergency,
medical, evacuation or electrical-work instruction. Ready.gov access was unavailable
and is not claimed as reviewed evidence. Print/download include only this kit.

## 5. Exact snapshot schema and prohibited-field audit

Storage uses only `gridguide.preparedness.snapshot.v1`, written by **Save this demo
snapshot**. No snapshot is created automatically. The root keys are exactly:

- `schema_version` = `preparedness-snapshot-v1`.
- `app_version` = `v1.1-phase6` (development schema identity, not a published release).
- `saved_at` = ISO UTC timestamp from the local browser clock.
- `frame` = one approved fictional frame.

The frame keys are exactly `schema_version`, `mode`, `provenance`, `scenario_id`,
`scenario_revision`, `label`, `input_fingerprint`, `model_version`, `policy_id`,
`duration_assumption`, `step`, `step_label`, `elapsed_hours`, `nodes`, `customers`,
`released_customers`, `unresolved_customers`, `completion_hours`, `result_fingerprint`.

Each node contains exactly `id`, `kind`, `label`, `state`, `repair_id`,
`prerequisite_ids`, `reason`. Each customer contains exactly `id`, `label`, `asset_ids`,
`unresolved_link_from_ids`, `required_repair_ids`, `release_state`, `reason`.
These customer IDs refer solely to independently authored fictional records.

Runtime validation checks root/frame keys, version, timestamp format, synthetic origin,
50,000-byte record limit and full content SHA256 membership in the build-approved list.
The full digest establishes exact nested field names **and values**, rather than accepting
arbitrary text merely because its TypeScript shape fits. Serialization uses the validated
frame and newly constructed root, never raw health/catalog/API responses. No simulation
profile identifier is stored because these are deterministic frames, not G5 trials.

Tests reject nested contact fields, extra declarations, arbitrary replacement text,
challenge mode, corrupt JSON and unknown versions. No contacts, personal/free text,
coordinates, addresses, source records, customer declarations, tailored guidance,
credentials or tokens are persisted. API payloads and source topology are never cached.
Challenge-local permits only the generic kit; entering that mode removes a prior fictional
snapshot on this origin. Removal denial is explicit, with browser site-data guidance.

## 6. Worker scope and security boundaries

Worker scope is `/preparedness/`, never the original dashboard. It excludes APIs, POSTs,
external tiles, third-party assets, fonts, raw/processed data and even `frames.json`.
Only an explicitly saved eligible frame persists. Cache storage and snapshot localStorage
are distinct; neither is logged or sent to a provider. External AI is not involved.

Same-origin scripts, browser extensions and a compromised origin are outside this
integrity boundary: hashes are not signatures, encryption, access control or XSS protection.
The app does not promise authenticated timestamps or tamper-proof audit records.
HTTPS or localhost is required. This is not a hosted package or remediation of historical
repository data exposure. The test server's worker-version control route is exclusively
in `frontend/preparedness-tests/server.py`; it is not an application route.

## 7. Browser restart and network-denied reproduction

After installing the repository's pinned Python/web dependencies and `npm --prefix frontend ci`:

```sh
# Terminal 1: source-free catalog service; no credentials required
GRIDGUIDE_MODE=synthetic-demo .venv/bin/python -m uvicorn backend.runtime:app --host 127.0.0.1 --port 8000
# Terminal 2: compiled frontend (development mode does not generate a worker)
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:5173/preparedness/`. Choose an example/milestone, save explicitly,
enable/check the offline kit and wait for verified readiness. Close the browser entirely,
disable networking, reopen the same browser profile and URL, then **Open saved snapshot**.
Generic guidance and historical fiction must remain visible. Example selection and saving
are disabled. Restore connectivity and explicitly reconnect/refresh to revalidate inputs.

Automated reproduction uses a real FastAPI synthetic app and compiled static build on
one local origin (18186); it creates a persistent Chrome profile, closes the browser
process, launches another process with that same profile and denies all networking:

```sh
cd frontend
npx playwright test -c playwright.preparedness.config.ts
```

The blocked scenario retains null full completion after restart. The record bytes are
unchanged and no new result is computed. A separate offline screenshot uses an unresolved
scenario. Tests use fault injection for denied storage and mode failures, while restart,
CacheStorage, worker installation/update and cross-tab events use actual browser behavior.

## 8. Accessibility evidence and manual status

Automated axe-core 4.14.0 audits report **zero serious or critical findings** across all
six scenario states, saved historical view, mobile/reduced-motion view and offline view.
Native headings, fieldsets, ordered lists, buttons, accessible state labels and live
inspection/status regions expose the same content without a pointer. Keyboard tests
verify Enter selection, Tab exit and visible outline. The desktop/mobile screenshots
were visually inspected for clipping, wrapping and state clarity.

**Prior human-reported K and steps 1–8 passes are preserved; targeted retesting of steps 2, 3, 7 and 8 is required.** The executed keyboard
checks are Playwright automation, not manual assistive-technology verification. No
VoiceOver/NVDA, full WCAG certification or cross-browser accessibility claim is made.
Use the [macOS VoiceOver walkthrough and observation record](G6_VOICEOVER_WALKTHROUGH.md).
The owner/tester supplied Pass for every row, with no detailed speech/focus observations
or environment metadata. The walkthrough document preserves that exact report and its
limits. No material issue was reported and no remedial change/retest is claimed. Owner
review and final G6/merge approval remain pending. The supplemental report explicitly
marks speech/focus observations and environment unknown. See the walkthrough
[targeted retest record](G6_VOICEOVER_WALKTHROUGH.md#supplemental-report-and-required-targeted-retest);
the unknown interactions must be manually retested and reviewed. No full walkthrough
repeat is required. Automated checks are not a substitute.

## 9. Mobile and reduced motion

The new view is tested at 390×844 and desktop 1280×900. The ordered layout becomes a
single column on narrow screens; controls retain labels and 44-pixel minimum height.
Tests verify no horizontal overflow at the tested width and no animation under reduced
motion. Original responsive regressions continue to cover the challenge dashboard.
No all-device/mobile-browser guarantee follows from this Chromium evidence.

## 10. Performance, storage and migration limitations

There is no interactive solver or browser numerical engine. Only 18 prepared frames
are fetched online, and one approved frame is saved. Exact shell/frame byte counts and
hashes are in [verification](../research/phase6/verification.json). Build timing is an
observation, not a response-time benchmark or utility performance claim.

API verification has a 10-second deadline. Worker install waiting and readiness messaging
are bounded; failure leaves print/download available. Cache actions are serialized in the
UI to prevent install/reset overlap. Browsers can evict data, deny storage or run out of
quota; a previously ready status is not an availability guarantee. Offline-first access
is impossible before the shell was installed. The generic kit's review date never means
it contains current official alerts.

Unknown snapshot schemas or altered content are rejected, not silently migrated. Users
can delete and explicitly save a new record. Worker updates install a separate content
cache, wait while the existing client is active, and expose an explicit apply/reload action.
Activation removes only older GridGuide preparedness caches; unrelated caches survive.
Reset removes the snapshot, unregisters the scoped worker and verifies own-cache removal.
Cross-tab changes invalidate an opened historical view; stale asynchronous reads/saves
cannot restore it. Corrupted cache entries are never treated as verified readiness.

## 11. Executed regressions and preservation

Executed on this Phase 6 branch:

| Check | Result |
|---|---|
| Python suite | 327 passed (322 existing + 5 customer-path tests) |
| Existing browser suite | 49 passed |
| Production preparedness browser suite | 13 passed, including actual process restart/network denial |
| TypeScript/Vite production build | Passed; generated worker manifest verified |
| API type consistency | Regeneration byte-identical to checked-in generated types |
| Original golden CLI | Passed |
| Source pins | All four SHA256 pins match |
| Legacy restoration | 24 source-dependent cases passed |
| G2/G3 | Frozen input/result preservation and regression tests in full suite passed |
| G4 | Decision replay byte-identical; zero models, null probabilities preserved |
| G5 | 66 committed package checksums verified; numerical implementation/artifacts unchanged |
| New prepared artifacts | All 18 frames and trust manifest regenerate byte-for-byte |
| G1 publication boundary | Catalog-only 12-file artifact inspection passed; extracted source-free tests passed |

The earlier two browser timeouts were test-label selection errors, corrected to select
the combobox by accessible role/name. They did not require changing numerical results.
Current logs, checksums and artifact measurements are in the verification record.

Historical G5 full Monte Carlo reproduction is **reused evidence**, not rerun in Phase 6.
No millions-of-trials rerun was needed: its numerical code and artifacts are unchanged.
The 15 unstable diagnostics, all 56 presets, G2/G3 evaluation data and G4 ledger remain
unchanged. v1.0.0 identity/history, source data and teammate pipeline/attribution remain
preserved. Root README remains product-focused and unchanged. No release/tag/deployment.

## 12. Phase 7 handoff and effort

Phase 7 remains unauthorized. Future operator interfaces should reuse validated Python
results and exact artifact bindings, invalidate review after input changes, and retain
human review. Keep the strongest fixed baseline as default; CP-SAT remains optional and
experimental. Preserve combined 0.351% versus fixed and incremental 0.174% beyond
best-of-four, failed 5% median target, case regressions, fairness and critical-service
tradeoffs. No learned probability should bypass the versioned G4 evidence gate.

Any future G5 display must separately identify stable, unstable, unresolved and unsupported
outputs; unassessed convergence is not stable. Keep all 15 failures and diagnostics,
withhold finite ETRs for unresolved completion and never call conditional synthetic
intervals empirically calibrated restoration confidence. Use only vetted bounded
precomputed fictional artifacts; no unrestricted simulation API or browser engine.
Snapshot integrity is not an authenticated operator audit trail.

The previous Phase 6 estimate of 5–8 human engineering days remains provisional; this
agent-assisted execution is not a measured human effort sample. Subtracting that planned
allowance from G5's 18–28 remaining-day estimate leaves approximately **13–20 provisional
engineering days** for remaining required work, plus independent review fixes. Recalibrate
after G6 review; no calendar deadline or automatic next-phase authorization follows.

## 13. G6 checklist and unresolved acceptance questions

- [x] Six declared fictional scenarios, 18 validated milestones, no geographic inference.
- [x] Synchronized repair/customer states, explicit unknowns/nulls, fixed baseline only.
- [x] Ordered keyboard/text equivalent, mobile/reduced-motion checks, zero serious/critical axe findings.
- [x] Reviewed generic kit, explicit verified offline caching, printable/downloadable fallback.
- [x] Strict synthetic snapshot allowlist, fail-closed provenance, no sensitive persistence.
- [x] Real browser restart with complete network denial; storage/cache/update/delete tests.
- [x] Applicable regressions and source/history/G2–G5 preservation checks.
- [x] Screenshots, reproduction commands, limitations and future integration guidance.
- [x] Owner conditionally accepts the architecture and fictional power-path semantics, subject to manual accessibility verification.
- [x] Human tester reports K and steps 1–8 passed; no issues reported. Detailed notes/environment not supplied.
- [ ] Human performs targeted steps 2, 3, 7 and 8 and records actual speech/focus observations; environment recorded if known.
- [ ] Material accessibility issues, if found, are resolved/retested and the owner reviews the resulting manual evidence.
- [x] Owner conditionally accepts synthetic-only persistence, scoped caching and documented storage limitations; existing limitations remain explicit.
- [ ] Owner approves G6 and separately authorizes merge; later phases remain gated.

Remaining acceptance question: does the actual human keyboard/VoiceOver walkthrough
communicate controls, dependency states, updated inspection and snapshot lifecycle clearly?
Record actual observations and resolve/retest material issues; the owner must review the
results before final acceptance or merging. Conditional approval does not broaden browser
coverage or remove eviction, same-origin compromise or non-authenticating-hash limitations.
