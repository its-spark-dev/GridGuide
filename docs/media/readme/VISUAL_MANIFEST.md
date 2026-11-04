# Product README visual inventory

The redesign retains all previously published screenshot bytes and the exact approved
four-map gallery markup. Only one new application screenshot is added: the original
crew-planning workspace, captured through its real UI with two four-person crews.
No generated artwork, image edits, fabricated responses or changed numerical rules.

| Visual | Treatment |
| --- | --- |
| Integrated Overview | Retained as hero, beneath centered branding and four truthful badges |
| Original outlook + fictional power path | Paired to distinguish challenge-local and fictional experiences |
| Preparedness kit + original communication preview | Paired; preview explicitly labeled NOT SENT |
| Four geographic candidate maps | Exact approved 2×2 gallery retained unchanged |
| Original priority comparison + crew planning | Original image reused; new authentic crew workspace capture |
| Fictional policy comparison + review | Curated pair below geographic and original planning experiences |
| Mobile preparedness + operator | Optional expandable pair |
| Original preparation checklist and evidence screenshot | Audited; checklist linked, evidence already represented in the four-map workspace |

[Machine-readable image hashes and sizes](visual-manifest.json) bind every embedded local
image. [Crew capture metadata](crew-capture.json) records its application commit, browser,
viewport, timestamp and chosen controls. [Map provenance](grid-insights/provenance.json),
[original screenshot provenance](../v1.0.0/README.md), [integrated capture evidence](../v1.1.0-integrated/README.md)
and [preparedness provenance](README.md) remain unchanged.

To reproduce the crew view, run the authorized detached v1.0.0 application with external
AI disabled, open Grid insights, select 2 available crews and leave 4 people per crew,
clear access and the critical-proxy policy unchanged. At 1440×1100 with reduced motion,
scroll the crew panel to 24 pixels below the viewport top and capture the viewport once
the real result and local fonts finish loading. The external local Vite proxy port was
changed only in capture configuration; no application source was edited.

CI badge points to the real main-branch workflow; the version badge says release candidate.
No license, coverage, popularity or deployment claims are introduced. Screenshot pixels
keep their authentic light-theme UI even when GitHub's surrounding README uses dark mode.
Small gallery thumbnails link to unscaled originals; mobile gallery content is optional.
