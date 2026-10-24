# Verified geographic map — October 24, 2026

GREEN for the golden customer map and existing customer journey. This is source-derived, generalized geography, not a live outage map or an electrical-network reconstruction. Numerical credibility remains conditional on the labor-unit and calibration limitations in [MODEL_SPEC](MODEL_SPEC.md).

## Source audit and joins

The read-only audit used `backend.data.layer`, the existing prepared context, actual ZIP shapefiles and their `.prj` definitions. No archives were extracted or data files rewritten. The full 12-layer inventory remains in [DATA_AUDIT](DATA_AUDIT.md#gis-inventory); this slice directly reinspected these five layers:

| Archive / layer | Records | Geometry / horizontal CRS | Golden-scenario result |
|---|---:|---|---|
| Data1 / Customer_Clip | 117,642 | POINTZ / EPSG:4326 | Pinned customer record, verified against the supplied topology |
| Data2 / Transformer_Clip | 26,959 | POINTZ / EPSG:4326 | Exact typed upstream ID, location and circuit checks |
| Data1 / Fuse_Bank_Clip | 7,616 | POINTZ / EPSG:4326 | Exact typed upstream ID and circuit checks |
| Data1 / Primary_ExportFeatures | 62,788 | POLYLINE / EPSG:4326 | 1,746 source segments match the verified circuit code, alias and station; zero conflicts within that selection |
| Data2 / Secondary_ExportFeatures | 127,403 | POLYLINE / EPSG:4326 | 2,262 circuit-matching segments, zero alias/station conflicts; not displayed |

The primary join validates the relevant code/alias bijection rather than borrowing a nearest line. Known alias conflicts elsewhere in the dataset are not normalized away. Circuit association is verified; a directed service route through those lines is not. Supplied topology has no line/pole tokens establishing that route. Separate source records and multipart boundaries remain separate paths. No endpoints are snapped, new edges inferred or points shifted to separate icons.

Secondary geometry was inspected but omitted: incomplete endpoint fields do not establish a customer service path, and the additional layer adds detail without improving the validated upstream journey. There is no supplied geometry for the abstract Circuit Breaker terminal. It remains selectable as “schematic only,” with no marker or borrowed substation position. Unrelated poles, switches, reclosers and facilities are not displayed.

All displayed source layers already use WGS84, so their horizontal transformation to EPSG:4326 is an identity transformation. The implementation still reads the declared CRS and uses `Transformer(..., always_xy=True)`. Backend points are longitude/latitude; Leaflet explicitly receives latitude/longitude. Z is discarded. The existing audit identifies three facility layers with EPSG:3857 horizontal coordinates and a NAVD88 vertical definition; they are not mapped. A synthetic EPSG:3857 test checks transformation and multipart handling without adding facility data to the product.

The actual geography is Virginia. The interface retains the AEP Ohio-derived customer style but labels the data region accurately.

## Privacy and geometric limits

The public API exposes only demo aliases, approved labels, layer/provenance tags and generalized coordinates. Raw customer/equipment/circuit/station IDs, addresses, annotations, critical-customer flags, exact locations and GIS attribute dictionaries remain private. No customer search or arbitrary record browsing is added.

Points and every primary-line vertex reuse the existing `public_point` policy: centers of 0.01° cells, approximately 0.9 km east/west by 1.1 km north/south here. Customer and transformer share one cell and one **C + T** marker; the fuse has a separate **F** marker. This does not imply physical co-location. Rectangles identify the approximate point areas.

Quantization preserves source vertex order, removes consecutive duplicates and omits any part with fewer than two distinct public cells. Of 1,746 primary parts (14,509 source vertices), **165** remain visible and **1,581** collapse below the privacy grid. The public circuit extent is approximately longitude −80.125 to −80.035, latitude 37.175 to 37.245. Lines are dashed and labeled generalized circuit context. Coarse grid-like shapes and apparent intersections are consequences of generalization, not verified line routing or connectivity. Two nearby source worksites can display in different cells; never measure travel or repair distances from this view. The engine continues using its private validated metric geometry.

Generalization reduces precision; it does not guarantee anonymity against external data linkage. This is a curated local demo, not authorization to publish the full utility network.

## Backend and browser behavior

`backend/geography.py` prepares the map once during API startup after source hashes match the analysis context. No map request rescans GIS. `GET /api/map?location_alias=demo-a` returns `GeographicMap`, schema `map-v1`, with:

- Snapshot, EPSG:4326, privacy precision and region.
- Customer, transformer, fuse and terminal assets with nullable positions, geometry status and provenance.
- Primary-line paths with verified circuit association, `topology_verified: false`, source/omission counts and limitations.
- Reviewed privacy, missing-geometry and geography-versus-topology disclosures.

The current compact response is about 36.4 KB. Unsupported aliases receive a sanitized 404. Ambiguous primary identity or invalid geometry withholds the line overlay, preserving verified points. Map preparation failure returns a safe 503 on the map route while analysis remains available. No risk, restoration or customer-guidance calculation changed.

`GeographicContext.tsx` requests this DTO independently of scenario evaluation. The golden customer is selected initially; keyboard-operable asset buttons select/pan to supported geometry. Shared-cell markers stay shared. Selecting the terminal closes any equipment popup and explains the missing position. “Show full context” restores the circuit overview. The map appears immediately before the authoritative dependency schematic, with a direct link and explicit distinction between geography and dependency order. Existing shell, scenario controls and preparation/alerts remain intact.

## Optional basemap and failure handling

Leaflet 1.9.4 and its CSS are bundled locally. Optional standard OpenStreetMap tiles use `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, normal browser caching/referrer behavior, and visible linked contributor attribution. No key, bulk downloading, prefetching, offline tile storage or proxy was introduced. See the [Leaflet reference](https://leafletjs.com/reference.html) and [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/).

The browser sends coarse map tile coordinates and ordinary connection/referrer metadata to OSM, not customer IDs or application DTOs. “Street basemap (online)” can be turned off. Initial tile loading times out after eight seconds; tile errors remove only the basemap and show a retry control. A neutral background, locally served vector areas/lines, asset list, schematic and entire analytical journey remain usable. Map-API errors have their own retry and do not hide analysis. An internet connection is unnecessary after local dependencies are installed; the local backend must still be running.

## Verification and rehearsal

Before changes, the 57 existing backend tests, production build and browser journey passed. After implementation, **66 backend tests pass**, including nine geography tests covering real source identity/axis order, primary circuit joins, EPSG:3857 conversion, multipart boundaries, collapsed/invalid geometry, missing equipment geometry, ambiguous joins, public-field/coordinate privacy, cached API/schema behavior and map-only startup failure. Source hashes remain unchanged.

Run from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m backend.demo
npm --prefix frontend run types:generate
npm --prefix frontend run build
```

The golden CLI, strict TypeScript and production bundle pass. Chrome browser verification against the real API covered:

1. Two map markers representing three verified assets, 165 primary paths plus two privacy rectangles, default customer selection, keyboard asset selection and no terminal marker.
2. Live OSM tiles and attribution, street-layer toggle, tile-network failure and successful retry, map-API 503 and successful retry.
3. CLEAR **11–18**, RESTRICTED **16–25**, BLOCKED **unavailable/null**; HIGH risk invariant and displayed values/explanations equal API responses, including when tiles are blocked.
4. All four message lifecycle previews, preparation content equal API values, estimate-update selection, preview-only eligibility, keyboard controls, stale request suppression and analysis/initial-load error recovery.
5. Desktop 1440 px, tablet 768 px and mobile 390 px without horizontal overflow; desktop/mobile map screenshots reviewed; no uncaught browser errors.

The numerical core, teammate `pipeline/`, tracked raw/processed data and previous tests are unchanged. No additional messages, external model, weather integration or deployment was added.

Remaining highest model risk: the workbook's labor-hour basis and prediction calibration are unresolved. Highest map limit: privacy generalization removes fine geometry and does not support operational routing. Recommended next product task: a constrained explanation adapter grounded exclusively in the existing validated public result, with strict reference validation and the current deterministic explanation as fallback; keep it a separately authorized slice.
