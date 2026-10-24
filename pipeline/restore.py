import pandas as pd

ILM = 4.5             # AEP sheet: multiply all labor by this (drive, safety, setup)
ACCESS_ADDER = 0.5    # AEP sheet: "Restricted Access Work" extra hours per item
SHIFT_HOURS = 16      # assumption: crews work 16-hour storm shifts

# Hours to fix ONE damaged item (install + remove). "src" says where it came from.
LABOR = {
    "Pole":           {"hrs": 2.50 + 0.93 + 0.37 + 0.21, "src": "AEP sheet (medium pole + crossarm)"},
    "Transformer":    {"hrs": 1.24 + 0.89,               "src": "AEP sheet (50 kVA)"},
    "Fuse Bank":      {"hrs": 1.0,  "src": "ASSUMPTION"},
    "Recloser Bank":  {"hrs": 3.0,  "src": "ASSUMPTION"},
    "Switch":         {"hrs": 2.0,  "src": "ASSUMPTION"},
    "Capacitor Bank": {"hrs": 2.0,  "src": "ASSUMPTION"},
    "primary":        {"hrs": 2.0,  "src": "ASSUMPTION (not in AEP sheet)"},
    "secondary":      {"hrs": 1.0,  "src": "ASSUMPTION (not in AEP sheet)"},
}

def estimate(damage, crews=5, access_frac=0.3):
    """damage = {"Pole": 3, "primary": 10, ...}  ->  restoration range in hours"""
    work = 0.0
    for asset, n in damage.items():
        per_item = LABOR.get(asset, {"hrs": 1.5})["hrs"]
        work += n * (per_item + access_frac * ACCESS_ADDER)
    crew_hours = work * ILM
    total = crew_hours / max(crews, 1)          # crews work in parallel
    low  = total * 0.4                          # your section gets fixed early
    high = total * 1.25                         # your section is last + surprises
    return {"crew_hours": round(float(crew_hours), 1),
            "low_hrs": round(float(low), 1), "high_hrs": round(float(high), 1),
            "low_days": round(float(low / SHIFT_HOURS), 1), "high_days": round(float(high / SHIFT_HOURS), 1)}

if __name__ == "__main__":
    cd = pd.read_csv("data/processed/circuit_damage.csv", dtype={"circuit": str})
    busiest = cd.groupby("circuit")["count"].sum().idxmax()
    print("Busiest circuit:", busiest)

    for storm in ["Feb 2025", "Sep 2024"]:
        rows = cd[(cd["circuit"] == busiest) & (cd["storm"] == storm)]
        dmg = dict(zip(rows["Asset_Type"], rows["count"]))
        acc = rows["access_issue"].mean() if len(rows) else 0.3
        print(f"\n== {storm} damage on this circuit: {dmg}")
        for crews in [2, 5, 10]:
            print(f"  {crews:>2} crews ->", estimate(dmg, crews, acc))

    print("\n== Slider demo: 3 poles + 5 wire spans down")
    base = {"Pole": 3, "primary": 5}
    print("  5 crews, easy access :", estimate(base, 5, 0.0))
    print("  5 crews, bad access  :", estimate(base, 5, 1.0))
    print("  2 crews, bad access  :", estimate(base, 2, 1.0))