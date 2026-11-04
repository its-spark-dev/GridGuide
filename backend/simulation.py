"""Assumption-based fixed-timetable replay; no policy selection or solver calls."""
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from benchmarks.contracts import canonical, duration_ticks
from backend.simulation_contracts import SimulationInput, SimulationMetadata

VERSION = 'fixed-timetable-simulation-v1'
PROFILE_PATH = Path(__file__).resolve().parents[1]/'benchmarks/simulation_profiles.json'
PROFILE_HASH = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()
PROFILES = json.loads(PROFILE_PATH.read_text())['profiles']
RNG = 'SHA256-keyed-PCG64/BoxMuller-cos-v1'


def digest(arrays):
    h=hashlib.sha256()
    for key,a in sorted(arrays.items()):
        a=np.ascontiguousarray(a)
        h.update(canonical([key,a.dtype.str,list(a.shape)]));h.update(a.tobytes())
    return h.hexdigest()


def uniforms(fingerprint, profile, seed, stream, trials):
    key=canonical([VERSION,fingerprint,profile,seed,stream])
    generator=np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(key).digest(),'big')))
    return generator.random((trials,2))


def normal(fingerprint, profile, seed, stream, trials):
    u=uniforms(fingerprint,profile,seed,stream,trials)
    return np.sqrt(-2*np.log1p(-u[:,0]))*np.cos(2*np.pi*u[:,1])


def draws(request):
    p=request.problem;n=request.trials;spec=PROFILES[request.profile];fingerprint=p.fingerprint
    shared=normal(fingerprint,request.profile,request.seed,'event',n) if spec['shared'] else np.zeros(n)
    values={}
    for task in sorted(p.tasks,key=lambda t:t.id):
        d=duration_ticks(p,task)
        if d is None: continue
        if spec['family']=='deterministic':m=np.ones(n)
        elif spec['family']=='uniform':m=.5+uniforms(fingerprint,request.profile,request.seed,task.id,n)[:,0]
        else:
            z=normal(fingerprint,request.profile,request.seed,task.id,n)
            m=np.exp(spec['sigma']*((shared+z)/np.sqrt(2) if spec['shared'] else z))
        raw=np.ceil(d*m)
        # Conservative bound allows sums/customer-weighting without int64 overflow.
        limit=(2**53-1)/(len(p.tasks)*sum(len(g.customer_ids) for g in p.groups))
        if not np.all(np.isfinite(raw)) or np.any(raw<1) or np.any(raw>limit):
            raise ValueError('Nonfinite or out-of-range sampled duration')
        values[task.id]=raw.astype('<i8')
    hold=np.ceil(uniforms(fingerprint,request.profile,request.seed,'hold',n)[:,0]*spec['hold_hours']*3600).astype('<i8')
    return values,hold


def replay(request, durations, hold):
    p=request.problem;s=request.schedule;n=request.trials
    if set(durations)!={t.id for t in p.tasks if duration_ticks(p,t) is not None}:
        raise ValueError('Draw task scope mismatch')
    if hold.shape!=(n,) or hold.dtype.kind not in 'iu' or np.any(hold<0) or np.any(hold>14400):
        raise ValueError('Invalid hold')
    for d in durations.values():
        if d.shape!=(n,) or d.dtype.kind not in 'iu' or np.any(d<=0) or np.any(d>2**52//(100*sum(len(g.customer_ids) for g in p.groups))):
            raise ValueError('Invalid duration array')
    tasks={t.id:t for t in p.tasks};crew={c.id:c for c in p.crews}
    assignments={a.task_id:a for a in s.assignments}
    dependencies={i:set(tasks[i].prerequisites) for i in assignments}
    for c in crew:
        ordered=sorted((a for a in s.assignments if a.crew_id==c),key=lambda a:(a.start_tick,a.task_id))
        for before,after in zip(ordered,ordered[1:]):dependencies[after.task_id].add(before.task_id)
    starts={};ends={}
    while len(ends)<len(assignments):
        ready=sorted(i for i in assignments if i not in ends and dependencies[i]<=ends.keys())
        if not ready:raise ValueError('Cyclic fixed crew/prerequisite order')
        for i in ready:
            a=assignments[i]
            start=np.maximum(a.start_tick+hold,crew[a.crew_id].available_tick+hold)
            for parent in dependencies[i]:start=np.maximum(start,ends[parent])
            starts[i]=start;ends[i]=start+durations[i]
            if not np.all(ends[i]>start):raise ValueError('Finish overflow')
    # Independently assert all constraints over every trial, including planned starts.
    for i,a in assignments.items():
        if np.any(starts[i]<a.start_tick+hold) or np.any(starts[i]<crew[a.crew_id].available_tick+hold):
            raise ValueError('Start violation')
        for parent in dependencies[i]:
            if np.any(starts[i]<ends[parent]):raise ValueError('Precedence/crew violation')
        if np.any(ends[i]-starts[i]!=durations[i]):raise ValueError('Duration violation')
    return starts,ends


def metrics(problem, ends, trials):
    """Vectorized G2 metric definitions. Missing values are NaN internally, JSON null externally."""
    p=problem;n=trials;groups=p.groups
    weights=np.array([len(g.customer_ids) for g in groups],dtype='<i8')
    population=int(weights.sum());h=p.horizon_ticks
    releases=np.stack([np.full(n,-1,dtype='<i8') if g.unresolved_dependency or any(t not in ends for t in g.required_tasks)
                        else np.maximum.reduce([ends[t] for t in g.required_tasks]) if g.required_tasks
                        else np.zeros(n,dtype='<i8') for g in groups],axis=1)
    makespan=np.maximum.reduce(list(ends.values()))/3600 if len(ends)==len(p.tasks) else np.full(n,np.nan)
    return metrics_from_releases(p,releases,makespan)


def metrics_from_releases(p,releases,makespan):
    n=len(releases);groups=p.groups
    weights=np.array([len(g.customer_ids) for g in groups],dtype='<i8')
    population=int(weights.sum());h=p.horizon_ticks
    known=releases>=0; unresolved=(~known)@weights; censored=(releases>h)@weights
    full=not np.any(unresolved)
    null=np.full(n,np.nan)
    out={'restricted_horizon_customer_hours':np.minimum(np.where(known,releases,h),h)@weights/3600,
         'modeled_customer_outage_hours':releases@weights/3600 if full else null.copy(),
         'unresolved_customers':unresolved,'censored_customers':censored,
         'unreleased_customers_at_horizon':unresolved+censored,
         'makespan_hours':makespan,
         'full_customer_release_hours':releases.max(axis=1)/3600 if full else null.copy()}
    sort=np.argsort(np.where(known,releases,np.iinfo(np.int64).max),axis=1,kind='stable')
    ordered=np.take_along_axis(releases,sort,axis=1);cumulative=np.cumsum(weights[sort],axis=1)
    for name,q in [('release_50_hours',.5),('release_90_hours',.9),('release_100_hours',1),('weighted_p95_hours',.95)]:
        idx=(cumulative>=int(np.ceil(q*population))).argmax(axis=1)
        selected=ordered[np.arange(n),idx];out[name]=np.where(selected>=0,selected/3600,np.nan)
    out['weighted_median_hours']=out['release_50_hours'].copy() if full else null.copy()
    if not full:out['weighted_p95_hours']=null.copy()
    out['maximum_wait_hours']=out['full_customer_release_hours'].copy()
    branches=[]
    for b in sorted({g.branch for g in groups}):
        mask=np.array([g.branch==b for g in groups])
        value=releases[:,mask]@weights[mask]/(3600*weights[mask].sum()) if np.all(known[:,mask]) else null.copy()
        out['branch:'+b]=value;branches.append(value)
    out['branch_mean_disparity_hours']=np.max(branches,axis=0)-np.min(branches,axis=0)
    small=np.array([len(g.customer_ids)<=5 for g in groups])
    out['small_group_mean_wait_hours']=releases[:,small]@weights[small]/(3600*weights[small].sum()) if small.any() and np.all(known[:,small]) else null.copy()
    for i,g in enumerate(groups):
        if g.critical_service:out['critical:'+g.id]=np.where(known[:,i],releases[:,i]/3600,np.nan)
    # Per-group release arrays are lossless milestone statistics: each disjoint group releases once.
    out['group_release_ticks']=releases
    return out


def simulate(value):
    if np.__version__!='2.5.4':raise RuntimeError('Use pinned NumPy 2.5.4')
    request=SimulationInput.model_validate(value.model_dump() if isinstance(value,SimulationInput) else value)
    if any(a.end_tick>2**40 for a in request.schedule.assignments) or any(c.available_tick>2**40 for c in request.problem.crews):
        raise ValueError('Schedule outside numerical range')
    population=sum(len(g.customer_ids) for g in request.problem.groups)
    origin=max([c.available_tick for c in request.problem.crews]+[a.start_tick for a in request.schedule.assignments])
    # Reserve half the exact float64 integer range for start/hold offsets. The
    # replay duration bound reserves the other half for at most 100 task lengths.
    # Individual start and duration bounds alone do not bound customer weighting.
    if max(origin+14400,request.problem.horizon_ticks)*population>2**52-1:
        raise ValueError('Customer-weighted schedule outside numerical range')
    durations,hold=draws(request)
    starts,ends=replay(request,durations,hold)
    arrays=metrics(request.problem,ends,request.trials)
    meta=SimulationMetadata(numerical_version=VERSION,
        input_fingerprint=hashlib.sha256(canonical(request.model_dump(mode='json'))).hexdigest(),
        schedule_fingerprint=hashlib.sha256(canonical(request.schedule.model_dump(mode='json'))).hexdigest(),
        problem_fingerprint=request.problem.fingerprint,profile_sha256=PROFILE_HASH,profile=request.profile,
        policy=request.schedule.policy,trials=request.trials,seed=request.seed,rng=RNG,
        duration_assumption=request.problem.duration_assumption,
        environment={'python':platform.python_version(),'numpy':np.__version__,'machine':platform.machine(),'system':platform.system()},
        array_units={k:'ticks; -1 means unresolved' if k=='group_release_ticks' else 'customers' if 'customers' in k else 'customer-hours' if 'customer_hours' in k or 'outage_hours' in k else 'hours' for k in arrays},
        numerical_sha256=digest(arrays))
    return meta.model_dump(mode='json'),arrays,starts,ends
