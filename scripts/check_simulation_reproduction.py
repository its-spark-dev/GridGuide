"""Repeat a complete simulation suite in an extracted source-free/network-denied tree."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]


def check(reference):
    expected=json.loads((reference/'manifest.json').read_text())
    with TemporaryDirectory(prefix='gridguide-simulation-replay-') as folder:
        temp=Path(folder);src=temp/'source';src.mkdir()
        shutil.copytree(ROOT/'benchmarks',src/'benchmarks',ignore=shutil.ignore_patterns('__pycache__'))
        files=['backend/'+p for p in ('__init__.py','contracts.py','risk_rules.py','simulation.py','simulation_contracts.py')]
        files+=['research/__init__.py','research/uncertainty.py','requirements-simulation.txt',
                'docs/research/phase5/SIMULATION_PROTOCOL.md']
        files+=['docs/benchmarks/phase3/published/'+p for p in ('manifest.json','results.jsonl.gz')]
        for name in files:
            dest=src/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        code='''
import sys
sys.path.insert(0,sys.argv[1])
def guard(event,args):
    if event=='socket.connect':raise AssertionError('Network forbidden')
    if event=='open' and isinstance(args[0],str) and any(p in args[0] for p in ('/data/raw/','/data/processed/','/data/external/')):raise AssertionError('Source data forbidden')
sys.addaudithook(guard)
from benchmarks.simulation_experiment import run
m=run(sys.argv[2],sys.argv[3])
assert all(r['status']=='ok' for r in m['records'])
assert not {'backend.config','backend.planning','backend.optimization'} & sys.modules.keys()
'''
        out=temp/'results'
        result=subprocess.run([sys.executable,'-I','-c',code,str(src),str(out),expected['suite']],cwd=src,
                              stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        if result.returncode:raise RuntimeError(result.stderr)
        actual=json.loads((out/'manifest.json').read_text())
        if actual['numerical_sha256']!=expected['numerical_sha256']:raise ValueError('Numerical replay mismatch')
        return {'suite':expected['suite'],'runs':len(actual['records']),'trials_per_run':actual['trials_per_run'],
                'numerical_sha256':actual['numerical_sha256'],'status':'passed',
                'reference_implementation_sha256':expected['implementation_sha256'],
                'replay_implementation_sha256':actual['implementation_sha256'],
                'scope':'full suite, isolated extraction, no source data/network/optimizer imports'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Refusing overwrite')
    result=check(args.reference)
    with args.output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('Source-free simulation reproduction passed')
