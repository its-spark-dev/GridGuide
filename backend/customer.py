"""Adapt teammate guidance to verified results; never run alternate numerical pipelines.

Unknown-duration preparation uses only actions invariant between zero and unbounded
rule probes. Those probes are not estimates and never enter DTOs or message text.
Teammate rules remain the sole preparation/eligibility threshold authority.
"""
from pipeline import guidance

from .contracts import (AlertEligibility, CommunicationPreview, Comparison,
                        CustomerJourney, Evaluation, Preparation)

TITLES = {"pre_storm": "Pre-storm", "outage_confirmed": "Outage confirmed",
          "estimate_updated": "Estimate updated", "restored": "Restored"}
BANDS = {"LOW": "Low", "MODERATE": "Medium", "HIGH": "High", "SEVERE": "High"}


def _preparation(risk: str, upper: float | None, confidence: str) -> Preparation:
    if upper is not None:
        prepared = guidance.prep_guidance(risk, upper, priority_needs=False, confidence=confidence)
        note = "Actions selected for this modeled scenario. No personal or medical needs have been declared."
    else:
        # Keep only duration-independent teammate actions. Avoid the low-confidence
        # 'longer end of the range' sentence when there is no range at all.
        prepared = guidance.prep_guidance(risk, 0, priority_needs=False, confidence="Medium")
        unbounded = guidance.prep_guidance(risk, float("inf"), priority_needs=False, confidence="Medium")
        prepared = {**prepared, "actions": [a for a in prepared["actions"] if a in unbounded["actions"]]}
        note = "Duration is unknown; showing general preparation only. No personal or medical needs have been declared."
    return Preparation(**prepared, duration_known=upper is not None, note=note)


def _eligibility(risk: str, upper: float | None, confidence: str) -> AlertEligibility:
    if upper is not None:
        plan = guidance.alert_plan(risk, upper, priority_needs=False, confidence=confidence)
    else:
        low = guidance.alert_plan(risk, 0, priority_needs=False, confidence=confidence)
        high = guidance.alert_plan(risk, float("inf"), priority_needs=False, confidence=confidence)
        if low["eligible"] != high["eligible"]:
            return AlertEligibility(eligible=None, reason="Duration is unknown; duration-based eligibility cannot be determined.",
                                    suggested_channels=("app",), timing={})
        plan = low
    return AlertEligibility(eligible=plan["eligible"], reason=plan["reason"],
                            suggested_channels=plan["channels"], timing=plan.get("timing", {}))


def _preview_text(text: str, risk: str) -> str:
    # Narrow, reviewed wording adaptations of the teammate templates. The functions
    # still generate all finite-range messages; browser code contains no message copy.
    return (text.replace("AEP GridGuide:", "GridGuide preview:")
            .replace(f"A storm is approaching. Your area has a {risk.upper()} chance of an outage.",
                     f"In this storm scenario, your outage risk band is {risk.upper()} (not a probability).")
            .replace("We know your power is out.", "If an outage is confirmed:")
            .replace("Estimated restoration:", "Provisional modeled restoration:")
            .replace("Power should be restored in your area.", "If the utility confirms restoration, power should be restored in your area.")
            .replace("restoration now expected", "provisional restoration outlook now")
            .replace("Crews are working in your area.", "This is a scenario change, not a live crew update."))


def customer_journey(result: Evaluation, previous: Evaluation | None = None,
                     comparison: Comparison | None = None) -> CustomerJourney:
    if previous is not None and (comparison is None or comparison.before_result_id != previous.result_id
                                 or comparison.after_result_id != result.result_id):
        raise ValueError("Customer comparison must reference the supplied results")
    risk = BANDS[result.risk.band]
    confidence = result.risk.predictive_confidence.title()
    bounds = result.restoration.display_hours
    old = previous.restoration.display_hours if previous else None
    alerts = _eligibility(risk, bounds.upper if bounds else None, confidence)
    changed = previous is not None and previous.restoration.display_hours != bounds
    availability_changed = previous is not None and (old is None) != (bounds is None)
    threshold = guidance.ALERT_RULES["update_threshold_hours"]
    # Interpret teammate's 'estimate moves' as either raw endpoint's absolute change.
    # The validated comparison, not rounded UI values, supplies these deltas.
    threshold_met = bool(comparison and any(c.field.startswith("restoration.raw_hours.")
                        and c.delta is not None and abs(c.delta) > threshold for c in comparison.changes))
    eligible_update = alerts.eligible is True and (threshold_met or availability_changed)
    update_reason = ("Estimate availability changed; preview an availability update." if availability_changed else
                     f"A modeled bound moved by more than {threshold:g} hours; eligible for an update preview." if threshold_met else
                     f"Update previews qualify when a modeled bound moves by more than {threshold:g} hours or availability changes.")
    generated = {}
    if bounds is not None:
        generated = guidance.messages(risk, bounds.lower, bounds.upper, confidence)
        if changed and old is not None:
            generated["estimate_updated"] = guidance.messages(risk, old.lower, old.upper, confidence,
                new_low=bounds.lower, new_high=bounds.upper)["estimate_updated"]
    # Null state copy adds behavior the teammate API cannot represent. No made-up
    # duration is passed to its formatter, and a blocked estimate stays unavailable.
    unavailable = "Estimate unavailable. Pending access clearance." if result.restoration.status == "pending_clearance" else "Estimate unavailable. Required information is missing."
    fallback = {
        "pre_storm": f"GridGuide preview: In this storm scenario, your outage risk band is {result.risk.band} (not a probability). {unavailable} Review preparation guidance.",
        "outage_confirmed": f"GridGuide preview: If an outage is confirmed: {unavailable} Review the safety guidance below.",
        "estimate_updated": (f"GridGuide preview: {unavailable} No finite restoration outlook is available." if bounds is None else
                             f"GridGuide preview: A provisional restoration outlook is available again: {bounds.lower:g} to {bounds.upper:g} hours."),
        "restored": "GridGuide preview: If the utility confirms restoration, check your service and report any continuing outage through the utility's official channels.",
    }
    previews = []
    for state, title in TITLES.items():
        available = state != "estimate_updated" or changed
        body = (_preview_text(generated[state], risk) if state in generated else fallback[state])
        if not available:
            body = "Change worksite access to preview an estimate update. No estimate change has occurred in this session."
        elif bounds is not None and state != "restored":
            body += " Hours are provisional, from when an assigned crew begins its response; not an official live AEP ETR."
        previews.append(CommunicationPreview(state=state, title=title, body=body, available=available,
            source="teammate_template_adapted" if state in generated else "null_state_adapter"))
    return CustomerJourney(result_id=result.result_id,
        preparation=_preparation(risk, bounds.upper if bounds else None, confidence), alerts=alerts,
        messages=tuple(previews), selected_state="estimate_updated" if changed else "pre_storm",
        estimate_update_eligible=eligible_update, update_reason=update_reason)
