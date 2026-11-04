"""Fictional comparison/review authority; no source data, solver execution or identity."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from benchmarks.contracts import BenchmarkProblem, Schedule, canonical
from benchmarks.policies import POLICIES, schedule
from benchmarks.metrics import calculate
from benchmarks.validation import validate
from .optimization import objective_ticks
from .review_contracts import (CompareRequest, OperatorComparison, PolicyResult, ReviewCatalog, ReviewScenario,
    ReviewRequest, ReviewRecord, ReviewArtifact, ReviewExport)

CATALOG = Path(__file__).resolve().parents[1]/'data/operator/catalog.json'
CATALOG_SHA = '15a7c313cb2c91176abdb09232a7848b75ee08d515533808b62ead9c6e532f29'
FIXED = POLICIES[2]
EXPERIMENTAL = 'restoration-cpsat-v1'


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def inputs():
    raw = CATALOG.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CATALOG_SHA: raise ValueError('Unverified fictional catalog')
    return json.loads(raw)['cases']


def catalog() -> ReviewCatalog:
    return ReviewCatalog(catalog_fingerprint=CATALOG_SHA, scenarios=tuple(
        ReviewScenario(scenario_id=p.id, scenario_fingerprint=p.fingerprint, problem=p,
                       label='Fictional '+p.id.removeprefix('syn-micro-').replace('-',' '))
        for row in inputs() for p in [BenchmarkProblem.model_validate(row['problem'])]))


def problem_for(request: CompareRequest) -> tuple[BenchmarkProblem, dict]:
    row = next((r for r in inputs() if r['problem']['id']==request.scenario_id),None)
    if row is None: raise ValueError('Unknown fictional scenario')
    base = BenchmarkProblem.model_validate(row['problem'])
    if base.revision != request.scenario_revision or base.fingerprint != request.scenario_fingerprint:
        raise ValueError('Stale scenario binding')
    data = base.model_dump(mode='json')
    tasks={t['id']:t for t in data['tasks']}
    edges=set()
    for edge in request.precedence:
        pair=(edge.before,edge.after)
        if (pair in edges or edge.before not in tasks or edge.after not in tasks or
            edge.before==edge.after or edge.before in tasks[edge.after]['prerequisites']):
            raise ValueError('Invalid additional precedence')
        edges.add(pair)
        tasks[edge.after]['prerequisites'].append(edge.before)
    for t in data['tasks']:t['prerequisites'].sort()
    # Reparse catches cycles and undefined dependencies. Blocked clearance stays unknown.
    return BenchmarkProblem.model_validate(data), row


def tradeoffs(metrics, fixed):
    notes=[]
    for key in ('modeled_customer_outage_hours','restricted_horizon_customer_hours','makespan_hours',
                'weighted_p95_hours','branch_mean_disparity_hours','small_group_mean_wait_hours'):
        a,b=metrics[key],fixed[key]
        if a is None or b is None: notes.append(key+': unavailable comparison')
        else: notes.append(key+(': regression' if a>b else ': improvement' if a<b else ': tie')+' versus fixed baseline')
    for group,a in metrics['critical_service_latency_hours'].items():
        b=fixed['critical_service_latency_hours'][group]
        notes.append('Critical '+group+(': unavailable' if a is None or b is None else ': regression' if a>b else ': improvement' if a<b else ': tie'))
    return tuple(notes)


def compare(value: CompareRequest | dict) -> OperatorComparison:
    request=CompareRequest.model_validate(value.model_dump() if isinstance(value,CompareRequest) else value)
    problem,row=problem_for(request)
    plans=[(policy,schedule(problem,policy),None) for policy in POLICIES]
    state='not_requested'
    if request.include_experimental:
        state='unsupported_override' if request.precedence else 'supported_frozen'
        if not request.precedence:
            frozen=row['protected']
            plans.append((EXPERIMENTAL,Schedule.model_validate(frozen['schedule']),frozen))
    if request.selected_policy not in {p for p,_,_ in plans}:raise ValueError('Selected policy is unsupported')
    fixed=calculate(problem,plans[2][1])
    results=[]
    for policy,plan,frozen in plans:
        metrics=calculate(problem,plan)
        if validate(problem,plan,metrics):raise ValueError('Plan failed independent validation')
        extra={} if frozen is None else {k:v for k,v in frozen.items() if k!='schedule'}
        bound = extra.get('best_bound_ticks')
        objective = objective_ticks(problem, metrics)
        gap = None if bound is None else max(0, objective-bound)/max(1, abs(objective))
        results.append(PolicyResult(policy=policy,schedule=plan,metrics=metrics,
            origin='recomputed_baseline' if frozen is None else 'frozen_g3_protected_result',
            timing_scope='not_recorded' if frozen is None else 'historical_g3_wrapper',
            relative_gap=gap,
            tradeoffs=tradeoffs(metrics,fixed),
            explanation=('Recomputed under identical declared inputs. ' if frozen is None else 'Optional frozen G3 protected comparison; not a new solve. ')+
            'Customer release waits for all required repairs; unknown evidence remains unresolved. See case-level tradeoffs; no utility approval is implied.',
            **({'returned_source':'baseline','baseline_policy':policy} if frozen is None else extra)))
    best = min(results[:4], key=lambda r: (
        objective_ticks(problem, r.metrics.model_dump(mode='json')),
        max((a.end_tick for a in r.schedule.assignments), default=0), r.policy))
    result=OperatorComparison(catalog_fingerprint=CATALOG_SHA,request=request,problem=problem,results=tuple(results),
        best_of_four_policy=best.policy,
        experimental_status=state,result_fingerprint='0'*64,
        explanation='The fixed release-per-person-hour baseline remains the default after the failed G3 5% median promotion target. It prioritizes marginal modeled release per person-hour among ready work; it is not always best for critical latency or fairness. Completed customer-hours require finite full outcomes; restricted customer-hours score all customers through 168 hours, without assigning finite ETRs to unresolved work. No G5 quantiles or calibrated restoration confidence are supplied.')
    data=result.model_dump(mode='json');data.pop('result_fingerprint')
    return result.model_copy(update={'result_fingerprint':digest(data)})


def summary(artifact: ReviewArtifact) -> str:
    c,r=artifact.comparison,artifact.review
    chosen=next(p for p in c.results if p.policy==r.selected_policy)
    m=chosen.metrics
    return '\n'.join(['GridGuide — Reviewed in demo; fictional decision support',
        'Scenario: '+c.request.scenario_id+' / scenario revision '+str(c.request.scenario_revision)+
        ' / request revision '+str(c.request.revision),
        'Input: '+c.request.scenario_fingerprint, 'Catalog: '+c.catalog_fingerprint,
        'Versions: '+c.version+' / '+c.evidence.version+' / '+chosen.metrics.version,
        'Recommended: '+c.recommended_policy, 'Selected: '+r.selected_policy, 'Reason: '+r.reason,
        'Per-instance best-of-four reference: '+c.best_of_four_policy,
        'Reviewed at: '+r.timestamp, 'Result: '+r.result_fingerprint,
        'Completed modeled customer-hours: '+str(m.modeled_customer_outage_hours),
        'Restricted 168-hour customer-hours: '+str(m.restricted_horizon_customer_hours),
        'Unresolved customers: '+str(m.unresolved_customers)+'; censored: '+str(m.censored_customers),
        *chosen.tradeoffs, 'Null/None means unavailable, not zero. Conditional fiction, not utility confirmation.',
        'Checksums detect content changes; they do not authenticate reviewer identity or prevent malicious rewriting.',
        'Artifact SHA256: '+artifact.checksum])+'\n'


def export_review(value: ReviewRequest | dict) -> ReviewExport:
    req=ReviewRequest.model_validate(value.model_dump() if isinstance(value,ReviewRequest) else value)
    c=compare(req.request)
    if c.result_fingerprint!=req.result_fingerprint:raise ValueError('Stale review result')
    review=ReviewRecord(timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        reason=req.reason,acknowledgements=req.acknowledgements,selected_policy=req.request.selected_policy,
        result_fingerprint=c.result_fingerprint)
    a=ReviewArtifact(comparison=c,review=review,checksum='0'*64)
    data=a.model_dump(mode='json');data.pop('checksum')
    a=a.model_copy(update={'checksum':digest(data)})
    return ReviewExport(artifact=a,summary=summary(a))


def replay(value: dict) -> str:
    a=ReviewArtifact.model_validate(value)
    data=a.model_dump(mode='json');checksum=data.pop('checksum')
    if digest(data)!=checksum:raise ValueError('Artifact integrity mismatch')
    expected=compare(a.comparison.request)
    if expected.model_dump(mode='json')!=a.comparison.model_dump(mode='json'):
        raise ValueError('Recomputed comparison mismatch')
    if (a.review.result_fingerprint!=expected.result_fingerprint or
        a.review.selected_policy!=expected.request.selected_policy):raise ValueError('Review binding mismatch')
    return summary(a)
