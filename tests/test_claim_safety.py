"""Untrusted prose cannot replace the bound deterministic public explanation."""
import copy
import unittest
from backend import review

class ClaimSafetyTests(unittest.TestCase):
    def test_unfounded_claims_rejected_even_with_new_checksum(self):
        s=next(s for s in review.catalog().scenarios if s.scenario_id=='syn-micro-blocked')
        c=review.compare(dict(scenario_id=s.scenario_id,scenario_fingerprint=s.scenario_fingerprint,include_experimental=True))
        self.assertEqual(c.recommended_policy,review.FIXED)
        self.assertIsNone(c.results[2].metrics.modeled_customer_outage_hours)
        artifact=review.export_review(dict(request=c.request.model_dump(),result_fingerprint=c.result_fingerprint,
            reason='demonstration-comparison',acknowledgements={k:True for k in
            ['fictional','modeled_not_field_confirmed','gaps_and_unresolved','objective_and_tradeoffs','experimental_and_simulation_limits']})).artifact.model_dump(mode='json')
        for claim in ['CP-SAT proves this blocked plan optimal.','These synthetic intervals are calibrated confidence.',
                      'This fictional connection is observed electrical topology.','NOAA reports validate these outage outcomes.',
                      'Unknown clearance is zero.','Simulated release is utility-confirmed restoration.',
                      'CP-SAT is the default recommended policy.']:
            with self.subTest(claim=claim):
                forged=copy.deepcopy(artifact);forged['comparison']['explanation']=claim
                forged['checksum']=review.digest({k:v for k,v in forged.items() if k!='checksum'})
                with self.assertRaises(ValueError):review.replay(forged)
        self.assertIn('Reviewed in demo',review.replay(artifact))
