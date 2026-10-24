# Data audit

Audit date: 2026-10-24. Starting local revision: `6e35ee6` (“Project skeleton + challenge data”), preceded by `d7c8aea`. Working tree was clean. Existing dependencies: unpinned `geopandas`, `pandas`, `openpyxl`, `fastapi`, `uvicorn`. No frontend, server, tests, package lock, or product pipeline existed.

**Verdict: YELLOW.** The data supports a credible, explicitly simulated customer journey using validated paths and rule-based risk bands. It does not support calibrated outage probabilities, observed current outage status, or empirically calibrated restoration promises.

## Reproducibility and source integrity

`scripts/audit_data.py` is deliberately retained as a read-only inspection utility. It checks ZIP integrity, every GIS schema and geometry, identifier coverage, upstream graph structure, damage quality, and every workbook sheet. It produces aggregate JSON outside raw data; it neither extracts files nor builds product datasets. This is the only code added in this planning pass.

Run with Python 3.10+ and inspection dependencies `pyshp`, `pyproj`, `shapely`, `openpyxl`:

```sh
python scripts/audit_data.py --output /tmp/gridguide-audit.json
```

The audit was executed with Python 3.12.14, pyshp 3.1.6, pyproj 3.8.0, shapely 2.2.0 and openpyxl 3.1.5. Three small missing libraries were installed into a disposable temporary directory; bundled openpyxl was reused. No project runtime dependencies were installed or changed. To reproduce in an isolated environment, use a Python 3.12 interpreter with `python -m venv /tmp/gridguide-audit-venv`, install those four pinned inspection packages with that environment's pip, then run the command above with its Python. Do not install the entire product stack just to inspect data.

The JSON output is intentionally not versioned. [DATA_SCHEMA.md](DATA_SCHEMA.md) preserves every exact DBF field name, type, missing count, and unique-value count for this snapshot. The script's “missing” definition is null or blank/whitespace string; it does not silently convert `Unknown`, `0`, or other sentinel values to null.

The official repository was inspected at [revision 28a5520](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff). All four local files have exactly matching Git blob hashes. The local workbook lives under `data/raw/`; upstream places it directly under `data/`.

| Local file | Bytes | Git blob SHA-1 | Contents |
|---|---:|---|---|
| `data/raw/Data1.zip` | 19,210,707 | `baeeb0dc1c0419838972edc648101b535e604548` | 8 layers, 64 members; 222,111,975 expanded bytes |
| `data/raw/Data2.zip` | 12,683,324 | `12a3521bf24c427047e837d37391083ae98acdec` | 4 layers, 32 members; 146,303,688 expanded bytes |
| `data/raw/matched_upstream.zip` | 1,499,517 | `5d29b464d00a4067481c13d6bc47419591edfbe9` | `matched_upstream.txt`, 28,418,273 bytes |
| `data/raw/Install_Labor_HackOHIO.xlsx` | 24,161 | `dcfb1c2a29511df5487dcecf1e17dbfa493eaa4c` | 5 sheets |

All ZIP CRC checks passed. Every GIS stem below has `.cpg`, `.dbf`, `.prj`, `.sbn`, `.sbx`, `.shp`, `.shp.xml`, `.shx`. Encoding declarations are UTF-8. XML field aliases largely repeat the truncated DBF names; they do not supply a trustworthy expanded business dictionary. Do not invent full names from truncated labels.

## GIS inventory

Each filename below is the exact `.shp` name within its archive. All listed point layers are POINTZ; ignore Z for MVP because vertical semantics are not uniformly established. Lines are two-dimensional POLYLINE, read as LineString. All 12 layers parsed successfully; no empty/invalid geometries or zero-length lines were found in the geometry validity pass. Geometric validity does not establish electrical connectivity.

| Archive / file | Features | Geometry / horizontal CRS | Keys and useful fields | Purpose and limitation |
|---|---:|---|---|---|
| Data1 / `Customer_Clip.shp` | 117,642 | POINTZ / EPSG:4326 | `premise_nu`, `id`, `aep_xfmr_l`, `circuit_id` | Customer-to-path anchor; public aliases required |
| Data1 / `arcos_prod_damage_09_28_Clip.shp` | 1,659 | POINTZ / EPSG:4326 | `Circuit`, `Substation`, `Asset_Type`, `Inform_Wor`, `Report_Tim`, `Repaired`, `Repaired_D`, `Access_Iss` | Historical damage evidence, not current outage state or event outcomes |
| Data1 / `Fuse_Bank_Clip.shp` | 7,616 | POINTZ / EPSG:4326 | `id`, `location_n`, `upstream_l`, `circuit_id`, `aep_circui`, `aep_statio`, `normal_sta`, `mounting` | Protective dependencies; location labels are not unique |
| Data1 / `Pole_Clip.shp` | 107,013 | POINTZ / EPSG:4326 | `id`, `location_n`, `height`, `material`, `class` | Pole context and potential size lookup; absent from upstream path tokens |
| Data1 / `Primary_ExportFeatures.shp` | 62,788 | POLYLINE / EPSG:4326 | `id`, `circuit_id`, `aep_circui`, `aep_statio`, `mounting`, `location_n`, `location_1`, `Shape_Leng` | Map/context geometry; no validated directed node-edge network |
| Data1 / `Ambulance_Servi_Pairwis_Clip.shp` | 10 | POINTZ / EPSG:3857 | `PERMANENT_`, `FTYPE`, `FCODE`, `NAME`, `ADDRESS` | Optional public priority locations; exclude exact locations/names from MVP |
| Data1 / `Fire_Stations_E_Pairwis_Clip.shp` | 37 | POINTZ / EPSG:3857 | Same priority-layer schema | Optional aggregate context, not customer medical classification |
| Data1 / `Hospitals_Medic_Pairwis_Clip.shp` | 5 | POINTZ / EPSG:3857 | Same priority-layer schema | Precise facility coordinates and identifying attributes remain present |
| Data2 / `Transformer_Clip.shp` | 26,959 | POINTZ / EPSG:4326 | `id`, `location_n`, `upstream_l`, `circuit_id`, `aep_circui`, `mounting`, `a_phase_sp`, `b_phase_sp`, `c_phase_sp` | Strong first-hop join; per-phase specs are text, not a clean capacity column |
| Data2 / `Recloser_Bank_Clip.shp` | 331 | POINTZ / EPSG:4326 | `id`, `location_n`, `device_typ`, `upstream_l`, `normal_sta`, `circuit_id` | All 322 recloser token IDs fail direct GIS ID join; candidate location reconciliation is unverified |
| Data2 / `Switch_Clip.shp` | 900 | POINTZ / EPSG:4326 | `id`, `location_n`, `device_typ`, `normal_sta`, `upstream_l` | `upstream_l` blank in all 900; no ordinary Switch tokens in supplied paths |
| Data2 / `Secondary_ExportFeatures.shp` | 127,403 | POLYLINE / EPSG:4326 | Primary fields plus `spec_name`; `location_n`, `location_1` | 74,409 missing `location_1`; cannot assume complete service connectivity |

### Coordinates and geospatial rules

The customer extent is approximately longitude −80.252 to −79.647, latitude 36.995 to 37.480, in Virginia, not Ohio. Do not use Columbus weather just because this is HackOHI/O. Three facility layers use Web Mercator with a NAVD88 vertical definition; horizontal reprojection resolves to EPSG:3857. The other nine layers use WGS84 degrees. Normalize horizontal geometry to EPSG:4326 for maps, and use EPSG:32617 for regional metric distance checks. Always use longitude/latitude axis order at GIS boundaries; Leaflet positions use latitude/longitude.

`NEAR_DIST` ranges 0–0.000546791667619, and `NEAR_FID` ranges 482–63,094. Neither is a verified asset relationship or meter distance. No `NEAR_FID` joins to pole or primary `id`. The source FID table/units are not supplied. `Shape_Leng` and `report_len` also require unit validation before use. Do not treat line vertex order, crossing lines, or nearest geometry as power-flow direction.

## Topology: supported relationships and failures

`matched_upstream.txt` has 117,599 nonblank, headerless tab-separated records, one unique premise per record. The first token is a **string** premise identifier. Each later token has four `*`-separated fields:

```text
entity_table * entity_id * equipment_description * location_or_circuit_code
```

The observed order is customer → distribution transformer → protective/other upstream devices → circuit breaker. This interpretation is supported by 117,593 first-transformer GIS matches and 117,588 customer/terminal circuit agreements, not a live switching-state specification. Preserve source order and provenance. Customer identifiers have leading zeros in 11,774 topology records; never coerce them to numbers. Equipment keys are `(entity_table, entity_id_string)`, not location labels.

| Measurement | Result / implication |
|---|---|
| Customer `premise_nu` ↔ first topology token | 117,595 / 117,642 customer rows (99.960%); 47 missing paths |
| Topology premises absent from customer layer | 4 |
| Repeated/conflicting premise records; malformed lines; repeated nodes within a path | 0 each |
| Customer `aep_xfmr_l` → transformer `location_n` | 117,615 unique matches; 27 unmatched |
| Path first transformer → transformer `id` | 117,593 customer rows; 2 path-bearing customers fail |
| Customer transformer-location agreement after ID match | 117,566 / 117,593; 27 disagree |
| Customer transformer-circuit agreement after ID match | 117,591 / 117,593; 2 disagree |
| All non-circuit path nodes resolve by typed entity ID | 52,321 / 117,642 (44.475%); this is a coverage ceiling, not a full consistency-pass count |
| Unique topology equipment/circuit nodes; edges | 32,600; 32,551 |
| Graph union | Acyclic, but 60 nodes have more than one parent; not a single verified radial tree |
| Path length | 2–13 equipment/circuit nodes; customer is additional |
| Immediate-parent location agrees with GIS `upstream_l` | 28,785 / 31,900 raw comparisons; another 1,410 use the valid `CIRCUIT` terminal sentinel; 1,705 residual disagreements require investigation |

Unique topology types: Distribution 25,302; Step 108; Fuse 6,757; Hydraulic Recloser 286; Electronic Recloser 36; Sectionalizer 1; Circuit Breaker 110. There are no line, pole, ordinary Switch, or separate substation path tokens.

Typed ID matching resolves 25,300 / 25,410 transformer-entity nodes and 6,656 / 7,080 isolating-equipment nodes. The 534 unresolved non-circuit nodes comprise 322 reclosers, 101 fuses, 108 step transformers, one sectionalizer, and two distribution transformers. Of those, 328 have a unique location-and-type candidate, four have multiple candidates, and 202 have none. **Do not promote these candidates to confirmed identity automatically.** A bank versus installation identifier difference is a hypothesis requiring reconciliation. Among ID-matched nodes, two transformer location labels disagree; all 6,656 matched isolating-device location labels agree.

The 110 `eo_circuit` terminal nodes have no separate GIS geometry. Represent them as abstract circuit supply terminals. `aep_statio`/`Substation` are labels, not a located substation layer or demonstrated breaker-to-bus connection. Do not fabricate substation points or switching opportunities.

Duplicate location labels are substantial: fuse rows have 6,698 distinct `location_n` values for 7,616 rows; transformers 26,950 for 26,959; reclosers 330 for 331; switches 885 for 900. IDs are unique within each GIS layer. Exact typed ID joins take priority; never select the first match from a location-label join.

### Circuit mismatch discovered during falsification

Damage `Circuit` uses aliases such as `CIR72`; customer `circuit_id` uses padded codes. There are zero direct damage `Circuit` → primary `circuit_id` matches. Matching `Circuit` to primary `aep_circui` finds 1,652 rows, but that is a many-segment association, not a damaged-asset join. Seven damage rows have no alias match across the inspected GIS asset layers.

Across the layers there are 121 aliases; **14 aliases and 14 codes participate in contradictory mappings**. The aliases are `CIR2` through `CIR16`, excluding `CIR13`. For example, `CIR6` corresponds to code `0000005` in device layers and `0000006` in line layers. All aliases have a single station label, so adding station does not fix this conflict. Do not apply a guessed numeric offset. P0 must use a code/alias pair unique in both directions across relevant layers and consistent with the selected customer's path. Otherwise historical circuit evidence is unavailable and line overlays must be withheld or explicitly approximate.

## Damage records and probability feasibility

Exact attributes are listed in [DATA_SCHEMA.md](DATA_SCHEMA.md). Key findings:

- `Outage_Num` and `Incident_W` are 0 for every record; `Event` is `Default` for every record. They cannot identify incidents or storms.
- `Report_Tim` is DBF date-only, not a timestamp: 55 dates from 2022-10-01 through 2026-08-18. `Repaired_D` has 55 dates through 2026-09-04. Records span years but are not an exposure/event panel.
- `Repaired` is Yes for 1,583 and No for 76; **all 76 No rows still have a repair date**. These are not negative outage examples.
- 500 repair dates equal the report date; 1,159 occur later. No negative date differences. Calendar-day differences do not establish outage duration, work duration, or customer restoration time.
- 25 rows duplicate all DBF attributes; 103 duplicate coordinates beyond the first occurrence. On the narrower inspected-field set, 27 rows repeat. Do not conflate those measures or sum duplicate observations as damaged-unit quantities.
- `District`, `Crew_Area`, `Reporting_`, `Reporting1`, `TASK_Crew`, `TASK_Job_I`, `Status`, `Repaired_B` are entirely blank.
- `Access_Iss`: Yes 535, No 1,123, blank 1. `Special_Eq`: 286 nonblank, with nine categories; descriptive requests do not prove resource availability.
- `Longitude`/`Latitude` agree with point geometry within 0.000001°. There is no explicit quantity, outage-start time, customer restoration timestamp, current crew count, road graph, storm intensity, or event exposure denominator.

| `Asset_Type` | Records | `Inform_Wor` |
|---|---:|---|
| `primary` | 704 | `Damaged Wire` |
| `Pole` | 355 | `Damaged Pole` |
| `Fuse Bank` | 280 | `Damaged Switch` |
| `secondary` | 156 | `Damaged Wire` |
| `Transformer` | 74 | `Damaged Equipment` |
| `Recloser Bank` | 58 | `Damaged Switch` |
| `Switch` | 19 | `Damaged Switch` |
| `Capacitor Bank` | 6 | `Damaged Equipment` |
| `Light` | 5 | `Damaged Light` |
| `Step Transformer` | 1 | `Damaged Equipment` |
| blank | 1 | `Damaged Wire` |

**Supervised outage probability: NO-GO.** Damage rows are selected positive damage reports, not even confirmed premise-level outage positives. There are no verified non-outage controls, event IDs, observation windows, storm exposures, or ascertainment process. Unmatched customers and undamaged-looking assets cannot be labeled negative. Repair flags cannot become outage labels. Random row train/test splits would also leak repeated locations and likely storm clusters. Use the uncalibrated, explicitly defined scenario risk band in [MODEL_SPEC.md](MODEL_SPEC.md). Historical evidence is a small contextual indicator, not an empirical probability or a failure-rate denominator.

## Labor workbook

| Exact sheet | Used extent | Actual content / caveats |
|---|---|---|
| `CNC` | A1:G96 | 95 unique connector CU rows, `CD_CU`, `INSTALL_HOURS`, `REMOVE_HOURS` in A:C; E3:G3 summary formulas. Independent means 0.2151578947368421 install, 0.0448 remove agree with cached results. No zero-hour rows despite the generic note mentioning them. |
| `Labor time material related` | A1:D90 | Multiple separate tables, not one rectangular dataset. Crossarm, bracket, poles by height, transformers by kVA, anchor, lead, grounding, guying, dead-end, insulator, pin, recloser, secondary attachment, service, switch, fuse cutout summaries. |
| `Labor only work` | A1:E12 | `Original Intent`, `Anonymized Work Type`, `Anonymized Labor Description`, `INSTALL_HOURS`; E has no header. Restricted/backyard/off-road adders 0.5 each. D8 missing for Complex Work Location. Manual/difficult excavation rows have per-cubic-foot units in E5:E6. Later rows change layout and omit descriptions. |
| `Indirect Labor Multiplier` | A1:B3 | B1 = **4.5**; A3 says multiply labor hours to include driving, safety discussion, setup, etc. Apply once, not as an additional 450% and not plus another default travel multiplier. |
| `CU Group descriptions` | A1:B18 | 17 category descriptions. Descriptions alone do not supply rates or universal damage-to-CU mappings. |

Useful exact cells on `Labor time material related`: pole small/medium/large C12:D14; transformer size/counted references A19:D30; 100 kVA C25=1.2800000000000007 and D25=0.944; recloser A68:B70; service A78:B80; switch A83:B85; fuse cutout A88:B90, with A90=0.25600000000000017 and B90=0.12800000000000009. A transformer's `CU Count` is the number of reference CU definitions averaged, **not** a number of damaged units. Freeze these cell mappings with workbook hash validation.

The workbook does not state whether hours are person-hours or elapsed hours for a standard crew, nor define standard crew size. Values are installation/removal work references, not complete storm repair job durations. There is no supplied calibrated uncertainty distribution. Treat hours as provisional reference-crew effort only under the prominent assumption in MODEL_SPEC; ask an AEP mentor to clarify before claiming operational accuracy. Unsupported items (wire spans, lights, capacitors, step transformers, unspecified excavation) must not silently receive zero or a generic average. The first demo explicitly simulates one fuse cutout and one 100-kVA transformer unit.

## Privacy and absent sources

The package is not safe for indiscriminate browser/LLM exposure. Customer `address`, `address_nu`, `macss_mete`, `special_op` are blank, but `road_name` is populated in 117,577 rows; `city`, `anno_strin`, and `critical_c` are populated in every row. Customer coordinates remain precise. Priority-layer `NAME` and `ADDRESS` are populated. Asset fields include internal IDs, source-system strings, phase specifications, operational states, and ownership fields. Export a strict public allowlist; do not rely on a denylist or the word “anonymized.” Never infer medical needs from `critical_c`.

Absent locally: structure diagrams, standalone substation layer, road/access network, actual crew rosters, current weather, utility outage/alert account service, and priority-location-to-premise crosswalk. The official repository additionally has a [nine-page raster structure-drawing PDF](https://github.com/hackohio/aep_challenge_hack26/blob/28a5520262b71a9fbf753b3031abf67781ca66ff/docs/structure_drawings.pdf). Visual samples show transformer/cutout/bracket, conductor support, grounding, guying and pole assemblies. These can explain component scope but do not identify which actual assets or materials were damaged. Do not turn drawings into an automatic bill of materials.

## Validated candidate and remaining limits

For the pinned Data1 hash, **1-based DBF record 1077** in `Customer_Clip` is a reproducible internal selection for public alias `demo-a`. Its unique source path is Distribution → Fuse → Circuit Breaker; both non-circuit nodes resolve; the transformer is Overhead; customer/transformer/terminal circuit agrees; the code/alias mapping is unambiguous. The transformer `upstream_l` matches the fuse location; the fuse uses the `CIRCUIT` sentinel, consistent with the abstract terminal. Its path nodes have no conflicting parent. All three phase-spec strings say `100 kVA XFR PL`. Transformer and fuse points are 140.266 meters apart geodesically, supporting two distinct modeled worksites under the team's 50-meter grouping rule. There are 140 historical damage records with the same circuit alias. These are historical context, not current damage to this selected premise. Production preprocessing should derive and retain private stable keys, not use row offsets as runtime identifiers. The pinned row offset is only the audit locator.

Final falsification changed the plan: location-label joins were rejected; ambiguous circuit mappings were excluded; generic switches and substations were removed from claimed trace coverage; all positive-probability and learned-duration proposals were dropped; current damage and quantities became declared simulations; the first counterfactual became access rather than guaranteed crew speedup. Live weather cannot repair the missing labels or be paired with old damage as if simultaneous.

## Validation completed in the original planning pass

- Read the supplied five-page challenge and visually checked its requirements page; compared repository inventory and all four source blob hashes with the official pinned commit.
- Audited all 452,363 GIS features across 12 layers, all three archives, every topology line, and all five workbook sheets. Verified the golden candidate's identity, circuit, parent/sentinel, mounting and worksite-distance checks.
- Independently recomputed connector summary formulas and the golden base, restricted-access and extra-unit examples directly from workbook cells; results agree within floating-point tolerance.
- Verified Markdown links/code fences, parsed both JSON examples, checked Python syntax, and confirmed the audit utility rejects an output path inside `data/raw/` before processing.
- Rechecked raw SHA-256 hashes against the initial inspection and checked Git whitespace/diffs. No raw input, existing dependency file, or ignore rule changed. Disposable inspection downloads, renders, reports and libraries were removed after review.

That planning pass ran no product tests. The later implementation checkpoint is recorded below and in EXECUTION_PLAN.

## Implementation re-verification — October 24

The full audit was repeated before writing the engine. Source hashes, the row-1077 golden path, 140 historical circuit records, overhead mounting, three 100-kVA phase specifications, and 140.266 m worksite separation reproduced without discrepancy. The engine uses the pinned row only as an internal locator, derives the source premise and typed asset IDs at startup, and rejects changed files or inconsistent joins before evaluation.

Re-read the official challenge and every workbook sheet/label, including comments, defined names and document metadata. No comments or defined names clarify labor units; document metadata supplies no person-hour/crew-hour definition either. The previous unit ambiguity therefore remains. Installation/removal cells, restricted-access D2 and ILM B1 are read at runtime with source hashes and relevant recipe-label checks; no final demo durations are stored as calculation inputs.

The implemented CLI and 36 tests now verify the real-data path, independently recomputed labor arithmetic, deterministic risk, access behavior, private/public separation and immutable raw bytes. Minimal preparation is in memory; no derived file or raw edit is needed. Detailed commands and measured results are in [EXECUTION_PLAN.md](EXECUTION_PLAN.md).
