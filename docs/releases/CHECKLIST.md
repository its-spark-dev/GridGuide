# v1.0.0 owner review and release checklist

Review date: **November 3, 2026**. Branch: `chore/v1.0.0-portfolio-polish`.

**Ready for local portfolio review; official release BLOCKED on unresolved data rights and sensitive files/history.** The repository is intentionally already public. Visibility is context, not a release blocker. No push, tag, merge, or GitHub Release is authorized by this checklist.

`READY` means checked for this local preparation. `BLOCKED` means an unresolved issue prevents a responsible release as currently packaged. `NEEDS OWNER APPROVAL` marks a decision or action reserved for the owner. A passing check is not permission to publish.

| Item | Status | Evidence / next action |
| --- | --- | --- |
| Preserve implementation and original commits | READY | Documentation/media-only changes against `bb7c53c`; no runtime, model, API, data, pipeline, dependency, or test edits. Existing history retained. |
| Permission from all contributors | NEEDS OWNER APPROVAL | Confirm all three teammates agree to publication of their work and the intended license. |
| Complete team attribution | NEEDS OWNER APPROVAL | Preserve Git attribution; obtain missing preferred public names/handles. Do not infer roles or three people from author strings. |
| Hackathon provenance | READY | `bb7c53ce2e0733c6770c9de631a75df094407727` is labeled last known hackathon-period checkpoint. Exact submitted SHA is unconfirmed; confirm it only if external submission evidence becomes available. |
| AEP data redistribution and license verification | BLOCKED | No explicit grant found in inspected upstream materials. Resolve raw data, derived data, metadata, workbook, and screenshot/aggregate permissions. [Audit](PUBLIC_RELEASE_AUDIT.md). |
| Sensitive data in current files and repository history | BLOCKED | Raw GIS/topology and customer CSV with coordinates/identifiers/inferred support field remain in the tree and history. Approve a disposition or separate cleared distribution; do not silently rewrite history. |
| Credential scan and local staging safety | READY | No credential-pattern or local-key matches in inspected reachable objects; ignored `.env` excluded. Scope is bounded; remote-only refs and other copies are not certified. |
| Project software license | NEEDS OWNER APPROVAL | Confirm ownership, select code terms, and distinguish third-party materials. No root license added. |
| Third-party notices | NEEDS OWNER APPROVAL | Inventory prepared; existing Barlow OFL/source notice retained. Review artifact-specific dependency and map obligations before any compiled/hosted distribution. |
| README and documentation links | READY | Local targets/anchors and Markdown structure checked; no docs moved. Owner should inspect the final GitHub rendering after an authorized push. |
| README claims and architecture | READY | Compared with code, tests, and MODEL_SPEC. Diagram separates optional reference selection from deterministic numerical authority. |
| Test/build results | READY | 194 Python tests, 49 Chrome browser tests, generated-type consistency, CLI scenario checks, and production build pass. [Verification](VERIFICATION.md). |
| Setup and reproducibility statement | READY | Actual pinned environment exercised; required source files, Chrome, ports, and offline limits disclosed. No clean-clone installation or license-free reproduction claim. |
| Screenshots | READY | Five authentic 1440×1000 captures, visually reviewed; no synthetic UI, altered values, raw IDs, precise map coordinates, or declared personal needs. Publication rights remain covered by the data-rights gate above. |
| Optional public demo video | NEEDS OWNER APPROVAL | No verified public video URL found. Supply one if desired; it is not required for this release. |
| GitHub About description and topics | NEEDS OWNER APPROVAL | Suggested metadata below; nothing changed remotely. |
| Release notes | READY | [Draft text](v1.0.0.md) distinguishes hackathon implementation from later presentation work and deferred v1.1.0 improvements. |
| Version tag placement | NEEDS OWNER APPROVAL | After blockers and review, select the final approved commit for a new annotated `v1.0.0` tag. Do not tag the historical checkpoint as though it contains this documentation. No existing tags changed. |
| Push and merge | NEEDS OWNER APPROVAL | Review the local branch, then explicitly authorize the desired push/review/merge path. No remote changes made. |
| GitHub Release publication | NEEDS OWNER APPROVAL | Publish only after blockers are resolved and the final tag/commit and source archive are reviewed. No draft or published GitHub Release created. |
| Repository visibility change | READY | Not required: already intentionally public, confirmed by owner. Visibility left unchanged. Any later change requires a separate instruction. |
| LinkedIn / portfolio showcase | NEEDS OWNER APPROVAL | After rights review, choose approved images, team credits, and release link. No social post or message prepared for delivery or sent. |

## Suggested GitHub metadata

**About:** Explainable storm outage scenarios, dependency-aware repair planning, and customer guidance. Independent HackOHI/O 2026 prototype.

This replaces the current description's unqualified “risk prediction” emphasis with the implemented scenario scope.

**Topics:** `hackohio`, `hackathon`, `outage-management`, `decision-support`, `explainable-ai`, `geospatial`, `fastapi`, `react`, `typescript`, `python`.

**Website:** leave unset unless the owner supplies a verified working public demo. No live deployment or video URL is invented.

## Order of remaining work

1. Review the [data/history findings](PUBLIC_RELEASE_AUDIT.md), obtain rights clarification, and approve the distribution path. Resolve sensitive-data disposition before creating a tag or source archive.
2. Confirm contributor consent, public team credits, and software/third-party license decisions.
3. Review the README, screenshots, release text, and full local diff. Update resolved gate statements and verification dates before tagging; keep the historical checkpoint reference qualified.
4. Explicitly authorize any push and merge; inspect GitHub rendering and update approved metadata. If any code/data packaging changes are later approved, rerun the relevant verification.
5. Approve the final release commit; create and push a new `v1.0.0` tag only on instruction. Check the actual tagged tree and automatic source archive. Before pasting the draft into GitHub Releases, remove the local-review preface and resolve its repository-relative links to the approved tagged file URLs; then publish the approved text.
6. Use the approved release and assets for any separately authorized portfolio or LinkedIn announcement.
