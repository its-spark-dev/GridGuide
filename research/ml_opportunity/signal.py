"""Frozen labels/features and fitted weights, inspected without fitting anything."""
from collections import Counter, defaultdict
from itertools import combinations
from statistics import mean

from .audit import STUDENTS
from .evidence import ROOT
from .statistics import distribution


def training_signal(sources):
    # Optional historical numerical adapters. Aggregation remains independent.
    from research.learned_dispatch.features import feature_rows, FEATURE_NAMES
    from research.learned_dispatch.models import load_model
    from research.learned_dispatch.teacher import restore
    base = "docs/learned-dispatch/evidence"
    inventory = sources.json(base+"/training/training.json")
    models = {name: load_model(sources.path(base+"/training/"+inventory["models"][name]["file"]),
                              inventory["models"][name]["sha256"])[0] for name in STUDENTS}
    counts = Counter(within_state_equal_vector_pairs=0, within_state_contradictory_pairs=0)
    action_counts, distinct_counts, margins, positive_margins = [], [], [], []
    vector_targets, pair_signs = defaultdict(list), defaultdict(set)
    errors = {name: defaultdict(list) for name in STUDENTS}
    group_stats = {}
    ranges = [[] for _ in FEATURE_NAMES]
    for path in sorted((ROOT/base/"teacher").glob("*.jsonl.gz")):
        shard, = sources.rows(path.relative_to(ROOT))
        gcount = Counter()
        episode_map = {e["episode_id"]: e for e in shard["episodes"]}
        counts["episodes"] += len(episode_map)
        for row in shard["states"]:
            counts["unique_states"] += 1
            counts["visits"] += len(row["visits"])
            lab = row["label"]
            if not lab["discretionary"]:
                counts["forced_states"] += 1
                continue
            counts["discretionary_states"] += 1
            gcount["discretionary"] += 1
            actions, matrix = feature_rows(restore(shard, row))
            if [vars(a) for a in actions] != lab["actions"]:
                raise ValueError("Feature/action order mismatch")
            targets = lab["targets"]
            if len(targets) != len(actions) or min(targets) != 0:
                raise ValueError("Invalid target rows")
            counts["action_rows"] += len(actions)
            counts["zero_regret_rows"] += sum(t == 0 for t in targets)
            wait = lab["teacher"]["task_id"] is None
            counts["wait_teacher_states"] += wait
            gcount["wait_teacher_states"] += wait
            counts["wait_legal_states"] += any(a.task_id is None for a in actions)
            counts["distinct_optimal_tie_states"] += len({a["task_id"] for a in lab["ties"]}) > 1
            task_target = {}
            for a, t in zip(actions, targets):
                if a.task_id in task_target and abs(task_target[a.task_id]-t) > 1e-12:
                    raise ValueError("Crew alias has contradictory target")
                task_target[a.task_id] = t
            unique_costs = sorted(task_target.values())
            margin = unique_costs[1]-unique_costs[0]
            margins.append(margin)
            positive_margins.extend([margin] if margin > 1e-12 else [])
            action_counts.append(len(actions))
            distinct_counts.append(len(task_target))
            vectors = [tuple(x) for x in matrix.tolist()]
            for x, t in zip(vectors, targets):
                vector_targets[x].append(t)
                for column, v in zip(ranges, x):
                    column.append(v)
            # Collapse crew aliases; equal vectors with different task targets are genuine lost signal.
            choices = {}
            for action, x, t in zip(actions, vectors, targets):
                choices.setdefault(action.task_id, (x, t))
            for (xa, ta), (xb, tb) in combinations(choices.values(), 2):
                if xa == xb:
                    counts["within_state_equal_vector_pairs"] += 1
                    counts["within_state_contradictory_pairs"] += abs(ta-tb) > 1e-12
                    continue
                if xa > xb:
                    xa, xb, ta, tb = xb, xa, tb, ta
                sign = 0 if abs(ta-tb) <= 1e-12 else (1 if ta > tb else -1)
                pair_signs[xa, xb].add(sign)
            pure_seen = any(episode_map[v["episode_id"]]["index"] == 0 for v in row["visits"])
            population = "pure_teacher_seen" if pure_seen else "mixed_only"
            counts[population] += 1
            for name, model in models.items():
                predictions = model.predict(matrix).tolist()
                # Same deterministic action order/tie rule as frozen policy.
                chosen = min(range(len(actions)), key=lambda i:(predictions[i], actions[i].task_id is None,
                                                                actions[i].task_id or "", actions[i].crew_id or ""))
                errors[name][population].append(dict(group=shard["group_id"], regret=targets[chosen],
                    agrees=vars(actions[chosen]) in lab["ties"], wait_chosen=actions[chosen].task_id is None,
                    wait_truth=wait))
        group_stats[shard["group_id"]] = dict(gcount)
    summary = {}
    for name, populations in errors.items():
        summary[name] = {}
        for population in [*populations, "all"]:
            values = [v for p in populations.values() for v in p] if population == "all" else populations[population]
            by_group = defaultdict(list)
            for v in values:
                by_group[v["group"]].append(v["regret"])
            summary[name][population] = dict(states=len(values), agreements=sum(v["agrees"] for v in values),
                regret=distribution(v["regret"] for v in values),
                equal_group_mean_regret=mean(mean(v) for v in by_group.values()),
                wait_chosen=sum(v["wait_chosen"] for v in values),
                wait_teacher=sum(v["wait_truth"] for v in values),
                wait_correct=sum(v["wait_chosen"] and v["wait_truth"] for v in values))
    return dict(counts=dict(counts), legal_action_counts=distribution(action_counts),
        distinct_task_or_wait_counts=distribution(distinct_counts),
        best_second_distinct_action_margin=distribution(margins), positive_margin=distribution(positive_margins),
        feature_count=len(FEATURE_NAMES), unique_feature_vectors=len(vector_targets),
        repeated_feature_vectors=sum(len(v)>1 for v in vector_targets.values()),
        inconsistent_target_vectors=sum(max(v)-min(v)>1e-12 for v in vector_targets.values()),
        pair_vectors=len(pair_signs), opposing_rank_pairs=sum(-1 in v and 1 in v for v in pair_signs.values()),
        tie_vs_strict_pairs=sum(0 in v and len(v)>1 for v in pair_signs.values()),
        feature_ranges={n: [min(v), max(v)] for n,v in zip(FEATURE_NAMES, ranges)},
        groups=group_stats, frozen_model_train_state_error=summary,
        limits=["Exact collisions only; high-dimensional non-collision does not prove identifiability",
                "Regret is normalized approximate teacher cost, not realized policy advantage",
                "Training-state agreement is in-sample and not comparable causally to new-group on-policy agreement",
                "A shared-state additive Ridge term cancels within each decision; interactions can still affect ranking"])
