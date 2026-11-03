"""Execute preregistered optimization comparisons; rendering is separate."""
from dataclasses import asdict
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from backend.optimization import SolverSettings, optimize, validated_baselines, objective_ticks
from benchmarks.contracts import canonical, Schedule
from benchmarks.metrics import calculate
from benchmarks.oracle import exhaustive
from benchmarks.policies import POLICIES
from benchmarks.scenarios import FAMILIES, DEVELOPMENT_SEEDS, FROZEN_SHA256, generate, load_evaluation, microcases
from benchmarks.validation import validate

ROOT=Path(__file__).resolve().parents[1]


def select_comparator():
    directory=ROOT/'docs/benchmarks/phase2/standard'
    manifest=json.loads((directory/'manifest.json').read_text())
    payload=gzip.decompress((directory/'results.jsonl.gz').read_bytes())
    if hashlib.sha256(payload).hexdigest()!=manifest['results_uncompressed_sha256']:
        raise ValueError('Published G2 results changed')
    rows=[json.loads(line) for line in payload.splitlines()]
    ids={p.id for p in load_evaluation()}
    evaluation=[r for r in rows if r['split']=='evaluation']
    if len(evaluation)!=len(ids)*4 or {(r['case_id'],r['policy']) for r in evaluation}!={(i,p) for i in ids for p in POLICIES}:
        raise ValueError('Incomplete published baseline results')
    finite={r['case_id'] for r in evaluation if r['metrics']['modeled_customer_outage_hours'] is not None}
    values={policy:[] for policy in POLICIES}
    for r in evaluation:
        if r['status']!='ok' or r['violations']:
            raise ValueError('Invalid published baseline result')
        if r['case_id'] in finite:
            v=r['metrics']['modeled_customer_outage_hours']
            if v is None: raise ValueError('Non-common finite scope')
            values[r['policy']].append(v)
    scores={p:sum(v)/len(v) for p,v in values.items()}
    return min(scores,key=lambda p:(scores[p],p)),scores


def split_timing(result):
    result=dict(result)
    timing={'end_to_end_seconds':result.pop('end_to_end_seconds')}
    if result['solver'] is not None:
        result['solver']=dict(result['solver'])
        for phase in ('primary','secondary'):
            if result['solver'][phase] is not None:
                result['solver'][phase]=dict(result['solver'][phase])
                timing[phase+'_wall_seconds']=result['solver'][phase].pop('wall_seconds')
    return result,timing


def run(output,suite='development',mode='offline'):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    fixed,scores=select_comparator()
    if suite=='published':
        problems=load_evaluation()
    elif suite=='development':
        problems=[generate(f,n,c,seed,split='development') for f in FAMILIES for n in (10,25)
                  for c in (1,2,4) for seed in DEVELOPMENT_SEEDS]
    elif suite=='micro': problems=[]
    else: raise ValueError('Unknown suite')
    problems+=microcases()
    settings=SolverSettings(mode=mode)
    records,timings=[],[]
    for p in problems:
        row={'case_id':p.id,'family':p.family,'task_count':len(p.tasks),'crew_count':len(p.crews),
             'seed':p.seed,'split':p.split,'input_fingerprint':p.fingerprint}
        try:
            baselines=validated_baselines(p)
            result=optimize(p,settings)
            result,timing=split_timing(result)
            timings.append({'case_id':p.id,**timing})
            row.update(status='ok',result=result,baselines={s.policy:m for s,m in baselines})
            oracle=exhaustive(p)
            row['oracle']={k:v for k,v in oracle.items() if k!='schedule'}
            row['oracle_gap_ticks']=None
            if oracle['status']=='optimal':
                assert not validate(p,oracle['schedule'],calculate(p,oracle['schedule']))
                row['oracle_gap_ticks']=result['objective_ticks']-oracle['objective_ticks']
                if row['oracle_gap_ticks']!=0: row['status']='oracle_mismatch'
            if result['violations']: row['status']='invalid'
        except Exception as error:
            row.update(status='failed',error_type=type(error).__name__)
        records.append(row)
    payload=b'\n'.join(canonical(r) for r in records)+b'\n'
    (output/'results.jsonl.gz').write_bytes(gzip.compress(payload,mtime=0))
    (output/'timings.json').write_text(json.dumps(timings,indent=2,sort_keys=True)+'\n')
    source_files=['backend/optimization.py','benchmarks/optimization_experiment.py','benchmarks/optimization_reporting.py',
                  'scripts/run_optimization.py','scripts/report_optimization.py','requirements-optimization.txt',
                  'docs/research/phase3/EVALUATION_PROTOCOL.md']
    source_files += ['benchmarks/'+f+'.py' for f in ('contracts','policies','metrics','validation','oracle','scenarios')]
    manifest={'version':'optimization-experiment-v1','suite':suite,'settings':asdict(settings),
              'fixed_comparator':fixed,'comparator_selection_scores':scores,'cases':{p.id:p.fingerprint for p in problems},
              'frozen_phase2_manifest_sha256':FROZEN_SHA256,'results_sha256':hashlib.sha256(payload).hexdigest(),
              'software':{name:importlib.metadata.version(name) for name in ('ortools','pydantic','numpy','pandas','protobuf')},
              'python':platform.python_version(),'host':{'system':platform.system(),'machine':platform.machine()},
              'implementation_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files},
              'untouched_final_holdout':False,'protocol':'docs/research/phase3/EVALUATION_PROTOCOL.md'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return records
