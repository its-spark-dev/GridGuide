"""Reproduce the exploratory audit into a new directory; never train or tune."""
import argparse
from pathlib import Path

from research.ml_lab.access import isolated
from . import VERSION
from .evidence import ROOT, Sources, save_new
from .audit import cohort, static_audit
from .signal import training_signal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--exact", action="store_true", help="also reproduce the bounded fresh Bellman diagnostic")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must not exist")
    sources = Sources()
    with isolated():
        results = {}
        for study, stage in [("adaptive-dispatch", "confirmation"), ("learned-dispatch", "dev"),
                             ("learned-dispatch", "final_id"), ("learned-dispatch", "final_shift")]:
            print(f"Auditing {study}/{stage}", flush=True)
            results["adaptive_confirmation" if study == "adaptive-dispatch" else stage] = cohort(sources, study, stage)
        print("Auditing static labels and frozen dispatch feature/target signal", flush=True)
        results["static"] = static_audit(sources)
        results["signal"] = training_signal(sources)
        results["resources"] = sources.json("docs/learned-dispatch/evidence/training/runtime.json")
        results["version"] = VERSION
        files = {"audit.json": results}
        if args.exact:
            from .exact import run
            print("Integrating fresh four-task Bellman diagnostic", flush=True)
            files["exact.json"] = run(sources)
        # Bind adapters and our analysis implementation as well as all consumed evidence.
        for directory in ("research/ml_opportunity", "research/learned_dispatch", "research/adaptive_dispatch"):
            for path in sorted((ROOT/directory).glob("*.py")):
                sources.path(path.relative_to(ROOT))
        for path in ("benchmarks/contracts.py", "benchmarks/metrics.py", "benchmarks/validation.py",
                     "benchmarks/policies.py", "backend/contracts.py", "backend/risk_rules.py",
                     "docs/research/ml-opportunity/PROTOCOL.md"):
            sources.path(path)
        files["sources.json"] = sources.hashes
        save_new(args.output, files)
        print(f"Wrote {args.output}; zero fits and no new final evaluation", flush=True)


if __name__ == "__main__":
    main()
