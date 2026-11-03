"""Presentation of existing result artifacts; never runs scheduling."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics


def report(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    payload=gzip.decompress((directory/'results.jsonl.gz').read_bytes())
    if hashlib.sha256(payload).hexdigest()!=manifest['results_uncompressed_sha256']:
        raise ValueError('Result content hash mismatch')
    rows=[json.loads(line) for line in payload.splitlines()]
    expected={(case,policy) for case in manifest['cases'] for policy in manifest['policies']}
    if len(rows)!=len(expected) or {(r['case_id'],r['policy']) for r in rows}!=expected:
        raise ValueError('Missing, duplicate or unexpected result rows')
    if any(r['input_fingerprint']!=manifest['cases'][r['case_id']] for r in rows):
        raise ValueError('Result input fingerprint mismatch')
    groups=defaultdict(list)
    for r in rows:
        groups[(r['split'],r['family'],r['task_count'],r['crew_count'],r['policy'])].append(r)
    aggregated=[]
    for (split,family,tasks,crews,policy),values in sorted(groups.items()):
        valid=[v for v in values if v['status']=='ok']
        full=[v['metrics']['modeled_customer_outage_hours'] for v in valid if v['metrics']['modeled_customer_outage_hours'] is not None]
        aggregated.append(dict(split=split,family=family,tasks=tasks,crews=crews,policy=policy,cases=len(values),
            failures=len(values)-len(valid),finite_full_cases=len(full),unavailable_full_cases=len(valid)-len(full),
            mean_completed_customer_hours=statistics.mean(full) if full else None,
            mean_restricted_customer_hours=statistics.mean(v['metrics']['restricted_horizon_customer_hours'] for v in valid) if valid else None,
            total_unresolved_customers=sum(v['metrics']['unresolved_customers'] for v in valid),
            total_censored_customers=sum(v['metrics']['censored_customers'] for v in valid)))
    (directory/'aggregates.json').write_text(json.dumps(aggregated,indent=2,sort_keys=True)+'\n')
    lines=['# Phase 2 baseline report','', 'Synthetic modeled waiting after response origin; no utility outcomes or optimizer gains.',
        '',f"{len(rows)} policy runs / {manifest['case_count']} cases. Failures/invalid: {sum(r['status']!='ok' for r in rows)}.",
        'All cases retained, including ties, blocked cases and unavailable full totals.',
        'Completed totals are averaged ONLY over finite cases, with their denominator shown. Restricted totals are a different metric.',
        'Runtime/resource observations are separate from reproducible numerical results.', '',
        '| Split / family | Tasks | Crews | Policy | Cases / finite / failures | Mean completed customer-hours | Mean restricted customer-hours |',
        '|---|---:|---:|---|---|---:|---:|']
    for r in aggregated:
        def fmt(v): return 'unavailable' if v is None else f'{v:.3f}'
        lines.append(f"| {r['split']} / {r['family']} | {r['tasks']} | {r['crews']} | {r['policy']} | {r['cases']} / {r['finite_full_cases']} / {r['failures']} | {fmt(r['mean_completed_customer_hours'])} | {fmt(r['mean_restricted_customer_hours'])} |")
    lines+=['','## Microcase oracle checks','','| Case | Policy | Oracle status | Nodes | Baseline gap (customer-hours) |','|---|---|---|---:|---:|']
    for r in rows:
        if r['split']=='micro':
            lines.append(f"| {r['case_id']} | {r['policy']} | {r['oracle']['status']} | {r['oracle']['nodes']} | {r.get('oracle_gap_customer_hours')} |")
    (directory/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return aggregated
