# Current-branch package verification

PR #16's failed run 41790933190 changed exactly one packaged input:
`THIRD_PARTY_NOTICES.md`. LICENSE was absent from the allowlist; README is not a
package input. The resulting manifest and ZIP therefore correctly differed from the
frozen v1.1.0 archive. The 102 tests passed before the stale comparison failed.

Current builds now include the standard MIT LICENSE explicitly and update the local
package instructions to explain the grant's scope. Collective copyright attribution
`2026 GridGuide contributors` covers the three contributors whose agreement the owner
confirmed; it does not invent individual identities or extend ownership to external data.

`current-package.json` pins the exact current 48-file package. CI retains recursive
allowlist/content checks, two-build reproducibility tests, source/privacy checks and
production/container tests. Future intentional package changes require a reviewed update
to this current manifest, never to a historical release manifest.

Separately, CI downloads the published v1.1.0 ZIP and verifies its original archive
checksum, exact 47-member tree and all member hashes using `verify_frozen_release.py`.
A network failure fails this check rather than skipping it. Historical manifests,
checksums, tags, release bodies and assets are unchanged. Current CI artifacts are not
replacement release assets; no new release or product behavior is introduced.

MIT applies only to contributor-owned original software/documentation. AEP raw and
derived data, external references, fonts, tiles and dependencies retain separate rights
and terms. Historical permission/privacy findings remain unresolved. The dependency
notice generator's statement that it grants no project/data license refers to that
inventory itself; the separately included LICENSE supplies the original-software grant.

The first maintenance CI attempt passed Python, archive and browser checks but failed
container startup: the explicit Docker COPY list also needed LICENSE. That list now
includes the same approved file; startup integrity checks remain unchanged.
