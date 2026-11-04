# v1.1.0 stable portfolio finalization

The owner authorized a focused finalization PR, merge commit, annotated `v1.1.0` tag,
stable GitHub Release and two verified download assets. The starting main was
`c4611d628e42f1f04c9bd7015f7553033d4abd2d` (merged PR #14); its CI run
[41784454589](https://github.com/its-spark-dev/GridGuide/actions/runs/41784454589) passed.
No v1.1.0 tag or Release existed at baseline. This workflow authorizes no hosting,
new features, research experiments, history rewriting or additional license grant.

## Current package and historical evidence

[Stable manifest](package.json) · [download checksum](SHA256SUMS) ·
[preservation checks](preservation.json) · [local verification](verification.json).

- Stable standalone ZIP: **47 files**, **864,085 bytes**; SHA-256
  `62bb4afec34e50ab15da511d4c360ecec0c99e4deb29e8721316b18e151cebb2`.
- Previous approved integrated package: **47 files**, **863,720 bytes**; SHA-256
  `dbf1c3251fd5e297f223b424898f35f18ac27cbb182b24dd1656486cffc32ebf`.
- Product remains `1.1.0`; `/ready.release_status` becomes `stable`, and the shared
  footer reads “GridGuide 1.1.0 portfolio release.” No numerical/default/schema change.
- The only changed allowlisted source inputs are `backend/public_app.py`,
  `frontend/src/PublicShell.tsx` (compiled) and `deploy/README.md`. Dependent bundle
  filenames, HTML references, owned preparedness cache/worker hashes and the package
  manifest regenerate. The explicit packaging allowlist and dependency locks are unchanged.

The approved G9 and PR #12–14 recordings, screenshots, manifests, visual provenance and
review documents are historical snapshots and remain byte-identical to the baseline.
Their candidate/pending-review wording records that stage. In particular, the integrated
recording's footer and hash are not silently relabeled as the stable package. Its actual
export still replays against the stable package. The model specification, requirements
coverage and final benchmark report also retain their candidate-era introductions and
accepted scientific results. Current status is owned by the release notes, runtime and
this record. No new demonstration footage or numerical result is claimed.

## Executed verification

Local verification used Python 3.12.14, Node 26.5.0, Chrome 156 and a local arm64 Docker
engine. Final-head CI uses its unchanged pinned Python 3.12.14 / Node 22.22.0 / Ubuntu
amd64 setup and must independently match the stable archive hash before merge/publication.

- Strict frontend build, public build and generated API type consistency passed.
- Public Python lane: **102 executed, 102 passed** with source reads/network denied.
  Initial disposable test-environment attempts lacked test-only HTTPX and legacy import
  dependencies; after installing the existing pinned test dependencies, the full lane
  passed. No application fix or dependency-lock change was needed.
- Production Chromium browser suite: **6/6** directly and **6/6** in the local container,
  including actual downloaded export/replay, all prepared milestones, fixed default,
  explicit offline save/reopen/delete after restart and new stable metadata assertions.
- Container rehearsal: all **47 application files** verified, nonroot UID/GID 10001,
  read-only root, capabilities dropped, shutdown/restart and network-none comparison passed.
  This is not an OS vulnerability scan or a hosting/security certification.
- Runtime dependency installation/check and generated dependency notices matched existing
  locks/notices. Two independently built ZIPs matched byte-for-byte; recursive inspection
  and actual package startup passed. The historical integrated review JSON replay passed.
- Frozen checker passed **20 G2/G3, 66 G5, 10 G6 and 19 G7** file checks. No optimization,
  Monte Carlo, prediction or benchmark experiment was rerun.
- **316** historical preservation pins, **31** integrated-media checksums, **15** README
  image checksums, **four** map hashes and **four** raw-source hashes matched. README
  tables/gallery and original attribution are unchanged. Remaining source, model, default,
  research and media files have no diff from the baseline.

The 196 source-dependent and 51 research regression methods are not rerun for this
metadata-only finalization and are not counted as new passes. The accepted earlier
349-test/G2 reproduction evidence remains historical. Ordinary CI explicitly reports
unavailable/deferred lanes and runs the existing G6/G7, media, production/container and
dependency checks. Exact run and merged/tagged commit identities are recorded on the
finalization PR and GitHub Release, rather than self-referentially embedded in this commit.

## Publication boundary and completion checks

Only `gridguide-v1.1.0-public.zip` and `SHA256SUMS` are intended release attachments.
Build/inspect again from the exact merged main tree and require the recorded hash before
creating the annotated tag. Verify the remote tag target, stable/latest Release flags,
public downloads/checksums and README media after publication. Never move an existing tag.

GitHub's automatic source archives include original challenge material and are not
source-free. The standalone ZIP does not remove historical exposure or grant rights to
redistribute that material. All prior scientific, privacy, licensing, browser, accessibility
and dependency limitations remain in the [release notes](../v1.1.0.md). No website,
cloud resources, domain or operational service is part of this final portfolio release.
