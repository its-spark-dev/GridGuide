"""Paired reporting from stored artifacts. No solver calls or model fitting."""
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from benchmarks.policies import POLICIES

FIELDS=('modeled_customer_outage_hours','restricted_horizon_customer_hours')


def pct(b,o):
    return 100*(b-o)/b if b else (0.0 if o==0 else None)


def describe(pairs):
    percentages=[pct(b,o) for b,o in pairs]
    finite=[v for v in percentages if v is not None]
    return {'pairs':len(pairs),'undefined_percentages':len(pairs)-len(finite),
            'mean_percent':statistics.mean(finite) if finite else None,
            'median_percent':statistics.median(finite) if finite else None,
            'micro_percent':pct(sum(b for b,_ in pairs),sum(o for _,o in pairs)) if pairs else None,
            'baseline_mean_hours':statistics.mean(b for b,_ in pairs) if pairs else None,
            'optimizer_mean_hours':statistics.mean(o for _,o in pairs) if pairs else None,
            'mean_absolute_improvement_hours':statistics.mean(b-o for b,o in pairs) if pairs else None,
            'wins':sum(o<b for b,o in pairs),'ties':sum(o==b for b,o in pairs),'regressions':sum(o>b for b,o in pairs),
            'worst_percent':min(finite) if finite else None}


def clustered_interval(cells,replicates=5000):
    families=sorted({f for f,s in cells});seeds=sorted({s for f,s in cells})
    if not families or not seeds or any((f,s) not in cells for f in families for s in seeds): return None
    # Both crossed effects are resampled; scale/crew variants stay together.
    rng=random.Random(20261103); means=[];medians=[]
    for _ in range(replicates):
        fs=rng.choices(families,k=len(families));ss=rng.choices(seeds,k=len(seeds))
        values=[v for f in fs for s in ss for v in cells[f,s]]
        means.append(statistics.mean(values));medians.append(statistics.median(values))
    def interval(values):
        values=sorted(values)
        return [values[math.ceil(.025*len(values))-1],values[math.ceil(.975*len(values))-1]]
    return {'mean_95':interval(means),'median_95':interval(medians),'families':len(families),'seeds':len(seeds),
            'resamples':replicates,'method':'crossed-family-seed-pigeonhole; all scale/crew variants retained'}


def summarize(rows,fixed,field,comparator):
    pairs=[];cells={};families={};breakdown={};worst=[]
    for r in rows:
        if r['status']!='ok': continue
        o=r['result']['metrics'][field]
        if comparator=='best-of-four':
            costs=[m[field] for m in r['baselines'].values() if m[field] is not None]
            b=min(costs) if costs else None
        else: b=r['baselines'][fixed if comparator=='fixed' else comparator][field]
        if b is None or o is None: continue
        pairs.append((b,o));value=pct(b,o)
        if value is not None: cells.setdefault((r['family'],r['seed']),[]).append(value)
        families.setdefault(r['family'],[]).append((b,o))
        for dimension,key in [('family',r['family']),('tasks',r['task_count']),('crews',r['crew_count'])]:
            breakdown.setdefault(f'{dimension}:{key}',[]).append((b,o))
        worst.append({'case_id':r['case_id'],'percent':value,'absolute_hours':b-o})
    summary=describe(pairs)
    summary['excluded_unavailable_or_failed_cases']=len(rows)-len(pairs)
    summary['macro_family_mean_percent']=statistics.mean(describe(ps)['mean_percent'] for ps in families.values()) if families else None
    summary['cluster_interval']=clustered_interval(cells)
    summary['breakdowns']={key:describe(ps) for key,ps in sorted(breakdown.items())}
    summary['worst_cases']=sorted(worst,key=lambda r:(r['percent'] if r['percent'] is not None else -math.inf,r['case_id']))[:10]
    return summary


def render(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    payload=gzip.decompress((directory/'results.jsonl.gz').read_bytes())
    if hashlib.sha256(payload).hexdigest()!=manifest['results_sha256']: raise ValueError('Result hash mismatch')
    rows=[json.loads(line) for line in payload.splitlines()]
    if len(rows)!=len(manifest['cases']) or {r['case_id'] for r in rows}!=manifest['cases'].keys():
        raise ValueError('Missing/duplicate cases')
    if any(r['input_fingerprint']!=manifest['cases'][r['case_id']] for r in rows): raise ValueError('Input binding mismatch')
    compared=[r for r in rows if r['split']!='micro']
    policies=list(POLICIES)
    summaries={field:{c:summarize(compared,manifest['fixed_comparator'],field,c) for c in ['fixed','best-of-four',*policies]} for field in FIELDS}
    failures=[{'case_id':r['case_id'],'status':r['status'],'error_type':r.get('error_type')} for r in rows if r['status']!='ok']
    status=Counter();fallbacks=Counter();gaps=[];tradeoffs=[]
    for r in rows:
        if r['status']!='ok': continue
        result=r['result'];solver=result['solver']
        status[solver['primary']['status'] if solver else 'NOT_RUN']+=1
        if result['fallback_reason']: fallbacks[result['fallback_reason']]+=1
        if solver and solver['primary']['objective_ticks'] is not None:
            value=solver['primary']['objective_ticks'];bound=solver['primary']['best_bound']
            gaps.append({'case_id':r['case_id'],'objective_ticks':value,'bound':bound,'relative_gap':(value-bound)/max(1,abs(value))})
        base=r['baselines'][manifest['fixed_comparator']];out=result['metrics']
        def delta(key):
            return None if base[key] is None or out[key] is None else out[key]-base[key]
        tradeoffs.append({'case_id':r['case_id'],'makespan_delta_hours':delta('makespan_hours'),
            'branch_disparity_delta_hours':delta('branch_mean_disparity_hours'),
            'small_group_wait_delta_hours':delta('small_group_mean_wait_hours'),
            'critical_latency_delta_hours':{g:None if v is None or base['critical_service_latency_hours'][g] is None else
                 v-base['critical_service_latency_hours'][g] for g,v in out['critical_service_latency_hours'].items()}})
    primary=summaries[FIELDS[0]]['fixed'];ci=primary['cluster_interval']
    promotion=bool(manifest['suite']=='published' and not failures and primary['pairs']==225 and
                   primary['median_percent']>=5 and ci and ci['median_95'][0]>0)
    report={'version':'optimization-report-v1','summaries':summaries,'failures':failures,'solver_statuses':dict(status),
            'fallback_reasons':dict(fallbacks),'solver_gaps':gaps,'tradeoffs':tradeoffs,
            'promotion_target_met_on_published_suite':promotion,
            'oracle_checks':[{'case_id':r['case_id'],**r['oracle'],'gap_ticks':r['oracle_gap_ticks']} for r in rows if 'oracle' in r and r['split']=='micro'],
            'raw_candidate_rejections':[{'case_id':r['case_id'],'reason':r['result']['fallback_reason'],
                 'candidate_ticks':r['result']['candidate_objective_ticks']} for r in rows if r.get('result',{}).get('fallback_reason')]}
    (directory/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=['# Phase 3 optimization comparison','',f"Fixed comparator: `{manifest['fixed_comparator']}`.",
        f"Cases: {len(rows)}; failed/invalid: {len(failures)}. Previously inspected synthetic benchmark; no blind-holdout claim.",
        f"Promotion target on published suite met: **{promotion}**.",'',
        '| Metric | Comparator | Finite pairs | Median improvement % | Mean improvement % | Clustered 95% median interval | Wins / ties / regressions |',
        '|---|---|---:|---:|---:|---|---|']
    for field,comparators in summaries.items():
        for name,s in comparators.items():
            lines.append(f"| {field} | {name} | {s['pairs']} | {s['median_percent']} | {s['mean_percent']} | {s['cluster_interval'] and s['cluster_interval']['median_95']} | {s['wins']} / {s['ties']} / {s['regressions']} |")
    lines+=['','## Breakdowns versus fixed comparator','','| Metric / subset | Pairs | Mean % | Median % | Wins / ties / regressions |','|---|---:|---:|---:|---|']
    for field in FIELDS:
        for key,s in summaries[field]['fixed']['breakdowns'].items():
            lines.append(f"| {field} / {key} | {s['pairs']} | {s['mean_percent']} | {s['median_percent']} | {s['wins']} / {s['ties']} / {s['regressions']} |")
    lines+=['','## Status and interpretation','',f'Solver statuses: {dict(status)}',f'Fallbacks: {dict(fallbacks)}',
        '','Full per-case metrics, releases, critical/fairness tradeoffs, raw statuses, bounds, failures and rejected candidates are retained in results.jsonl.gz and report.json.',
        'Intervals resample family and seed clusters, retaining all scale/crew variants. Only five seeds and five finite families: no population-valid confidence claim.',
        'Restricted costs retain unknown customers at the horizon without assigning finite restoration. Completed costs exclude unavailable full outcomes with their counts disclosed.',
        'Missing/failed cases prohibit promotion; all nulls, ties, negative results and budget-stopped searches remain visible. Runtime observations are separate.']
    (directory/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return report
