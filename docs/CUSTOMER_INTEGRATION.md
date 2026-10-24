# Preparation, declared needs and communication

`pipeline/guidance.py` owns existing preparation, eligibility, safety and lifecycle templates. `backend/customer.py` adapts them to typed engine results without editing teammate files. Do not import the alternate batch builder/restoration pipeline or infer life-support needs from its `critical_c` flag. Numerical authority remains `backend/engine.py`.

## Explicit declarations

The UI offers optional powered-medical-equipment/medical need, accessibility assistance, critical responsibility and None/clear. The request accepts only those enums, no free text/contact/medical records. Default is empty. Selections are held only in page memory and request processing; refresh clears them. They cannot change risk, person-hours, elapsed bounds, asset counts or facility priority. They are removed before every provider context/cache is created, and the browser sends empty declarations with explanation requests.

Reviewed fixed copy adds a provider/device-supplier backup plan for medical devices; support-network, transport and communication planning for accessibility; continuity/coordinator planning for critical responsibility. The adapter uses the teammate's explicit `priority_needs` input to recommend phone contact, and adds a direct-support escalation message even when duration is unknown. This is prototype guidance, not AEP program enrollment, medical advice, automated contact or dispatch.

Medical source: [FDA emergency-device preparedness](https://www.fda.gov/medical-devices/emergency-situations-medical-devices/fda-offers-tips-about-medical-devices-and-natural-disasters). Accessibility planning: [Ready.gov disability planning](https://www.ready.gov/disability), also reflected by [Alameda County emergency planning](https://www.acgov.org/ready/disability.htm). Existing safety/food copy remains teammate-owned; references include [Ohio EMA](https://ema.ohio.gov/prepare-respond/preparedness-resources/power-outages) and [FoodSafety.gov](https://www.foodsafety.gov/keep-food-safe/food-safety-in-disaster-or-emergency).

## Elapsed-time policy

Preparation consumes the displayed elapsed upper endpoint and LOW confidence. Default four-person CLEAR is 2.5–12 elapsed hours; RESTRICTED 4–16.5; BLOCKED null. Neither finite golden state triggers >24-hour preparation. Person-hours never feed elapsed thresholds.

Existing HIGH/SEVERE eligibility, Medium >12 hours, pre-storm timing and strict >6-hour update threshold are **prototype policies**, not AEP rules. Eligibility is separate from consent. An update qualifies for an eligible customer if either absolute raw elapsed endpoint delta exceeds six hours, or duration availability changes. Exactly six is excluded. CLEAR→RESTRICTED at four people changes the upper endpoint by 4.5 hours and does not qualify; RESTRICTED eight→two changes the lower endpoint by 6.0885 hours and does qualify despite unchanged person-hours. A viewable estimate-update sample is not proof of qualifying delivery.

Unknown duration uses internal zero/unbounded rule probes to retain only invariant teammate guidance/eligibility; these are never claimed as estimates. HIGH eligibility survives unknown duration. Declared support remains available without a finite ETA. No long-duration tip or zero-hour restoration is fabricated.

## Messages and state

Four lifecycle previews are hypothetical: pre-storm, outage-confirmed, estimate-updated and restoration-complete. Finite messages come from the teammate generator; the adapter replaces probability/live-utility assertions, preserves the canonical half-hour range and adds conditional time origin. BLOCKED uses reviewed null-state messages. All delivery is `preview_only`.

The API returns preparation/alerts/messages with the same result ID and revision. The browser verifies ID, crew/access and declaration selection, cancels stale requests and hides old guidance during pending/error states. It does not calculate thresholds or persist declarations. See full test/browser evidence in [DEMO_FREEZE.md](DEMO_FREEZE.md).
