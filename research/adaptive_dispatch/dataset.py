"""Fresh configuration groups, pinned input-only manifests, no benchmark outcomes."""
from collections import Counter
from pathlib import Path
import random

from benchmarks.contracts import BenchmarkCrew, BenchmarkProblem
from research.ml_lab.artifacts import (ROOT, digest, file_hash, read_json, read_rows,
    require_committed, revision, validate_hashes, write_json, write_rows)
from research.ml_lab.contracts import GenerationConfig, topology_hash
from research.ml_lab.generator import ID_MECHANISMS, _base_problem, configuration
from . import VERSION

GENERATOR_VERSION = "adaptive-generator-v1"
MASTER_SEED = 2026110403


def source_hashes():
    paths = list((ROOT / "research/adaptive_dispatch").glob("*.py"))
    paths += [ROOT / "research/ml_lab" / f"{name}.py" for name in ("generator", "contracts", "artifacts", "access")]
    paths += [ROOT / "benchmarks" / f"{name}.py" for name in ("contracts", "policies", "metrics", "validation")]
    paths += [ROOT / "backend/contracts.py", ROOT / "backend/risk_rules.py", ROOT / "requirements-ml.lock",
              ROOT / "docs/adaptive-dispatch/PROTOCOL.md"]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths) if p.name not in ("report.py", "__main__.py")}


def generate(profile="full"):
    if profile not in ("full", "smoke"):
        raise ValueError("Unknown input profile")
    seen = set()
    cases = []
    for partition, count in (("discovery", 3), ("confirmation", 6)):
        for mechanism in ID_MECHANISMS:
            for index in range(count if profile == "full" else 1):
                group = f"adaptive-{profile}-{partition}-{mechanism.replace('_', '-')}-{index:03d}"
                for attempt in range(100):
                    seed = int(digest([MASTER_SEED, group, attempt])[:12], 16)
                    rng = random.Random(seed ^ 0xADA)
                    original = configuration(mechanism, seed, attempt)
                    cfg = GenerationConfig.model_validate({**original.model_dump(),
                        "task_count": rng.randint(10, 14), "group_count": rng.randint(8, 16),
                        "incomplete_mode": "none"})
                    base = _base_problem(cfg, group, "train")
                    signature = topology_hash(base)
                    if signature not in seen:
                        break
                else:
                    raise RuntimeError("Input-only topology rejection exhausted")
                seen.add(signature)
                arrivals = [round(rng.uniform(0, cfg.crew_delay_hours) * 3600) for _ in range(3)]
                for crew_count in (2, 3):
                    p = BenchmarkProblem.model_validate({**base.model_dump(), "id": f"syn-{group}-c{crew_count}",
                        "crews": [BenchmarkCrew(id=f"syn-crew-{c}", available_tick=arrivals[c]) for c in range(crew_count)]})
                    cases.append(dict(version=VERSION, generator_version=GENERATOR_VERSION, group_id=group,
                        partition=partition, configuration=cfg.model_dump(mode="json"), graph_hash=signature,
                        problem=p.model_dump(mode="json"), input_fingerprint=p.fingerprint))
    return cases


def validate_cases(cases):
    groups, signatures, identities, seeds = {}, {}, set(), {}
    for row in cases:
        if row["version"] != VERSION or row["generator_version"] != GENERATOR_VERSION:
            raise ValueError("Adaptive input version mismatch")
        cfg = GenerationConfig.model_validate(row["configuration"])
        p = BenchmarkProblem.model_validate(row["problem"])
        group, partition = row["group_id"], row["partition"]
        if partition not in ("discovery", "confirmation") or p.seed != cfg.seed or p.family != cfg.mechanism:
            raise ValueError("Configuration lineage mismatch")
        if len(p.tasks) != cfg.task_count or len(p.groups) != cfg.group_count or p.fingerprint != row["input_fingerprint"]:
            raise ValueError("Input identity mismatch")
        if p.id in identities:
            raise ValueError("Duplicate problem")
        identities.add(p.id)
        signature = topology_hash(p)
        if signature != row["graph_hash"] or signatures.setdefault(signature, group) != group:
            raise ValueError("Cross-configuration graph duplicate")
        if seeds.setdefault(cfg.seed, group) != group:
            raise ValueError("Cross-configuration seed reuse")
        structural = digest([cfg.model_dump(mode="json"), [t.model_dump(mode="json") for t in p.tasks],
                             [g.model_dump(mode="json") for g in p.groups]])
        previous = groups.setdefault(group, [partition, structural, set()])
        if previous[:2] != [partition, structural] or len(p.crews) in previous[2]:
            raise ValueError("Group split/structure/crew variant mismatch")
        previous[2].add(len(p.crews))
        if any(t.access != "clear" or t.total_person_hours is None for t in p.tasks) or any(g.unresolved_dependency for g in p.groups):
            raise ValueError("Primary cohort requires complete input scope")
    if any(v[2] != {2, 3} for v in groups.values()):
        raise ValueError("Incomplete paired crew variants")
    return dict(cases=len(cases), groups=len(groups), partitions=dict(Counter(r["partition"] for r in cases)))


def prepare(destination: Path, profile="full"):
    if destination.exists():
        raise ValueError("Input destination already exists")
    rows = generate(profile)
    counts = validate_cases(rows)
    write_rows(destination / "cases.jsonl.gz", rows)
    manifest = dict(version=VERSION, generator_version=GENERATOR_VERSION, profile=profile,
        revision=revision(), source_hashes=source_hashes(), counts=counts,
        cases_sha256=file_hash(destination / "cases.jsonl.gz"), input_identity=digest(rows),
        partitions={p: digest([r for r in rows if r["partition"] == p]) for p in ("discovery", "confirmation")},
        configurations=[{k: r[k] for k in ("group_id", "partition", "configuration", "graph_hash")}
                        for r in rows if len(r["problem"]["crews"]) == 2])
    write_json(destination / "manifest.json", manifest)
    return manifest


def load(destination: Path, committed=False):
    manifest = read_json(destination / "manifest.json")
    validate_hashes(destination, {"cases.jsonl.gz": manifest["cases_sha256"]})
    rows = read_rows(destination / "cases.jsonl.gz")
    if validate_cases(rows) != manifest["counts"] or digest(rows) != manifest["input_identity"]:
        raise ValueError("Input manifest mismatch")
    if committed:
        require_committed([destination / "manifest.json", destination / "cases.jsonl.gz"])
    return manifest, rows


def episode_seed(profile, partition, index):
    """Disjoint scientific/smoke and discovery/confirmation random namespaces."""
    if profile not in ("full", "smoke") or partition not in ("discovery", "confirmation") or type(index) is not int or index < 0:
        raise ValueError("Invalid duration seed namespace")
    return int(digest([VERSION, "duration-episode", profile, partition, index])[:15], 16)
