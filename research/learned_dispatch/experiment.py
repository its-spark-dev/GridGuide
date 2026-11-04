"""Development selection and an exclusive, resumable once-only final reveal."""
from datetime import datetime, timezone
from pathlib import Path
import resource
import sys
import time

from benchmarks.contracts import Assignment, BenchmarkProblem
from research.adaptive_dispatch.environment import checked_result, sample_durations
from research.adaptive_dispatch.validation import validate_trajectory
from research.ml_lab.access import isolated
from research.ml_lab.artifacts import (ROOT, digest, environment, file_hash, read_json, read_rows,
    require_committed, revision, write_json, write_rows)
from . import VERSION
from .analysis import select, summarize
from .dataset import PARTITIONS, episode_seed, load, source_hashes
from .features import schema
from .models import CANDIDATES
from .rollout import BASELINES, FIXED, execute
from .training import approved_models


def _files(training):
    info = read_json(training/"training.json")
    return {"training.json": file_hash(training/"training.json"),
            **{v["file"]: v["sha256"] for v in info["models"].values()}}


def freeze(dataset: Path, training: Path, development: Path, destination: Path):
    if destination.exists() or (dataset/"evaluation-receipt.json").exists():
        raise ValueError("Freeze already exists or final cohort spent")
    manifest = read_json(dataset/"manifest.json")
    audit(dataset, training, development)
    selection = select(read_json(development/"summary.json"))
    full = manifest["profile"] == "full"
    files = _files(training)
    if full:
        require_committed([dataset/"manifest.json", *[dataset/f"{p}.jsonl.gz" for p in PARTITIONS],
            *[training/p for p in files], development/"completion.json", development/"summary.json",
            *[ROOT/p for p in source_hashes()], ROOT/"docs/learned-dispatch/feature-schema.json"])
    payload = dict(version=VERSION, revision=revision(), input_identity=manifest["input_identity"],
        dataset_manifest_sha256=file_hash(dataset/"manifest.json"), source_hashes=source_hashes(),
        feature_schema_sha256=digest(schema()), training_files=files,
        development_completion_sha256=file_hash(development/"completion.json"), selection=selection,
        methods=list(BASELINES)+list(selection["family_winners"].values()), environment=environment())
    write_json(destination, payload)
    return payload


def _verify_freeze(dataset, training, path, committed=False):
    frozen = read_json(path)
    manifest = read_json(dataset/"manifest.json")
    if (frozen["version"] != VERSION or frozen["input_identity"] != manifest["input_identity"]
            or frozen["dataset_manifest_sha256"] != file_hash(dataset/"manifest.json")
            or frozen["source_hashes"] != source_hashes() or frozen["feature_schema_sha256"] != digest(schema())
            or frozen["training_files"] != _files(training)):
        raise ValueError("Frozen input/source/model identity mismatch")
    if committed:
        require_committed([path])
    return frozen


def _shard_paths(output, group):
    return output/"shards"/f"{group}.jsonl.gz", output/"shards"/f"{group}.timings.jsonl.gz", output/"shards"/f"{group}.json"


def _read_shard(output, group):
    numeric, times, receipt = _shard_paths(output, group)
    record = read_json(receipt)
    if record["numeric_sha256"] != file_hash(numeric) or record["timing_sha256"] != file_hash(times):
        raise ValueError("Immutable evaluation shard changed")
    return read_rows(numeric), read_rows(times)


def run(dataset: Path, training: Path, output: Path, partition: str, max_groups=4, frozen_path: Path | None = None):
    if partition not in ("dev", "final_id", "final_shift") or type(max_groups) is not int or max_groups < 1:
        raise ValueError("Invalid experiment stage/batch bound")
    if (output/"completion.json").exists():
        raise ValueError("Completed evaluation cannot be rerun; use read-only audit")
    full = read_json(dataset/"manifest.json")["profile"] == "full"
    final = partition.startswith("final")
    if not final and (dataset/"evaluation-receipt.json").exists():
        raise ValueError("Final cohort spent; development is closed")
    if final:
        if frozen_path is None:
            raise ValueError("Final evaluation requires committed selection freeze")
        frozen = _verify_freeze(dataset, training, frozen_path, committed=full)
        methods = frozen["methods"]
        champion = frozen["selection"]["champion"]
        identity = dict(version=VERSION, freeze_sha256=file_hash(frozen_path),
                        input_identity=frozen["input_identity"], output_root=str(output.parent.resolve()))
        spent = dataset/"evaluation-receipt.json"
        if spent.exists():
            receipt = read_json(spent)
            if any(receipt.get(k) != v for k, v in identity.items()):
                raise ValueError("Final cohort was already spent under a different freeze/destination")
        else:
            # Exclusive file creation occurs before loading final problems or executing policies.
            write_json(spent, {**identity, "started_at": datetime.now(timezone.utc).isoformat(), "revision": revision()})
        denied = []
    else:
        methods, champion = list(BASELINES)+list(CANDIDATES), None
        denied = [dataset/"final_id.jsonl.gz", dataset/"final_shift.jsonl.gz"]
    with isolated(*denied):
        manifest, cases = load(dataset, partition, committed=full)
        models, load_timings = approved_models(training, [m for m in methods if m not in BASELINES])
        identity = dict(version=VERSION, partition=partition, input_identity=manifest["input_identity"],
            training_files=_files(training), source_hashes=source_hashes(), methods=methods,
            freeze_sha256=file_hash(frozen_path) if final else None, champion=champion,
            dataset_manifest_sha256=file_hash(dataset/"manifest.json"))
        receipt_path = output/"receipt.json"
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            if any(receipt.get(k) != v for k, v in identity.items()):
                raise ValueError("Evaluation resume changed registered identities")
        else:
            write_json(receipt_path, {**identity, "started_at": datetime.now(timezone.utc).isoformat(),
                "revision": revision(), "environment": environment(), "model_load_nanoseconds": load_timings})
        started, completed = time.perf_counter(), 0
        groups = sorted({c["group_id"] for c in cases})
        try:
            for group_index, group in enumerate(groups):
                numeric, times, done = _shard_paths(output, group)
                if done.exists():
                    _read_shard(output, group)
                    continue
                if numeric.exists() or times.exists():
                    raise ValueError("Partial immutable shard write; inspect evidence before recovery")
                if completed >= max_groups:
                    break
                rows, timing_rows = [], []
                stochastic_count = (4 if final else 2) if full else 1
                for case_index, case in enumerate(c for c in cases if c["group_id"] == group):
                    p = BenchmarkProblem.model_validate(case["problem"])
                    for profile in ("deterministic", "low", "high"):
                        for index in range(1 if profile == "deterministic" else stochastic_count):
                            seed = episode_seed(manifest["profile"], partition, index)
                            offset = (group_index+case_index+index+("deterministic", "low", "high").index(profile)) % len(methods)
                            for method in methods[offset:]+methods[:offset]:
                                result, timing = execute(p, profile, seed, method, models.get(method))
                                common = dict(case_id=p.id, group_id=group, mechanism=p.family, crew_count=len(p.crews),
                                    profile=profile, episode_seed=seed, method=method)
                                rows.append({**common, **result})
                                timing_rows.append({**common, **timing})
                            if time.perf_counter()-started > 1800:
                                raise RuntimeError("Prospective 30-minute command cap exceeded")
                write_rows(numeric, rows)
                write_rows(times, timing_rows)
                peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024**2 if sys.platform == "darwin" else 1024)
                write_json(done, dict(numeric_sha256=file_hash(numeric), timing_sha256=file_hash(times),
                    method_episodes=len(rows), peak_rss_mib=peak))
                if peak > 2048:
                    raise RuntimeError("Prospective 2-GiB memory cap exceeded")
                completed += 1
                print(f"{partition}: sealed {group}; {time.perf_counter()-started:.1f}s in this command", flush=True)
            finished = sum(_shard_paths(output, g)[2].exists() for g in groups)
            if finished == len(groups):
                rows, timing_rows = [], []
                for group in groups:
                    r, t = _read_shard(output, group)
                    rows.extend(r)
                    timing_rows.extend(t)
                summary = summarize(rows, timing_rows, methods, champion)
                if not final:
                    summary["selection"] = select(summary)
                write_json(output/"summary.json", summary)
                hashes = {str(p.relative_to(output)): file_hash(p) for p in sorted((output/"shards").glob("*"))}
                hashes.update({p: file_hash(output/p) for p in ("receipt.json", "summary.json")})
                write_json(output/"completion.json", dict(version=VERSION, files=hashes, method_episodes=len(rows),
                    numerical_identity=digest(rows), configurations=len(groups), partition=partition))
            return dict(partition=partition, processed=completed, completed_groups=finished, total_groups=len(groups),
                        complete=finished == len(groups))
        except Exception as error:
            failure = dict(type=type(error).__name__, reason=str(error), at=datetime.now(timezone.utc).isoformat(),
                           elapsed_seconds=time.perf_counter()-started, completed_this_command=completed)
            write_json(output/"failures"/f"{digest(failure)}.json", failure)
            raise


def audit(dataset: Path, training: Path, output: Path):
    receipt, completion = read_json(output/"receipt.json"), read_json(output/"completion.json")
    manifest, cases = load(dataset, receipt["partition"])
    if (receipt["input_identity"] != manifest["input_identity"] or receipt["training_files"] != _files(training)
            or receipt["source_hashes"] != source_hashes()):
        raise ValueError("Evaluation input/source/model identity changed")
    for relative, expected in completion["files"].items():
        path = (output/relative).resolve()
        if not path.is_relative_to(output.resolve()) or file_hash(path) != expected:
            raise ValueError("Completed evidence hash mismatch")
    rows, timings = [], []
    for group in sorted({r["group_id"] for r in cases}):
        r, t = _read_shard(output, group)
        rows.extend(r)
        timings.extend(t)
    final = receipt["partition"].startswith("final")
    count = (4 if final else 2) if manifest["profile"] == "full" else 1
    expected = {(c["problem"]["id"], profile, episode_seed(manifest["profile"], receipt["partition"], i), method)
                for c in cases for profile in ("deterministic", "low", "high")
                for i in range(1 if profile == "deterministic" else count) for method in receipt["methods"]}
    actual = {(r["case_id"], r["profile"], r["episode_seed"], r["method"]) for r in rows}
    if (actual != expected or len(actual) != len(rows) or completion["numerical_identity"] != digest(rows)
            or completion["method_episodes"] != len(rows)):
        raise ValueError("Full evaluation coverage/identity mismatch")
    by_id = {c["problem"]["id"]: c for c in cases}
    for row in rows:
        case = by_id[row["case_id"]]
        p = BenchmarkProblem.model_validate(case["problem"])
        if (row["group_id"] != case["group_id"] or row["mechanism"] != p.family or row["crew_count"] != len(p.crews)
                or row["durations"] != sample_durations(p, row["profile"], row["episode_seed"])):
            raise ValueError("Result input pairing mismatch")
        checked = checked_result(p, row["durations"], tuple(Assignment.model_validate(a) for a in row["schedule"]["assignments"]), row["method"])
        if any(row[k] != v for k, v in checked.items()):
            raise ValueError("Independent schedule/metric mismatch")
        if row["method"] != FIXED and validate_trajectory(p, row["profile"], row["durations"], row["trace"], row["schedule"]):
            raise ValueError("Independent trajectory mismatch")
    summary = summarize(rows, timings, receipt["methods"], receipt["champion"])
    if not final:
        summary["selection"] = select(summary)
    if summary != read_json(output/"summary.json"):
        raise ValueError("Grouped summary regeneration mismatch")
    return dict(status="PASS", method_episodes=len(rows), independent_schedule_metric_trajectory_validation=True,
                numerical_identity=digest(rows))
