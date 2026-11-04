"""Independent guard regressions; no scientific final labels or model fitting."""
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from research.ml_lab.access import isolated
from research.ml_lab.artifacts import ROOT, file_hash, read_json, validate_hashes, write_json
from research.ml_lab.dataset import write_dataset
from research.ml_lab.workflow import evaluate, train


class WorkflowGuardTests(unittest.TestCase):
    def test_experiments_deny_challenge_sources_and_network(self):
        with isolated():
            with self.assertRaises(PermissionError):
                (ROOT / 'data/raw/never-open-a-source.txt').read_bytes()
            with socket.socket() as sock, self.assertRaises(PermissionError):
                sock.connect(('127.0.0.1', 9))

    def test_nested_isolation_preserves_outer_holdout_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            heldout = Path(tmp) / 'holdout-input.txt'
            heldout.write_text('input only')
            with isolated(heldout):
                with self.assertRaises(PermissionError):
                    heldout.read_text()
                with isolated():
                    with self.assertRaises(PermissionError):
                        heldout.read_text()
                with self.assertRaises(PermissionError):
                    heldout.read_text()
            self.assertEqual(heldout.read_text(), 'input only')

    def test_hash_inventory_rejects_path_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = root / 'artifacts'
            artifacts.mkdir()
            outside = root / 'outside.txt'
            outside.write_text('outside')
            (artifacts / 'link').symlink_to(outside)
            for relative in ('../outside.txt', 'link'):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    validate_hashes(artifacts, {relative: file_hash(outside)})

    def test_spent_dataset_cannot_start_model_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / 'data'
            write_dataset(dataset, 'smoke', 'a' * 40)
            write_json(dataset / 'evaluation-receipt.json', {'status': 'STARTED'})
            with patch('research.ml_lab.workflow._training_inputs',
                       side_effect=AssertionError('Fitting must not start after reveal')) as load:
                with self.assertRaises(ValueError):
                    train(dataset, root / 'training', smoke=True)
                load.assert_not_called()

    def test_training_cannot_accidentally_read_final_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / 'data'
            write_dataset(dataset, 'smoke', 'a' * 40)
            def accidental_holdout_access(path):
                return (path / 'final_id.jsonl.gz').read_bytes()
            with patch('research.ml_lab.workflow._training_inputs',
                       side_effect=accidental_holdout_access):
                with self.assertRaises(PermissionError):
                    train(dataset, root / 'training', smoke=True)

    def test_failure_receipt_precedes_labels_and_prevents_retry(self):
        # Deliberately fail before producing labels; this tests transaction ordering,
        # not a successful or scientific evaluation.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / 'data'
            dataset.mkdir()
            frozen = root / 'freeze.json'
            write_json(frozen, {'test_fixture': True})
            seal = {'profile': 'smoke', 'dataset_hash': 'a' * 64, 'champion': 'fixed'}
            def failed_evaluation(*args):
                self.assertTrue((dataset / 'evaluation-receipt.json').is_file())
                raise RuntimeError('intentional pre-label failure')
            with patch('research.ml_lab.workflow._check_freeze', return_value=(seal, {})), \
                    patch('research.ml_lab.workflow._final_results', side_effect=failed_evaluation) as run:
                with self.assertRaisesRegex(RuntimeError, 'intentional pre-label failure'):
                    evaluate(dataset, root / 'training', frozen, root / 'final', smoke=True)
                receipt_bytes = (dataset / 'evaluation-receipt.json').read_bytes()
                self.assertTrue(read_json(root / 'final/failure.json')['receipt_preserved'])
                with self.assertRaises(FileExistsError):
                    evaluate(dataset, root / 'training', frozen, root / 'different-output', smoke=True)
                self.assertEqual(run.call_count, 1)
                self.assertEqual((dataset / 'evaluation-receipt.json').read_bytes(), receipt_bytes)


if __name__ == '__main__':
    unittest.main()
