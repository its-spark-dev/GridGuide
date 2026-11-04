"""Reproduce the bounded fictional G2/G3 operator catalog without fitting or solving."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from benchmarks.scenarios import microcases
from backend.review import CATALOG_SHA


def prepare():
    source=ROOT/'docs/benchmarks/phase3/published'
    raw=(source/'results.jsonl.gz').read_bytes()
    manifest=json.loads((source/'manifest.json').read_text())
    if hashlib.sha256(gzip.decompress(raw)).hexdigest()!=manifest['results_sha256']:
        raise ValueError('Frozen G3 source mismatch')
    rows={r['case_id']:r for r in map(json.loads,gzip.decompress(raw).splitlines())}
    times={r['case_id']:r for r in json.loads((source/'timings.json').read_text())}
    cases=[]
    for problem in microcases():
        row=rows[problem.id]
        if row['status']!='ok' or row['input_fingerprint']!=problem.fingerprint:raise ValueError('Invalid reference case')
        r=row['result'];primary=r['solver']['primary'] if r['solver'] else None
        cases.append({'problem':problem.model_dump(mode='json'),'protected':{'schedule':r['schedule'],
            'returned_source':r['returned_source'],'baseline_policy':r['baseline_policy'],
            'fallback_reason':r['fallback_reason'],'primary_optimal':r['primary_optimal'],
            'solver_status':primary['status'] if primary else 'not_run',
            'best_bound_ticks':primary['best_bound'] if primary else None,
            'recorded_seconds':times[problem.id]['end_to_end_seconds']}})
    content=(json.dumps({'version':'operator-catalog-v1','source_artifact_sha256':hashlib.sha256(raw).hexdigest(),
                        'cases':cases},sort_keys=True,indent=2)+'\n').encode()
    if hashlib.sha256(content).hexdigest()!=CATALOG_SHA:raise ValueError('Operator catalog pin mismatch')
    return content

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with args.output.open('xb') as target:target.write(prepare())
