"""Fresh configuration groups with separate, sealed partition files (inputs only)."""
from collections import Counter
from pathlib import Path
import random

from benchmarks.contracts import BenchmarkCrew, BenchmarkProblem
from research.ml_lab.artifacts import (ROOT, digest, file_hash, read_json, read_rows,
    require_committed, revision, validate_hashes, write_json, write_rows)
from research.ml_lab.contracts import GenerationConfig, topology_hash
from research.ml_lab.generator import ID_MECHANISMS, SHIFT_MECHANISMS, _base_problem, configuration
from . import VERSION, SEED

PARTITIONS = ("train", "dev", "final_id", "final_shift")
GENERATOR_VERSION = "learned-dispatch-generator-v1"


def historical_signatures():
    paths = [ROOT/"docs/ml-lab/evidence/dataset/manifest.json",
             ROOT/"docs/adaptive-dispatch/evidence/dataset/manifest.json"]
    signatures = set()
    # Only published input metadata, never historical labels or scores.
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "graph_hash":
                    signatures.add(item)
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    for path in paths:
        visit(read_json(path))
    if not signatures:
        raise ValueError("Historical topology exclusion metadata missing")
    return signatures, {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def source_hashes():
    from research.adaptive_dispatch.dataset import source_hashes as inherited
    hashes = inherited()
    paths = list((ROOT/"research/learned_dispatch").glob("*.py"))
    paths += [ROOT/"docs/learned-dispatch/PROTOCOL.md"]
    hashes.update({str(p.relative_to(ROOT)): file_hash(p) for p in paths
                   if p.name not in ("report.py", "__main__.py")})
    return dict(sorted(hashes.items()))


def generate(profile="full"):
    if profile not in ("full", "smoke"):
        raise ValueError("Unknown generation profile")
    seen, _ = historical_signatures()
    cases = []
    for partition, count in zip(PARTITIONS, (48, 16, 24, 24)):
        mechanisms = SHIFT_MECHANISMS if partition == "final_shift" else ID_MECHANISMS
        for index in range(count if profile == "full" else 2):
            mechanism = mechanisms[index % len(mechanisms)]
            group = f"learned-{profile}-{partition.replace('_', '-')}-{index:03d}"
            shifted = partition == "final_shift"
            for attempt in range(100):
                seed = int(digest([SEED, GENERATOR_VERSION, group, attempt])[:12], 16)
                rng = random.Random(seed ^ 0xD1571)
                cfg = GenerationConfig.model_validate({**configuration(mechanism, seed, attempt).model_dump(),
                    "task_count": rng.randint(18, 24) if shifted else rng.randint(10, 14),
                    "group_count": rng.randint(12, 20) if shifted else rng.randint(8, 16),
                    "incomplete_mode": "none"})
                base = _base_problem(cfg, group, partition)
                signature = topology_hash(base)
                if signature not in seen:
                    break
            else:
                raise RuntimeError("Input-only topology rejection exhausted")
            seen.add(signature)
            forced_critical = not any(g.critical_service for g in base.groups)
            if forced_critical:
                base = BenchmarkProblem.model_validate({**base.model_dump(), "groups": [
                    {**g.model_dump(), "critical_service": g.critical_service or i == 0}
                    for i, g in enumerate(base.groups)]})
            arrivals = [round(rng.uniform(0, cfg.crew_delay_hours)*3600) for _ in range(4)]
            for crew_count in ((1, 4) if shifted else (2, 3)):
                p = BenchmarkProblem.model_validate({**base.model_dump(), "id": f"syn-{group}-c{crew_count}",
                    "crews": tuple(BenchmarkCrew(id=f"syn-crew-{i}", available_tick=arrivals[i])
                                   for i in range(crew_count))})
                cases.append(dict(version=VERSION, generator_version=GENERATOR_VERSION, group_id=group,
                    partition=partition, configuration=cfg.model_dump(mode="json"), graph_hash=signature,
                    forced_critical=forced_critical, problem=p.model_dump(mode="json"), input_fingerprint=p.fingerprint))
    return cases


def validate_cases(cases, complete=True):
    groups, signatures, seeds, identities = {}, {}, {}, set()
    old, _ = historical_signatures()
    for row in cases:
        if row["version"] != VERSION or row["generator_version"] != GENERATOR_VERSION:
            raise ValueError("Input version mismatch")
        cfg = GenerationConfig.model_validate(row["configuration"])
        p = BenchmarkProblem.model_validate(row["problem"])
        group, partition = row["group_id"], row["partition"]
        if partition not in PARTITIONS or p.seed != cfg.seed or p.family != cfg.mechanism:
            raise ValueError("Configuration lineage mismatch")
        shifted = partition == "final_shift"
        if (p.split != ("evaluation" if partition.startswith("final") else "development")
                or cfg.mechanism not in (SHIFT_MECHANISMS if shifted else ID_MECHANISMS)
                or not (18 <= len(p.tasks) <= 24 if shifted else 10 <= len(p.tasks) <= 14)
                or len(p.tasks) != cfg.task_count or len(p.groups) != cfg.group_count
                or p.fingerprint != row["input_fingerprint"] or p.id in identities):
            raise ValueError("Input scope/identity mismatch")
        identities.add(p.id)
        signature = topology_hash(p)
        if signature in old or signature != row["graph_hash"] or signatures.setdefault(signature, group) != group:
            raise ValueError("Historical/cross-configuration graph duplicate")
        if seeds.setdefault(cfg.seed, group) != group:
            raise ValueError("Cross-configuration seed reuse")
        structure = digest([cfg.model_dump(mode="json"), [t.model_dump(mode="json") for t in p.tasks],
                            [g.model_dump(mode="json") for g in p.groups], row["forced_critical"]])
        prev = groups.setdefault(group, [partition, structure, set()])
        if prev[:2] != [partition, structure] or len(p.crews) in prev[2]:
            raise ValueError("Group split/structure/crew variant mismatch")
        prev[2].add(len(p.crews))
        if (any(t.access != "clear" or t.total_person_hours is None for t in p.tasks)
                or any(g.unresolved_dependency for g in p.groups) or not any(g.critical_service for g in p.groups)
                or any(c.people != 4 for c in p.crews) or p.duration_assumption != "one_effective_worker"):
            raise ValueError("Primary complete-scope assumptions violated")
    if complete and any(v[2] != ({1, 4} if v[0] == "final_shift" else {2, 3}) for v in groups.values()):
        raise ValueError("Incomplete crew variants")
    return dict(cases=len(cases), groups=len(groups), partitions=dict(Counter(r["partition"] for r in cases)))


def prepare(destination: Path, profile="full"):
    if destination.exists():
        raise ValueError("Input destination already exists")
    rows = generate(profile)
    counts = validate_cases(rows)
    hashes = {}
    for partition in PARTITIONS:
        path = destination/f"{partition}.jsonl.gz"
        write_rows(path, [r for r in rows if r["partition"] == partition])
        hashes[path.name] = file_hash(path)
    old, exclusions = historical_signatures()
    manifest = dict(version=VERSION, generator_version=GENERATOR_VERSION, profile=profile,
        revision=revision(), source_hashes=source_hashes(), counts=counts, partition_files=hashes,
        input_identity=digest(rows), historical_inputs=exclusions, excluded_topologies=len(old),
        configurations=[{k: r[k] for k in ("group_id", "partition", "configuration", "graph_hash", "forced_critical")}
                        for r in rows[::2]])
    write_json(destination/"manifest.json", manifest)
    return manifest


def load(destination: Path, partition: str, committed=False):
    if partition not in PARTITIONS:
        raise ValueError("Unknown partition")
    manifest = read_json(destination/"manifest.json")
    if manifest["version"] != VERSION or manifest["generator_version"] != GENERATOR_VERSION:
        raise ValueError("Dataset manifest version mismatch")
    filename = f"{partition}.jsonl.gz"
    validate_hashes(destination, {filename: manifest["partition_files"][filename]})
    rows = read_rows(destination/filename)
    counts = validate_cases(rows)
    if (any(r["partition"] != partition for r in rows)
            or counts["cases"] != manifest["counts"]["partitions"][partition]):
        raise ValueError("Partition manifest mismatch")
    if committed:
        require_committed([destination/"manifest.json", destination/filename])
    return manifest, rows


def episode_seed(profile, partition, index):
    if profile not in ("full", "smoke") or partition not in PARTITIONS or type(index) is not int or index < 0:
        raise ValueError("Invalid episode namespace")
    return int(digest([VERSION, "private-episode", profile, partition, index])[:15], 16)
