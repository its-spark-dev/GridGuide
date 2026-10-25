"""Customer journey contracts, delegation and real API regressions."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.contracts import Bounds, DeclaredNeeds
from backend.customer import _eligibility, _preparation, customer_journey
from backend.data import prepare_context, source_hashes
from backend.engine import compare_access, compare_scenarios, default_scenario, evaluate
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

    def test_four_states_keep_teammate_templates_and_adapter_comparison(self):
        with patch('backend.customer.guidance.messages', wraps=guidance.messages) as messages:
            journey = self.transition('clear', 'restricted')
            messages.assert_called_once_with('High', 4.0, 16.5, 'Low')
        self.assertEqual([m.state for m in journey.messages], ['pre_storm', 'outage_confirmed', 'estimate_updated', 'restored'])
        self.assertTrue(all(m.source == 'teammate_template_adapted' for m in journey.messages))
        updated = next(m for m in journey.messages if m.state == 'estimate_updated')
        self.assertIn('4–16.5 elapsed hours', updated.body)
        self.assertTrue(updated.available)
        self.assertEqual(journey.selected_state, 'estimate_updated')
        self.assertFalse(journey.estimate_update_eligible)  # raw upper elapsed delta 4.5 is below the prototype threshold

    def test_finite_updates_compare_both_endpoints_without_directional_claims(self):
        # Real engine scenarios cover lower-only, upper-only, both-endpoint and
        # crossing changes. Assertions check meaning/order, not an entire snapshot.
        cases = (
            ('clear', 4, 'clear', 2, (2.5, 12), (5.5, 12)),
            ('clear', 2, 'clear', 4, (5.5, 12), (2.5, 12)),
            ('restricted', 8, 'restricted', 2, (2, 16.5), (8, 16.5)),
            ('restricted', 4, 'clear', 4, (4, 16.5), (2.5, 12)),
            ('clear', 4, 'restricted', 4, (2.5, 12), (4, 16.5)),
            ('clear', 2, 'restricted', 8, (5.5, 12), (2, 16.5)),
            ('restricted', 8, 'clear', 2, (2, 16.5), (5.5, 12)),
            ('clear', 4, 'restricted', 6, (2.5, 12), (2.5, 16.5)),
            ('restricted', 6, 'clear', 4, (2.5, 16.5), (2.5, 12)),
        )
        for access, crew, new_access, new_crew, old_bounds, new_bounds in cases:
            with self.subTest(before=(access, crew), after=(new_access, new_crew)):
                before = evaluate(self.context, default_scenario(self.context, access=access, crew_size=crew))
                after = evaluate(self.context, default_scenario(self.context, access=new_access,
                    crew_size=new_crew, scenario_revision=2))
                self.assertEqual(before.restoration.display_hours, Bounds(lower=old_bounds[0], upper=old_bounds[1]))
                self.assertEqual(after.restoration.display_hours, Bounds(lower=new_bounds[0], upper=new_bounds[1]))
                journey = customer_journey(after, before, compare_scenarios(before, after))
                update = next(m for m in journey.messages if m.state == 'estimate_updated')
                self.assertTrue(update.available)
                self.assertIn(f'from {old_bounds[0]:g}–{old_bounds[1]:g} to {new_bounds[0]:g}–{new_bounds[1]:g}', update.body)
                self.assertIn('elapsed hours', update.body)
                self.assertIn('conditional', update.body)
                self.assertNotRegex(update.body.lower(), r'\b(sooner|later)\b')
                self.assertEqual(journey.selected_state, 'estimate_updated')

    def test_range_availability_transitions_never_imply_a_direction(self):
        for before, after in (('clear', 'clear'), ('clear', 'blocked'),
                              ('blocked', 'clear'), ('blocked', 'blocked')):
            with self.subTest(before=before, after=after):
                journey = self.transition(before, after)
                message = next(m for m in journey.messages if m.state == 'estimate_updated')
                self.assertNotRegex(message.body.lower(), r'\b(sooner|later)\b')
                self.assertEqual(message.available, before != after)
                if before == after:
                    self.assertIn('No estimate change', message.body)
                elif after == 'blocked':
                    self.assertIn('Pending access clearance', message.body)
                    self.assertIn('No finite restoration', message.body)
                    self.assertNotRegex(message.body, r'\d')
                else:
                    self.assertIn('conditional restoration range is available again', message.body)
                    self.assertIn('2.5–12 elapsed hours', message.body)

    def test_api_crew_updates_preserve_numbers_eligibility_and_neutral_comparison(self):
        with TestClient(create_app(lambda: self.context, lambda: None)) as client:
            for access, crew, new_crew, eligible in (('clear', 4, 2, False),
                    ('clear', 2, 4, False), ('restricted', 8, 2, True)):
                with self.subTest(access=access, before=crew, after=new_crew):
                    response = client.post('/api/evaluate', json={'access': access, 'crew_size': new_crew,
                        'scenario_revision': 2, 'previous': {'access': access, 'crew_size': crew, 'scenario_revision': 1}})
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    expected = evaluate(self.context, default_scenario(self.context, access=access,
                        crew_size=new_crew, scenario_revision=2))
                    self.assertEqual(data['result'], expected.model_dump(mode='json'))
                    journey = data['customer_journey']
                    self.assertIs(journey['estimate_update_eligible'], eligible)
                    self.assertEqual(journey['alerts']['suggested_channels'], ['sms', 'app'])
                    message = next(m for m in journey['messages'] if m['state'] == 'estimate_updated')
                    self.assertNotRegex(message['body'].lower(), r'\b(sooner|later)\b')
                    self.assertIn('from ', message['body'])
                    self.assertIn(' to ', message['body'])

    def test_unknown_risk_keeps_restoration_general_and_declared_preparation(self):
        for facts in ({'transformer_mounting': 'Unknown'}, {'historical_circuit_evidence': None}):
            context = replace(self.context, facts=self.context.facts.model_copy(update=facts))
            for access in ('clear', 'restricted', 'blocked'):
                for selections in ((), ('medical', 'accessibility', 'critical_responsibility')):
                    with self.subTest(facts=facts, access=access, selections=selections):
                        result = evaluate(context, default_scenario(context, access=access))
                        original = result.model_dump_json()
                        journey = customer_journey(result, declared_needs=DeclaredNeeds(selections=selections))
                        self.assertEqual(result.model_dump_json(), original)
                        self.assertIsNone(result.risk.band)
                        self.assertIsNone(result.risk.score)
                        self.assertEqual(result.risk.status, 'insufficient_data')
                        self.assertEqual(result.risk.predictive_confidence, 'LOW')
                        self.assertTrue(result.risk.missing_inputs)
                        self.assertEqual(result.restoration, self.results[access].restoration)
                        self.assertIn('Charge phones and power banks.', journey.preparation.actions)
                        self.assertIn('Find flashlights and fresh batteries.', journey.preparation.actions)
                        self.assertTrue(journey.preparation.safety)
                        self.assertIn('Risk evidence is insufficient', journey.preparation.note)
                        self.assertEqual(len(journey.preparation.declared_actions), len(selections))
                        self.assertEqual(journey.preparation.duration_known, access != 'blocked')
                        self.assertIs(journey.alerts.eligible, True if selections else None)
                        self.assertEqual(journey.alerts.priority_needs_declared, bool(selections))
                        self.assertEqual(journey.alerts.suggested_channels,
                                         ('sms', 'app', 'phone_call') if selections else ('app',))
                        text = ' '.join(m.body for m in journey.messages)
                        for band in ('LOW', 'MEDIUM', 'MODERATE', 'HIGH', 'SEVERE', 'None'):
                            self.assertNotIn(f'risk band is {band}', text)
                        self.assertIn('No risk band has been assigned', text)
                        if access == 'blocked':
                            self.assertIsNone(result.restoration.display_hours)
                            self.assertNotIn('elapsed hours', text)
                            self.assertNotIn('longer end of the range', ' '.join(journey.preparation.actions))
                        else:
                            bounds = result.restoration.display_hours
                            self.assertIn(f'{bounds.lower:g}–{bounds.upper:g} elapsed hours', text)

    def test_unknown_risk_alerts_use_only_independent_declaration_and_duration_evidence(self):
        for upper in (0, 3.99, 4, 12, 72, None):
            with self.subTest(upper=upper):
                unknown = _eligibility(None, upper, 'Low')
                self.assertIsNone(unknown.eligible)
                self.assertEqual(unknown.suggested_channels, ('app',))
                self.assertEqual(unknown.timing, {})
                declared = _eligibility(None, upper, 'Low', True)
                self.assertTrue(declared.eligible)
                self.assertIn('declared priority needs', declared.reason)
                self.assertEqual('phone_call' in declared.suggested_channels, upper is None or upper >= 4)

    def test_api_unknown_risk_returns_usable_partial_results_without_internal_errors(self):
        context = replace(self.context, facts=self.context.facts.model_copy(update={'historical_circuit_evidence': None}))
        with TestClient(create_app(lambda: context, lambda: None), raise_server_exceptions=False) as client:
            for access in ('clear', 'blocked'):
                for selections in ([], ['medical', 'accessibility', 'critical_responsibility']):
                    with self.subTest(access=access, selections=selections):
                        response = client.post('/api/evaluate', json={'access': access,
                            'declared_needs': {'selections': selections}})
                        self.assertEqual(response.status_code, 200)
                        data = response.json()
                        expected = evaluate(context, default_scenario(context, access=access))
                        self.assertEqual(data['result'], expected.model_dump(mode='json'))
                        risk = data['result']['risk']
                        self.assertIsNone(risk['band'])
                        self.assertIsNone(risk['score'])
                        self.assertEqual(risk['status'], 'insufficient_data')
                        self.assertEqual(risk['missing_inputs'], ['verified_historical_circuit_context'])
                        self.assertEqual(risk['predictive_confidence'], 'LOW')
                        journey = data['customer_journey']
                        self.assertTrue(journey['preparation']['actions'])
                        self.assertEqual(len(journey['preparation']['declared_actions']), len(selections))
                        self.assertIs(journey['alerts']['eligible'], True if selections else None)
                        self.assertEqual(len(journey['messages']), 4)
                        self.assertEqual(journey['result_id'], data['result']['result_id'])
                        self.assertEqual(response.headers['cache-control'], 'no-store')
                        for private in ('KeyError', 'Traceback', 'analysis_unavailable', self.context.private_premise):
                            self.assertNotIn(private, response.text)

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
