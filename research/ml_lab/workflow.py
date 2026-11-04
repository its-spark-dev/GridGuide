"""Two-stage experiment: sealed inputs → train/dev → committed freeze → one reveal.

Joblib artifacts are repository-owned executable serialization. Only artifacts bound
by a verified local freeze are loaded; do not substitute untrusted downloaded models.
Hashes establish consistency, not authorship or a malicious-author security boundary.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import resource
import sys
import time
import warnings

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from .access import isolated
from .artifacts import (ROOT, digest, environment, file_hash, read_json, read_rows,
                        require_committed, revision, source_hashes, validate_hashes, write_json, write_rows)
from .baselines import fit_baselines, heuristic
from .dataset import load_partition, read_manifest, write_dataset
from .features import FEATURE_NAMES, FEATURE_SCHEMA, FEATURE_VERSION, extract_features, inference_supported
from .labels import evaluate_problem
from .models import catalog, importance, matrix, model_bytes, predict
from .scoring import ACCEPTANCE, paired, summarize, support

MAX_SECONDS = 1800
MAX_RSS_BYTES = 2 * 1024**3


def _resources(start: float) -> dict:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(peak if sys.platform == 'darwin' else peak*1024)
    result = {'elapsed_seconds':time.perf_counter()-start, 'peak_process_rss_bytes':peak_bytes}
    if result['elapsed_seconds']>MAX_SECONDS or peak_bytes>MAX_RSS_BYTES:
        raise RuntimeError(f'Preregistered resource bound exceeded: {result}')
    return result


def label_cases(cases) -> list[dict]:
    return [dict(evaluate_problem(c.problem), case_id=c.case_id, group_id=c.group_id,
                 partition=c.partition, family=c.configuration.mechanism,
                 task_count=len(c.problem.tasks), features=extract_features(c.problem),
                 heuristic=heuristic(c.problem)) for c in cases]


def prepare(output: Path, profile: str = 'full') -> dict:
    with isolated():
        return write_dataset(output, profile, revision())


def _training_inputs(dataset: Path):
    return {p: load_partition(dataset,p) for p in ('train','dev')}


def train(dataset: Path, output: Path, *, smoke: bool = False) -> dict:
    dataset, output = Path(dataset), Path(output)
    if output.exists():
        raise FileExistsError('Training run already exists')
    if (dataset/'evaluation-receipt.json').exists():
        raise ValueError('Final cohort has been spent; model selection cannot be repeated')
    manifest = read_manifest(dataset)
    if smoke != (manifest['profile']=='smoke'):
        raise ValueError('Smoke and scientific datasets cannot be interchanged')
    if not smoke:
        require_committed([dataset/'manifest.json',dataset/'final_id.jsonl.gz',dataset/'final_shift.jsonl.gz'])
    output.mkdir(parents=True)
    start = time.perf_counter()
    # Even accidental file access to final inputs is forbidden during fitting.
    with isolated(dataset/'final_id.jsonl.gz',dataset/'final_shift.jsonl.gz', ROOT/'docs/ml-lab/evidence/final'), threadpool_limits(limits=1):
        cases = _training_inputs(dataset)
        rows = {p:label_cases(cases[p]) for p in ('train','dev')}
        for p in rows:
            write_rows(output/f'{p}-labels.jsonl.gz', rows[p])
        eligible = {p:[r for r in rows[p] if r['eligible']] for p in rows}
        if any(not r for r in eligible.values()):
            raise ValueError('No eligible training/development cases')
        training, dev = eligible['train'], eligible['dev']
        x,y = matrix(training),np.array([r['label'] for r in training])
        xd = matrix(dev)
        groups = np.array([r['group_id'] for r in training])
        if len(set(y))<2 or len(set(groups))<3:
            raise ValueError('Insufficient training class or configuration diversity')
        baseline = fit_baselines(rows['train'])
        cv = list(GroupKFold(n_splits=3).split(x,y,groups))
        fold_manifest = [{'train_groups':sorted(set(groups[a])), 'validation_groups':sorted(set(groups[b]))} for a,b in cv]
        if any(set(f['train_groups']) & set(f['validation_groups']) for f in fold_manifest):
            raise AssertionError('CV group leakage')
        candidates = {}
        runtime = {}
        (output/'models').mkdir()
        for name, template in catalog().items():
            candidate_start = time.perf_counter()
            with warnings.catch_warnings():
                warnings.simplefilter('error',ConvergenceWarning)
                oof = [None]*len(training)
                for a,b in cv:
                    estimator = clone(template).fit(x[a],y[a])
                    for index,p in zip(b,estimator.predict(x[b])):
                        oof[index] = str(p)
                fitted = clone(template).fit(x,y)
                second = clone(template).fit(x,y)
            train_pred = fitted.predict(x).tolist()
            dev_pred = fitted.predict(xd).tolist()
            if not np.array_equal(fitted.predict(xd),second.predict(xd)) or not np.allclose(
                    fitted.predict_proba(np.concatenate((x,xd))),second.predict_proba(np.concatenate((x,xd))),rtol=0,atol=1e-10):
                raise AssertionError('Deterministic model replay failed')
            first_bytes,second_bytes = model_bytes(fitted),model_bytes(second)
            if first_bytes != second_bytes:
                raise AssertionError('Same-environment serialized model replay differs')
            path = output/'models'/f'{name}.joblib'
            path.write_bytes(first_bytes)
            candidates[name] = {'family':name.split('-')[0], 'parameters':template.named_steps['model'].get_params(),
                'train':summarize(training,train_pred), 'grouped_cv':summarize(training,oof),
                'development':summarize(dev,dev_pred), 'development_predictions':dev_pred,
                'training_predictions':train_pred, 'grouped_cv_predictions':oof,
                'interpretation':importance(fitted), 'model_file':str(path.relative_to(output)),
                'model_sha256':file_hash(path), 'model_size_bytes':len(first_bytes),
                'deterministic_replay':{'predictions_equal':True,'probability_atol':1e-10,'artifact_bytes_equal':True}}
            inference_start = time.perf_counter()
            for _ in range(20):
                fitted.predict(xd)
            runtime[name] = {'training_cv_replay_seconds':time.perf_counter()-candidate_start,
                             'batch_inference_seconds_per_case':(time.perf_counter()-inference_start)/(20*len(dev))}
            _resources(start)
        def dev_regret(name):
            return candidates[name]['development']['absolute_regret_customer_hours']['mean']
        family_winners = {family:min((n for n in candidates if n.startswith(family)),key=lambda n:(dev_regret(n),n))
                          for family in ('logistic','forest','boosting')}
        best_ml = min(candidates,key=lambda n:(dev_regret(n),n))
        fixed_dev = summarize(dev,[baseline['fixed']]*len(dev))
        champion = best_ml if dev_regret(best_ml)<fixed_dev['absolute_regret_customer_hours']['mean'] else 'fixed'
        report = {'version':'ml-training-v1','dataset_hash':manifest['dataset_hash'],
            'input_manifest_sha256':file_hash(dataset/'manifest.json'), 'source_revision':revision(),
            'source_hashes':source_hashes(), 'feature_version':FEATURE_VERSION,
            'feature_names':list(FEATURE_NAMES), 'feature_schema':FEATURE_SCHEMA,
            'baselines':baseline, 'fixed_development':fixed_dev,
            'majority_development':summarize(dev,[baseline['majority']]*len(dev)),
            'heuristic_development':summarize(dev,[r['heuristic'] for r in dev]),
            'support':{p:support(rows[p]) for p in rows}, 'cv_folds':fold_manifest,
            'class_counts':dict(sorted(Counter(y).items())),
            'candidates':candidates,'family_winners':family_winners,'best_ml':best_ml,'champion':champion,
            'selection_rule':'lowest mean absolute development regret; fixed retained unless strictly beaten',
            'final_data_accessed':False,'environment':environment()}
        write_json(output/'training.json',report)
        write_json(output/'runtime.json',dict(_resources(start),environment=environment(),models=runtime))
    return report


def freeze(dataset: Path, training: Path, output: Path, *, smoke: bool = False) -> dict:
    dataset,training,output = map(Path,(dataset,training,output))
    manifest, fitted = read_manifest(dataset),read_json(training/'training.json')
    if smoke != (manifest['profile']=='smoke') or fitted['dataset_hash'] != manifest['dataset_hash']:
        raise ValueError('Dataset/training identity mismatch')
    if fitted['source_hashes'] != source_hashes():
        raise ValueError('Training code changed: replay training before freeze')
    files = {str(p.relative_to(training)):file_hash(p) for p in sorted(training.rglob('*')) if p.is_file()}
    if not smoke:
        require_committed([dataset/'manifest.json']+[training/p for p in files]+[ROOT/p for p in source_hashes()])
    result = {'version':'ml-selection-freeze-v1','dataset_hash':manifest['dataset_hash'],
        'dataset_manifest_sha256':file_hash(dataset/'manifest.json'), 'training_files':files,
        'feature_names':list(FEATURE_NAMES),'champion':fitted['champion'],'best_ml':fitted['best_ml'],
        'family_winners':fitted['family_winners'],'baselines':fitted['baselines'],
        'acceptance':ACCEPTANCE,'source_hashes':source_hashes(),'source_revision':revision(),
        'environment':environment(),'profile':manifest['profile'],
        'isolation_limit':'procedural developer-controlled seal, not externally independent blind evaluation'}
    write_json(output,result)
    return result


def _check_freeze(dataset: Path, training: Path, frozen: Path, *, allow_environment_difference=False) -> tuple[dict,dict]:
    seal,fitted = read_json(frozen),read_json(training/'training.json')
    if read_manifest(dataset)['dataset_hash'] != seal['dataset_hash'] or file_hash(dataset/'manifest.json') != seal['dataset_manifest_sha256']:
        raise ValueError('Final input seal mismatch')
    if source_hashes() != seal['source_hashes'] or seal['acceptance'] != ACCEPTANCE or seal['feature_names'] != list(FEATURE_NAMES):
        raise ValueError('Frozen source/protocol/schema changed')
    validate_hashes(training,seal['training_files'])
    if fitted['champion'] != seal['champion'] or fitted['baselines'] != seal['baselines']:
        raise ValueError('Frozen selector changed')
    for name,candidate in fitted['candidates'].items():
        expected_path = f'models/{name}.joblib'
        if (candidate['model_file'] != expected_path or expected_path not in seal['training_files']
                or candidate['model_sha256'] != seal['training_files'][expected_path]):
            raise ValueError('Model path/hash is not bound to the frozen artifact inventory')
    current_environment = environment()
    if not allow_environment_difference and (current_environment['packages'] != seal['environment']['packages']
            or current_environment['python'] != seal['environment']['python']):
        raise ValueError('Frozen Python/package versions differ')
    return seal,fitted


def _final_results(dataset: Path, training: Path, fitted: dict) -> tuple[list[dict],dict,dict]:
    models = {n:joblib.load(training/c['model_file']) for n,c in fitted['candidates'].items()}
    start = time.perf_counter()
    rows = []
    inference_times = {n:0.0 for n in models}
    for partition in ('final_id','final_shift'):
        cases = load_partition(dataset,partition)
        labeled = label_cases(cases)
        for case,row in zip(cases,labeled):
            predictions = {}
            for name,model in models.items():
                begin = time.perf_counter()
                predictions[name] = predict(model,case.problem)
                inference_times[name] += time.perf_counter()-begin
            predictions.update({name:policy if row['eligible'] else None for name,policy in fitted['baselines'].items()})
            predictions['heuristic'] = row['heuristic']
            predictions['champion'] = predictions[fitted['champion']]
            predictions['hindsight'] = row['label']
            row['predictions'] = predictions
            rows.append(row)
        _resources(start)
    report = {'version':'ml-final-results-v1','partitions':{},'acceptance':ACCEPTANCE,
              'champion':fitted['champion'],'best_ml':fitted['best_ml'],'baselines':fitted['baselines']}
    for partition in ('final_id','final_shift'):
        selected = [r for r in rows if r['partition']==partition]
        selectors = list(selected[0]['predictions'])
        def summaries(subset):
            return {name:{'metrics':summarize(subset,[r['predictions'][name] for r in subset]),
                          'versus_fixed':paired(subset,[r['predictions'][name] for r in subset],fitted['baselines']['fixed'])}
                    for name in selectors}
        report['partitions'][partition] = {'support':support(selected),'selectors':summaries(selected),
            'families':{family:summaries([r for r in selected if r['family']==family]) for family in sorted({r['family'] for r in selected})},
            'scales':{scale:summaries([r for r in selected if lo<=r['task_count']<=hi])
                      for scale,lo,hi in [('10–20',10,20),('21–36',21,36),('40–64',40,64)]
                      if any(lo<=r['task_count']<=hi for r in selected)}}
    runtime = dict(_resources(start),inference_seconds=inference_times,
                   inference_denominator_cases=len(rows),environment=environment())
    return rows,report,runtime


def evaluate(dataset: Path, training: Path, frozen: Path, output: Path, *, smoke: bool = False) -> dict:
    dataset,training,frozen,output = map(Path,(dataset,training,frozen,output))
    seal,fitted = _check_freeze(dataset,training,frozen)
    if smoke != (seal['profile']=='smoke'):
        raise ValueError('Smoke mode cannot reveal a scientific final set')
    if not smoke:
        require_committed([frozen]+[ROOT/p for p in seal['source_hashes']])
    # Receipt belongs to the input seal, not the chosen output directory. Alternate
    # output paths cannot silently reveal the same frozen cohort again.
    receipt_path = dataset/'evaluation-receipt.json'
    receipt = {'version':'ml-evaluation-invocation-v1','started_utc':datetime.now(timezone.utc).isoformat(),
        'dataset_hash':seal['dataset_hash'],'freeze_sha256':file_hash(frozen),
        'invocation_revision':revision(),'profile':seal['profile'],
        'command':'python -m research.ml_lab evaluate --dataset DATASET --training TRAINING --freeze FREEZE --output FINAL',
        'champion':seal['champion'],'status':'STARTED; do not retry as a new final evaluation'}
    if output.exists():
        raise FileExistsError('Final output exists')
    write_json(receipt_path,receipt)  # Exclusive creation occurs before any label access.
    output.mkdir(parents=True)
    try:
        with isolated(), threadpool_limits(limits=1):
            rows,report,runtime = _final_results(dataset,training,fitted)
        write_rows(output/'cases.jsonl.gz',rows)
        write_json(output/'results.json',report)
        write_json(output/'runtime.json',runtime)
        complete = {'status':'COMPLETE','invocation_sha256':file_hash(receipt_path),
            'freeze_sha256':file_hash(frozen),'dataset_hash':seal['dataset_hash'],
            'numerical_rows_sha256':digest(rows),'results_sha256':digest(report),
            'artifacts':{p.name:file_hash(p) for p in sorted(output.iterdir()) if p.is_file()}}
        write_json(output/'completion.json',complete)
    except Exception as exc:
        write_json(output/'failure.json',{'status':'FAILED','exception_type':type(exc).__name__,
            'message':str(exc),'receipt_preserved':True})
        raise
    return report


def audit(dataset: Path, training: Path, frozen: Path, final: Path, *, replay: bool = True) -> dict:
    dataset,training,frozen,final = map(Path,(dataset,training,frozen,final))
    seal,fitted = _check_freeze(dataset,training,frozen)
    completed,receipt = read_json(final/'completion.json'),read_json(dataset/'evaluation-receipt.json')
    if completed['invocation_sha256']!=file_hash(dataset/'evaluation-receipt.json') or completed['freeze_sha256']!=file_hash(frozen):
        raise ValueError('Evaluation invocation/freeze binding mismatch')
    if receipt['dataset_hash']!=seal['dataset_hash'] or receipt['freeze_sha256']!=file_hash(frozen):
        raise ValueError('Invocation input binding mismatch')
    validate_hashes(final,completed['artifacts'])
    existing_rows,existing_report = read_rows(final/'cases.jsonl.gz'),read_json(final/'results.json')
    if digest(existing_rows)!=completed['numerical_rows_sha256'] or digest(existing_report)!=completed['results_sha256']:
        raise ValueError('Numerical evidence mismatch')
    if replay:
        with isolated(), threadpool_limits(limits=1):
            rows,report,_ = _final_results(dataset,training,fitted)
        if digest(rows)!=completed['numerical_rows_sha256'] or digest(report)!=completed['results_sha256']:
            raise ValueError('Read-only numerical replay differs')
    return {'status':'PASS','replayed':replay,'cases':len(existing_rows),
            'numerical_rows_sha256':completed['numerical_rows_sha256'],
            'results_sha256':completed['results_sha256'],
            'interpretation':'audit of spent final evidence; no fitting or selection'}
