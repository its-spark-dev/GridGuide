# Fictional scenario catalog v1

These six small graphs were authored from literals in `scripts/generate_synthetic.py`.
No challenge file was loaded, sampled, anonymized, moved, or transformed to create them.
IDs use the `syn-` namespace. They have no geographic coordinates, real addresses,
asset identifiers, source-row locators, or personal needs. They are fictional examples,
not observed events, utility plans, or statistically representative benchmark cases.

The simple, branching, overlapping-dependency, blocked-access, missing-evidence and
critical-service cases each isolate a boundary. Customer identity is unique even when
paths overlap. An unresolved device/link remains explicit; complete dependency counts
are withheld for that scenario. Critical services are declared fictional attachments.

Effort values are independently selected **total person-hours**, not workbook rates or
elapsed-time observations. No multiplier is applied by the catalog. Crew availability,
supply and damage are scenario assumptions; repair precedence is a prototype policy.
The evidence ledger binds every important input. Actual productivity, outage status,
restoration outcomes and blocked clearance remain unknown. Phase 1 performs no risk,
duration, scheduling, optimization or simulation calculation.

Regenerate into a new temporary directory and compare `catalog.json`; the generator
refuses to overwrite an existing directory. Updates require a catalog/definition version
review, a new SHA-256 pin in `backend/scenarios.py`, regenerated TypeScript, and tests.
Do not modify fixtures to improve later benchmark results. These boundary examples do
not replace Phase 2's preregistered benchmark suite.

New fixtures are project-authored; no third-party dataset is embedded. No new project
license or third-party redistribution permission is implied. Existing contributor and
third-party notices remain applicable to distributed code.
