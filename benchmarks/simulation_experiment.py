"""Fixed policies loaded before sampling. Complete bounded suites; no optimization."""
import gzip
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np
from benchmarks.contracts import Schedule,canonical
from benchmarks.scenarios import load_evaluation,microcases
from benchmarks.policies import POLICIES,schedule
from benchmarks.metrics import calculate
from backend.simulation import simulate,PROFILES,PROFILE_HASH,VERSION
from backend.simulation_contracts import SimulationInput

ROOT=Path(__file__).resolve().parents[1]
LABELS=('fixed','cpsat','fifo','customer-count','best-of-four')


def frozen_schedules():
    folder=ROOT/'docs/benchmarks/phase3/published'
    manifest=json.loads((folder/'manifest.json').read_text())
    raw=gzip.decompress((folder/'results.jsonl.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest()!=manifest['results_sha256']:raise ValueError('G3 result hash mismatch')
    return {r['case_id']:r for r in map(json.loads,raw.splitlines())},manifest['results_sha256']


def policies(p, frozen):
    r=frozen[p.id]
    if r['input_fingerprint']!=p.fingerprint or r['status']!='ok':raise ValueError('Frozen result binding mismatch')
    return {'fixed':schedule(p,POLICIES[2]),'cpsat':Schedule.model_validate(r['result']['schedule']),
            'fifo':schedule(p,POLICIES[0]),'customer-count':schedule(p,POLICIES[1]),
            'best-of-four':schedule(p,r['result']['baseline_policy'])}


def run(output,suite):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    frozen,g3hash=frozen_schedules()
    cases=load_evaluation()+microcases() if suite=='standard' else microcases()
    if suite=='convergence':cases=[p for p in cases if all(t.access=='clear' and t.total_person_hours is not None for t in p.tasks) and not any(g.unresolved_dependency for g in p.groups)]
    trials={'smoke':32,'standard':2000,'convergence':10000}[suite]
    records=[];timings=[];begun=time.perf_counter()
    sources=['backend/simulation.py','backend/simulation_contracts.py','research/uncertainty.py',
             'benchmarks/simulation_experiment.py','benchmarks/simulation_reporting.py',
             'benchmarks/simulation_profiles.json','docs/research/phase5/SIMULATION_PROTOCOL.md',
             'requirements-simulation.txt']
    inputs={}
    for p in cases:
        plans=policies(p,frozen);inputs[p.id]={'problem':p.model_dump(mode='json'),
                                             'schedules':{k:s.model_dump(mode='json') for k,s in plans.items()}}
        for profile in PROFILES:
            # Avoid storing identical policy realizations more than once.
            stored={}
            for label in LABELS:
                start=time.perf_counter();row={'case':p.id,'profile':profile,'policy':label,'trials':trials}
                try:
                    request=SimulationInput(problem=p,schedule=plans[label],profile=profile,trials=trials)
                    meta,arrays,starts,ends=simulate(request)
                    if profile=='deterministic-v1':
                        expected=calculate(p,plans[label])
                        for a in plans[label].assignments:
                            if not np.all(starts[a.task_id]==a.start_tick) or not np.all(ends[a.task_id]==a.end_tick):
                                raise ValueError('Deterministic schedule mismatch')
                        for k,v in arrays.items():
                            if k=='group_release_ticks':
                                wanted=np.array([-1 if expected['release_ticks'][g.id] is None else expected['release_ticks'][g.id] for g in p.groups])
                            elif k.startswith('branch:'):wanted=expected['branch_mean_wait_hours'][k[7:]]
                            elif k.startswith('critical:'):wanted=expected['critical_service_latency_hours'][k[9:]]
                            else:wanted=expected[k]
                            if wanted is None:
                                if not np.all(np.isnan(v)):raise ValueError('Deterministic null mismatch')
                            elif not np.all(v==wanted):raise ValueError('Deterministic metric mismatch: '+k)
                    key=meta['numerical_sha256']
                    if key in stored:filename=stored[key]
                    else:
                        filename=f'{p.id}--{profile}--{label}.npz'
                        # Lossless sufficient statistics for all G2 customer metrics/milestones.
                        np.savez_compressed(output/filename,group_release_ticks=arrays['group_release_ticks'],makespan_hours=arrays['makespan_hours'])
                        stored[key]=filename
                    row.update(status='ok',file=filename,metadata=meta)
                except Exception as error:
                    row.update(status='failed',error_type=type(error).__name__,error=str(error))
                records.append(row);timings.append({'case':p.id,'profile':profile,'policy':label,'seconds':time.perf_counter()-start})
        print(p.id,flush=True)
    manifest={'version':'simulation-run-v1','suite':suite,'trials_per_run':trials,'profiles':list(PROFILES),
              'policies':list(LABELS),'seed':20261103,'inputs':inputs,'records':records,
              'profile_sha256':PROFILE_HASH,'g3_results_sha256':g3hash,
              'implementation_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources}}
    manifest['numerical_sha256']=hashlib.sha256(canonical(records)).hexdigest()
    (output/'manifest.json').write_bytes(canonical(manifest)+b'\n')
    # macOS ru_maxrss bytes; Linux KiB. Includes interpreter/numpy, process high-water mark.
    import platform
    memory=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024)
    (output/'timing.json').write_bytes(canonical({'total_seconds':time.perf_counter()-begun,'peak_process_rss_bytes':memory,
                                                'measurement':'ru_maxrss process high-water mark, one worker','runs':timings})+b'\n')
    return manifest
