# Judge-facing policy and UX hardening — October 24, 2026

**Verdict: FREEZE.** The initial recommendation now explains the prototype policy, the one-versus-23 tradeoff and its evidence boundary without a disclosure or presenter narration. This pass started from clean commit `e64edd5` and changes presentation and grounded explanation only. The matching, reverse indexing, criticality association, ranking, effort and scheduling modules remain byte-for-byte unchanged from that baseline.

## 1. Recommendation and policy

The lead label is **Scenario recommendation**. The active policy appears immediately below the action, with a **Prototype policy** badge. The two choices are:

- **Critical-service aware:** “Spatial critical-service context before release / effort. Electrical attachment is unverified.”
- **Customer-impact focused:** “Prioritize marginal premise release / effort, with criticality preference disabled.”

The control explicitly says **GridGuide prototype · not an AEP setting**. No weights or third mode were added.

The initial card says one potential premise release, 1.728 repair person-hours and Crew 1. It also states that Customer-impact focused would lead with Historical fuse replay: 23 potential releases for 1.728 repair person-hours. A comparison below shows both actions and their access-adjusted effort. Both outcomes come from the existing server algorithm with identical inputs except `use_critical_proxy`. The client does not rank or calculate.

Policy comparisons bind revision, crews, people, access, candidate membership and valid recommendation identity. They hide during scenario changes. A missing/mismatched alternative never replaces the current plan and has an explicit retry. Both policies may correctly choose the same candidate or no executable repair when access/evidence changes.

## 2. Evidence and terminology

- **28 unique premise dependencies in this scenario**, not a current outage count.
- **Historical replay · qualified spatial hypothesis, not exact identity**, alongside the historical candidate.
- **Spatial critical-premise proxy / Critical-service spatial context**, with **Facility service attachment is not verified** beside the indicator.
- **Potential premise release** and **Dependency-release milestones · not confirmed restoration**.
- **Conditional scenario time / Whole plan · prototype envelope**, separate from repair and access-adjusted person-hours.

Known/source-derived, modeled, spatial, prototype-policy and unavailable states use a small consistent badge treatment. The formal six-class ledger remains available and unchanged. Missing electrical attachment is not styled as a verified connection.

Selecting a candidate synchronizes its generalized map, source-dependency explanation, selected card and highlighted crew task. Crew-task selection works in the reverse direction too. The historical evidence chain is historical observation → qualified spatial match → source fuse → reverse topology → dependent premises. Expanded details show method, no exact identifier match, device/runner-up/pole distances and circuit/station/type checks. No additional location or identity is exposed.

Story links jump directly from the recommendation to selected evidence or the crew plan; keyboard activation focuses the destination heading. The selected-repair dependency view is explicitly not a complete electrical diagram.

## 3. Crews, timing and unavailable work

Available crews controls independent work; people per crew controls the ideal lower task-duration boundary. Helper text explains each next to its input. The numerical model remains unchanged.

Crew lanes state the preceding task and explicitly show **Wait for Golden upstream fuse** before the transformer. Default start labels no longer expose raw three-decimal times; rounded server finish envelopes remain visible. At two crews, Crew 1 handles critical-context fuse then golden fuse; Crew 2 handles historical fuse, waits for the golden fuse, then handles the transformer. Milestones remain 24 → 27 → 28.

Blocking the golden fuse prominently defers its transformer while showing 24 independent potential releases and unavailable full completion. All blocked produces no recommendation or scheduled tasks. Clearance duration is never invented. A pending/error state hides stale numerical claims and comparison results.

## 4. Grounded hostile questions

The existing three plan questions remain. Five more exact curated questions are available under **Challenge the policy and evidence**; this is not unrestricted chat. Raw user questions still never reach Gemini. The model selects approved references; mandatory answers remain server-owned.

| Question | Mandatory answer boundary | Live Gemini result |
|---|---|---|
| Why are you prioritizing one customer over 23? | Recomputed selected/alternative policies, current release and effort values; prototype tradeoff; no AEP weights; facility attachment unverified | AI-assisted, 852 ms |
| Is that fire station actually powered by this fuse? | Cannot verify; only the nearby premise's path is verified | AI-assisted, 736 ms |
| Are 28 customers currently out? | No current outage count; the figure is scenario dependency membership | AI-assisted, 816 ms |
| Why does adding a second crew not cut the time in half? | Independent work overlaps; the transformer still waits for its fuse; individual work is not divided | AI-assisted, 706 ms |
| Can switching restore all of them? | Cannot confirm switching restoration from the supplied evidence; dependency release requires separate conditions | AI-assisted, 851 ms |

All five rendered successfully in the browser. Standard answers use exactly the same mandatory text. Mocked invalid output, timeout and provider errors retain those answers. Tests also verify changed policy, blocked critical work, all blocked, mismatched comparison inputs, forged client comparison and appended prompt injection.

## 5. Executed verification

- Full backend regression: **177 tests passed in 58.508 seconds**, including six new judge-explanation tests. No existing assertions weakened.
- Generated types reproduce byte-for-byte; strict TypeScript and production Vite build pass.
- **19 browser regression groups passed:** first-view semantics/tradeoff; policy counterfactual; two-crew wait/milestones; people versus crews; map/dependency/lane synchronization; historical details; restricted effort; blocked ancestor; all blocked; five Standard hostile answers; keyboard/focus; four responsive widths; alternative failure/retry; AI latency/stale cancellation; AI HTTP failure/retry; mismatched alternative revision; plan failure/retry; original customer flow; no runtime errors.
- Additional targeted verification passed after the final copy/navigation adjustment: story-link keyboard focus, crew sequencing/wait labels, rounded finish-only presentation and responsive 768/390/320 layouts. Malformed and duplicate alternative candidates are withheld without hiding the current plan. The customer outlook is explicitly labeled a separate two-repair Demo A scenario.
- Desktop 1440×1000, 768 px, 390 px and 320 px screenshots were inspected. No page overflow/truncation was observed. The narrow milestone table has an intentionally scrollable, keyboard-focusable region.
- All four raw source hashes match. Numerical/matching modules, teammate pipelines and raw/processed data remain unchanged. `.env`, IDE files, schema intermediates and build output remain ignored; index empty. No commit or push during this pass.

Transient scripts/screenshots/logs use `/tmp/gridguide-ux-*` and are not runtime dependencies or repository artifacts. Live success does not verify billing settings; the user's Free Tier/billing-disabled intent remains user-declared.

## 6. First-impression assessment and remaining weaknesses

**First 10 seconds:** pass in structured review of the desktop first view. The action, active prototype policy, one-versus-23 counterfactual, unverified facility attachment, scenario impact, person-hours, conditional time and non-AEP authority are visible without expansion. **30-second story:** the comparison plus direct evidence/schedule links supports the damage → dependency → tradeoff → crews → conditional-time chain without engineering documentation.

These are implementation/screenshot assessments, not measured sessions with independent AEP judges. At 320 px, the same information requires more vertical scrolling; it remains readable rather than being compressed or hidden. “Premise” and “dependency release” remain technical but necessary distinctions, explained beside the numbers. The full page still contains the separate customer journey; the two scenarios are labeled distinctly. No formal screen-reader or WCAG certification is claimed. Provider availability and all operational evidence gaps remain open.

## 7. Exact 2 minute 45 second demo

| Time | Interaction and narration |
|---|---|
| 0:00–0:20 | Start at Which repair first? “This is a scenario recommendation under GridGuide's Critical-service aware prototype policy—not AEP dispatch. The facility connection is spatial, not electrically verified.” |
| 0:20–0:40 | Point to one versus 23 and equal 1.728 repair person-hours. “This policy explicitly chooses the spatial critical-service context first. Customer-impact focused makes the historical fuse lead.” Select that policy, then return to Critical-service aware. |
| 0:40–1:05 | Select Historical fuse replay and use the evidence link. “Historical observation, qualified spatial match, source fuse, then 23 independently validated premise paths. Exact ARCOS identity and current outage count remain unavailable.” Open match details briefly. |
| 1:05–1:20 | Point to the 28-premise union. “These are 28 unique premise dependencies under this scenario. The transformer premise also depends on its fuse; we do not count it twice.” |
| 1:20–1:50 | Keep four people and change one available crew to two. Use the crew-plan link. “Independent fuse tasks overlap. Crew 2 must still wait for the golden fuse before its transformer. Potential release milestones are 24, 27, 28. The conditional envelope changes from 3.75–15.25 to 3.25–13.5 hours; effort remains 15.192 person-hours.” |
| 1:50–2:10 | Block the golden fuse. “Its transformer is deferred. Independent work retains 24 potential releases; complete time is unavailable because clearance is unknown.” |
| 2:10–2:35 | Restore clear access, open Challenge the policy and evidence, ask “Is that fire station actually powered by this fuse?” Read the unverified-attachment answer. “The server owns the facts; Gemini only selects supporting evidence.” |
| 2:35–2:45 | “Potential dependency release is not confirmed restoration. Actual switching and efficiency remain unavailable. The same safe answer works without AI.” |

## 8. Freeze recommendation

**FREEZE.** No additional implementation is needed for this scoped UX pass. Preserve the current numerical and evidence boundaries. Review this uncommitted patch, rehearse the script, and retain the offline fallback. Do not add new matching, dispatch, data or communications features.


## 9. Exact changed-file manifest

This pass changes 16 intended files. All are unstaged; no commit or push was made.

```text
README.md
backend/api.py
backend/contracts.py
backend/explanations.py
backend/plan_explanations.py
docs/AI_EXPLANATIONS.md
docs/DEMO_FREEZE.md
docs/EXECUTION_PLAN.md
docs/JUDGE_UX_HARDENING.md
docs/Q2_Q4_DECISION_SUPPORT.md
frontend/src/App.tsx
frontend/src/RestorationDecision.css
frontend/src/RestorationDecision.tsx
frontend/src/RestorationEvidence.tsx
frontend/src/api.generated.ts
tests/test_judge_explanations.py
```
