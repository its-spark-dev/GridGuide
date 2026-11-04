"""Source-free precomputed customer dependency states, not observed restoration."""
import json
from pathlib import Path
import unittest
from pydantic import ValidationError
from backend.contracts import CustomerPathFrame
from backend.scenarios import prepare_synthetic
from scripts.prepare_customer_paths import prepare, fingerprint


class CustomerPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = prepare_synthetic()
        cls.artifact = prepare()

    def test_checked_in_frames_reproduce(self):
        stored = json.loads((Path(__file__).resolve().parents[1]/'frontend/public/preparedness/frames.json').read_text())
        self.assertEqual(self.artifact, stored)
        self.assertEqual(len(stored['frames']), 18)

    def test_every_frame_binds_exact_definition_and_only_declared_paths(self):
        for frame in self.artifact['frames']:
            CustomerPathFrame.model_validate(frame)
            data = {k:v for k,v in frame.items() if k != 'result_fingerprint'}
            self.assertEqual(fingerprint(data), frame['result_fingerprint'])
            source = self.catalog.scenarios[frame['scenario_id']]
            self.assertEqual(frame['input_fingerprint'], self.catalog.metadata[source.id].input_fingerprint)
            for path, authored in zip(frame['customers'], source.customer_paths):
                self.assertEqual(path['asset_ids'], list(authored.asset_ids))
                self.assertEqual(set(path['required_repair_ids']), {r.id for r in source.repairs if r.asset_id in authored.asset_ids})
            self.assertNotIn('coordinates', json.dumps(frame))
            self.assertTrue(all(n['repair_id'] is None for n in frame['nodes'] if n['kind']=='supply_terminal'))

    def test_no_early_release_and_monotone_unique_counts(self):
        for sid in self.catalog.scenarios:
            previous = 0
            for f in (r for r in self.artifact['frames'] if r['scenario_id']==sid):
                completed = {n['repair_id'] for n in f['nodes'] if n['state']=='completed_simulated'}
                released = [c for c in f['customers'] if c['release_state']=='released_simulated']
                for c in released:self.assertTrue(set(c['required_repair_ids'])<=completed)
                self.assertEqual(len({c['id'] for c in released}), f['released_customers'])
                self.assertGreaterEqual(f['released_customers'], previous)
                previous = f['released_customers']

    def test_blocked_and_unknown_never_gain_finite_completion(self):
        for f in self.artifact['frames']:
            if f['scenario_id'] in ('syn-blocked','syn-missing'):
                self.assertIsNone(f['completion_hours'])
                self.assertGreater(f['unresolved_customers'],0)
            if f['scenario_id']=='syn-missing':
                self.assertTrue(any(n['state']=='unresolved' for n in f['nodes']))
                self.assertTrue(f['customers'][0]['unresolved_link_from_ids'])
            if f['scenario_id']=='syn-blocked':
                self.assertTrue(any(n['state']=='blocked' for n in f['nodes']))
                self.assertTrue(any(n['state']=='dependency_blocked' for n in f['nodes']))

    def test_public_frame_schema_rejects_private_extra_fields(self):
        f=self.artifact['frames'][0]
        for key in ('contact','latitude','declarations','road_name','source_id'):
            with self.assertRaises(ValidationError):CustomerPathFrame.model_validate({**f,key:'forbidden'})
        raw={**f,'nodes':[{**f['nodes'][0],'coordinates':[1,2]},*f['nodes'][1:]]}
        with self.assertRaises(ValidationError):CustomerPathFrame.model_validate(raw)


if __name__=='__main__':unittest.main()
