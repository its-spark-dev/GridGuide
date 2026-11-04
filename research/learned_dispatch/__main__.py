"""CLI orchestration; numerical definitions live in the frozen implementation modules."""
import argparse
import json
from pathlib import Path

from threadpoolctl import threadpool_limits

from . import dataset, experiment, training
from .models import LearnedPolicy, load_model
from .public import from_public_dict
from .teacher import collect
from research.ml_lab.artifacts import read_json


def smoke(output):
    if output.exists():
        raise ValueError("Smoke output already exists")
    d, t, labels = output/"dataset", output/"training", output/"teacher"
    dataset.prepare(d, "smoke")
    collect(d, labels, max_groups=4)
    trained = training.fit(d, labels, t)
    experiment.run(d, t, output/"dev", "dev")
    frozen = output/"freeze.json"
    experiment.freeze(d, t, output/"dev", frozen)
    audits = {"dev": experiment.audit(d, t, output/"dev")}
    for partition in ("final_id", "final_shift"):
        experiment.run(d, t, output/partition, partition, frozen_path=frozen)
        audits[partition] = experiment.audit(d, t, output/partition)
    return dict(status="PASS", trained_models=list(trained["models"]), training_rows=trained["rows"], audits=audits)


def main():
    parser = argparse.ArgumentParser(description="Isolated learned adaptive dispatch research")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--profile", choices=("full", "smoke"), default="full")
    p = sub.add_parser("collect")
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--max-groups", type=int, default=4)
    p = sub.add_parser("fit")
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--teacher", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    for command in ("evaluate", "audit", "freeze"):
        p = sub.add_parser(command)
        p.add_argument("--dataset", required=True, type=Path)
        p.add_argument("--training", required=True, type=Path)
        p.add_argument("--output", required=True, type=Path)
        if command == "evaluate":
            p.add_argument("--partition", choices=("dev", "final_id", "final_shift"), required=True)
            p.add_argument("--freeze", type=Path)
            p.add_argument("--max-groups", type=int, default=4)
        if command == "freeze":
            p.add_argument("--development", required=True, type=Path)
    p = sub.add_parser("smoke")
    p.add_argument("--output", required=True, type=Path)
    p = sub.add_parser("report")
    p.add_argument("--evidence", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    for command in ("infer", "episode"):
        p = sub.add_parser(command)
        p.add_argument("--model", type=Path, required=True)
        p.add_argument("--sha256", required=True)
        if command == "infer":
            p.add_argument("--state", type=Path, required=True)
        else:
            p.add_argument("--problem", type=Path, required=True)
            p.add_argument("--profile", choices=("deterministic", "low", "high"), default="high")
            p.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == "prepare":
            result = dataset.prepare(args.output, args.profile)
            result = {k: result[k] for k in ("counts", "input_identity", "excluded_topologies")}
        elif args.command == "collect":
            result = collect(args.dataset, args.output, args.max_groups)
        elif args.command == "fit":
            result = training.fit(args.dataset, args.teacher, args.output)
            result = {k: result[k] for k in ("models", "rows", "features", "configurations", "scores")}
        elif args.command == "evaluate":
            result = experiment.run(args.dataset, args.training, args.output, args.partition, args.max_groups, args.freeze)
        elif args.command == "audit":
            result = experiment.audit(args.dataset, args.training, args.output)
        elif args.command == "freeze":
            result = experiment.freeze(args.dataset, args.training, args.development, args.output)["selection"]
        elif args.command == "smoke":
            result = smoke(args.output)
        elif args.command == "report":
            from .report import render
            result = render(args.evidence, args.output)
        else:
            model, load_ns = load_model(args.model, args.sha256)
            if args.command == "infer":
                policy = LearnedPolicy(model)
                state = from_public_dict(read_json(args.state))
                action = policy(state)
                result = dict(candidate=model.candidate, action=vars(action), fallbacks=policy.fallbacks,
                    learned_priority=policy.score(state, action) if not policy.fallbacks else None,
                    model_load_nanoseconds=load_ns)
            else:
                from benchmarks.contracts import BenchmarkProblem
                from .rollout import execute
                result, timing = execute(BenchmarkProblem.model_validate(read_json(args.problem)),
                                         args.profile, args.seed, model.candidate, model)
                result = dict(candidate=model.candidate, trajectory_validated=result["trajectory_validated"],
                              metrics=result["metrics"], schedule=result["schedule"], fallbacks=result["fallbacks"], timing=timing)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
