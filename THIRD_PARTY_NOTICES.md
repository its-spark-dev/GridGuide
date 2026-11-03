# Third-party materials and license status

This inventory records materials used by the preserved application. It is not a project license or a grant of rights to AEP data. No project-wide software license has been selected. The released snapshot retains its existing third-party notices.

| Material | Local evidence and release handling |
| --- | --- |
| AEP challenge GIS, upstream topology, and labor workbook | Four tracked raw files, plus derived CSVs. The [pinned upstream repository](https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff) has no license file or explicit redistribution grant in the documents inspected. These inputs remain in the released repository. No concrete redistribution prohibition was identified in the inspected materials, and no additional permission grant is inferred. The [publication assessment](docs/releases/PUBLIC_RELEASE_AUDIT.md) records the unresolved privacy/permission findings and retention decision. |
| Barlow fonts by Jeremy Tribby | Four unmodified WOFF2 files. Preserve [OFL 1.1](frontend/public/fonts/OFL.txt) and the [source/revision notice](frontend/public/fonts/SOURCE.txt) with redistributed fonts. |
| Leaflet 1.9.4 | BSD-2-Clause in installed package metadata and its license file. Preserve the applicable notice when distributing a compiled application. |
| React and React DOM | MIT in the pinned packages. Preserve applicable notices in redistributed bundles. |
| Optional OpenStreetMap tiles | Existing UI includes linked contributor attribution. Tiles are fetched from the standard tile service, not bundled or cached for offline redistribution. Review the [tile policy](https://operations.osmfoundation.org/policies/tiles/) for any future hosting change. The evidence portfolio screenshot includes live OpenStreetMap tiles with contributor attribution visible; the other four captures block external requests. |
| Python and frontend dependencies | [Pinned engine dependencies](requirements-checkpoint.txt), [web dependencies](requirements-web.txt), and [npm lockfile](frontend/package-lock.json) record versions. Direct installed Python packages declare MIT or BSD-3-Clause; the npm lock includes MIT, Apache-2.0, ISC, BSD, Python-2.0, CC-BY-4.0, and MIT-or-CC0 terms. This is an inventory, not a complete distribution-compliance review. |

The historical pipeline has a separate, unpinned [requirements file](requirements.txt). It is preserved and is not installed by the dashboard setup. Optional Gemini/OpenAI services have their own account and service terms; no account access or credentials are distributed.

## Project license status

A future software license requires agreement from the relevant contributors and rights holders. No license choice is implied by this release. A project code license would not extend to AEP datasets, external reference materials, fonts, or dependencies beyond their own terms.

For any later binary, hosted, or downloadable application distribution, review the complete transitive dependency notices, font notices, and map-provider requirements for that artifact. The repository does not include tracked `node_modules`, virtual environments, or compiled frontend output.
