"""Independent fictional benchmark generator. Never imports challenge data.

Hash-derived integers avoid dependence on random-library algorithms. The checked-in
manifest binds every problem's content; default runs verify it, never rewrite it.
"""
import hashlib
import json
from pathlib import Path
from .contracts import BenchmarkProblem, BenchmarkTask, BenchmarkCrew, CustomerGroup, canonical

FAMILIES = ('serial-chain','independent-branches','upstream-bottleneck','overlapping-dependencies','blocked-prerequisites','critical-tradeoffs')
EVALUATION_SEEDS = (101,211,307,401,503)
DEVELOPMENT_SEEDS = (17,29)
FROZEN = Path(__file__).parent/'frozen'/'evaluation-v1.json'
# Set once at preregistration, before policy results. Updates require a new suite/version.
FROZEN_SHA256 = '985b1e1963fa4006f83417586ce3cb18ed6981dc9f77c3e56cc512e007338527'


def number(seed, key, maximum):
    return int.from_bytes(hashlib.sha256(f'benchmark-generator-v1:{seed}:{key}'.encode()).digest()[:8], 'big') % maximum


def generate(family, size, crews, seed, split='evaluation'):
    if family not in FAMILIES or size not in (10,25,100) or crews not in (1,2,4):
        raise ValueError('Outside preregistered matrix')
    task_ids = [f'syn-task-{i:03d}' for i in range(size)]
    tasks, groups = [], []
    for i, task_id in enumerate(task_ids):
        prerequisites = ()
        if family == 'serial-chain' and i:
            prerequisites=(task_ids[i-1],)
        elif family in ('upstream-bottleneck','blocked-prerequisites') and i:
            prerequisites=(task_ids[0],)
        # Effort is independent total person-hours, not workbook-derived.
        tasks.append(BenchmarkTask(id=task_id,total_person_hours=str(1+number(seed,f'effort-{i}',12)),
            prerequisites=prerequisites,report_order=number(seed,f'order-{i}',size),
            access='blocked' if family=='blocked-prerequisites' and i==0 else 'clear'))
        deps = (task_id,)
        if family in ('serial-chain','upstream-bottleneck','blocked-prerequisites'):
            deps = tuple(task_ids[:i+1]) if family=='serial-chain' else tuple(dict.fromkeys((task_ids[0],task_id)))
        elif family=='overlapping-dependencies':
            deps=tuple(sorted({task_id,task_ids[(i+1)%size],task_ids[0]}))
        count=1+number(seed,f'customers-{i}',20)
        groups.append(CustomerGroup(id=f'syn-group-{i:03d}',customer_ids=tuple(f'syn-customer-{i:03d}-{j:02d}' for j in range(count)),
            required_tasks=deps,branch=f'syn-branch-{i%4}',critical_service=family=='critical-tradeoffs' and i%5==0))
    return BenchmarkProblem(id=f'syn-{family}-{size}-{crews}-{seed}',family=family,seed=seed,split=split,
        tasks=tuple(tasks),groups=tuple(groups),crews=tuple(BenchmarkCrew(id=f'syn-crew-{c}',available_tick=0 if c==0 else number(seed,f'availability-{c}',3)*3600) for c in range(crews)))


def manifest():
    return {'version':'evaluation-manifest-v1','generator':'benchmark-generator-v1',
        'evaluation_seeds':list(EVALUATION_SEEDS),'development_seeds':list(DEVELOPMENT_SEEDS),
        'tasks':[10,25,100],'crews':[1,2,4],'families':list(FAMILIES),
        'cases':[{'id':p.id,'family':f,'tasks':n,'crews':c,'seed':seed,'sha256':p.fingerprint}
                 for f in FAMILIES for n in (10,25,100) for c in (1,2,4) for seed in EVALUATION_SEEDS
                 for p in (generate(f,n,c,seed),)]}


def load_evaluation():
    payload = FROZEN.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=FROZEN_SHA256:
        raise ValueError('Frozen evaluation manifest changed')
    pinned = json.loads(payload)
    if pinned != manifest():
        raise ValueError('Generator no longer reproduces frozen evaluation inputs')
    return [generate(c['family'],c['tasks'],c['crews'],c['seed']) for c in pinned['cases']]


def microcase(name, efforts, counts, deps=None, prerequisites=None, crews=1, availability=None, blocked=(), unresolved=(), critical=()):
    ids=[f'syn-task-{i}' for i in range(len(efforts))]
    return BenchmarkProblem(id=f'syn-micro-{name}',family='micro',seed=0,split='micro',
        tasks=tuple(BenchmarkTask(id=ids[i],total_person_hours=None if e is None else str(e),report_order=i,
            access='blocked' if i in blocked else 'clear',prerequisites=tuple(ids[j] for j in (prerequisites or {}).get(i,()))) for i,e in enumerate(efforts)),
        groups=tuple(CustomerGroup(id=f'syn-group-{i}',customer_ids=tuple(f'syn-customer-{i}-{j}' for j in range(count)),
            required_tasks=tuple(ids[j] for j in (deps or {}).get(i,(i,))),branch=f'syn-branch-{i}',
            unresolved_dependency=i in unresolved,critical_service=i in critical) for i,count in enumerate(counts)),
        crews=tuple(BenchmarkCrew(id=f'syn-crew-{c}',available_tick=(availability or {}).get(c,0)) for c in range(crews)))


def microcases():
    return [microcase('weighted',[4,1],[1,10]),
            microcase('overlap',[2,3],[2,1],deps={0:(0,1),1:(0,)}),
            microcase('chain-eight',[1]*8,[1]*8,prerequisites={i:(i-1,) for i in range(1,8)}),
            microcase('two-crews',[3,2,1],[2,3,1],crews=2,availability={1:3600}),
            microcase('blocked',[2,1],[4,2],prerequisites={1:(0,)},blocked=(0,)),
            microcase('unknown',[None,1],[2,3],unresolved=(0,)),
            microcase('censored',[200,1],[1,1]),
            microcase('critical',[4,1],[1,10],critical=(0,))]
