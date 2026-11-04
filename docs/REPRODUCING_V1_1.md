# Reproducing GridGuide 1.1.0 release candidate

Use the [G9 evidence packet](planning/V1_1_0_PHASE9.md) for the tested candidate commit,
CI link, current manifest and checksums. There is no v1.1.0 tag or published Release yet.
Do not substitute the historical G8 ZIP for the version-aligned candidate.

## 1. Required public candidate verification

### Acquire and inspect the standalone package

Open the candidate PR's successful **Synthetic verification** Actions run and download
the **synthetic-verification** artifact. These CI artifacts expire after 14 days; this is
review distribution, not a permanent release asset. Extract the outer verification ZIP
outside the repository. Its `artifacts/phase8/gridguide-public.zip` is the standalone
package (the CI directory name is historical). Compare its SHA256 to
[`research/phase9/package.json`](research/phase9/package.json) from the reviewed commit,
then extract into a new directory. Python 3.12 is required; set `GG_PYTHON` to its actual
executable. The local verification used the existing `.venv/bin/python` solely to create
a new environment; CI/container use freshly installed Python 3.12.14.

```sh
export GG_PYTHON=python3.12  # or absolute path to your Python 3.12 executable
"$GG_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3,12)'
"$GG_PYTHON" -m zipfile -e /path/to/synthetic-verification.zip /tmp/gridguide-verification
"$GG_PYTHON" -c 'import hashlib; from pathlib import Path; print(hashlib.sha256(Path("/tmp/gridguide-verification/artifacts/phase8/gridguide-public.zip").read_bytes()).hexdigest())'
# Continue only if that hash matches the reviewed package.json archive_sha256.
"$GG_PYTHON" -m zipfile -e /tmp/gridguide-verification/artifacts/phase8/gridguide-public.zip /tmp/gridguide-public
cd /tmp/gridguide-public
export PYTHONDONTWRITEBYTECODE=1
"$GG_PYTHON" -c 'from pathlib import Path; from backend.public_integrity import verify_tree; verify_tree(Path.cwd()); print("exact tree verified")'
"$GG_PYTHON" -m venv /tmp/gridguide-runtime
/tmp/gridguide-runtime/bin/pip install --require-hashes -r deploy/requirements.lock
/tmp/gridguide-runtime/bin/pip check
/tmp/gridguide-runtime/bin/python deploy/serve.py
```

Open http://127.0.0.1:8000/; `/ready` must report product_version `1.1.0`,
release_status `release-candidate`, synthetic mode, no external AI and no interactive solver.
Keep the virtual environment, downloads and exports **outside the immutable extracted
tree**. Startup rejects extra files, including caches. Install/build needs registry access;
installed operation does not. No source records, keys, `.env` or paid service is needed.
Hashes establish consistency, not authenticated origin: obtain the expected hash through
the reviewed commit. The complete 38-file manifest is in `package.json` and the package's
`PUBLIC_MANIFEST.json`; the latter excludes its own recursively impossible self-hash.

### Container path

From that same extraction, after stopping the Python server if it owns port 8000:

```sh
docker build -f deploy/Dockerfile -t gridguide-rc .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m -p 127.0.0.1:8000:8000 gridguide-rc
```

The context must be the inspected extraction, never a broad repository checkout.
Python base digest, runtime hashes and dependency notices are pinned. UID/GID 10001,
SIGTERM, readiness, actual outage/restart and network-none calculations were verified.
Do not treat local HTTP or these resource bounds as an approved public-host configuration.
Before hosting, assess current OS/container CVEs and HTTPS, explicit allowed hosts,
reverse proxy, slow-client and resource-limit controls. There is no deployment permission.

### User journey and replay

1. In `/preparedness/`, inspect an ordered fictional path. Select milestones, then blocked
   and missing-evidence cases. Unavailable full restoration stays unavailable.
2. Enable/check the offline kit. Explicitly save a snapshot. It is historical immediately.
   Stop the service, restart the browser with networking disabled and reopen the saved
   snapshot. Numerical controls remain disabled. Generic guidance remains; storage can
   still be denied/evicted. Reconnect, refresh and delete/reset storage when finished.
3. Open `/operator/` while connected. Compare all four baselines on the same inputs;
   inspect critical/fairness regressions. Optional CP-SAT is frozen, not a new solve.
4. Add a permitted precedence edge. The service recomputes; cycles fail validation.
   Changing settings/reason invalidates review. Complete all five acknowledgements,
   select a structured reason, then download JSON and the readable summary.
5. Independently replay your own downloaded JSON outside the package:

```sh
cd /tmp/gridguide-public
PYTHONDONTWRITEBYTECODE=1 /tmp/gridguide-runtime/bin/python scripts/replay_review.py /path/to/review.json
```

Replay rebuilds comparisons, bindings, metrics and explanations. It does not authenticate
a reviewer or certify operational decisions. The operator page is not cached offline.

### Build and test from an authorized code checkout

If the temporary CI artifact has expired, acquire a sparse source-free build checkout
instead of checking out the repository's original data. These paths match the tested
CI lane. Confirm its head against the approved PR before executing code:

```sh
git clone --depth 1 --filter=blob:none --sparse --branch feat/v1.1-phase9-release-candidate \
  https://github.com/its-spark-dev/GridGuide.git /tmp/gridguide-code
git -C /tmp/gridguide-code sparse-checkout set .github backend benchmarks data/synthetic \
  data/operator deploy docs frontend pipeline research scripts tests
cd /tmp/gridguide-code
git rev-parse HEAD
test ! -e data/raw
test ! -e data/processed
```

Only fictional data directories are materialized. Git metadata is still present in this
build checkout and must never become the distribution context. Build the allowlisted ZIP
using the commands below, then inspect/extract it as above. No original-source permission
or sanitized-history claim follows from sparse checkout.

Use the candidate branch/commit linked in G9. A repository clone contains historical
source material; the standalone package is the preferred public acquisition path.
Public CI uses a sparse depth-one checkout of code, fictional data and documentation,
with `data/raw` and `data/processed` explicitly absent. Its exact setup is in
[`ci.yml`](../.github/workflows/ci.yml); no source access or private CI runner is required.

```sh
"$GG_PYTHON" -m venv .venv
.venv/bin/pip install -r requirements-web.txt
npm --prefix frontend ci
npm --prefix frontend run types:generate
git diff --exit-code -- frontend/src/api.generated.ts
npm --prefix frontend run build
.venv/bin/python scripts/build_public_frontend.py
# Public runtime plus test-only NumPy; original challenge environment pins are separate.
.venv/bin/pip install --require-hashes -r deploy/requirements.lock
.venv/bin/pip install numpy==2.5.4
.venv/bin/python scripts/run_test_lane.py --lane public --report /tmp/public-tests.json
.venv/bin/python scripts/check_frozen_artifacts.py
.venv/bin/python scripts/package_demo.py --build /tmp/gridguide-public.zip
.venv/bin/python scripts/package_demo.py --inspect /tmp/gridguide-public.zip
```

No generated API type is hand-edited. Public Python tests deny source opens/network
connections and count **102** methods. Install Playwright's Chromium in Linux CI with
`cd frontend && npx playwright install --with-deps chromium`; local macOS tests use
installed Google Chrome. Then, from `frontend/`:

```sh
npx playwright test -c playwright.preparedness.config.ts
GRIDGUIDE_PACKAGE=/tmp/gridguide-public GRIDGUIDE_PUBLIC_PYTHON=/tmp/gridguide-runtime/bin/python \
  npx playwright test -c playwright.distribution.config.ts
GRIDGUIDE_CONTAINER=gridguide-rc GRIDGUIDE_PACKAGE=/tmp/gridguide-public \
  GRIDGUIDE_PUBLIC_PYTHON=/tmp/gridguide-runtime/bin/python \
  npx playwright test -c playwright.distribution.config.ts --output test-results-container
```

Use a clean extraction from the freshly built ZIP. Ports 18186 and 18188 must be free;
the harness starts/stops its own actual services. `CI=1` selects installed bundled Chromium
instead of Chrome. The container rehearsal command, from repository root, additionally
checks every application layer and starts a network-none container on an isolated path:

```sh
.venv/bin/python scripts/rehearse_container.py --image gridguide-rc --output /tmp/container-check.json
```

Port 18189 must be free. The production browser tests verify real downloaded replay,
offline browser restart, service stop/start and HTTP limits; G6/G7 tests cover mobile,
keyboard, storage migration, overrides, invalidation and automated accessibility.

## 2. Authorized source-dependent verification

This lane cannot run without permission to use the four pinned original files and
the original application dependencies. Do not upload challenge data into public CI.
Use a separate original `.venv` installed from `requirements-web.txt` (do not overwrite
its FastAPI pin with the public lock). Run:

```sh
.venv/bin/python scripts/run_test_lane.py --lane challenge --report /tmp/challenge-tests.json
.venv/bin/python -m backend.demo
.venv/bin/python scripts/run_legacy_benchmark.py --output /tmp/legacy-plans.json
npm --prefix frontend test
```

There are 196 methods in this conservatively grouped source-dependent lane; some legacy
modules include synthetic checks too. Source absence means **NOT EXECUTED/unavailable**,
not passed. Legacy browser tests need Chrome and ports 15173/18080/18081.
Source pins, v1.0.0 and teammate pipeline/attribution remain untouched. No automatic
challenge-data download, redistribution permission or historical exposure remediation
is implied. Original optional provider behavior is preserved, but is not in the public ZIP.

## 3. Optional resource-intensive reproduction

Use a separate research environment; install the existing pinned requirements. Outputs
must be new paths. Renderers read results rather than selecting new cases or tuning.

```sh
"$GG_PYTHON" -m venv /tmp/gridguide-research
/tmp/gridguide-research/bin/pip install -r requirements-optimization.txt -r requirements-simulation.txt
/tmp/gridguide-research/bin/python scripts/run_test_lane.py --lane research --report /tmp/research-tests.json
/tmp/gridguide-research/bin/python scripts/run_benchmarks.py --suite standard --output /tmp/g2-standard
/tmp/gridguide-research/bin/python scripts/report_benchmarks.py /tmp/g2-standard
/tmp/gridguide-research/bin/python scripts/check_optimization_reproduction.py \
  --reference docs/benchmarks/phase3/published --output /tmp/g3-replay.json
```

Research regression comprises 51 methods and is deferred in ordinary PR CI. Phase 9
actually reran G2 standard: compare `results_uncompressed_sha256` in its manifest against
the [frozen manifest](benchmarks/phase2/standard/manifest.json), not timing bytes. The G3
full reproduction command was verified historically in G3 and **not rerun in G9**.
Do not replace frozen cases or change solver budgets in pursuit of a better result.

For full G5 standard/convergence generation and canonical-array verification, follow the
complete [G5 artifact commands](research/phase5/ARTIFACTS.md). Those multi-million-trial
runs were **not rerun in G9**. The normal frozen check verifies all 66 committed G5 hashes
and 20 G2/G3 files; it is an integrity check, not fresh numerical or empirical validation.
The original fixed-timetable protocol, seven profiles, 195 stable/15 unstable results and
same-environment-only numerical guarantees remain unchanged.

Reference versions: Python 3.12.14, Node 22.22.0 in CI, Playwright 1.64.1,
OR-Tools 9.14.6206 and NumPy 2.5.4 for research. Local hardware: Apple M4 Pro, 12 cores,
24 GiB, macOS 26.6.2; local container arm64 and GitHub Ubuntu amd64. No cross-platform
bitwise simulation guarantee, broad browser compatibility or real outage calibration follows.
