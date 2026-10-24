"""Customer journey contracts, delegation and real API regressions."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.contracts import Bounds
from backend.customer import _eligibility, _preparation, customer_journey
from backend.data import prepare_context, source_hashes
from backend.engine import compare_access, default_scenario, evaluate
from pipeline import guidance


class CustomerJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = source_hashes()
        cls.context = prepare_context()
        cls.results = {access: evaluate(cls.context, default_scenario(cls.context, access=access))
                       for access in ('clear', 'restricted', 'blocked')}

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.hashes:
            raise AssertionError('Raw data changed')

    def transition(self, before, after):
        a, b = self.results[before], self.results[after]
        return customer_journey(b, a, compare_access(a, b))

    def test_finite_preparation_and_eligibility_delegate_to_teammate(self):
        for access in ('clear', 'restricted'):
            result = self.results[access]
            upper = result.restoration.display_hours.upper
            with patch('backend.customer.guidance.prep_guidance', wraps=guidance.prep_guidance) as prep, \
                 patch('backend.customer.guidance.alert_plan', wraps=guidance.alert_plan) as alerts:
                journey = customer_journey(result)
                prep.assert_called_once_with('High', upper, priority_needs=False, confidence='Low')
                alerts.assert_called_once_with('High', upper, priority_needs=False, confidence='Low')
            expected = guidance.prep_guidance('High', upper, False, 'Low')
            self.assertEqual(journey.preparation.actions, tuple(expected['actions']))
            self.assertEqual(journey.preparation.safety, tuple(expected['safety']))
            self.assertTrue(journey.alerts.eligible)
            self.assertFalse(journey.alerts.priority_needs_declared)
            self.assertEqual(journey.alerts.suggested_channels, ('sms', 'app'))
        clear = customer_journey(self.results['clear']).preparation.actions
        restricted = customer_journey(self.results['restricted']).preparation.actions
        self.assertEqual(restricted, clear)  # Both corrected upper bounds remain below 24 elapsed hours.

    def test_teammate_rule_changes_are_consumed(self):
        with patch('backend.customer.guidance.prep_guidance', return_value={'actions': ['team-owned-action'], 'safety': ['team-owned-safety']}):
            self.assertEqual(customer_journey(self.results['clear']).preparation.actions, ('team-owned-action',))
        with patch.dict(guidance.ALERT_RULES, update_threshold_hours=10):
            self.assertFalse(self.transition('clear', 'restricted').estimate_update_eligible)

    def test_unknown_duration_does_not_invent_estimate_or_duration_tips(self):
        journey = customer_journey(self.results['blocked'])
        self.assertFalse(journey.preparation.duration_known)
        self.assertTrue(journey.alerts.eligible)  # HIGH is independent of duration.
        text = journey.model_dump_json()
        for misleading in ('0 hours', 'inf', 'longer end of the range', 'more than a day', 'multi-day'):
            self.assertNotIn(misleading, text)
        for state in ('pre_storm', 'outage_confirmed'):
            body = next(m.body for m in journey.messages if m.state == state)
            self.assertIn('Estimate unavailable', body)
        self.assertIsNone(_eligibility('Medium', None, 'Low').eligible)
        self.assertFalse(_eligibility('Low', None, 'Low').eligible)
        self.assertFalse(_eligibility('Medium', 11, 'Low').eligible)
        self.assertTrue(_eligibility('Medium', 12, 'Low').eligible)

    def test_four_states_and_finite_messages_come_from_teammate(self):
        with patch('backend.customer.guidance.messages', wraps=guidance.messages) as messages:
            journey = self.transition('clear', 'restricted')
            self.assertEqual(messages.call_count, 2)
            messages.assert_called_with('High', 2.5, 12.0, 'Low', new_low=4.0, new_high=16.5)
        self.assertEqual([m.state for m in journey.messages], ['pre_storm', 'outage_confirmed', 'estimate_updated', 'restored'])
        self.assertTrue(all(m.source == 'teammate_template_adapted' for m in journey.messages))
        updated = next(m for m in journey.messages if m.state == 'estimate_updated')
        self.assertIn('4–16.5 elapsed hours', updated.body)
        self.assertTrue(updated.available)
        self.assertEqual(journey.selected_state, 'estimate_updated')
        self.assertFalse(journey.estimate_update_eligible)  # raw upper elapsed delta 4.5 is below the prototype threshold

    def test_null_transitions_and_no_change(self):
        for before in self.results:
            for after in self.results:
                with self.subTest(before=before, after=after):
                    journey = self.transition(before, after)
                    updated = next(m for m in journey.messages if m.state == 'estimate_updated')
                    self.assertEqual(updated.available, before != after)
                    self.assertEqual(journey.estimate_update_eligible, (before == 'blocked') != (after == 'blocked'))
                    if after == 'blocked' and before != after:
                        self.assertIn('Estimate unavailable', updated.body)
                        self.assertNotIn('hours', updated.body)
        self.assertFalse(next(m for m in customer_journey(self.results['clear']).messages if m.state == 'estimate_updated').available)

    def test_templates_do_not_claim_live_facts_or_probability(self):
        for access in self.results:
            journey = self.transition('clear', access)
            text = ' '.join(m.body for m in journey.messages)
            for bad in ('chance of an outage', 'We know your power is out', 'Crews are working in your area', 'AEP GridGuide:'):
                self.assertNotIn(bad, text)
            self.assertIn('If the utility confirms restoration', text)
            self.assertEqual(journey.alerts.delivery, 'preview_only')
            self.assertIn('no alert has been sent', journey.delivery_note)

    def test_wrong_comparison_is_rejected(self):
        with self.assertRaises(ValueError):
            customer_journey(self.results['restricted'], self.results['clear'], compare_access(self.results['blocked'], self.results['restricted']))

    def test_update_threshold_uses_raw_comparison_not_display_rounding(self):
        a = self.results['clear']
        raw = a.restoration.raw_hours
        for delta, expected in ((6, False), (6.001, True)):
            restoration = a.restoration.model_copy(update={'raw_hours': Bounds(lower=raw.lower+delta, upper=raw.upper+delta),
                                                          'display_hours': Bounds(lower=17, upper=24)})
            b = a.model_copy(update={'restoration': restoration, 'result_id': 'test-only-threshold'})
            journey = customer_journey(b, a, compare_access(a, b))
            self.assertEqual(journey.estimate_update_eligible, expected)

    def test_api_journey_bound_to_same_result_and_private_fields_rejected(self):
        with TestClient(create_app(lambda: self.context)) as client:
            for access in self.results:
                response = client.post('/api/evaluate', json={'access': access})
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data['result'], self.results[access].model_dump(mode='json'))
                self.assertEqual(data['customer_journey']['result_id'], data['result']['result_id'])
                self.assertNotIn(self.context.private_premise, str(data['customer_journey']))
                self.assertEqual(data['result']['risk']['band'], 'HIGH')
            for field in ('critical_c', 'priority_needs', 'phone', 'email', 'lifecycle_state'):
                response = client.post('/api/evaluate', json={field: 'private-test-value'})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('private-test-value', response.text)


if __name__ == '__main__':
    unittest.main()
