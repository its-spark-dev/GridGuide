## Summary

Prepare GridGuide’s first official portfolio release while preserving the HackOHI/O 2026 implementation and original history.

- Rework the README around the actual customer journey, policy comparison, architecture, setup, and evidence limits.
- Add five authentic application screenshots, organized documentation, contribution guidance, third-party notices, and release materials.
- Distinguish the last known hackathon-period checkpoint from post-event documentation polish and deferred v1.1.0 work.

No application code, API contracts, numerical rules, dependencies, source data, tests, or teammate pipelines change. The owner accepts the existing challenge data for this release and directs retention of the original data/history. Concrete exposure findings remain documented; this decision is not presented as a new license grant.

## Verification

194 Python tests and 49 browser tests passed during portfolio preparation. Production build, generated-type consistency, golden scenarios, and documented startup passed. Screenshots and local documentation links were reviewed. See `docs/releases/VERIFICATION.md` for scope and limitations. Live AI was not re-tested.

## Release handling

Merge into `main` with a merge commit after owner approval. Tag the approved resulting main commit as `v1.0.0` only with separate authorization. Release title: **GridGuide v1.0.0 | HackOHI/O 2026 Portfolio Release**. Release body/changelog: `docs/releases/v1.0.0.md`.

GitHub rendering, especially the Mermaid block, should be checked in this PR. This PR does not itself authorize tag creation or release publication.
