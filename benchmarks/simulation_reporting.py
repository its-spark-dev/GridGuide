"""Read and verify retained lossless trial statistics; never run numerical sampling."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np
from benchmarks.contracts import BenchmarkProblem,canonical
from backend.simulation import metrics_from_releases,digest
from research.uncertainty import summarize,paired,convergence


def read_arrays(folder,row,problem):
    path=folder/row['file']
    if Path(row['file']).name!=row['file']:raise ValueError('Invalid artifact path')
    with np.load(path,allow_pickle=False) as z:
        release=z['group_release_ticks'];span=z['makespan_hours']
    if release.shape!=(row['trials'],len(problem.groups)) or span.shape!=(row['trials'],):raise ValueError('Shape mismatch')
    if release.dtype.kind!='i' or np.any(release < -1):raise ValueError('Invalid release ticks')
    arrays=metrics_from_releases(problem,release,span)
    if digest(arrays)!=row['metadata']['numerical_sha256']:raise ValueError('Trial hash mismatch')
    return arrays


def report(folder):
    folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text())
    records=manifest['records']
    if hashlib.sha256(canonical(records)).hexdigest()!=manifest['numerical_sha256']:raise ValueError('Manifest hash mismatch')
    expected={(case,profile,policy) for case in manifest['inputs'] for profile in manifest['profiles'] for policy in manifest['policies']}
    if len(records)!=len(expected) or {(r['case'],r['profile'],r['policy']) for r in records}!=expected:
        raise ValueError('Incomplete/duplicate run matrix')
    indexed={(r['case'],r['profile'],r['policy']):r for r in records}
    summaries=[];contrasts=[];checks=[];failures=[r for r in records if r['status']!='ok']
    for case,inputs in manifest['inputs'].items():
        p=BenchmarkProblem.model_validate(inputs['problem'])
        for profile in manifest['profiles']:
            arrays={}
            for policy in manifest['policies']:
                r=indexed[case,profile,policy]
                if r['status']!='ok':continue
                if r['metadata']['problem_fingerprint']!=p.fingerprint:raise ValueError('Problem binding mismatch')
                a=arrays[policy]=read_arrays(folder,r,p)
                row={'case':case,'profile':profile,'policy':policy,'family':p.family,'tasks':len(p.tasks),'crews':len(p.crews),
                     'metrics':{k:summarize(v) for k,v in a.items() if k!='group_release_ticks'}}
                summaries.append(row)
                if manifest['suite']=='convergence':checks.append({'case':case,'profile':profile,'policy':policy,**convergence(a['full_customer_release_hours'])})
            if 'fixed' not in arrays:continue
            for policy,a in arrays.items():
                if policy=='fixed':continue
                for ref in ('fixed','best-of-four') if policy=='cpsat' else ('fixed',):
                    if ref not in arrays:continue
                    contrasts.append({'case':case,'profile':profile,'policy':policy,'reference':ref,'family':p.family,
                        'metrics':{k:paired(a[k],arrays[ref][k]) for k in a if k!='group_release_ticks'}})
    aggregate=[]
    for profile in manifest['profiles']:
        for policy in manifest['policies']:
            rows=[r for r in summaries if r['profile']==profile and r['policy']==policy and (r['family']!='micro' or manifest['suite']!='standard')]
            for field in ('modeled_customer_outage_hours','restricted_horizon_customer_hours','full_customer_release_hours','branch_mean_disparity_hours'):
                vals=[r['metrics'][field]['mean'] for r in rows if r['metrics'][field]['mean'] is not None]
                aggregate.append({'profile':profile,'policy':policy,'metric':field,'finite_cases':len(vals),
                                  'unavailable_cases':len(rows)-len(vals),'mean_of_case_means':statistics.mean(vals) if vals else None})
    result={'version':'simulation-report-v1','suite':manifest['suite'],'numerical_sha256':manifest['numerical_sha256'],
            'runs':len(records),'trials_per_run':manifest['trials_per_run'],'failures':failures,
            'aggregate':aggregate,'summaries':summaries,'paired_comparisons':contrasts,'convergence':checks,
            'calibrated_to_observed_restoration':False,'default_policy_changed':False}
    (folder/'report.json').write_bytes(canonical(result)+b'\n')
    lines=['# Assumption-based restoration simulation','',f"Suite: {manifest['suite']}; {len(records)} runs × {manifest['trials_per_run']} trials; failures: {len(failures)}.",
           'Synthetic distributions only. No empirical restoration calibration or default-policy promotion.','',
           '| Profile | Policy | Metric | Finite cases | Unavailable cases | Mean of case means |','|---|---|---|---:|---:|---:|']
    for r in aggregate:
        lines.append(f"| {r['profile']} | {r['policy']} | {r['metric']} | {r['finite_cases']} | {r['unavailable_cases']} | {r['mean_of_case_means']} |")
    lines+=['','Completed and restricted customer-hours use different denominators; unresolved scope stays null for full outcomes.',
            'Paired candidate-minus-reference differences, every secondary metric and quantile are retained in report.json.',
            'Quantile batch standard errors describe Monte Carlo numerical variation, not real-world confidence.',
            f"Convergence: {sum(c['status']=='stable' for c in checks)} stable, {sum(c['status']=='unstable_at_cap' for c in checks)} unstable at 10000-trial cap."]
    (folder/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return result
