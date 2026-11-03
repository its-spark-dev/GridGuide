# Application screenshots — v1.0.0

Captured **November 3, 2026** from the unchanged implementation at `bb7c53ce2e0733c6770c9de631a75df094407727`, the last known hackathon-period checkpoint. These are new portfolio captures, not evidence of the exact competition submission or screenshots taken during the event.

All five images are direct **1440×1000 PNG** viewport captures at device scale 1 from installed Google Chrome through the existing Playwright dependency. The normal [browser fixture](../../../frontend/tests/server_fixture.py) runs the production API and pinned source preparation, with no explanation provider. The separate insufficient-risk fixture was not used. Vite serves the actual frontend. API requests are routed to the normal local fixture without changing response content; external browser requests are blocked. No DOM content, application code, source data, or numerical results were changed for these captures.

| Image | Visible state |
| --- | --- |
| [Customer Overview](overview.png) | Demo location A; four people; clear access; HIGH concern with low predictive confidence; conditional 2.5–12 hours; no declared needs. |
| [Preparation](preparation.png) | Default preparation and safety guidance; no tasks completed and no personal needs declared. |
| [Communication preview](communication-preview.png) | The “Outage confirmed” example selected through the real UI. It explicitly says hypothetical, preview-only, and not sent. |
| [Grid Insights](grid-insights.png) | Critical-service-aware policy selected; one crew, four people, clear access; comparison with the 23-premise alternative. |
| [Evidence and crew assignment](evidence.png) | Historical fuse selected for inspection while the critical-service-aware recommendation remains active; two crews, four people each, clear access. The Street map control is off; generalized source cells and the existing evidence chain remain visible. |

The evidence image is scrolled to the map/lineage workspace; the communication image is scrolled to the lifecycle preview. This is ordinary viewport capture, not a composite. All files are unretouched, with no generated visuals, redaction overlays, numerical substitutions, or post-capture image editing. No developer tools, unrelated windows, credentials, precise coordinates, facility identities, or raw customer/equipment identifiers are visible. Leaflet attribution remains visible on the map. The UI's generalization does not itself resolve redistribution rights; see the [release audit](../../releases/PUBLIC_RELEASE_AUDIT.md).

## Reproduce the views

Use the [documented local setup](../../../README.md#getting-started) with authorized source access and external AI disabled, then open Chrome at a 1440×1000 viewport. Navigate Overview → Prepare & alerts → Grid insights. Select the communication stage and evidence/crew settings listed above. Disable Street map through its existing control for the evidence view. Wait for results and local fonts before capturing; keep the entire scenario/uncertainty copy intact.

For automated QA, the existing browser harness starts the normal API fixture on 18080 and Vite on 15173, and routes `/api/**` to that fixture. It blocks external requests. Portfolio capture used those same conditions, with zero browser runtime errors. Temporary capture scripts/reports were kept outside the tracked repository. No new screenshot dependency or product endpoint was introduced.

## File integrity

SHA-256 hashes below identify the reviewed, unmodified PNGs.

| File | SHA-256 |
| --- | --- |
| `overview.png` | `6a2a2dbc78d708102f39bcc6534c36dc765e6b24574b6b0182ba8cc945fda0d0` |
| `preparation.png` | `49314d8614cb6e0ec9858aa61397fdfa9870b85cee4275e4ec35c15bc4283322` |
| `communication-preview.png` | `8d04f745b40c216a5d67e9763547bf1124c96e0d8c26e1f95bd88a373caf43f6` |
| `grid-insights.png` | `8e655adb9601e66442eb435807195082faae1f16385a35a356e84f21b9ed075d` |
| `evidence.png` | `76e2adc1a09ee56c86d8b9b8b243c500f9b3ed5bb9abad98ae02654eeaa17118` |
