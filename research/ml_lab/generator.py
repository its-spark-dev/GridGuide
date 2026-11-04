"""New parameterized synthetic DAG mechanisms; no G2 generator or outcomes imported."""
from decimal import Decimal
import random

from benchmarks.contracts import BenchmarkCrew, BenchmarkProblem, BenchmarkTask, CustomerGroup
from .contracts import GenerationConfig, MLCase, digest, topology_hash

ID_MECHANISMS = ('random_ordered', 'layered', 'bottleneck', 'modular')
SHIFT_MECHANISMS = ('preferential', 'deep_sparse')
PARTITIONS = ('train', 'dev', 'final_id', 'final_shift')
MASTER_SEED = 2026110401


def configuration(mechanism: str, seed: int, attempt: int) -> GenerationConfig:
    rng = random.Random(seed)
    shifted = mechanism in SHIFT_MECHANISMS
    return GenerationConfig(
        mechanism=mechanism, task_count=rng.randint(40, 64) if shifted else rng.randint(10, 36),
        edge_density=round(rng.uniform(.06, .32), 6), layers=rng.randint(3, 8),
        modules=rng.randint(2, 5), effort_family=rng.choice(('uniform', 'lognormal', 'mixture')),
        effort_scale=round(rng.uniform(.5, 6), 6), effort_spread=round(rng.uniform(.3, 1.3), 6),
        overlap=round(rng.uniform(.05, .8), 6), group_count=rng.randint(8, 28),
        size_skew=round(rng.uniform(0, 1), 6), critical_prevalence=round(rng.uniform(0, .4), 6),
        report_mode=rng.choice(('random', 'effort', 'membership')),
        crew_delay_hours=round(rng.uniform(0, 8 if shifted else 3), 6),
        incomplete_mode=rng.choices(('none', 'blocked', 'missing_effort', 'unresolved_dependency'),
                                   weights=(85, 5, 5, 5))[0], seed=seed, attempt=attempt)


def _edges(cfg: GenerationConfig, rng: random.Random) -> list[set[int]]:
    n, p, mode = cfg.task_count, cfg.edge_density, cfg.mechanism
    parents: list[set[int]] = [set() for _ in range(n)]
    levels = sorted([0, cfg.layers-1] + [rng.randrange(cfg.layers) for _ in range(n-2)])
    hubs = sorted(rng.sample(range(1, n-2), min(3, n//5)))
    degree = [1] * n
    for j in range(1, n):
        for i in range(j):
            chance = p
            if mode == 'layered':
                chance = min(.85, p*2.5) if levels[j] == levels[i]+1 else (p*.12 if levels[j] > levels[i] else 0)
            elif mode == 'bottleneck':
                chance = .7 if i in hubs and j > i else p*.3
            elif mode == 'modular':
                chance = min(.8, p*2) if i % cfg.modules == j % cfg.modules else p*.12
            elif mode == 'preferential':
                chance = min(.8, degree[i] * 1.6 / sum(degree[:j]))
            elif mode == 'deep_sparse':
                chance = .86 if i == j-1 else p*.08
            if rng.random() < chance:
                parents[j].add(i)
                degree[i] += 1
        if mode == 'bottleneck' and j in hubs:
            parents[j].update(i for i in range(j) if rng.random() < .5)
    # Every mechanism has many draws; no fixed family-specific adjacency template.
    return parents


def _base_problem(cfg: GenerationConfig, group_id: str, partition: str) -> BenchmarkProblem:
    rng = random.Random(cfg.seed ^ 0xB17D)
    n = cfg.task_count
    parents = _edges(cfg, rng)
    # Randomize task identifiers independently of topological order. IDs are not features.
    ids = [f'syn-t-{i:03d}' for i in rng.sample(range(n), n)]
    effort = []
    for _ in range(n):
        if cfg.effort_family == 'uniform':
            value = cfg.effort_scale * rng.uniform(.2, 2)
        elif cfg.effort_family == 'lognormal':
            value = cfg.effort_scale * rng.lognormvariate(0, cfg.effort_spread)
        else:
            value = cfg.effort_scale * rng.uniform(.1, .8) * (rng.choice((1, 1, 1, 8)))
        effort.append(Decimal(str(round(max(.02, value), 4))))
    groups = []
    memberships = [0] * n
    hot = rng.sample(range(n), min(n, max(2, n//5)))
    for g in range(cfg.group_count):
        count = max(1, min(60, round(rng.uniform(1, 12) + cfg.size_skew*rng.expovariate(1/18))))
        required = {rng.randrange(n)}
        if rng.random() < cfg.overlap:
            required.update(rng.sample(hot, min(len(hot), rng.randint(1, 4))))
        if rng.random() < cfg.overlap*.5:
            required.update(rng.sample(range(n), rng.randint(1, min(4, n))))
        for i in required:
            memberships[i] += count
        groups.append(CustomerGroup(id=f'syn-g-{g:03d}',
            customer_ids=tuple(f'syn-c-{g:03d}-{c:03d}' for c in range(count)),
            required_tasks=tuple(sorted(ids[i] for i in required)),
            unresolved_dependency=cfg.incomplete_mode == 'unresolved_dependency' and g == 0,
            branch=f'syn-b-{g % cfg.modules}', critical_service=rng.random() < cfg.critical_prevalence))
    order = list(range(n))
    if cfg.report_mode == 'random':
        rng.shuffle(order)
    elif cfg.report_mode == 'effort':
        order.sort(key=lambda i: (effort[i], rng.random()))
    else:
        order.sort(key=lambda i: (-memberships[i], rng.random()))
    report = {i: rank for rank, i in enumerate(order)}
    # Ensure blocked/missing effort affects an actual customer, not an unneeded task.
    unavailable = ids.index(groups[0].required_tasks[0])
    tasks = tuple(BenchmarkTask(id=ids[i], total_person_hours=None if
        cfg.incomplete_mode == 'missing_effort' and i == unavailable else effort[i],
        prerequisites=tuple(sorted(ids[p] for p in parents[i])), report_order=report[i],
        access='blocked' if cfg.incomplete_mode == 'blocked' and i == unavailable else 'clear') for i in range(n))
    return BenchmarkProblem(id=f'syn-{group_id}-c1', family=cfg.mechanism, seed=cfg.seed,
        split='evaluation' if partition.startswith('final') else 'development', tasks=tasks,
        groups=tuple(groups), crews=(BenchmarkCrew(id='syn-crew-0', available_tick=0),))


def generate_suite(profile: str = 'full') -> list[MLCase]:
    """Group entire graph/customer realizations; three crew variants never cross splits."""
    if profile not in ('full', 'smoke'):
        raise ValueError('Unknown dataset profile')
    counts = (30, 10, 10, 20) if profile == 'full' else (3, 2, 2, 2)
    cases: list[MLCase] = []
    seen_graphs: set[str] = set()
    for partition, count in zip(PARTITIONS, counts):
        mechanisms = SHIFT_MECHANISMS if partition == 'final_shift' else ID_MECHANISMS
        for mechanism in mechanisms:
            for index in range(count):
                group_id = f'ml-{partition.replace("_", "-")}-{mechanism.replace("_", "-")}-{index:03d}'
                for attempt in range(100):
                    seed = int(digest([MASTER_SEED, profile, group_id, attempt])[:12], 16)
                    cfg = configuration(mechanism, seed, attempt)
                    base = _base_problem(cfg, group_id, partition)
                    graph_hash = topology_hash(base)
                    if graph_hash not in seen_graphs:
                        break
                else:
                    raise RuntimeError('Graph diversity rejection budget exhausted')
                seen_graphs.add(graph_hash)
                rng = random.Random(seed ^ 0xC2E7)
                availability = [round(rng.uniform(0, cfg.crew_delay_hours)*3600) for _ in range(4)]
                for crew_count in (1, 2, 4):
                    problem = BenchmarkProblem.model_validate({**base.model_dump(),
                        'id': f'syn-{group_id}-c{crew_count}',
                        'crews': tuple(BenchmarkCrew(id=f'syn-crew-{c}', available_tick=availability[c])
                                       for c in range(crew_count))})
                    cases.append(MLCase(partition=partition, group_id=group_id,
                        configuration=cfg, graph_hash=graph_hash, problem=problem))
    return cases
