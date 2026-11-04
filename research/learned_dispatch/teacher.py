"""Actual median-search supervision, never simulated realized-future labels."""
from collections import Counter
from pathlib import Path
import time

import numpy as np

from benchmarks.contracts import BenchmarkProblem
from research.adaptive_dispatch.environment import Action, WAIT, keyed_choice, run_episode
from research.adaptive_dispatch.policies import action_values, heuristic
from research.ml_lab.access import isolated
from research.ml_lab.artifacts import digest, file_hash, read_json, read_rows, write_json, write_rows
from . import VERSION
from .dataset import episode_seed, load, source_hashes
from .features import feature_rows
from .public import action_key, from_public_dict, public_dict, validate_state


def label(state):
    view = validate_state(state)
    if not view.supported or not view.actions:
        raise ValueError("Teacher supervision requires supported complete scope")
    canonical = state.actions(canonical_crew=True)
    if len(canonical) == 1:
        return dict(actions=[vars(a) for a in view.actions], teacher=vars(canonical[0]),
                    ties=[vars(a) for a in view.actions], costs=None, targets=None,
                    crew_aliases=True, discretionary=False)
    costs = action_values(state, median=True)
    selected = min(costs, key=lambda row: (row[1], action_key(row[0])))[0]
    by_task = {a.task_id: q for a, q in costs}
    minimum = min(by_task.values())
    scale = view.context.customers * view.context.mean_nominal / 3600
    expanded = [by_task[a.task_id] for a in view.actions]
    return dict(actions=[vars(a) for a in view.actions], teacher=vars(selected),
        ties=[vars(a) for a, q in zip(view.actions, expanded) if abs(q-minimum) <= 1e-12],
        costs=expanded, targets=[(q-minimum)/scale for q in expanded],
        crew_aliases=True, discretionary=True)


def demonstrations(rows, profile):
    """One immutable configuration shard, preserving every visit and deduplicated states."""
    if not rows or len({r["group_id"] for r in rows}) != 1 or any(r["partition"] != "train" for r in rows):
        raise ValueError("Training demonstrations require one training configuration")
    states, statics, episodes = {}, {}, []
    started = time.perf_counter()
    for row in rows:
        p = BenchmarkProblem.model_validate(row["problem"])
        for stochastic, count in (("deterministic", 1), ("low", 2), ("high", 2)):
            for index in range(count):
                episode_id = digest([p.fingerprint, stochastic, index])
                decision = 0
                def callback(state):
                    nonlocal decision
                    payload = public_dict(state)
                    static = payload.pop("static")
                    static_id = digest(static)
                    statics.setdefault(static_id, static)
                    payload["static_id"] = static_id
                    state_id = digest(payload)
                    if state_id not in states:
                        states[state_id] = dict(state_id=state_id, public=payload, label=label(state), visits=[])
                    target = states[state_id]["label"]
                    chosen = Action(**target["teacher"])
                    behavior = "teacher"
                    if stochastic != "deterministic" and index == 1:
                        mixture = keyed_choice(tuple(range(10)), [VERSION, "behavior-only", episode_id, decision])
                        behavior = "teacher" if mixture < 6 else "downstream" if mixture < 9 else "critical"
                        if behavior != "teacher":
                            chosen = heuristic(state, behavior)
                    states[state_id]["visits"].append(dict(episode_id=episode_id, decision=decision,
                        behavior=behavior, action=vars(chosen)))
                    decision += 1
                    return chosen
                result = run_episode(p, stochastic, episode_seed(profile, "train", index), callback, "training-behavior")
                # Actual futures/outcomes do not enter supervised records; retain validated trajectory identity.
                episodes.append(dict(episode_id=episode_id, input_fingerprint=p.fingerprint, profile=stochastic,
                    index=index, decisions=decision, trajectory_validated=result["trajectory_validated"],
                    schedule_sha256=digest(result["schedule"])))
    records = list(states.values())
    return dict(version=VERSION, group_id=rows[0]["group_id"], input_identity=digest(rows),
        statics=statics, states=records, episodes=episodes,
        diagnostics=dict(episodes=len(episodes), visits=sum(len(s["visits"]) for s in records),
            unique_states=len(records), discretionary_states=sum(s["label"]["discretionary"] for s in records),
            action_rows=sum(len(s["label"]["actions"]) for s in records if s["label"]["discretionary"]),
            teacher_wait_visits=sum(len(s["visits"]) for s in records if s["label"]["teacher"] == vars(WAIT)),
            actions_per_state=dict(Counter(str(len(s["label"]["actions"])) for s in records)),
            behavior=dict(Counter(v["behavior"] for s in records for v in s["visits"]))),
        elapsed_seconds=time.perf_counter()-started)


def restore(shard, row):
    payload = dict(row["public"])
    static_id = payload.pop("static_id")
    static = shard["statics"][static_id]
    if digest(static) != static_id or digest(row["public"]) != row["state_id"]:
        raise ValueError("Public-state identity mismatch")
    payload["static"] = static
    return from_public_dict(payload)


def training_matrix(shards):
    X, y, weights, lineage = [], [], [], []
    groups = set()
    for shard in shards:
        if shard["version"] != VERSION or shard["group_id"] in groups:
            raise ValueError("Duplicate/wrong-version training group")
        groups.add(shard["group_id"])
        discretionary = [r for r in shard["states"] if r["label"]["discretionary"]]
        if not discretionary:
            raise ValueError("Training group has no discretionary states")
        identities = set()
        for row in discretionary:
            state = restore(shard, row)
            actions, features = feature_rows(state)
            if row["state_id"] in identities or [vars(a) for a in actions] != row["label"]["actions"]:
                raise ValueError("Duplicate state or invalid action labels")
            identities.add(row["state_id"])
            target = row["label"]["targets"]
            if (len(target) != len(actions) or not all(type(v) in (int, float) and np.isfinite(v) and v >= 0 for v in target)
                    or min(target) != 0):
                raise ValueError("Invalid supervised costs")
            X.extend(features)
            y.extend(target)
            weights.extend([1/len(discretionary)/len(actions)]*len(actions))
            lineage.extend([(shard["group_id"], row["state_id"])]*len(actions))
    w = np.asarray(weights)
    if not len(w):
        raise ValueError("Empty supervised dataset")
    w /= w.mean()
    return np.asarray(X), np.asarray(y), w, lineage


def collect(dataset: Path, destination: Path, max_groups=4):
    if (dataset/"evaluation-receipt.json").exists():
        raise ValueError("Final cohort already spent; training is closed")
    with isolated(dataset/"final_id.jsonl.gz", dataset/"final_shift.jsonl.gz"):
        manifest, rows = load(dataset, "train", committed=read_json(dataset/"manifest.json")["profile"] == "full")
        identity = dict(version=VERSION, input_identity=manifest["input_identity"], source_hashes=source_hashes())
        registry = destination/"collection.json"
        if registry.exists():
            if read_json(registry) != identity:
                raise ValueError("Teacher collection source/input changed")
        else:
            write_json(registry, identity)
        completed = 0
        for group in sorted({r["group_id"] for r in rows}):
            path = destination/f"{group}.jsonl.gz"
            receipt = destination/f"{group}.json"
            if receipt.exists():
                if file_hash(path) != read_json(receipt)["sha256"]:
                    raise ValueError("Teacher shard hash mismatch")
                continue
            if path.exists():
                raise ValueError("Incomplete teacher write; inspect without overwriting evidence")
            if completed >= max_groups:
                break
            shard = demonstrations([r for r in rows if r["group_id"] == group], manifest["profile"])
            elapsed = shard.pop("elapsed_seconds")  # timings never alter numerical/label artifact identities
            write_rows(path, [shard])
            write_json(receipt, dict(sha256=file_hash(path), diagnostics=shard["diagnostics"],
                                    elapsed_seconds=elapsed))
            completed += 1
        return dict(processed=completed, expected_groups=len(rows)//2,
                    completed_groups=len(list(destination.glob("learned-*.jsonl.gz"))))


def load_shards(dataset: Path, destination: Path):
    manifest, rows = load(dataset, "train")
    registry = read_json(destination/"collection.json")
    if registry["input_identity"] != manifest["input_identity"] or registry["source_hashes"] != source_hashes():
        raise ValueError("Teacher input/source mismatch")
    shards = []
    for group in sorted({r["group_id"] for r in rows}):
        path = destination/f"{group}.jsonl.gz"
        if file_hash(path) != read_json(destination/f"{group}.json")["sha256"]:
            raise ValueError("Teacher shard hash mismatch")
        shard, = read_rows(path)
        if shard["group_id"] != group or shard["input_identity"] != digest([r for r in rows if r["group_id"] == group]):
            raise ValueError("Teacher lineage mismatch")
        shards.append(shard)
    return shards
