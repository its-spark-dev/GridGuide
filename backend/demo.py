"""Run from the repository root: .venv/bin/python -m backend.demo [--json]."""
import argparse
import json
import sys

from pydantic import ValidationError

from .contracts import Evaluation
from .data import CheckpointError, prepare_context
from .engine import compare_access, default_scenario, evaluate


def access_arg(value: str) -> str:
    normalized = value.lower()
    if normalized == "normal":
        return "clear"
    if normalized not in {"clear", "restricted", "blocked"}:
        raise argparse.ArgumentTypeError("access must be clear (normal), restricted, or blocked")
    return normalized


def display_range(result: Evaluation) -> str:
    restoration = result.restoration
    if restoration.display_hours is None:
        return f"unavailable ({restoration.status}: {', '.join(restoration.missing_inputs)})"
    bounds = restoration.display_hours
    return f"{bounds.lower:g}–{bounds.upper:g} conditional elapsed hours after crew response begins"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Source-verified GridGuide checkpoint; damage/access/storm are explicit simulations.")
    parser.add_argument("--location", default="demo-a", help="Only the audited demo-a alias is supported")
    parser.add_argument("--access", type=access_arg, help="Evaluate one state; omit to compare clear, restricted and blocked")
    parser.add_argument("--storm-level", type=int, default=2)
    parser.add_argument("--crew-count", type=int, default=1)
    parser.add_argument("--crew-size", type=int, default=4, help="People in the assigned crew (2–8); default is a scenario assumption")
    parser.add_argument("--json", action="store_true", help="Emit the public structured contract, without private source IDs")
    parser.add_argument("--schema", action="store_true", help="Emit the evaluation JSON Schema without reading source data")
    args = parser.parse_args(argv)
    if args.schema:
        print(json.dumps(Evaluation.model_json_schema(), indent=2, sort_keys=True))
        return 0
    try:
        context = prepare_context(location_alias=args.location)
        states = [args.access] if args.access else ["clear", "restricted", "blocked"]
        results = [evaluate(context, default_scenario(context, access=state, scenario_revision=i+1,
                    storm_level=args.storm_level, crew_count=args.crew_count, crew_size=args.crew_size)) for i, state in enumerate(states)]
        comparisons = [compare_access(results[0], r) for r in results[1:]]
        if args.json:
            payload = {"results": [r.model_dump(mode="json") for r in results],
                       "comparisons": [c.model_dump(mode="json") for c in comparisons]}
            print(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False))
        else:
            first = results[0]
            print(f"Customer: {first.location.alias} ({first.location.label}; approximate location)")
            print("Verified upstream path: customer → " + " → ".join(a.kind for a in first.location.upstream_assets))
            print(f"Risk: {first.risk.band or 'unavailable'}; predictive confidence: {first.risk.predictive_confidence}; not a probability")
            for factor in first.risk.factors:
                print(f"  {factor.label}: {factor.value} (+{factor.contribution_points or 0} points)")
            for result in results:
                label = "NORMAL / clear" if result.simulated_inputs.access == "clear" else result.simulated_inputs.access.upper()
                print(f"Restoration, {label}: {display_range(result)}")
                print(f"  Repair effort: {result.restoration.repair_person_hours:g} person-hours; total with access: {result.restoration.total_person_hours}; crew: {result.simulated_inputs.crew_size} people")
            for comparison in comparisons:
                print("Why changed: " + comparison.explanation)
            print("Scope: simulated replacement of listed components; no live outage or AEP ETR.")
            print("Units: AEP direct labor × 4.5 = total person-hours, not elapsed time. Actual crew efficiency is unknown; the ideal-to-single-effective-worker envelope is a prototype policy.")
        return 0
    except CheckpointError as error:
        problem = {"status": "unavailable", "error": {"code": error.code, "message": str(error)}}
    except ValidationError:
        # Pydantic's full input echo is deliberately not returned across the public boundary.
        problem = {"status": "unavailable", "error": {"code": "invalid_input", "message": "Scenario fields failed validation; check supported types, bounds and identifiers."}}
    print(json.dumps(problem, sort_keys=True) if args.json else f"Unavailable: {problem['error']['code']} — {problem['error']['message']}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
