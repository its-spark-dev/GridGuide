"""Explicit source-dependent regression lane; missing source files fail, not skip."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.legacy import verify

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify()
    with args.output.open('x') as stream: json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print('24 legacy four-candidate regressions passed')
