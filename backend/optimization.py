"""Versioned CP-SAT adapter over the frozen offline contract; no source loading.

The legacy planner and HTTP contracts are deliberately unchanged. OR-Tools is lazy
and optional. Every accepted candidate passes the independent G2 validator.
"""
from dataclasses import asdict, dataclass
import math
import time
from benchmarks.contracts import Assignment, BenchmarkProblem, Schedule, duration_ticks
from benchmarks.metrics import calculate
from benchmarks.policies import POLICIES, schedule
from benchmarks.validation import validate

VERSION = 'restoration-cpsat-v1'
SOLVER_VERSION = '9.14.6206'


@dataclass(frozen=True)
class SolverSettings:
    mode: str = 'offline'
    primary_deterministic_limit: float = .2
    secondary_deterministic_limit: float = .05
    seed: int = 20261103
    workers: int = 1

    def __post_init__(self):
        if self.mode not in ('offline','interactive') or self.workers != 1:
            raise ValueError('Unsupported execution configuration')
        if not all(math.isfinite(v) and v >= 0 for v in (self.primary_deterministic_limit,self.secondary_deterministic_limit)):
            raise ValueError('Invalid deterministic budget')


def objective_ticks(problem, metrics):
    """Exact integer primary, including unresolved mass for partial problems."""
    releases = metrics['release_ticks']
    complete = all(t is not None for t in releases.values())
    return sum(len(g.customer_ids) * (releases[g.id] if complete else
               min(problem.horizon_ticks, releases[g.id] if releases[g.id] is not None else problem.horizon_ticks))
               for g in problem.groups)


def validated_baselines(problem):
    outcomes = []
    for policy in POLICIES:
        s = schedule(problem,policy)
        m = calculate(problem,s)
        violations = validate(problem,s,m)
        if violations:
            raise ValueError('Baseline failed independent verification')
        outcomes.append((s,m))
    return outcomes


def _cp_solve(problem, incumbent, incumbent_metrics, settings):
    import ortools
    from ortools.sat.python import cp_model
    if ortools.__version__ != SOLVER_VERSION:
        raise RuntimeError('Unpinned solver version')
    tasks = {t.id:t for t in problem.tasks}
    eligible = sorted(a.task_id for a in incumbent.assignments)
    durations = {i:duration_ticks(problem,tasks[i]) for i in eligible}
    horizon = max(c.available_tick for c in problem.crews)+sum(durations.values())
    if max(horizon,problem.horizon_ticks) * sum(len(g.customer_ids) for g in problem.groups) >= 2**50:
        raise ValueError('Outside exact bounded solver range')
    model = cp_model.CpModel()
    starts, ends, chosen = {}, {}, {}
    intervals = {c.id:[] for c in problem.crews}
    for i in eligible:
        starts[i] = model.new_int_var(0,horizon,'start-'+i)
        ends[i] = model.new_int_var(0,horizon,'end-'+i)
        for c in sorted(problem.crews,key=lambda c:c.id):
            chosen[i,c.id] = model.new_bool_var('assign-'+i+'-'+c.id)
            intervals[c.id].append(model.new_optional_interval_var(starts[i],durations[i],ends[i],chosen[i,c.id],i+'-'+c.id))
            model.add(starts[i]>=c.available_tick).only_enforce_if(chosen[i,c.id])
        model.add_exactly_one(chosen[i,c.id] for c in problem.crews)
    for c in problem.crews:
        model.add_no_overlap(intervals[c.id])
    for i in eligible:
        for parent in tasks[i].prerequisites:
            model.add(starts[i]>=ends[parent])
    partial = any(v is None for v in incumbent_metrics['release_ticks'].values())
    terms = []
    for g in problem.groups:
        if g.unresolved_dependency or any(i not in ends for i in g.required_tasks):
            terms.append(len(g.customer_ids)*problem.horizon_ticks)
            continue
        release = model.new_int_var(0,horizon,'release-'+g.id)
        model.add_max_equality(release,[ends[i] for i in g.required_tasks] or [0])
        if partial:
            clipped=model.new_int_var(0,min(horizon,problem.horizon_ticks),'clipped-'+g.id)
            model.add_min_equality(clipped,[release,problem.horizon_ticks])
            release=clipped
        terms.append(len(g.customer_ids)*release)
    max_objective = max(horizon,problem.horizon_ticks)*sum(len(g.customer_ids) for g in problem.groups)
    primary = model.new_int_var(0,max_objective,'customer-ticks')
    model.add(primary==sum(terms))
    model.add(primary<=objective_ticks(problem,incumbent_metrics))
    makespan=model.new_int_var(0,horizon,'executable-makespan')
    model.add_max_equality(makespan,list(ends.values()) or [0])
    for a in incumbent.assignments:
        model.add_hint(starts[a.task_id],a.start_tick)
        model.add_hint(ends[a.task_id],a.end_tick)
        for c in problem.crews:
            model.add_hint(chosen[a.task_id,c.id],int(c.id==a.crew_id))
    model.minimize(primary)
    solve_start = time.monotonic()
    def solve(limit,wall_limit=None):
        solver=cp_model.CpSolver()
        solver.parameters.num_search_workers=settings.workers
        solver.parameters.random_seed=settings.seed
        solver.parameters.max_deterministic_time=limit
        if wall_limit is not None:
            solver.parameters.max_time_in_seconds=max(0,wall_limit)
        status=solver.solve(model)
        info={'status':solver.status_name(status),'best_bound':solver.best_objective_bound,
              'deterministic_time':solver.response_proto.deterministic_time,
              'wall_seconds':solver.wall_time,'branches':solver.num_branches,'conflicts':solver.num_conflicts}
        return solver,status,info
    solver,status,first=solve(settings.primary_deterministic_limit,1.5 if settings.mode=='interactive' else None)
    candidate=None
    def extract(solver):
        return Schedule(problem_fingerprint=problem.fingerprint,policy=VERSION,
            assignments=tuple(Assignment(task_id=i,crew_id=next(c.id for c in problem.crews if solver.value(chosen[i,c.id])),
                start_tick=solver.value(starts[i]),end_tick=solver.value(ends[i])) for i in eligible),
            unscheduled_tasks=incumbent.unscheduled_tasks)
    first['objective_ticks']=None
    second=None
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        candidate=extract(solver)
        first['objective_ticks']=solver.value(primary)
    if status==cp_model.OPTIMAL:
        model.add(primary==solver.value(primary))
        model.minimize(makespan)
        remaining=2-(time.monotonic()-solve_start) if settings.mode=='interactive' else None
        if remaining is None or remaining>0:
            other,secondary_status,second=solve(settings.secondary_deterministic_limit,remaining)
            if secondary_status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
                second['makespan_ticks']=other.value(makespan)
                # Retain the first solution if secondary search is worse than it.
                if second['makespan_ticks'] <= max((a.end_tick for a in candidate.assignments),default=0):
                    candidate=extract(other)
    return candidate,{'solver_version':ortools.__version__,'primary':first,'secondary':second}


def optimize(problem, settings=SolverSettings()):
    begun=time.perf_counter()
    # Reparse even model instances so unchecked model_copy updates cannot bypass validation.
    problem=BenchmarkProblem.model_validate(problem.model_dump() if isinstance(problem,BenchmarkProblem) else problem)
    baselines=validated_baselines(problem)
    def key(item):
        s,m=item
        return objective_ticks(problem,m),max((a.end_tick for a in s.assignments),default=0),s.policy
    incumbent,im= min(baselines,key=key)
    result={'version':VERSION,'input_fingerprint':problem.fingerprint,'settings':asdict(settings),
        'objective_scope':'completed_customer_ticks' if im['modeled_customer_outage_hours'] is not None else 'restricted_horizon_customer_ticks',
        'baseline_policy':incumbent.policy,'baseline_objective_ticks':objective_ticks(problem,im),
        'returned_source':'baseline','fallback_reason':None,'solver':None,'candidate_objective_ticks':None,
        'candidate_violations':[],'primary_optimal':False}
    accepted,metrics=incumbent,im
    if settings.mode=='interactive' and len(problem.tasks)>25:
        result['fallback_reason']='interactive_size_limit'
    elif not incumbent.assignments:
        result['fallback_reason']='no_executable_tasks'
    else:
        try:
            candidate,info=_cp_solve(problem,incumbent,im,settings)
            result['solver']=info
            if candidate is None:
                result['fallback_reason']='solver_'+info['primary']['status'].lower()
            else:
                violations=validate(problem,candidate)
                cm=calculate(problem,candidate) if not violations else None
                if cm is not None:
                    violations=validate(problem,candidate,cm)
                    result['candidate_objective_ticks']=objective_ticks(problem,cm)
                result['candidate_violations']=violations
                if violations:
                    result['fallback_reason']='invalid_candidate'
                elif info['primary']['status'] not in ('OPTIMAL','FEASIBLE'):
                    result['fallback_reason']='untrusted_solver_status'
                elif result['candidate_objective_ticks'] != info['primary']['objective_ticks']:
                    result['fallback_reason']='objective_mismatch'
                elif key((candidate,cm))[:2] > key((incumbent,im))[:2]:
                    result['fallback_reason']='candidate_worse_than_baseline'
                else:
                    accepted,metrics=candidate,cm
                    result['returned_source']='solver'
                    result['primary_optimal']=info['primary']['status']=='OPTIMAL'
        except ImportError:
            result['fallback_reason']='solver_dependency_unavailable'
        except Exception as error:
            result['fallback_reason']='solver_error:'+type(error).__name__
    violations=validate(problem,accepted,metrics)
    if violations:
        raise RuntimeError('No independently valid result available')
    result.update(schedule=accepted.model_dump(mode='json'),metrics=metrics,violations=violations,
                  objective_ticks=objective_ticks(problem,metrics),end_to_end_seconds=time.perf_counter()-begun)
    return result
