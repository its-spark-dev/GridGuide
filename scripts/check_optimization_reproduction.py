"""Repeat a published optimization run in a source-free, network-denied extraction.

Only repeat the same reviewed model/settings for reproducibility, never tuning.
The supplied reference artifact and all original outputs remain untouched.
"""
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
    if expected['suite']!='published' or expected['settings']['mode']!='offline':
        raise ValueError('This verifier requires the fixed published/offline configuration')
    with TemporaryDirectory(prefix='gridguide-optimization-reproduction-') as folder:
        temp=Path(folder); isolated=temp/'source';isolated.mkdir()
        shutil.copytree(ROOT/'benchmarks',isolated/'benchmarks',ignore=shutil.ignore_patterns('__pycache__'))
        for path in ('backend','scripts','docs/research/phase3','docs/benchmarks/phase2/standard'):
            (isolated/path).mkdir(parents=True,exist_ok=True)
        files=['backend/'+name for name in ('__init__.py','contracts.py','risk_rules.py','optimization.py')]
        files+=['scripts/run_optimization.py','scripts/report_optimization.py','requirements-optimization.txt',
                'docs/research/phase3/EVALUATION_PROTOCOL.md']
        files+=['docs/benchmarks/phase2/standard/'+name for name in ('manifest.json','results.jsonl.gz')]
        for name in files: shutil.copyfile(ROOT/name,isolated/name)
        code='''
import sys
sys.path.insert(0,sys.argv[1])
def audit(event,args):
    if event=='socket.connect': raise AssertionError('External network forbidden')
    if event=='open' and isinstance(args[0],str) and ('/data/raw/' in args[0] or '/data/processed/' in args[0]):
        raise AssertionError('Challenge data forbidden')
sys.addaudithook(audit)
from benchmarks.optimization_experiment import run
rows=run(sys.argv[2],'published')
assert len(rows)==278 and all(r['status']=='ok' for r in rows)
assert 'backend.config' not in sys.modules and 'backend.planning' not in sys.modules
'''
        result=subprocess.run([sys.executable,'-I','-c',code,str(isolated),str(temp/'results')],
                              cwd=isolated,capture_output=True,text=True,timeout=600)
        if result.returncode: raise RuntimeError('Isolated benchmark verification failed: '+result.stderr)
        actual=json.loads((temp/'results/manifest.json').read_text())
        if actual['results_sha256']!=expected['results_sha256']:
            raise ValueError('Numerical result hash does not reproduce')
        return {'status':'passed','cases':278,'results_sha256':actual['results_sha256'],
                'scope':'full published matrix and microcases; no challenge files or external network',
                'purpose':'identical numerical reproduction, no tuning',
                'forbidden_imports_absent':['backend.config','backend.planning']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError('Refusing to overwrite verification record')
    result=check(args.reference)
    with args.output.open('x') as out: json.dump(result,out,indent=2,sort_keys=True);out.write('\n')
    print('Source-free numerical reproduction passed')
