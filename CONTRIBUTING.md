# Contributing to GridGuide

GridGuide v1.0.0 preserves the HackOHI/O 2026 implementation. Documentation corrections and reproducible issue reports help readers understand and run the prototype. Propose functional changes separately, with their evidence and validation scope; the released tag remains an immutable reference.

Before changing product behavior, read [AGENTS.md](AGENTS.md), the [architecture](docs/ARCHITECTURE.md), and the [model specification](docs/MODEL_SPEC.md). Keep formulas and numerical validation in Python, API contracts centralized, and presentation in React/TypeScript. Preserve teammate work and immutable source files.

## Useful contributions

- Correct a documented claim against a specific code path or source reference.
- Improve setup instructions with a recorded environment and verification result.
- Improve accessible documentation or authentic, privacy-reviewed screenshots.
- Describe a reproducible issue using anonymous demo aliases and the relevant scenario settings.

Do not attach customer identifiers, exact customer/facility locations, raw GIS, source-derived customer tables, credentials, or `.env` contents to issues or pull requests. Public payload privacy does not establish permission to redistribute the underlying dataset. See the [release audit](docs/releases/PUBLIC_RELEASE_AUDIT.md).

## Checks

Follow [local setup](README.md#getting-started) with authorized access to the pinned data. Use the existing [verification commands](README.md#verify), and record any checks that could not run. Documentation-only changes require link, formatting, claim, and asset review; do not add implementation-mirroring tests just for prose edits.

If an API contract changes in a future release, regenerate `frontend/src/api.generated.ts` with `npm --prefix frontend run types:generate`; never edit generated types by hand. Keep fail-safe unavailable states, source pins, privacy, revision binding, and offline Standard explanations intact.

Preserve original commits and contributor attribution. No project-wide software license has been selected; see [license status and third-party notices](THIRD_PARTY_NOTICES.md). Agree on contribution rights with the maintainers before submitting code. Repository visibility does not grant rights to third-party data.
