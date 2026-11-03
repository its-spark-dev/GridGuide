"""Offline execution. Deterministic results are separate from runtime observations."""
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import tracemalloc
from .contracts import canonical
from .metrics import calculate
from .oracle import exhaustive
from .policies import POLICIES, schedule
from .scenarios import FAMILIES, DEVELOPMENT_SEEDS, FROZEN_SHA256, generate, load_evaluation, microcases
from .validation import validate


def run(output, suite='standard'):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    problems = (load_evaluation() if suite=='standard' else
                [generate(f,10,2,DEVELOPMENT_SEEDS[0],split='development') for f in FAMILIES] if suite=='smoke' else [])
    problems += microcases()
    records, observations = [], []
    for p in problems:
        oracle=exhaustive(p) if len(p.tasks)<=8 else {'status':'unsupported','nodes':0,'objective_ticks':None,'schedule':None}
        if oracle['schedule'] is not None:
            violations=validate(p,oracle['schedule'],calculate(p,oracle['schedule']))
            if violations:
                raise RuntimeError('Oracle returned invalid schedule: '+','.join(violations))
        for policy in POLICIES:
            wall, cpu = time.perf_counter(), time.process_time()
            tracemalloc.start()
            try:
                s=schedule(p,policy)
                metrics=calculate(p,s)
                violations=validate(p,s,metrics)
                record={'case_id':p.id,'family':p.family,'task_count':len(p.tasks),'crew_count':len(p.crews),
                    'seed':p.seed,'split':p.split,'input_fingerprint':p.fingerprint,'policy':policy,
                    'status':'invalid' if violations else 'ok','violations':violations,
                    'schedule':s.model_dump(mode='json'),'metrics':metrics,
                    'oracle':{k:v for k,v in oracle.items() if k!='schedule'},'oracle_gap_customer_hours':None}
                if oracle['status']=='optimal' and metrics['modeled_customer_outage_hours'] is not None:
                    record['oracle_gap_customer_hours']=metrics['modeled_customer_outage_hours']-oracle['objective_ticks']/3600
                    if record['oracle_gap_customer_hours'] < -1e-9:
                        raise RuntimeError('Baseline beats exhaustive bound')
            except Exception as error:
                record={'case_id':p.id,'family':p.family,'task_count':len(p.tasks),'crew_count':len(p.crews),
                        'seed':p.seed,'split':p.split,'input_fingerprint':p.fingerprint,'policy':policy,
                        'status':'failed','error_type':type(error).__name__,'metrics':None,'oracle':{k:v for k,v in oracle.items() if k!='schedule'}}
            finally:
                _, peak=tracemalloc.get_traced_memory()
                tracemalloc.stop()
            records.append(record)
            observations.append({'case_id':p.id,'policy':policy,'wall_seconds':time.perf_counter()-wall,
                'cpu_seconds':time.process_time()-cpu,'peak_traced_python_bytes':peak})
    payload=b'\n'.join(canonical(r) for r in records)+b'\n'
    compressed=gzip.compress(payload,mtime=0)
    (output/'results.jsonl.gz').write_bytes(compressed)
    (output/'runtime_observations.json').write_text(json.dumps(observations,indent=2)+'\n')
    root=Path(__file__).resolve().parents[1]
    sources=[*sorted((root/'benchmarks').glob('*.py')),root/'scripts/run_benchmarks.py',root/'scripts/report_benchmarks.py']
    manifest={'version':'benchmark-run-v1','suite':suite,'evidence':'synthetic deterministic scheduling; no observed outages',
        'evaluation_manifest_sha256':FROZEN_SHA256,'case_count':len(problems),'policy_count':len(POLICIES),
        'cases':{p.id:p.fingerprint for p in problems},'policies':list(POLICIES),
        'results_uncompressed_sha256':hashlib.sha256(payload).hexdigest(),
        'software':{'python':platform.python_version(),'pydantic':importlib.metadata.version('pydantic')},
        'reference_host':{'system':platform.system(),'machine':platform.machine(),'processor':platform.processor()},
        'implementation_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'settings':{'workers':1,'ticks_per_hour':3600,'oracle_node_limit':250000,'oracle_max_tasks':8,
                    'wall_timeout':None,'duration':'one_effective_worker','timing_includes':'scheduler + metric computation + independent validation; tracemalloc active',
                    'memory_measurement':'peak traced Python allocations per policy; not RSS or native allocations',
                    'oracle_budget_exhaustion':'reported separately; no optimality claim',
                    'runtime_reproducibility':'not promised; deterministic result payload is separate'}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return records
