"""Offline optimizer experiments; default development data, no silent overwrite."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.optimization_experiment import run

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--suite',choices=('development','published','micro'),default='development')
    p.add_argument('--mode',choices=('offline','interactive'),default='offline')
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();rows=run(args.output,args.suite,args.mode)
    failures=sum(r['status']!='ok' for r in rows)
    print(f'{len(rows)} cases; {failures} failed/invalid/oracle mismatches')
    sys.exit(bool(failures))
