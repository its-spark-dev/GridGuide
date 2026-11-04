"""Tamper checks at serialized experiment boundaries; no scientific evaluation here.

Fixtures deliberately contain non-executable model bytes. Tests exercise verification
before deserialization, rather than mocking a successful model fit or evaluation.
The separate CLI smoke lane executes real fitting, freezing, evaluation and replay.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.ml_lab.artifacts import (canonical, digest, environment, file_hash,
    read_json, source_hashes, write_json, write_rows)
from research.ml_lab.dataset import write_dataset
from research.ml_lab.features import FEATURE_NAMES
from research.ml_lab.scoring import ACCEPTANCE
from research.ml_lab.workflow import _check_freeze, audit


class SerializedIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.dataset = Path(cls.directory.name)/'dataset'
        cls.manifest = write_dataset(cls.dataset, 'smoke', 'a'*40)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.training = self.root/'training'
        self.model = self.training/'models'/'fixture.joblib'
        self.model.parent.mkdir(parents=True)
        self.model.write_bytes(b'non-executable model artifact verification fixture')
        self.fitted = {'champion': 'fixed', 'baselines': {'fixed': 'fifo-v1', 'majority': 'fifo-v1'},
            'candidates': {'fixture': {'model_file': 'models/fixture.joblib',
                                      'model_sha256': file_hash(self.model)}}}
        write_json(self.training/'training.json', self.fitted)
        self.seal = {'dataset_hash': self.manifest['dataset_hash'],
            'dataset_manifest_sha256': file_hash(self.dataset/'manifest.json'),
            'source_hashes': source_hashes(), 'acceptance': ACCEPTANCE,
            'feature_names': list(FEATURE_NAMES), 'champion': 'fixed',
            'baselines': self.fitted['baselines'], 'environment': environment(),
            'training_files': {str(p.relative_to(self.training)): file_hash(p)
                               for p in self.training.rglob('*') if p.is_file()}}
        self.frozen = self.root/'freeze.json'
        write_json(self.frozen, self.seal)

    def replace_seal(self, value):
        self.frozen.write_bytes(canonical(value))

    def test_valid_serialized_inventory_verified_without_loading_models(self):
        with patch('research.ml_lab.workflow.joblib.load', side_effect=AssertionError('must not deserialize')):
            seal, fitted = _check_freeze(self.dataset, self.training, self.frozen)
        self.assertEqual(seal['champion'], 'fixed')
        self.assertEqual(fitted, self.fitted)

    def test_changed_model_bytes_rejected_before_deserialization(self):
        self.model.write_bytes(b'changed bytes')
        with patch('research.ml_lab.workflow.joblib.load', side_effect=AssertionError('must not deserialize')):
            with self.assertRaisesRegex(ValueError, 'Artifact hash mismatch'):
                _check_freeze(self.dataset, self.training, self.frozen)

    def test_model_path_must_be_the_sealed_candidate_artifact(self):
        self.fitted['candidates']['fixture']['model_file'] = '../unlisted.joblib'
        (self.training/'training.json').write_bytes(canonical(self.fitted))
        self.seal['training_files']['training.json'] = file_hash(self.training/'training.json')
        self.replace_seal(self.seal)
        with self.assertRaisesRegex(ValueError, 'Model path/hash'):
            _check_freeze(self.dataset, self.training, self.frozen)

    def test_protocol_schema_and_python_identity_cannot_drift(self):
        mutations = [('acceptance', {}), ('feature_names', list(reversed(FEATURE_NAMES))),
                     ('environment', {**environment(), 'python': '0.0.0'})]
        for key, value in mutations:
            with self.subTest(key=key):
                changed = deepcopy(self.seal)
                changed[key] = value
                self.replace_seal(changed)
                with self.assertRaises(ValueError):
                    _check_freeze(self.dataset, self.training, self.frozen)

    def test_dataset_manifest_identity_is_bound_to_freeze(self):
        changed = deepcopy(self.seal)
        changed['dataset_manifest_sha256'] = '0'*64
        self.replace_seal(changed)
        with self.assertRaisesRegex(ValueError, 'Final input seal mismatch'):
            _check_freeze(self.dataset, self.training, self.frozen)

    def test_final_result_tamper_rejected_by_artifact_and_numerical_hashes(self):
        final = self.root/'final'
        final.mkdir()
        # This fixture exercises the spent-evidence verifier only; no model outcome
        # or successful scientific experiment is claimed by the fixture values.
        rows, report = [], {'fixture': 'numerical evidence'}
        write_rows(final/'cases.jsonl.gz', rows)
        write_json(final/'results.json', report)
        receipt = self.dataset/'evaluation-receipt.json'
        self.addCleanup(lambda: receipt.unlink(missing_ok=True))
        write_json(receipt, {'dataset_hash': self.seal['dataset_hash'],
                            'freeze_sha256': file_hash(self.frozen)})
        complete = {'invocation_sha256': file_hash(receipt),
            'freeze_sha256': file_hash(self.frozen), 'numerical_rows_sha256': digest(rows),
            'results_sha256': digest(report),
            'artifacts': {p.name: file_hash(p) for p in final.iterdir() if p.is_file()}}
        write_json(final/'completion.json', complete)
        verified = audit(self.dataset, self.training, self.frozen, final, replay=False)
        self.assertFalse(verified['replayed'])
        (final/'results.json').write_bytes(canonical({'fixture': 'tampered'}))
        with self.assertRaisesRegex(ValueError, 'Artifact hash mismatch'):
            audit(self.dataset, self.training, self.frozen, final, replay=False)
        complete['artifacts']['results.json'] = file_hash(final/'results.json')
        (final/'completion.json').write_bytes(canonical(complete))
        with self.assertRaisesRegex(ValueError, 'Numerical evidence mismatch'):
            audit(self.dataset, self.training, self.frozen, final, replay=False)


if __name__ == '__main__':
    unittest.main()
