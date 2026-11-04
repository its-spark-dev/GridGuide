# Phase 9 — v1.1.0 release-candidate preservation (G9 review)

> Historical G9 packet: PR #11 was owner-approved and merged, followed by the approved
> continuity correction in PR #12. The original evidence, hashes and review-time
> checklist below are retained. Current release-facing media and package identity:
> [integrated demonstration](../media/v1.1.0-integrated/README.md). No publication or
> deployment authorization follows from those merges.

**Recommendation: Go for independent G9 review of the local fictional portfolio
candidate; no approval is self-issued. No-Go for public hosting under current evidence.**
Merge, v1.1.0 tagging, GitHub Release publication and deployment remain unauthorized.

Base main: `f6165cc32a4a2d4f9b8b7e543782b53c4a14dde2`.
Branch: `feat/v1.1-phase9-release-candidate`. [PR #11](https://github.com/its-spark-dev/GridGuide/pull/11).
Frozen release-candidate **application/capture-code commit**:
`a793b5c18f3962461085b495d72198a5e59235b4`.
The application payload is unchanged from `04b44cc64ddaf7f352e7ca18c8be0b158ac9d3ca`; the capture tool then received a cleanup correction. Later commits add documentation and authentic evidence only. The final PR head, including
this packet, is recorded exactly in the PR and in CI's `candidate.json`
(`candidate_head_sha`; the separately recorded tested checkout may be GitHub's merge ref).
This avoids pretending that a committed document can contain its own commit hash.
The distribution manifest binds the same candidate payload across those evidence commits.

## Release-readiness inventory and scope freeze

| Category | Disposition |
|---|---|
| Completed product | Six fictional customer scenarios/18 prepared frames, power-path inspection, generic offline kit, explicit historical snapshot, eight operator cases, four policies, optional frozen CP-SAT, bounded precedence override, review invalidation, JSON/text export and replay |
| Completed engineering | Independent scheduling validation, frozen benchmarks, evidence gates, conditional simulation CLI, source-free CI, allowlisted package, one-origin nonroot container and local outage rehearsal |
| Intentionally deferred/excluded | Detailed G5 UI, live crew editing, arbitrary graphs/locations, unrestricted solving, trained outage probabilities, dispatch, messaging, accounts and public hosting |
| Scientific findings | G3 failed promotion target; G4 evidence-bounded No-Go; G5 195 stable/15 unstable combinations with assumption-based fixed-timetable semantics |
| Security/legal/accessibility limits | Retained scoped dependency advisories, unexecuted OS scan, no software license/data redistribution grant, historical exposure, Chromium-only coverage, missing detailed VoiceOver evidence, storage eviction and non-authenticating hashes |
| Preparation blockers | None found in executed candidate checks; independent owner G9 disposition is pending |
| Public-host blockers | Current OS/container assessment and host-specific HTTPS, allowed-host, proxy, slow-client and resource-control review; separate deployment authorization |

Only product version metadata, narrow snapshot compatibility and verification/capture
code changed. No data acquisition, model, tuning, baseline, numerical profile or speculative
UI was added. Product 1.1.0 is visible in the two public footers and `/ready`; internal
model/evidence/schema IDs and older composition metadata retain their historical meaning.
New snapshots record 1.1.0; only validated 1.1.0 and historical `v1.1-phase6` records are
accepted. Unknown strings, non-string versions and private fields remain rejected.
Current asset hashes rebuild the scoped worker without changing approved frame hashes.

## G1–G9 acceptance matrix

Owner approvals below come from the recorded review instructions and merged history;
historical unchecked boxes in old packets are not rewritten as new scientific evidence.

| Gate | Evidence / accepted outcome | Status |
|---|---|---|
| G1 | [Evidence register, feasibility and synthetic isolation](V1_1_0_PHASE1.md); licensing, observation coverage and data-use limitations explicit | Owner approved/integrated |
| G2 | [Frozen suite, four policies, independent validator/oracle](V1_1_0_PHASE2.md) | Owner approved/integrated; fresh standard replay matches |
| G3 | [Valid experiment, failed 5% median target](V1_1_0_PHASE3.md); limited cluster inference, no blind holdout, secondary regressions retained | Owner approved/integrated; no default promotion |
| G4 | [Evidence-bounded No-Go](V1_1_0_PHASE4.md); no trained model or real-data split validation | Owner approved/integrated; ledger replay identical |
| G5 | [Fixed-timetable simulation and convergence limits](V1_1_0_PHASE5.md) | Owner approved/integrated; all 15 failures preserved |
| G6 | [Fictional paths and offline persistence](V1_1_0_PHASE6.md) | Owner accepted human-reported passes with missing detailed speech/focus observations; no new manual claim |
| G7 | [Bounded comparison, override, review/export](V1_1_0_PHASE7.md) | Owner approved/integrated; frozen-only CP-SAT and G5 UI deferral |
| G8 | [CI, package and preparation infrastructure](V1_1_0_PHASE8.md) | Owner approved; OS-scan gap accepted for preparation only; hosting not authorized |
| G9 | This packet, [final report](../benchmarks/v1.1.0.md), [reproduction](../REPRODUCING_V1_1.md), [candidate notes](../releases/v1.1.0.md) and [demo](../media/v1.1.0/README.md) | **Pending independent review** |

## Fresh verification versus inherited evidence

| Actually executed in Phase 9 | Result |
|---|---|
| Full authorized Python suite | 349 passed; no failures/errors/skips |
| Final public Python lane | 102 passed; source/network-denial checks retained |
| Original browser suite | 49 passed |
| Final G6/G7 browser suite | 21 passed, including new strict version/backward-compatibility check; mobile/keyboard/axe and worker migration checks included |
| Final extracted-package / container production browser | 3 / 3 passed, including actual JSON **and text** downloads, replay, offline browser restart, shutdown and recovery |
| Strict build / supported API-type generation | Passed; generated TypeScript unchanged |
| G2 standard CLI + report generation | 278 cases × four policies = 1,112 runs, zero failures/invalid schedules; numerical hash exactly matches frozen G2 |
| Golden CLI / exact legacy plan lane | Passed / 24 passed |
| Four source pins / historical artifact hashes | Matched; G2/G3 20, G5 66, G6 10, G7 19; G8 evidence also unchanged |
| G4 cached decision | Byte-identical No-Go |
| Fresh hash-locked runtime install | Passed in separate environment; container and CI install independently |
| Fresh sparse source-free clone/build | Raw/processed directories absent; fresh npm install/build produced the identical ZIP |
| Recursive package/image checks | 38 exact files; every application image-layer file verified; no protected source/credential-pattern finding |
| Docker operation | Nonroot, read-only/cap-drop/no-new-privileges, readiness, stop/start and network-none comparison passed |
| Dependency checks | Fresh Python/npm assessments retain accepted G8 findings; no new undispositioned finding |

Reports and complete sample measurements are in [`docs/research/phase9/`](../research/phase9/).
The full Python run preceded the final strict snapshot-parser guard; the final 102-method
public and 21 browser checks were rerun after that guard. The unchanged legacy numerical
suite is not misrepresented as rerun for a frontend-only correction. No failed recording
attempt is counted as successful application verification.

**Not rerun/not executed:** full G3 optimization evaluation, full G5 Monte Carlo caches,
real-data prediction/split validation, empirical calibration, manual VoiceOver and
non-Chromium browsers, external-host load/availability tests, OS vulnerability scan.
Historical G3/G5 numerical reproduction remains inherited evidence. G2 was freshly rerun
for reproducibility only, with unchanged data, policies, budgets and report methods.

Ordinary public CI reports **196 source-dependent tests unavailable** and **51 research
tests deferred**, never passed. The local full suite executed those regression methods;
that does not mean the full research experiments ran. CI also tests generated contracts,
21 G6/G7 browser checks, 3 package and 3 container checks, pinned installs, notices and
dependency dispositions. CI status and exact head are linked from PR #11; raw test counts
and candidate identity are machine-readable in the verification artifact.

## Distribution, demonstration and provenance

Candidate ZIP SHA256:
`2b5e55549bf7714af50fb2431fcc5b21cd0e0d8ca22eb875c0614bb2dd1da82d`.
[Complete manifest](../research/phase9/package.json) records every path, content hash and
byte count. Only the inspected extraction is a Docker context. Dependency locks/notices
are unchanged; `THIRD_PARTY_NOTICES.md` and all original attribution remain intact.
The [reproduction guide](../REPRODUCING_V1_1.md) covers acquisition, exact inspection,
fresh installation, local container, actual journeys/replay and three separate test lanes.

Reference host: Apple M4 Pro, 12 cores, 24 GiB, macOS 26.6.2; Python 3.12.14;
local Node 26.5.0, CI Node 22.22.0; Chrome 156.0.8078.80 / Playwright 1.64.1;
Docker 29.8.1, arm64 locally and Ubuntu amd64 in CI. Host/runtime observations are not
SLA commitments. No public endpoint executes a new optimizer: optional comparison loads
frozen G3 output and revalidates it. The two-second solver budget is not falsely attached
to current HTTP measurements; G3 fallback checks are preserved regression evidence.

The demonstration uses actual candidate browser footage, authentic screenshots, explicit
caption timings and an actual CLI transcript from its downloaded review. The script
stops the real service and disables networking for the offline scene. See the
[media provenance/recording status](../media/v1.1.0/README.md). Earlier G8 screenshots are
not substituted as current proof. This is automated demonstration evidence, not human
accessibility acceptance. Browser restart is additionally verified by production tests.

## Security, licensing and preservation decision

Five unique retained Starlette advisories have G8's documented scope mitigations or
non-reachability; ten audit records include duplicates. Three moderate npm affected
packages remain excluded build-tool dependencies, with no high/critical npm findings.
The fresh Docker Scout attempt again requires login: OS CVE scanning is **unexecuted**,
not passed or proof of a vulnerability-free image. No credential/account/hosting purchase
was made. Application-layer scanning is not an OS assessment or public security certification.

Public hosting remains blocked pending current OS/container and host-security review,
plus explicit authorization. The current scope is local portfolio/reproduction preparation.
No project-wide software license or additional source-data publication right is inferred;
relevant rights-holder agreement is required. Original source exposure in Git history is
not repaired by this package. Original three-person hackathon attribution, teammate
guidance, pole-replacement work, raw/processed data and v1.0.0 tag/commit remain preserved.

Scientific limits do not disappear at release: the fixed baseline remains default;
0.351% combined versus 0.174% incremental gains are distinct and the 5% median target
failed. G4 remains evidence-bounded No-Go. All G5 convergence failures, unresolved outcomes,
case-level critical/fairness regressions and absence of empirical calibration remain visible.
No guaranteed support or dependency-maintenance SLA follows from preservation.

## Final acceptance checklist

- [x] Feature freeze; product versions aligned without renaming numerical identities.
- [x] Four-category final report, tested reproduction and release-candidate notes.
- [x] Authentic candidate demonstration and documented capture/replay provenance.
- [x] Fresh public/authorized verification with unavailable/deferred work explicit.
- [x] Exact package manifest, hashes, source exclusion and attribution/history preservation.
- [x] Security/license/accessibility/scientific limitations and hosting prerequisites explicit.
- [ ] Independent reviewer accepts G9 evidence and the bounded release scope.
- [ ] Owner separately authorizes merge, tag and Release publication as applicable.

The remaining work is review disposition and authorized publication, not another feature
phase. The original 4–6 engineering-day estimate was provisional; this agent-assisted
session is not a measurement of equivalent human effort. No further feature expansion,
automatic next phase or public deployment is proposed.
