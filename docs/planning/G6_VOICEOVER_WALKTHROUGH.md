# G6 manual VoiceOver walkthrough — macOS + Chrome

**Status: human reports all steps passed; final acceptance review pending.** The owner has conditionally accepted
Phase 6's architecture, fictional semantics, persistence, caching and storage limitations.
The owner/tester returned Pass for K and steps 1–8. Detailed speech/focus notes and
environment metadata were not supplied; do not infer them from expected behavior.
PR #8 must remain unmerged until this condition is satisfied and reviewed.

Allow approximately 10–15 minutes. Use fictional data only. Automated axe/Playwright
results do **not** substitute for this walkthrough or establish WCAG compliance.

## Setup

Use macOS **Google Chrome**, preserving the documented Chromium-only coverage. Record
macOS/Chrome versions and `git rev-parse HEAD`. Current application implementation is
`33c187186af277794896ef198dcf14e3bd41ecc7`; later documentation commits do not change it.
Use a separate test browser profile if you want to retain an existing saved demo snapshot.
The delete steps below remove the test profile's single GridGuide snapshot.

From the repository, with the existing dependencies installed:

```sh
# Terminal 1 — keep running
GRIDGUIDE_MODE=synthetic-demo .venv/bin/python -m uvicorn backend.runtime:app --host 127.0.0.1 --port 8000
# Terminal 2 — build once, then keep preview running
npm --prefix frontend run build
npm --prefix frontend run preview
```

Open `http://127.0.0.1:5173/preparedness/` in Chrome. Use the production preview, not
the Vite development server. Wait for “Synthetic demo verified.” If ports are already in
use or provenance cannot be verified, record a setup block rather than a test pass.
Do not use challenge-local mode for the snapshot steps.

First do a short **VoiceOver-off keyboard pass**: Tab/Shift-Tab through the page,
check visible focus, choose a scenario/milestone with the select's keyboard controls,
and activate a dependency with Enter and another with Space. Confirm you can leave
both the control and the path without a pointer. Record any browser/macOS keyboard
navigation setting you needed to change; do not count skipped controls as passed.

Then turn VoiceOver on with **Command-F5** (add Fn if your keyboard requires it).
Here **VO means Control-Option**. Use VO-Right/Left to read forward/backward,
VO-Space to activate, and VO-Shift-Down/Up to enter/leave a web area or group if needed.
Keep arrow-key Quick Nav off for native select navigation (Left+Right together toggles
it). For a select, VO-Space opens it; use arrows to hear options, then Return to commit
or Escape to cancel. Record any different keys required by your version.
These commands follow [Apple's VoiceOver command reference](https://www.apple.com/uk/voiceover/info/guide/_1131.html);
key setup is guidance, not a report of testing this application.

## Walkthrough and expected behavior

Use keyboard only. Record **actual speech and focus behavior** separately from these
expectations. Equivalent spoken wording is acceptable; a visible label alone is not
proof that it was announced. If a step fails, record it and continue where feasible.

| ID | Action | Expected information and behavior to verify manually |
|---|---|---|
| K | Perform the VoiceOver-off keyboard pass above. | Visible focus, logical order, both Enter/Space activation, reversible navigation and no trap. |
| 1 | With VoiceOver on, reach **Fictional scenario** and select **Fictional simple path**; select **Before repairs** in **Prepared milestone**. Read the result heading and summary. | Both controls have understandable names and selected values. Scenario/milestone changes are discoverable; summary says 0 released fictional customers. No unexpected focus loss. |
| 2 | In **Fictional customer 1**, reach **Transformer 2 — Declared damage**. Activate it with VO-Space, then read forward/backward as needed. | Button name conveys component/state; selection is conveyed (for example, pressed). Focus remains usable. Abstract supply is explicitly assumed intact and unlocated, not verified real-world equipment. |
| 3 | Immediately after selection, pause to listen. Then navigate to the inspection area's **Transformer 2** heading and read its contents with VO-Right. Select **Fuse 1** and repeat. | Record whether the polite update is announced, delayed, silent, duplicated or excessively verbose. Inspection must identify the selected component, known/assumed information, prerequisites (**Fuse 1** for Transformer 2) and affected fictional paths. Updated content must also be reachable without relying on an automatic announcement. Check that old details do not masquerade as the new selection. |
| 4 | Return to **Prepared milestone**, choose **Modeled milestone 2**, then read the result and first customer's dependency buttons. | 2 fictional customers have completed declared dependencies. Fuse 1 and Transformer 2 say **Completed in this fictional milestone**. Completion is modeled, not confirmed utility restoration. Selection/detail state stays consistent with the changed milestone. |
| 5 | Choose **Fictional blocked access**, then **Modeled milestone 1**. Inspect Fuse 1, Transformer 2 and the result summary. | **Blocked access** and **Blocked by prerequisite** remain distinguishable from completed independent work. Full completion is **Unavailable**; 1 customer is released and 1 unresolved. No finite ETR is substituted. |
| 6 | Choose **Fictional unresolved evidence**, then **Modeled milestone 1**. Read the ordered path and select **Unresolved 1**. | **Unknown connection** text is readable between components. Unresolved evidence differs from assumed intact and completed Fuse 2. Summary retains 0 released, 1 unresolved and unavailable full completion. Inspection explains missing evidence. |
| 7 | Activate **Save this demo snapshot** and listen/read for status. Then activate **Open saved snapshot**. Read the saved notice and expand **Versions and fictional provenance**. | Save success is discoverable; **Historical fictional snapshot**, save timestamp, app/model/policy versions and fictional provenance are readable. Scenario/milestone controls and saving are disabled in historical view. Timestamp age does not imply utility validity. Do not interpret a storage error as successful saving. |
| 8 | Activate **Delete saved snapshot**. Read status, then reload with Command-R and inspect the snapshot controls again. | Deletion is discoverable; historical notice disappears and **Open saved snapshot** is unavailable before and after reload. Any freshly loaded example is identified as a service-verified fictional example, not the deleted historical record. Focus remains recoverable after content changes. |

No offline restart is required for this remaining manual item: the real browser restart
and network-denial checks are existing automated evidence, not manual VoiceOver evidence.
Saving a snapshot alone does not install the offline shell or establish offline readiness.

## Observation record — return this to the PR/chat

Fill in only what was actually executed. Optional speech notes/recordings should contain
only the fictional test page; no personal browser/profile information is needed.

```text
Tester (name or alias):
Date/time and timezone:
Git SHA:
macOS version / Chrome version:
VoiceOver settings: modifier, Quick Nav, speech/language, web announcements, changes made:
Keyboard-only setup/settings:

ID | Pass / Fail / Blocked / Not run | Actual speech, focus behavior and reproduction notes
K  | Not run |
1  | Not run |
2  | Not run |
3  | Not run | Automatic announcement AND manual access to updated inspection:
4  | Not run |
5  | Not run |
6  | Not run |
7  | Not run |
8  | Not run |

Issues (ID, expected vs actual, user impact, workaround if any):
Fix/retest SHA and actual retest observations (if applicable):
Tester conclusion:
Independent reviewer disposition/date (leave pending until reviewed):
```

**Acceptance:** a human completes all rows, reports actual results, and any material issue
is fixed and manually retested on the resulting head before owner review. Trapped/lost
focus, inaccessible controls or updated inspection, misleading states, and inaccessible
save/open/delete status block acceptance. Report silent/repetitive live updates even if
manual navigation works; reviewer must assess their impact rather than silently waive them.
Untested/blocked rows remain pending. Do not copy expected wording into “actual” observations.

Browser coverage remains Chromium-only. Storage eviction/denial and same-origin compromise
remain limitations; hashes check content integrity but do not authenticate records, users
or timestamps. This walkthrough changes no models, source data, artifacts, defaults or
historical findings. No merge, Phase 7, release or deployment is authorized by this document.


## Received human report

Recorded November 3, 2026 (America/New_York), from the user's response in this chat.
These are human-reported outcomes, not automated results or agent-observed speech.
The response supplied the following rows with empty observation cells:

```text
K | Pass |
1 | Pass |
2 | Pass |
3 | Pass |
4 | Pass |
5 | Pass |
6 | Pass |
7 | Pass |
8 | Pass |
```

No issues were reported; this does not establish that every possible issue is absent.
Tester identity beyond the responding user, execution time, tested Git SHA, macOS/Chrome
versions, VoiceOver settings, exact speech and focus details were not supplied. The
walkthrough was issued at `57a423c55032d8a19eae8fd33569965c3cb3bf2d`; that is context,
not confirmation of the tested checkout. No remedial code change or retest is claimed.
The empty template above remains available for supplemental details.

Owner review of this report, final G6 acceptance and merge authorization remain pending.
All coverage, storage and integrity limitations above remain unchanged.
