import argparse
import json
from pathlib import Path
from research.ml_lab.access import isolated

from .dataset import prepare
from .experiment import audit, run


def main():
    parser = argparse.ArgumentParser(description="Fictional adaptive dispatch research")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--profile", choices=("full", "smoke"), default="full")
    p = sub.add_parser("run")
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--partition", required=True, choices=("discovery", "confirmation"))
    p.add_argument("--discovery", type=Path)
    p = sub.add_parser("audit")
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--discovery", type=Path)
    p.add_argument("--replay", action="store_true")
    p = sub.add_parser("report")
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--discovery", required=True, type=Path)
    p.add_argument("--confirmation", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with isolated():
        if args.command == "prepare":
            result = prepare(args.output, args.profile)
            print(json.dumps(result["counts"], indent=2))
        elif args.command == "run":
            result = run(args.dataset, args.output, args.partition, args.discovery)
            print(json.dumps({"selected": result["selected"], "gate": result["gate"]}, indent=2))
        elif args.command == "audit":
            print(json.dumps(audit(args.dataset, args.results, args.discovery, args.replay), indent=2))
        else:
            from .report import render
            print(json.dumps(render(args.dataset, args.discovery, args.confirmation, args.output), indent=2))


if __name__ == "__main__":
    main()
