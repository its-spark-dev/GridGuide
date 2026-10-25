# Customer product browser regression

From the repository root, run `npm --prefix frontend test`. The harness uses the
installed Google Chrome (`channel: chrome`) and starts its own Vite on 15173 and
API fixtures on 18080/18081. It does not stop or reuse the demo on 5173/8000.
Install the pinned frontend dev dependencies with `npm --prefix frontend ci` first.

Both fixture apps use the production `create_app`, pinned source preparation and
planning code. The second app replaces only historical risk evidence in memory to
exercise the valid insufficient-risk state. Neither fixture reads `.env`, creates
an external explanation provider, writes source data or adds a product endpoint.
External browser requests are blocked; API requests go to these real local apps.

The tests cover location, customer scope, B1/B2, preparation and declaration privacy,
the four communication previews, policy comparison, selected evidence, crews,
blocked work, Standard explanations, stale requests, failure/retry, six viewports,
keyboard and reduced motion. These are task simulations, not a human usability
study or formal accessibility certification. The Python suite remains authoritative
for numerical rules and the 324-plan regression.

Screenshots/traces/results are ignored in `test-results/` and `playwright-report/`.
Fixtures fail if their ports are already occupied. During an explicitly owned QA
session only, `GRIDGUIDE_REUSE_TEST_SERVERS=1` permits reusing those test servers.
Never use that switch to attach to an unrelated service.

The viewport cases include 1440, 1280, 1024, 768, 390 and 320 pixels; loading,
blocked, partial-risk and recoverable-error states receive separate screenshots.
First-view assertions cover 1440×900, 1280×800 and the preparation action at
390×844. Leaflet assertions check actual SVG and path dimensions as well as the
accessible map region, so a visible container alone cannot hide missing geometry.
