# Continuity correction verification

Local environment: macOS 26.6.2 arm64 / Apple M4 Pro, Python 3.12.14,
Node 26.5.0, Chrome 156.0.8078.80, Playwright 1.64.1. No external provider.
CI additionally exercises the production source-free package on Linux; see the PR's
exact-head GitHub Actions run rather than interpreting the local evidence as Linux proof.

| Check | Actual result / evidence |
|---|---|
| Full Python suite | [349 passed](python.log), including source-dependent and research tests |
| Source-denying public Python lane | [102 executed/passed](public-tests.json); no source/network fallback |
| Actual detached v1.0.0 frontend + API | [49 browser tests passed](v1-browser.log) |
| Current authorized challenge-local frontend + API | [49 browser tests passed](challenge-browser.log) |
| G6/G7 real-service browsers | [21 passed](preparedness-operator-browser.log), including state binding, all fictional path states, axe, snapshot lifecycle and offline restart |
| Actual extracted public package | [6 passed](package-browser.log), including all 18 frames, invalid-artifact/mode rejection, 1440/390/320px, keyboard, axe and export replay |
| Actual nonroot container | [Runtime/layer/network-none verification](container.json); [six production browser tests](container-browser.log) |
| TypeScript/build/schema | Strict TypeScript, normal and public Vite builds passed; generated API types have zero diff |
| Golden CLI | Passed; numerical model unchanged |
| Frozen evidence | [20 G2/G3, 66 G5, 10 G6, 19 G7 files](frozen.json) verified |
| Broader preservation | [Exact per-file bytes](preservation.json), compared with `ae6d9c4` before commit |
| Public artifact | [47-file exact manifest](package.json), archive reinspection and deterministic duplicate-build equality tests |

Archive SHA-256: `dbf1c3251fd5e297f223b424898f35f18ac27cbb182b24dd1656486cffc32ebf`.
The ZIP is a local/CI review artifact, not a published release asset. No deployment.
Every extracted byte, including the four original fonts and OFL/source notices, is
allowlisted. The two unchanged catalogs and G6 frames keep their approved pins. No
raw/processed data, `.git`, environment file, source loader, provider code or Leaflet
runtime enters the archive. Root and operator pages are not in the offline cache.

The full suite preceded the last presentation-only refinements; the public Python
lane, G6/G7 tests, production package/container tests and strict build were run on
those final refinements. No numerical/backend test dependency changed afterward.

The initial public axe audit caught a brand accessible-name/visible-label mismatch.
It was corrected and affected suites rerun to zero serious/critical findings. This
is automated Chromium evidence, not a new human VoiceOver result or accessibility
certification. Existing detailed speech/focus gaps remain documented.

Reproduce the applicable checks:

```sh
npm --prefix frontend run build
.venv/bin/python scripts/build_public_frontend.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_test_lane.py --lane public --report /tmp/continuity-public.json
.venv/bin/python scripts/check_frozen_artifacts.py
npm --prefix frontend run types:generate
git diff --exit-code -- frontend/src/api.generated.ts
npm --prefix frontend test
cd frontend
npx playwright test -c playwright.preparedness.config.ts
```

Build/inspect an archive with `scripts/package_demo.py`, install the hash-locked runtime
outside its extraction, then run `playwright.distribution.config.ts` with explicit
`GRIDGUIDE_PACKAGE` and `GRIDGUIDE_PUBLIC_PYTHON`. Add `GRIDGUIDE_CONTAINER` to exercise
the Docker image, using the extracted package as its only build context. The existing
[reproduction guide](../../REPRODUCING_V1_1.md) documents these commands and runtime bounds.
[Capture instructions](../../media/continuity/README.md) reproduce the visual comparison.

Accepted limitations remain: G3 failed promotion, no blind holdout, G4 evidence-bounded
No-Go, all 15 G5 unstable findings, synthetic/non-calibrated timing, Chromium-only
coverage, storage eviction, same-origin compromise, non-authenticating checksums,
retained dependency advisories, unexecuted OS CVE scan and unresolved licensing/history
exposure. None is reclassified by this UX correction. Public hosting requires a new
current OS/container and host-controls review and separate authorization.
