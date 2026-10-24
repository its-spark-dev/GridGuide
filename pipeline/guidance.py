    # Preparation guidance, alert eligibility, and customer messages.
# All thresholds below are TEAM ASSUMPTIONS unless AEP gives official rules.

ALERT_RULES = {
    "medium_risk_min_hours": 12,       # Medium risk gets alerts if outage could exceed this
    "priority_escalate_hours": 4,      # declared priority needs + outage longer than this -> phone call
    "update_threshold_hours": 6,       # re-alert if estimate moves by more than this
    "pre_storm_lead_hours": 24,        # send pre-storm alert this long before the storm
}

SAFETY = [
    "SAFETY: Stay at least 30 feet away from downed power lines and assume they are energized. Call 911.",
    "SAFETY: Never run a generator indoors or in a garage. Carbon monoxide can kill.",
]

def prep_guidance(risk, high_hrs, priority_needs=False, confidence="Medium"):
    tips = ["Charge phones and power banks.", "Find flashlights and fresh batteries."]
    if risk in ("Medium", "High"):
        tips += ["Keep the fridge and freezer closed; food stays cold about 4 hours (fridge) to 48 hours (full freezer).",
                 "Have water and non-perishable food ready."]
    if high_hrs >= 24:
        tips += ["Plan for possibly more than a day without power: consider where you could stay if needed.",
                 "Fill your car's gas tank before the storm."]
    if high_hrs >= 72:
        tips += ["Prepare for a multi-day outage: extra water (1 gallon per person per day), medications, cash."]
    if priority_needs:
        tips += ["You have declared medical or priority needs on file: make sure backup power for medical "
                 "equipment is charged, and have a plan to go somewhere with power if the outage is long."]
    if confidence == "Low":
        tips += ["Our estimate for your area is uncertain, so prepare for the longer end of the range."]
    return {"actions": tips, "safety": SAFETY}

def alert_plan(risk, high_hrs, priority_needs=False, confidence="Medium"):
    r = ALERT_RULES
    eligible = (risk == "High" or priority_needs or
                (risk == "Medium" and high_hrs >= r["medium_risk_min_hours"]))
    if not eligible:
        return {"eligible": False, "reason": "Low expected impact: information shown in app only.",
                "channels": ["app"], "escalate": False}
    channels = ["sms", "app"]
    escalate = priority_needs and high_hrs >= r["priority_escalate_hours"]
    if escalate:
        channels.append("phone_call")
    why = ("declared priority needs" if priority_needs else f"{risk} risk")
    return {"eligible": True, "reason": f"Eligible because of {why}.",
            "channels": channels, "escalate": escalate,
            "timing": {"pre_storm": f"{r['pre_storm_lead_hours']} hours before storm",
                       "update": f"when estimate changes by more than {r['update_threshold_hours']} hours"},
            "note": "Thresholds are team assumptions." }

def fmt(h):
    return f"{round(h)} hours" if h < 48 else f"{round(h / 24, 1)} days"

def messages(risk, low_hrs, high_hrs, confidence="Medium", new_low=None, new_high=None):
    est = f"{fmt(low_hrs)} to {fmt(high_hrs)}"
    unsure = " This estimate is uncertain." if confidence == "Low" else ""
    msgs = {
        "pre_storm": f"AEP GridGuide: A storm is approaching. Your area has a {risk.upper()} chance of an outage. "
                     f"If power goes out, restoration could take {est}.{unsure} Charge devices now.",
        "outage_confirmed": f"AEP GridGuide: We know your power is out. Estimated restoration: {est}.{unsure} "
                            "Stay away from downed lines. See the GridGuide app for safety apps.",
        "restored": "AEP GridGuide: Power should be restored in your area. If you are still out, "
                    "please report it so a crew can check your service.",
    }
    if new_low is not None:
        moved = "later" if new_high > high_hrs else "sooner"
        msgs["estimate_updated"] = (f"AEP GridGuide: Update: restoration now expected {moved}: "
                                    f"{fmt(new_low)} to {fmt(new_high)}. Crews are working in your area.")
    return msgs

if __name__ == "__main__":
    for case in [("High", 9, 29, True, "Medium"), ("Medium", 8, 25, False, "High"),
                 ("Low", 2, 6, False, "Low")]:
        risk, lo, hi, prio, conf = case
        print("\n================", case)
        print(prep_guidance(risk, hi, prio, conf))
        print(alert_plan(risk, hi, prio, conf))
        print(messages(risk, lo, hi, conf, new_low=20, new_high=40))