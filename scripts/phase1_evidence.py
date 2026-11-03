"""Reproduce aggregate Phase 1 source evidence; never write or export source rows."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import RAW, SNAPSHOT
from backend.damage import prepare_damage_audit
from backend.data import layer, records, verify_sources
from backend.network import prepare_network
from research.datasets import REGISTER_VERSION


def report():
    before = verify_sources()
    network = prepare_network()
    damage = prepare_damage_audit(RAW, network.topology)
    with layer(RAW, "Data1.zip", "arcos_prod_damage_09_28_Clip") as (reader, _):
        rows = tuple(records(reader, ("Outage_Num", "Incident_W", "Event", "Report_Tim", "Repaired_D", "Repaired")))
        quality = {
            "reports": len(rows),
            "zero_outage_ids": sum(r["Outage_Num"] == 0 for r in rows),
            "zero_incident_ids": sum(r["Incident_W"] == 0 for r in rows),
            "default_event_labels": sum(r["Event"] == "Default" for r in rows),
            "not_repaired_with_repair_date": sum(r["Repaired"] == "No" and bool(r["Repaired_D"]) for r in rows),
            "same_day_report_and_repair": sum(r["Report_Tim"] == r["Repaired_D"] for r in rows),
            "observed_outage_duration_targets": None,
            "verified_non_outage_controls": None,
        }
    complete_matches = sum(m.asset_key is not None and network.dependents(m.asset_key) is not None for m in damage.matches)
    if verify_sources() != before:
        raise RuntimeError("Source integrity changed during evidence reproduction")
    modules = ("backend/network.py", "backend/damage.py", "backend/data.py", "scripts/phase1_evidence.py")
    root = Path(__file__).resolve().parents[1]
    return {
        "version": REGISTER_VERSION, "source_snapshot": SNAPSHOT, "source_sha256": before,
        "implementation_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in modules},
        "network": network.coverage,
        "damage": damage.safe_summary(),
        "damage_quality": quality,
        "complete_reverse_spatial_candidate_observations": complete_matches,
        "warning": "Failure categories overlap and must not be added. Spatial candidates are hypotheses, not direct asset identity, observed outages or duration labels.",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
