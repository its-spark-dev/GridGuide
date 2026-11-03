# Third-party materials and license status

This inventory records materials used by the preserved application. It is not a project license or a grant of rights to AEP data. No root `LICENSE` was present at the audited checkpoint, and this documentation pass does not add one.

| Material | Local evidence and release handling |
| --- | --- |
| AEP challenge GIS, upstream topology, and labor workbook | Four tracked raw files, plus derived CSVs. The [pinned upstream repository](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff) has no license file or explicit redistribution grant in the documents inspected. The owner accepts these existing challenge inputs for v1.0.0 and directs their preservation; this is not a new license grant. See the [audit](docs/releases/PUBLIC_RELEASE_AUDIT.md). |
| Barlow fonts by Jeremy Tribby | Four unmodified WOFF2 files. Preserve [OFL 1.1](frontend/public/fonts/OFL.txt) and the [source/revision notice](frontend/public/fonts/SOURCE.txt) with redistributed fonts. |
| Leaflet 1.9.4 | BSD-2-Clause in installed package metadata and its license file. Preserve the applicable notice when distributing a compiled application. |
| React and React DOM | MIT in the pinned packages. Preserve applicable notices in redistributed bundles. |
| Optional OpenStreetMap tiles | Existing UI includes linked contributor attribution. Tiles are fetched from the standard tile service, not bundled or cached for offline redistribution. Review the [tile policy](https://operations.osmfoundation.org/policies/tiles/) for any future hosting change. The portfolio screenshots use the vector fallback with external requests blocked. |
| Python and frontend dependencies | [Pinned engine dependencies](requirements-checkpoint.txt), [web dependencies](requirements-web.txt), and [npm lockfile](frontend/package-lock.json) record versions. Direct installed Python packages declare MIT or BSD-3-Clause; the npm lock includes MIT, Apache-2.0, ISC, BSD, Python-2.0, CC-BY-4.0, and MIT-or-CC0 terms. This is an inventory, not a complete distribution-compliance review. |

The historical pipeline has a separate, unpinned [requirements file](requirements.txt). It is preserved and is not installed by the dashboard setup. Optional Gemini/OpenAI services have their own account and service terms; no account access or credentials are distributed.

## Owner decision

Confirm ownership and publication consent with all three teammates before choosing a software license. MIT is a possible simple choice for team-authored code **if all relevant owners agree**; it has not been selected or applied. A code license must not purport to license AEP datasets, external reference materials, fonts, or dependencies beyond their own terms.

For any later binary, hosted, or downloadable application distribution, review the complete transitive dependency notices, font notices, and map-provider requirements for that artifact. This release preparation does not commit `node_modules`, virtual environments, or compiled frontend output.
