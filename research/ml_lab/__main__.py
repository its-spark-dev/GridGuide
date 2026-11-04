"""Run from repository root; full final evaluation never silently overwrites evidence."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command',required=True)
    p = subs.add_parser('prepare')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',choices=['full','smoke'],default='full')
    for command in ('train','freeze','evaluate','audit'):
        p = subs.add_parser(command)
        p.add_argument('--dataset',type=Path,required=True)
        if command=='train':
            p.add_argument('--output',type=Path,required=True)
        else:
            p.add_argument('--training',type=Path,required=True)
            if command=='freeze':
                p.add_argument('--output',type=Path,required=True)
            else:
                p.add_argument('--freeze',type=Path,required=True)
                p.add_argument('--output' if command=='evaluate' else '--final',type=Path,required=True)
        if command!='audit':
            p.add_argument('--smoke',action='store_true')
        else:
            p.add_argument('--hash-only',action='store_true')
    p = subs.add_parser('report')
    p.add_argument('--training',type=Path,required=True)
    p.add_argument('--final',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p = subs.add_parser('smoke')
    p.add_argument('--output',type=Path,required=True)
    args = vars(parser.parse_args())
    command = args.pop('command')
    if command=='report':
        from .report import build_report
        result=build_report(**args)
    elif command=='smoke':
        from .workflow import prepare,train,freeze,evaluate,audit
        root=args['output']
        root.mkdir(parents=True,exist_ok=False)
        data,training,frozen,final=root/'dataset',root/'training',root/'freeze.json',root/'final'
        prepare(data,'smoke')
        train(data,training,smoke=True)
        freeze(data,training,frozen,smoke=True)
        evaluate(data,training,frozen,final,smoke=True)
        result=audit(data,training,frozen,final)
    else:
        from . import workflow
        if command=='audit':
            args['frozen']=args.pop('freeze')
            args['replay']=not args.pop('hash_only')
        elif command=='evaluate':
            args['frozen']=args.pop('freeze')
        result=getattr(workflow,command)(**args)
    if isinstance(result,dict):
        if 'candidates' in result:
            result={k:result[k] for k in ('champion','best_ml','baselines','class_counts')}
        elif 'partitions' in result:
            result={p:r['selectors']['champion'] for p,r in result['partitions'].items()}
        elif 'cases' in result and isinstance(result['cases'],list):
            result=result['audit']
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
