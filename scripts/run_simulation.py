"""Run complete offline simulation suites. No source data, API or provider calls."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.simulation_experiment import run
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--suite',choices=['smoke','standard','convergence'],default='smoke')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=run(args.output,args.suite)
    failures=sum(r['status']!='ok' for r in result['records'])
    print(len(result['records']),'runs;',failures,'failed');sys.exit(bool(failures))
