# Model and interface specification

Status: risk/restoration/access checkpoint implemented and tested in `backend/`; guidance, alerts and AI sections remain proposed. Numerical rules and golden values were reproduced without changes. Every coefficient labeled “team assumption” must be visible in the future assumptions panel and is already included in the structured result. Source facts are documented in [DATA_AUDIT.md](DATA_AUDIT.md); synthetic inputs are not observations.

## 1. Risk band: `scenario-risk-v1`

Use a transparent ordinal score for **relative outage concern under the selected storm scenario**. It is not a probability, calibrated forecast, or actual outage detection. The challenge accepts this representation (PDF p3 §1).

Inputs and rules:

| Input | Definition | Points / provenance |
|---|---|---|
| `storm_level` | Explicit scenario choice: calm, elevated, strong, severe | 0, 1, 2, 3; team-authored scenario scale, not meteorological thresholds |
| `overhead_transformer` | Selected premise's uniquely resolved first transformer has `mounting == "Overhead"` | 1 if overhead, 0 if Underground; observed inventory proxy for exposure, not the whole supply path |
| `historical_circuit_evidence` | At least one historical damage row on the selected **unambiguous** code/alias pair before the snapshot date | 1 if present, 0 if none found in this extract; observed historical context, not a failure rate |

`score = storm_level + overhead_transformer + historical_circuit_evidence`.

| Score | Band | Customer meaning |
|---:|---|---|
| 0 | LOW | Few concern signals in this limited scenario; interruption remains possible |
| 1–2 | MODERATE | Some concern signals; prepare and monitor information |
| 3–4 | HIGH | Several concern signals; prepare for a possible interruption |
| 5 | SEVERE | Highest concern category in these scenario rules |

Weights and cutoffs are **team assumptions**, chosen for clarity and monotonicity, not fitted to data. Storm level dominates the range of possible scores; inventory and history are small contextual additions. Expose each contribution in plain language. Do not use fabricated percentages, risk heatmaps that imply calibrated probabilities, or “90% confidence.”

Missing handling: absent/invalid storm level, missing first transformer, Unknown mounting, or ambiguous code/alias mapping produces `status: "insufficient_data"`, `band: null`, `score: null`. No historical records on an otherwise verified alias yields zero *historical uplift* plus “no records found in this extract; coverage unknown,” not “never had an outage.” Incomplete later upstream geometry may still allow this limited band, but the missing dependencies must be disclosed. Changing access, crew count, or restoration work quantities does not change this pre-storm risk score; damage impact is a separate scenario state.

Confidence has two meanings that must stay separate:

- `data_quality`: `verified_subset`, `partial`, or `unavailable`, determined by identity/circuit checks.
- `predictive_confidence`: always `LOW` for v1, because the score has no outcome calibration. A clean join does not create high predictive confidence.

No model training, scikit-learn, probability calibration, or accuracy claims in MVP. Later statistical work requires an event-by-premise exposure panel with positive/negative outages, consistent observation windows, storm features, reliable labels, and event/time-separated validation.

## 2. Restoration: `serial-path-v1`

### Supported scope

Calculate a **conditional duration range for declared repairs on the selected premise's verified dependency path**, measured from when an assigned crew begins its response. It includes the workbook's indirect work allowance. It excludes an unknown queue before crew assignment, unknown storm hold, unlisted damage, material shortages, actual switching decisions, and off-path work. These exclusions must accompany the estimate. The result is not a clock-time ETR or an AEP commitment.

The P0 path is serial: damaged upstream equipment must be completed before the downstream task's restoration stage. This is a conservative team sequencing assumption, not a claim that field crews cannot prepare work in parallel. Resolve task ancestry through the ordered source path, even across intact nodes. Preserve the distinction between a customer→upstream tracing edge and the reverse upstream→downstream repair prerequisite. Abstract circuit terminals are assumed available in the demo; no source data establishes their current state.

Each work item has a stable task ID, a public node alias, a component recipe, positive integer quantity, a workbook rate reference, an access state, and source classification. Quantity is explicitly simulated. One damage report is not one known damaged unit. Multiple customers sharing a damaged node must share one task in any future grouped scope.

### Rates, units, and formula

Provisional assumption **A1**: a workbook labor hour is treated as one reference-crew effort hour. The file does not define crew composition or person-hour versus crew-hour semantics. Do not divide by worker headcount. Seek organizer clarification; if contradicted, revise the conversion and golden results before making operational claims. Retain low confidence until clarified.

For damaged work item `i`:

```text
direct_i = quantity_i × (install_rate_i + remove_rate_i)
access_i = 0 for clear; 0.5 for restricted access at that repair worksite
effort_i = (direct_i + access_i) × 4.5
nominal_hours = sum(effort_i for the selected serial repair path)
raw_range_hours = [nominal_hours, nominal_hours × 1.5]
display_range_hours = [floor(raw_low), ceil(raw_high)]
```

- Install plus remove assumes replacement, not simple reset or inspection. Recipes must name that assumption.
- The 0.5 restricted-access rate comes from `Labor only work!D2`; applying it once per repair worksite is team assumption **A2** because the workbook does not define the application unit. Co-located jobs must share one access adder if they represent one worksite. Do not stack overlapping backyard, remote, and access adders automatically.
- 4.5 comes from `Indirect Labor Multiplier!B1`. Apply it exactly once to direct effort plus the selected labor adder. It already includes driving, safety discussion, and setup; do not add a second default travel factor.
- The upper factor 1.5 is team assumption **A3**, an illustrative scope/condition allowance. The interval is a scenario envelope, **not** a confidence interval, P10/P90, or validated coverage guarantee. Unmodeled conditions can exceed it.
- Outward integer-hour rounding avoids displaying many decimal places. Keep unrounded values for comparisons. No tasks produces “No repairs specified; restoration duration not determined,” with null duration, rather than a claim of power restoration.
- `crew_count` is an integer 0–4 in MVP (team UI limit). Zero means unavailable/pending assignment, null range. One or more crews gives the same serial-path duration: the bottleneck is dependencies. Label this plateau. Do not divide this chain's duration by crew count or add fake acceleration.
- `access = blocked` means pending clearance, null finite range. Restricted access is extra effort; blocked access is a gate, not a finite arbitrary multiplier. The LLM cannot invent clearance time.

Why this method: it is easy to compute, inspect and explain, gives reproducible interactive behavior, respects the verified chain, and does not invent probability distributions. Monte Carlo would add precision unsupported by samples; historical regression would learn unreliable calendar-date artifacts. Full crew scheduling and road routing are deferred. A P1 independent-branch demo may add crew benefits only after proving branch identity and testing scheduling behavior; it must have its own versioned model contract, not silently change v1.

### Recipe coverage

| Component | Source | MVP rule |
|---|---|---|
| Fuse cutout replacement | `Labor time material related!A90:B90` | One declared cutout; not a whole fuse bank unless the quantity explicitly says so |
| 100-kVA transformer unit replacement | Same sheet `C25:D25` | One declared unit; do not assume all phases/units in a bank are damaged |
| Pole replacement | Same sheet `C12:D14` | P1 only after known height class and explicit supporting-material scope |
| Recloser / switch / service | Same sheet `A70:B70`, `A85:B85`, `A80:B80` | P1, with reconciled identity and explicit component recipe |
| Primary/secondary wire, lights, capacitors, step transformers, excavation without volume | No complete validated recipe | Unavailable for numerical restoration; explain missing scope/rate, never zero |

Step restoration in P0: the dependency view shows that completing an upstream repair alone does not restore a premise with a remaining downstream damaged task. Completing the final prerequisite makes this premise *eligible for modeled restoration*, not confirmed energized. P1 may show two vetted customers on different branches reaching this condition at different stages. Do not simulate tie-switch energization or claim operational switching authority.

## 3. Scenario contract and invariants

| Control | Support | Expected behavior |
|---|---|---|
| Clear → restricted access | P0, workbook adder with declared application unit | Both unrounded endpoints nondecreasing; band unchanged |
| Restricted → blocked | P0 | Finite estimate withdrawn, clearance needed |
| More units of an existing supported damaged component | P0/P1 UI | Both endpoints nondecreasing; same frozen path and recipe |
| Additional supported damaged node on same verified path | P1 | Add work, never shorten; deduplicate shared tasks |
| Crew count 1 → 4 | Supported plateau in v1 | Equal duration, with explanation of serial dependency |
| Crew count → 0 | P0 edge case | Pending assignment, null range |
| Storm level increase | P0 | Risk score/band nondecreasing; restoration unchanged unless explicit work/access inputs change |
| Changed network assumptions | P1 | Revalidate path; unresolved/conflicting path withdraws estimate; no guessed edge |

Inputs must be typed and bounded. Reject negative/fractional quantities, NaN, unknown recipe IDs, forged node aliases, cycles, repeated tasks, invalid scenario revisions, and quantities outside the demo cap (1–10 per item, a team guardrail). Keep the scenario immutable per revision. Repeated identical inputs must yield byte-equivalent numerical results excluding request IDs/timestamps. Restoring an input restores the result. Never infer new damage from the risk band.

## 4. Golden demo scenario

Fixture locator: pinned Data1 file, `Customer_Clip` 1-based DBF record **1077**, privately mapped to `demo-a`. DATA_AUDIT records its verified Distribution → Fuse → Circuit Breaker path. A golden fixture must fail closed if source hashes or verification facts change.

Scenario: strong storm (`storm_level=2`), overhead transformer, historical evidence present (140 same-alias reports, used only as a binary indicator), one simulated fuse cutout replacement, one simulated 100-kVA transformer unit replacement at two separate modeled repair worksites, other bank units intact, circuit supply available, one reference crew, clear access. The source transformer and fuse points are 140.266 meters apart. Team assumption A2 groups sites within 50 meters; this candidate has two worksites. Pin this interpretation in preprocessing. This geometric grouping is not evidence of actual damaged assets or road access.

Risk: `2 + 1 + 1 = 4`, **HIGH**, predictive confidence **LOW**.

Base labor: fuse `0.256 + 0.128 = 0.384`; transformer `1.28 + 0.944 = 2.224`; total `2.608 × 4.5 = 11.736` hours. Base raw range `[11.736, 17.604]`; display **11–18 hours** after crew response begins.

Restricted access at two distinct worksites: `(2.608 + 2 × 0.5) × 4.5 = 16.236`; raw `[16.236, 24.354]`; display **16–25 hours**. Risk stays HIGH. Increasing crews to two leaves this serial estimate unchanged. Blocked access removes the finite range. Adding a second damaged 100-kVA unit at the existing transformer worksite gives clear-access raw `[21.744, 32.616]`, display **21–33 hours**.

These analytical acceptance values now pass real-data engine tests with independent workbook recomputation. A separate explicitly synthetic co-located-worksite test verifies one adder: raw `[13.986, 20.979]`, display **13–21 hours**. Do not apply that value to the two-worksite golden fixture. Source decimal values are normalized to 12 fractional places to remove Excel binary representation noise before arithmetic and outward rounding.

## 5. Validated explanation input

**Executable checkpoint contract:** [backend/contracts.py](../backend/contracts.py) is authoritative; generate its JSON Schema with `.venv/bin/python -m backend.demo --schema` and actual results with `--json`. `raw_hours` and `display_hours` use named `{ "lower": ..., "upper": ... }` bounds or null. Factors carry values, provenance, units, points and source references; labor contributions and repair stages are explicit. Assumptions carry their values and a model version, including the replaceable labor conversion. Source facts include mounting, historical count and unresolved labor-unit status. Safe node aliases, approximate points and dependency edges support a future map. Result IDs hash canonical results and private source hashes; there is no wall-clock field that breaks repeatability. `snapshot_date` is the audit cutoff, not an assertion that inventory was observed that day.

The `--json` CLI envelope contains `results` and `comparisons`. Each comparison contains before/after result IDs, changed field paths, before/after values, numerical deltas where defined, and causal factor IDs. Null range transitions explicitly represent blocking/recovery. Comparisons reject changes to other scenario inputs, facts, labor context or assumptions. The explanation is a deterministic template, and `generated_explanation` is null. No AI, profile, guidance or alert implementation is claimed.

The following **original full-product design sketch is not the executable checkpoint schema**. It retains the planned profile/guidance/alert additions for later integration; do not copy its array bounds, illustrative IDs or older factor names into clients. Internal source IDs, source medical/critical flags, exact coordinates, raw text fields, and contact details remain excluded. `customer_declared` would contain only explicit synthetic/session choices, never inferred attributes; a future LLM adapter should omit that object and use selected guidance references instead. Neither `source_facts` nor `confirmed_utility` implies live outage confirmation.

```json
{
  "schema_version": "1.0",
  "result_id": "demo-a:base:1",
  "scenario_revision": 1,
  "model_versions": {"risk": "scenario-risk-v1", "restoration": "serial-path-v1"},
  "data_snapshot": "aep-hack26-28a5520",
  "location": {"alias": "demo-a", "label": "Demo location A"},
  "source_facts": {
    "kind": "static_inventory_and_historical_extract",
    "path_types": ["Distribution", "Fuse", "Circuit Breaker"],
    "data_quality": "verified_subset",
    "overhead_transformer": true,
    "historical_circuit_evidence": true
  },
  "confirmed_utility": {"outage_status": null, "restoration_time": null},
  "simulated_inputs": {
    "storm_level": 2,
    "lifecycle_state": "pre_storm",
    "crew_count": 1,
    "access": "clear",
    "work_items": [
      {"task_id": "fuse-task", "node_alias": "protective-a", "recipe": "fuse-cutout-replace", "quantity": 1},
      {"task_id": "transformer-task", "node_alias": "transformer-a", "recipe": "transformer-100kva-replace", "quantity": 1}
    ]
  },
  "customer_declared": {"power_dependent_need": false, "accessible_format": "plain_text", "preferred_channel": "in_app", "opt_in": true},
  "risk": {
    "status": "available", "band": "HIGH", "score": 4, "probability": null,
    "predictive_confidence": "LOW",
    "factor_ids": ["storm-strong", "overhead-transformer", "historical-circuit-damage"]
  },
  "restoration": {
    "status": "available", "kind": "conditional_simulation",
    "time_origin": "assigned_crew_begins_response",
    "raw_hours": [11.736, 17.604], "display_hours": [11, 18],
    "predictive_confidence": "LOW",
    "factor_ids": ["serial-upstream-dependency", "two-replacement-tasks", "ilm-4.5"],
    "source_refs": ["Labor time material related!A90:B90", "Labor time material related!C25:D25", "Indirect Labor Multiplier!B1"]
  },
  "assumption_ids": ["A1-reference-crew-unit", "A2-worksite-access-adder", "A3-upper-factor-1.5", "supply-available", "listed-damage-only"],
  "limitations": ["not_calibrated", "no_live_utility_feed", "dispatch_queue_unknown", "storm_hold_unknown"],
  "missing_inputs": [],
  "guidance_ids": ["prepare-lighting-charging", "review-backup-plan", "generator-safety"],
  "alerts": {"eligibility": "eligible_demo", "rule_ids": ["high-risk-prestorm"], "recommended_channel": "in_app", "delivery": "preview_only"}
}
```

The engine boundary now uses Pydantic models; generated/shared TypeScript types and API/LLM integration remain future work. Checkpoint validation covers supported aliases, strict scenario bounds, score/factor/band consistency, null probability, ordered finite ranges only when available, null unavailable ranges with reasons, and private-field exclusion. Future integration must additionally validate current revisions and all AI action/factor references. Historical inventory may be source-confirmed without being real-time-confirmed. Use explicit `null`, not absent fields or zero substitutes, for unavailable outputs.

For a scenario comparison, pass two validated result IDs plus a server-computed change list. Never let the LLM recompute deltas. A response must match the latest `scenario_revision`; discard late answers after a newer scenario selection.

## 6. AI output and grounded rendering

P0 AI role: interpret the question and select relevant explanation/guidance clauses from the validated result. Request a constrained object such as:

```json
{
  "result_id": "demo-a:base:1",
  "answer_template_id": "explain_restoration",
  "factor_ids": ["serial-upstream-dependency", "two-replacement-tasks", "ilm-4.5"],
  "guidance_ids": ["review-backup-plan"]
}
```

The server validates references and renders concise natural language, inserting the authoritative numbers, units, caveats, and safety text itself. No numeric field or unconstrained operational claim is accepted from the LLM. This bounded AI orchestration is intentional: factual grounding can be verified by construction. A future free-prose mode needs additional evaluation; string-matching digits alone cannot detect invented claims in words.

On invalid JSON/references, timeout, missing key, or unsupported question: deterministic response from the same result; visibly label “Standard explanation” if the AI path was unavailable. For insufficient data: state the missing inputs, keep numerical outputs null, provide general preparation and escalation options. Never claim a notification was sent, an account enrolled, a crew dispatched, or a premise energized. Questions and retrieved data are untrusted text; they cannot modify model configuration, execute code, or override the source/provenance boundary.
