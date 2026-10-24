# Customer UI reference pass — 2026-10-24

Inspected live rendered pages in isolated Chrome with Playwright, using DOM,
computed styles and screenshots at 1440px and 390px. References:

- https://www.aepohio.com/
- https://www.aepohio.com/outages/
- https://outagemap.aepohio.com/

## Observations and adaptation

The home/customer shell uses white navigation, a light gray utility strip,
uppercase navigation and broad horizontal sections. The desktop navigation
measured 125px. Customer pages declare DIN 2014, Arial, Roboto, sans-serif.

The outage page uses red headings (#af2218), blue actions (#025a95), dark text
(#2d2d2d), white surfaces and substantial pale-gray section dividers. Desktop
content has 70px side gutters at 1440px; mobile has 30px at 390px. Main section
headings are 32–40px; the illustrated hero title is 66px. Mobile navigation
measured 75px. Desktop ZIP input measured 60px high with a 4px radius; primary
buttons use a 4px radius and 30px horizontal padding. Mobile actions measured
40px high. GridGuide keeps touch targets at least 44px where applicable.

The JavaScript outage map rendered successfully. Inspected toolbar, legend,
location/county/ZIP/district/OMS selectors, search dialog, summary menu and an
outage detail popup. Toolbar: 80px, #f3f3f3; map controls use Roboto, red actions,
8px radii and restrained shadows. Search input: 46px, 16px text. Summary labels:
14px/500; values: 24px/700. The menu separates counts from its last-updated
metadata. Detail separates customer count, start, restoration and status.
GridGuide adopts the label/value hierarchy without importing live utility data,
a timestamp, logos, icons, imagery, maps or downloaded fonts.

## Token and interaction decisions

`src/styles.css` owns the variables: white page/surface, #f3f3f3 secondary surface,
#2d2d2d text, #555 muted text, #af2218 heading/critical, #da291c shell accent,
#025a95 action/information, #9e9fa1 border, 4px controls, 8px panels and 1300px
usable desktop width. Amber risk is a GridGuide semantic adaptation, not an
assertion that AEP publishes this model band. Local condensed system fonts with
Arial fallback preserve offline operation; exact DIN typography is not shipped.

Previous hierarchy: introduction → access selector → risk/restoration → causal
explanation. New hierarchy: customer shell/location → risk/restoration → access
details → comparison → verified schematic → assumptions → future guidance/alerts.

Comparison refinement reduced mobile density with expandable risk evidence,
fixed badge alignment, and kept restoration ahead of the broader scenario
notice. The estimate itself always retains the provisional/not-official label.
Previous/current ranges are stored API results tied to the comparison's result
ID; no bounds, deltas, risk, or labor arithmetic is computed in the UI.

## Verification

Before and after: 48 backend/API tests, strict TypeScript production build,
golden CLI, and real browser flow pass. CLEAR 11–18; RESTRICTED 16–25; BLOCKED
null bounds/pending clearance; HIGH risk throughout. Browser checks compare
rendered values and explanation to responses, exercise keyboard selection,
rapid switching, failed requests/retry, initial load recovery and disclosures.
Desktop, 768px and 390px layouts checked; no horizontal overflow. Screenshots
were compared against live reference captures, followed by a refinement pass.
No numerical engine, API, generated type, dependency, raw data or teammate file
changed. No additional frontend test runner was introduced. No commit or push.
