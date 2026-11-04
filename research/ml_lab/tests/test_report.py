"""Renderer tests use explicit artificial evidence, never the scientific final set."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from benchmarks.policies import POLICIES
from research.ml_lab.artifacts import digest, file_hash, read_json, write_json, write_rows
from research.ml_lab.features import FEATURE_NAMES
from research.ml_lab.labels import evaluate_problem
from research.ml_lab.report import build_report
from research.ml_lab.scoring import ACCEPTANCE, paired, summarize, support
from research.ml_lab.tests.test_features_labels import example


def fixture(base: Path):
    """Small real policy outcomes plus artificial classifier metadata for rendering only."""
    train, final=base/'training',base/'final'
    candidates=('logistic-fixture','forest-fixture','boosting-fixture')
    rows=[]
    for partition in ('final_id','final_shift'):
        for index in range(3):
            p=example()
            if index==2:
                raw=p.model_dump(mode='json')
                raw['tasks'][0]['access']='blocked'
                p=raw
            row=evaluate_problem(p)
            row.update(case_id=f'{partition}-{index}', group_id=f'{partition}-group-{index}',partition=partition,
                       family='renderer-fixture',task_count=2)
            row['predictions']={name:POLICIES[0] if row['eligible'] else None for name in candidates}
            row['predictions'].update(fixed=POLICIES[1] if row['eligible'] else None,
                                      majority=POLICIES[1] if row['eligible'] else None,
                                      heuristic=POLICIES[2] if row['eligible'] else None,
                                      champion=POLICIES[0] if row['eligible'] else None,hindsight=row['label'])
            rows.append(row)
    def summaries(subset):
        return {name:{'metrics':summarize(subset,[r['predictions'][name] for r in subset]),
                      'versus_fixed':paired(subset,[r['predictions'][name] for r in subset],POLICIES[1])}
                for name in rows[0]['predictions']}
    parts={}
    for partition in ('final_id','final_shift'):
        selected=[r for r in rows if r['partition']==partition]
        parts[partition]={'support':support(selected),'selectors':summaries(selected),
                          'families':{'renderer-fixture':summaries(selected)},'scales':{'2':summaries(selected)}}
    report={'best_ml':candidates[0],'champion':candidates[0],
            'baselines':{'fixed':POLICIES[1],'majority':POLICIES[1]},'acceptance':ACCEPTANCE,'partitions':parts}
    models={name:{'development':parts['final_id']['selectors'][name]['metrics'],
                  'grouped_cv':parts['final_id']['selectors'][name]['metrics'],'model_size_bytes':100,
                  'interpretation':{'method':'standardized_logistic_coefficients',
                                    'magnitude_by_feature':{feature:1/(i+1) for i,feature in enumerate(FEATURE_NAMES)}}}
            for name in candidates}
    trained={**{key:report[key] for key in ('best_ml','champion','baselines')},'candidates':models,
             'family_winners':dict(zip(('logistic','forest','boosting'),candidates)),
             'class_counts':{POLICIES[1]:2},'environment':{'fixture':True},'dataset_hash':'renderer-fixture',
             'source_revision':'renderer-fixture'}
    (train/'models').mkdir(parents=True)
    for name,candidate in models.items():
        path=train/'models'/f'{name}.fixture'
        path.write_bytes(b'Explicit renderer fixture; not an executable trained model.')
        candidate['model_file']=str(path.relative_to(train))
        candidate['model_sha256']=file_hash(path)
    write_json(train/'training.json',trained)
    write_json(final/'results.json',report)
    write_rows(final/'cases.jsonl.gz',rows)
    frozen={**{key:trained[key] for key in ('best_ml','champion','baselines','family_winners','dataset_hash')},
            'acceptance':ACCEPTANCE,
            'training_files':{str(p.relative_to(train)):file_hash(p) for p in train.rglob('*') if p.is_file()}}
    write_json(base/'selection-freeze.json',frozen)
    completion={'status':'COMPLETE','freeze_sha256':file_hash(base/'selection-freeze.json'),
                'dataset_hash':trained['dataset_hash'],'numerical_rows_sha256':digest(rows),
                'results_sha256':digest(report),
                'artifacts':{p.name:file_hash(p) for p in final.iterdir() if p.is_file()}}
    write_json(final/'completion.json',completion)
    return train,final


class ReportTests(unittest.TestCase):
    def test_figures_and_markdown_reproduce_with_honest_missing_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            train,final=fixture(base)
            first=build_report(train,final,base/'presentation-a')
            second=build_report(train,final,base/'presentation-b')
            self.assertEqual(first,second)
            self.assertEqual(len(first['artifacts']),9)
            self.assertEqual(sum(path.endswith('.png') for path in first['artifacts']),4)
            self.assertEqual(sum(path.endswith('.svg') for path in first['artifacts']),4)
            text=(base/'presentation-a/REPORT.md').read_text()
            self.assertIn('No learned-selector promotion is supported',text)
            self.assertIn('2/3 eligible cases',text)
            self.assertIn('Training process: — seconds',text)
            self.assertIn('percentage improvement is undefined',text)
            self.assertNotIn('calibrated restoration confidence',text)
            with self.assertRaises(FileExistsError):
                build_report(train,final,base/'presentation-a')

    def test_identity_or_denominator_mismatch_refuses_report_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            train,final=fixture(base)
            original=read_json(final/'results.json')
            changed=deepcopy(original)
            changed['champion']='fixed'
            (final/'results.json').write_text(__import__('json').dumps(changed))
            with self.assertRaises(ValueError):
                build_report(train,final,base/'bad-identity')
            self.assertFalse((base/'bad-identity').exists())
            changed=deepcopy(original)
            changed['partitions']['final_id']['support']['cases']=999
            (final/'results.json').write_text(__import__('json').dumps(changed))
            with self.assertRaises(ValueError):
                build_report(train,final,base/'bad-support')
            self.assertFalse((base/'bad-support').exists())

    def test_corrupted_or_unsealed_evidence_refuses_render(self):
        mutations=('incomplete','row_digest','result_digest','results_bytes','case_bytes',
                   'training_metadata','model_bytes','missing_freeze','freeze_bytes')
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp)
                train,final=fixture(base)
                if mutation in ('incomplete','row_digest','result_digest'):
                    completion=read_json(final/'completion.json')
                    key={'incomplete':'status','row_digest':'numerical_rows_sha256',
                         'result_digest':'results_sha256'}[mutation]
                    completion[key]='corrupt'
                    (final/'completion.json').write_text(__import__('json').dumps(completion))
                elif mutation=='missing_freeze':
                    (base/'selection-freeze.json').unlink()
                else:
                    path={'results_bytes':final/'results.json','case_bytes':final/'cases.jsonl.gz',
                          'training_metadata':train/'training.json',
                          'model_bytes':train/'models/logistic-fixture.fixture',
                          'freeze_bytes':base/'selection-freeze.json'}[mutation]
                    path.write_bytes(path.read_bytes()+b' ')
                with self.assertRaises((ValueError,FileNotFoundError)):
                    build_report(train,final,base/'corrupted-report')
                self.assertFalse((base/'corrupted-report').exists())


if __name__=='__main__':
    unittest.main()
