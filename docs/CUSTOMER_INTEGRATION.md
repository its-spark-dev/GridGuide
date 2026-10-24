# Preparation and communication integration

## Source and ownership

Fetched origin on 2026-10-24. Teammate commits `44010cf` (guidance/alerts/messages),
`b52903e` (merge), and `41d4271` (message typo) were already on local main.
No merge/rebase was needed. The user then authorized a UI-only checkpoint commit:
`99cf8e2`, containing the completed AEP visual pass's three files. Integration
was committed as `f6bb5a2` (`feat: integrate outage preparation and alert journey`).
That checkpoint is now included in the shared branch. This section records the
integration's original ownership; see [the final freeze note](DEMO_FREEZE.md) for
current verification and remaining scope.

`pipeline/guidance.py` owns `prep_guidance`, `alert_plan`, `messages`, `SAFETY`
and `ALERT_RULES`. `backend/customer.py` calls these functions, adapts their
outputs to the verified engine and returns explicit typed customer contracts.
No teammate source or processed dataset was modified. No new dependencies.

`pipeline/build.py` is an alternate batch risk pipeline: proximity/percentile
scores, normalized circuit strings and inferred `critical_c` life-support flag.
It executes data reads/writes at import. Do not import it or use its CSV as the
browser's risk/profile source. `pipeline/restore.py` is an alternate aggregate
calculator: parallel crew division, per-item fractional access, generic fallback
recipes and 0.4/1.25 bounds. It does not model blocked/null access. Neither
replaces the typed topology, serial restoration or privacy boundary in backend.

## Public contract and rules

`POST /api/evaluate` adds `customer_journey` next to the unchanged `result` and
`comparison`. It is tied to the same result ID and request revision. Generated
OpenAPI types carry preparation, eligibility and four lifecycle previews. The
browser checks that ID, hides stale content during loading/errors and selects
one lifecycle message at a time. No lifecycle selection changes real utility
state or schedules delivery.

- Preparation uses the engine's displayed upper bound and LOW confidence, and
  the teammate's rule-selected actions/safety. Additional actions are expandable.
- Map MODERATE to the teammate's Medium and SEVERE to High (compatibility only;
  the engine band is unchanged). Demo A remains HIGH.
- No needs, contacts or subscriptions are inferred. `priority_needs=False` means
  no explicit declaration was collected; it is not a medical classification.
  The API rejects arbitrary priority/contact fields. No declaration UI added.
- HIGH is eligible for demo SMS/in-app suggestions. Delivery is always
  `preview_only`; no provider is connected and nothing is sent. The teammate's
  12-hour medium threshold and 24-hour pre-storm timing remain labeled assumptions.
- Interpret the teammate's >6-hour update rule as either absolute raw endpoint
  delta from `Comparison`. CLEAR → RESTRICTED has upper delta 6.75 and qualifies.
  The browser does not compute deltas. Identical scenarios do not create updates.
- Adapter extension: a finite/unavailable transition also qualifies for an
  availability preview. This is disclosed separately from the teammate threshold.
- For unknown duration, call teammate rules at zero and an unbounded policy probe
  and retain invariant actions/eligibility. These are internal rule probes, never
  estimated hours. Suppress the longer-end-of-range tip when no range exists;
  eligibility is unknown if the duration-dependent decisions differ. HIGH remains
  eligible without inventing a duration. Nulls remain null in engine/API output.

## Message wording and safety

Finite messages come from the teammate generator, using existing displayed
bounds. The adapter replaces probability-like “chance” with a risk band,
AEP-branded assertions with GridGuide previews, and live outage/crew/restoration
claims with hypothetical conditions. It appends the provisional time origin.
Null-state messages cover the missing teammate interface without formatting fake
numbers. Estimate-updated is unavailable until a scenario change exists. All four
stages are explicitly future samples, not a historical event stream.

Safety and food preparation text remains teammate-owned. Reviewed against:

- [Ohio EMA power outage guidance](https://ema.ohio.gov/prepare-respond/preparedness-resources/power-outages)
- [Columbus downed-line safety](https://www.columbus.gov/Government/Mayors-Office/Extreme-Weather-August-2026/Weather-Safety)
- [FoodSafety.gov outage guidance](https://www.foodsafety.gov/keep-food-safe/food-safety-in-disaster-or-emergency)

## Verification and demo

Run the existing README startup commands. At Demo Location A: CLEAR 11–18,
RESTRICTED 16–25, BLOCKED unavailable/null; HIGH throughout. In Preparation &
alerts, inspect the teammate actions and demo eligibility. Change access to
Restricted: Estimate updated selects automatically and displays the generated
16–25 message. Expand additional preparation to see the >24-hour actions.
Preview the other three stages; they never assert that delivery happened.

57 backend tests cover the original 48 plus source delegation, rule mutation,
nulls, eligibility boundaries, four states, privacy, comparison references,
all access transitions and the raw update threshold. Frontend typecheck/build,
golden CLI and real-API browser checks cover message/action equality, keyboard,
mobile, retry and stale requests. There is no separate frontend unit-test runner.

Remaining: organizer confirmation of labor units and alert assumptions; actual
customer declarations and real delivery remain outside this slice. Keep future
teammate template changes covered by the no-live-claims regression tests.
