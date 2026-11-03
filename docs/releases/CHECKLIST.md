# v1.0.0 release checklist

Updated November 3, 2026. Branch: `chore/v1.0.0-portfolio-polish`.

**Ready for owner review and authorized PR submission.** The owner accepts the existing challenge data as a release input and directs preservation of the original implementation, files, and history. Missing upstream license text alone is not a blocker. No concrete redistribution prohibition was identified in the inspected materials; no new license grant is claimed.

The previously identified customer identifiers/coordinates, inferred `life_support` field, and workstation metadata remain disclosed in the [assessment](PUBLIC_RELEASE_AUDIT.md). They are retained under the owner’s decision. No further broad audit, sanitization, history rewrite, or separate repository is planned.

| Item | Status | Evidence / decision |
| --- | --- | --- |
| README, documentation, screenshots | READY | Five genuine captures; provenance and evidence limits retained; local links checked. |
| Architecture | READY | Mermaid flow reviewed against code; verify GitHub rendering once a push is authorized. |
| Implementation and history | READY | Original runtime, data, dependencies, tests, and pipelines unchanged. |
| Challenge data | READY | Owner accepts existing inputs and retention; no additional permission is inferred. |
| Concrete exposure findings | READY | Disclosed in the assessment; retained under the owner’s instruction. |
| Secrets and staging | READY | Earlier bounded scan found no credential matches; no secrets staged. |
| Tests/build | READY | 194 Python tests, 49 browser tests, build, generated types, CLI and startup passed; see verification record. |
| Contributor publication consent | NEEDS OWNER APPROVAL | Confirm team agreement for the official release; preserve existing attribution without inventing identities or roles. |
| Complete team credit | NEEDS OWNER APPROVAL | Optional named credit awaits confirmed preferences; current README accurately credits three teammates collectively. |
| Software license | READY | No new license is added for v1.0.0. Any later license requires owner/contributor agreement. Existing third-party notices retained. |
| Demo assets | READY | Screenshots included. Public video is optional and no URL is invented. |
| PR text and release notes | READY | Local PR body prepared; release notes are the v1.0.0 changelog. |
| Metadata | NEEDS OWNER APPROVAL | Suggested About/topics below; no remote changes. |
| Tag | NEEDS OWNER APPROVAL | New annotated `v1.0.0` on the approved main merge commit; never on the earlier checkpoint. |
| Push, PR creation, merge, release publication | NEEDS OWNER APPROVAL | Execute only after explicit authorization for each requested scope. |
| Visibility | READY | Intentionally public; unchanged. |

## Metadata suggestion

About: Explainable storm outage scenarios, dependency-aware repair planning, and customer guidance. Independent HackOHI/O 2026 prototype.

Topics: `hackohio`, `hackathon`, `outage-management`, `decision-support`, `explainable-ai`, `geospatial`, `fastapi`, `react`, `typescript`, `python`.

## Release sequence

1. Owner reviews the local branch and confirms team agreement for the official release.
2. After explicit push/PR authorization, push this branch and create a PR against `main` using [PR_BODY.md](PR_BODY.md). Inspect README images and Mermaid on GitHub.
3. After explicit merge authorization, merge with a merge commit, preserving branch commits; do not squash or rebase the original history.
4. Fetch the merged main, verify its exact SHA and reviewed tree, and recheck that `v1.0.0` does not exist locally or remotely.
5. After explicit tag authorization, create and push an annotated `v1.0.0` on that approved merge SHA.
6. After explicit publication authorization, publish [v1.0.0.md](v1.0.0.md) as the release body. Its tagged-file links become valid when the tag is pushed. Review the automatic source archive, which intentionally includes the existing data.

The last known hackathon-period checkpoint remains `bb7c53ce2e0733c6770c9de631a75df094407727`; the exact submitted SHA is unconfirmed. Version labels already used by individual packages/APIs are unchanged: v1.0.0 names this repository release, not a runtime/package migration.
