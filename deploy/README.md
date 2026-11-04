# GridGuide 1.1.0 release candidate — local fictional distribution

This package is independently authored fiction, not a utility system or authenticated
review service. Original challenge data and external AI are absent. Project licensing
remains undecided; THIRD_PARTY_NOTICES.md preserves historical attribution/context and
DEPENDENCY_NOTICES.txt contains the licenses for bundled/runtime dependencies. References
in the historical notice may point to files intentionally excluded from this package.

From a clean extracted package, create the virtual environment **outside this directory**:

```sh
python3.12 -m venv /tmp/gridguide-runtime
/tmp/gridguide-runtime/bin/pip install --require-hashes -r deploy/requirements.lock
PYTHONDONTWRITEBYTECODE=1 /tmp/gridguide-runtime/bin/python deploy/serve.py
```

Open http://127.0.0.1:8000/ for fictional paths/preparedness; use the operator link to
compare/review/export. Readiness: `/ready`. Replay an explicitly exported record:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/gridguide-runtime/bin/python scripts/replay_review.py /path/outside/package/review.json
```

Package contents are immutable. Do not add a virtual environment, export, cache or secret
inside it: recursive startup inspection will reject unexpected files. Internet access is
needed to install dependencies; the running application needs no outgoing network.
An explicit safety-source link opens an external website only on user navigation.

Container build context must be this extracted directory, never the repository:

```sh
docker build -f deploy/Dockerfile -t gridguide-rc .
docker run --rm --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m -p 127.0.0.1:8000:8000 gridguide-rc
```

The process runs as UID/GID 10001. SIGTERM allows ten seconds for graceful shutdown.
`PORT` defaults to 8000. `GRIDGUIDE_ALLOWED_HOSTS` is an explicit comma-separated list,
defaulting to localhost,127.0.0.1,testserver. Set a reviewed domain before any separately
authorized hosting. Synthetic mode and `GRIDGUIDE_AI_PROVIDER=none` are mandatory.
The app supplies a restrictive same-origin CSP and no browser map/provider requests.
No runtime route browses files or exposes challenge APIs, Swagger, tests or uploads.

Install the offline kit while connected at `/preparedness/`. Only explicitly saved
fictional snapshots persist; they remain historical immediately. Recalculation requires
the Python service. Storage eviction, same-origin compromise and unsupported browsers
remain limits. Hashes prove consistency, not authenticated review history. G3's failed
promotion target leaves the fixed baseline default; CP-SAT is optional/frozen. G5
intervals remain deferred and G4 remains No-Go. This is a rehearsal package, not a release
or authorization to deploy publicly.

Before public hosting, complete a current OS/container vulnerability assessment and review HTTPS, allowed-host, reverse-proxy, slow-client and resource-limit controls. G8 preparation approval is not production security certification or deployment authorization.
