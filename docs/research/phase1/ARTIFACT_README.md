# GridGuide Phase 1 fictional catalog artifact

This development artifact contains only a read-only fictional catalog API and its
schemas. It is not the completed v1.1.0 product, a public deployment, an outage
prediction model, a restoration scheduler, or a browser demo. Later phases require
separate approval. No raw challenge data, processed customer tables, Git history,
external research observations, provider keys or provider code are included.

After extracting the archive into an empty directory, use Python 3.12:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-synthetic.txt
.venv/bin/python -m uvicorn backend.runtime:app --host 127.0.0.1 --port 8000 --no-access-log
```

The default `GRIDGUIDE_MODE=synthetic-demo` requires only the bundled fixture.
Read `/api/health`, `/api/v2/scenarios`, or `/api/v2/scenarios/syn-missing`.
`/docs` describes the catalog routes; Swagger's own optional assets use an external
CDN. API access and catalog preparation require no network after dependencies are
installed. Phase 1 exposes no numerical evaluation or AI capability.

Each definition carries independent-fiction provenance, exact evidence classes,
revision and input fingerprint. Effort values are assumed person-hours, not observed
elapsed time. Unknown dependencies withhold complete dependency coverage. Supply
terminals are abstract. No geographic location, individual needs or real status is
collected. Request logging should remain disabled.

`challenge-local` is intentionally unavailable in this artifact; it requires the
original authorized local repository and pinned files. Selecting it here fails;
there is no automatic substitute. The original v1.0.0 history is preserved outside
this archive. This boundary does not remove historical repository exposures.

`ARTIFACT_MANIFEST.json` records hashes for detecting changed bytes. It is not an
identity signature or proof of anonymity. Preserve `THIRD_PARTY_NOTICES.md`;
no project-wide software license or source-data redistribution grant is added.
Dependencies are installed separately and retain their own notices. The original
project was built by three teammates; no additional identity or role is inferred.
