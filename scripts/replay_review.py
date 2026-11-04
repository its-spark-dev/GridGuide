"""Independently invoke schema, input, schedule, metric and review replay checks."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.review import replay


def unique(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError('Duplicate JSON key')
        out[key]=value
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact',type=Path)
    args=parser.parse_args()
    try:
        with args.artifact.open('rb') as source:raw=source.read(1000001)
        if len(raw)>1000000:raise ValueError('Too large')
        result=replay(json.loads(raw,object_pairs_hook=unique))
    except Exception:
        print('Replay rejected: invalid, unsupported or mismatched review artifact.',file=sys.stderr)
        return 1
    print('Replay verified: all baseline schedules/metrics and release milestones recomputed; optional frozen G3 schedule independently validated against its pinned reference.')
    print(result,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
