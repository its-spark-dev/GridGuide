"""Deterministically audit pinned cached responses; no network or model fitting."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.risk.audit import audit
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=audit(args.cache)
    with args.output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
