"""Run the offline benchmark; existing output directories cannot be overwritten."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.runner import run

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=('standard','smoke','micro'),default='standard')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=run(args.output,args.suite)
    failed=sum(r['status']!='ok' for r in rows)
    print(f'{len(rows)} policy runs; {failed} failures/invalid; output: {args.output}')
    sys.exit(bool(failed))
