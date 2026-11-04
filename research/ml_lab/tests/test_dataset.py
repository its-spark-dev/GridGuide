import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from benchmarks.contracts import BenchmarkProblem
from research.ml_lab.contracts import MLCase, input_eligibility, topology_hash
from research.ml_lab.dataset import audit_cases, load_partition, read_manifest, write_dataset
from research.ml_lab.generator import generate_suite


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = generate_suite('smoke')

    def test_deterministic_generation(self):
        self.assertEqual([c.fingerprint for c in self.cases],
                         [c.fingerprint for c in generate_suite('smoke')])

    def test_contracts_counts_and_grouped_splits(self):
        result = audit_cases(self.cases)
        self.assertEqual(result['cases'], 96)
        self.assertEqual(result['groups'], 32)
        self.assertEqual(result['partition_counts'], {'train': 36, 'dev': 24, 'final_id': 24, 'final_shift': 12})
        self.assertEqual(result['groups'], result['unique_graph_hashes'])

    def test_graph_hash_ignores_node_names_and_order(self):
        problem = self.cases[0].problem
        values = problem.model_dump(mode='json')
        rename = {t.id: f'syn-renamed-{i}' for i, t in enumerate(reversed(problem.tasks))}
        for task in values['tasks']:
            task['id'] = rename[task['id']]
            task['prerequisites'] = [rename[i] for i in task['prerequisites']]
        values['tasks'].reverse()
        for group in values['groups']:
            group['required_tasks'] = [rename[i] for i in group['required_tasks']]
        self.assertEqual(topology_hash(problem), topology_hash(BenchmarkProblem.model_validate(values)))

    def test_related_variant_cannot_cross_split(self):
        values = self.cases[0].model_dump()
        values['partition'] = 'dev'
        changed = MLCase.model_validate(values)
        with self.assertRaisesRegex(ValueError, 'crosses partitions'):
            audit_cases([changed] + self.cases[1:])

    def test_missing_scope_is_preserved(self):
        incomplete = [c for c in self.cases if c.configuration.incomplete_mode != 'none']
        self.assertTrue(incomplete)
        for case in incomplete:
            self.assertFalse(input_eligibility(case.problem)['complete_customer_scope'])
            self.assertGreater(input_eligibility(case.problem)['unresolved_customers'], 0)
            self.assertIsNone(case.problem.observed_outcomes)

    def test_immutable_manifest_and_exact_file_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a', Path(tmp)/'b'
            ma = write_dataset(a, 'smoke', 'a'*40)
            mb = write_dataset(b, 'smoke', 'a'*40)
            self.assertEqual(ma, mb)
            for file in a.iterdir():
                self.assertEqual(file.read_bytes(), (b/file.name).read_bytes())
            self.assertEqual(len(load_partition(a, 'train')), 36)
            self.assertEqual(read_manifest(a), ma)
            with self.assertRaises(FileExistsError):
                write_dataset(a, 'smoke', 'a'*40)
            (a/'train.jsonl.gz').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                load_partition(a, 'train')

    def test_no_outcomes_in_input_artifacts(self):
        for case in self.cases:
            values = case.model_dump(mode='json')
            text = json.dumps(values)
            for forbidden in ('modeled_customer_outage_hours', 'selected_policy', 'assignments', 'data/raw', 'oracle'):
                self.assertNotIn(forbidden, text)
        source_dir = Path(__file__).resolve().parents[1]
        for filename in ('generator.py', 'dataset.py', 'contracts.py'):
            source = (source_dir/filename).read_text()
            for forbidden in ('from benchmarks.scenarios', 'from benchmarks.policies', 'from benchmarks.metrics',
                              'from backend.sources', 'data/raw'):
                self.assertNotIn(forbidden, source)

    def test_generation_with_source_and_network_access_denied(self):
        program = '''
import os, pathlib, sys
root = pathlib.Path.cwd()
def deny(event, args):
    if event == "socket.connect":
        raise PermissionError("network forbidden")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = pathlib.Path(os.fsdecode(args[0])).resolve()
        if any(path.is_relative_to(root/"data"/name) for name in ("raw", "processed", "external", "prepared")):
            raise PermissionError("source access forbidden")
sys.addaudithook(deny)
from research.ml_lab.generator import generate_suite
from research.ml_lab.dataset import audit_cases
assert audit_cases(generate_suite("smoke"))["cases"] == 96
'''
        subprocess.run([sys.executable, '-c', program], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
