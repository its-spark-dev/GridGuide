"""AEP person-hour semantics, conditional crew model and bounded decision support."""
import asyncio
import io
import json
import unittest
import zipfile
from dataclasses import replace
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from pyproj import Transformer
import shapefile

from backend.api import create_app
from backend.config import RAW
from backend.contracts import Bounds, DeclaredNeeds
from backend.customer import _eligibility, customer_journey
from backend.data import prepare_context, source_hashes, parse_topology
from backend.engine import compare_access, compare_scenarios, default_scenario, evaluate
from backend.explanations import build_context, explain
from backend.impact import prepare_impact
from tests.test_explanations import FakeProvider


class AepModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = source_hashes()
        cls.context = prepare_context()
        cls.base = evaluate(cls.context, default_scenario(cls.context))

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.hashes: raise AssertionError('Source bytes changed')

    def result(self, **changes):
        return evaluate(self.context, default_scenario(self.context, **changes))

    def test_person_hours_are_not_elapsed_hours_and_no_extra_travel(self):
        r = self.base.restoration
        self.assertEqual(r.installation_direct_hours, 1.536)
        self.assertEqual(r.removal_direct_hours, 1.072)
        self.assertEqual(r.direct_labor_hours, 2.608)
        self.assertEqual(r.repair_person_hours, 11.736)
        self.assertEqual(r.total_person_hours, 11.736)
        self.assertEqual(r.raw_hours, Bounds(lower=2.934, upper=11.736))
        self.assertEqual(r.display_hours, Bounds(lower=2.5, upper=12))
        self.assertEqual(r.access_labor_hours, 0)
        self.assertAlmostEqual(sum(s.repair_person_hours for s in r.repair_stages), r.repair_person_hours)
        self.assertIsNone(r.actual_conversion_efficiency)

    def test_crew_2_4_8_changes_only_conditional_elapsed_boundary(self):
        expected = {2: (5.868, 5.5), 4: (2.934, 2.5), 8: (1.467, 1)}
        for people, (low, display_low) in expected.items():
            with self.subTest(people=people):
                a = self.result(crew_size=people)
                self.assertEqual(a, self.result(crew_size=people))
                self.assertEqual(a.restoration.raw_hours, Bounds(lower=low, upper=11.736))
                self.assertEqual(a.restoration.display_hours, Bounds(lower=display_low, upper=12))
                self.assertEqual(a.restoration.total_person_hours, 11.736)
                self.assertEqual(a.risk, self.base.risk)
                self.assertEqual(a.location, self.base.location)
                self.assertEqual(a.restoration.repair_stages, self.base.restoration.repair_stages)
                self.assertIsNone(self.result(crew_size=people, access='blocked').restoration.display_hours)

    def test_access_direct_labor_multiplier_and_crew_conversion(self):
        for people in (2, 4, 8):
            r = self.result(access='restricted', crew_size=people).restoration
            self.assertEqual(r.access_labor_hours, 1)
            self.assertEqual(r.total_person_hours, 16.236)
            self.assertEqual(r.raw_hours, Bounds(lower=16.236/people, upper=16.236))
            self.assertEqual(r.repair_person_hours, 11.736)
        self.assertEqual(self.result(access='restricted').restoration.display_hours, Bounds(lower=4, upper=16.5))

    def test_null_access_effort_is_not_invented_but_repair_effort_stays_known(self):
        r = self.result(access='blocked').restoration
        self.assertIsNone(r.total_person_hours)
        self.assertIsNone(r.raw_hours)
        self.assertEqual(r.repair_person_hours, 11.736)
        self.assertEqual(r.priority.switching_feasibility, 'unavailable')
        self.assertTrue(all(s.release_status == 'conditional_only' for s in r.repair_stages))

    def test_crew_changes_compare_with_correct_causes_and_fixed_effort(self):
        a, b = self.result(crew_size=2), self.result(crew_size=8)
        comparison = compare_scenarios(a, b)
        self.assertEqual(comparison.changed_inputs, ('crew_size',))
        self.assertIn('Repair effort remains 11.736 person-hours', comparison.explanation)
        lower = next(c for c in comparison.changes if c.field.endswith('raw_hours.lower'))
        self.assertEqual(lower.delta, -4.401)
        self.assertIn('crew-size', lower.cause_factor_ids)
        self.assertEqual(next(c.delta for c in comparison.changes if c.field.endswith('total_person_hours')), 0)
        with self.assertRaises(ValueError): compare_access(a, b)
        mixed = compare_scenarios(a, self.result(crew_size=8, access='restricted'))
        self.assertEqual(mixed.changed_inputs, ('access', 'crew_size'))

    def test_invalid_crew_and_declarations_are_rejected_without_echo(self):
        with TestClient(create_app(lambda:self.context, lambda:None)) as client:
            for value in (1, 9, True, 4.5, '4'):
                self.assertEqual(client.post('/api/evaluate', json={'crew_size':value}).status_code,422)
                with self.assertRaises(ValidationError): self.result(crew_size=value)
            for declarations in ({'selections':['inferred-private']}, {'selections':['medical','medical']}, {'selections':[], 'medical_record':'private'}, {'selections':['medical'],'classification':'AEP-specified'}):
                response=client.post('/api/evaluate',json={'declared_needs':declarations})
                self.assertEqual(response.status_code,422)
                self.assertNotIn('private',response.text)

    def test_actual_dependency_counts_and_step_release(self):
        # Independent raw token membership and customer/circuit filtering.
        with zipfile.ZipFile(RAW/'Data1.zip') as z:
            with shapefile.Reader(dbf=io.BytesIO(z.read('Customer_Clip.dbf'))) as reader:
                premises={r['premise_nu'] for r in reader.iterRecords(fields=['premise_nu','circuit_id']) if r['circuit_id']==self.context.assets[0].circuit_id}
        with zipfile.ZipFile(RAW/'matched_upstream.zip') as z:
            rows=[line.split('\t') for line in z.read('matched_upstream.txt').decode().splitlines()]
        tokens={a.alias:f'{a.token.entity}*{a.token.identifier}*{a.token.kind}*{a.token.location_code}' for a in self.context.assets}
        paths=[r[1:] for r in rows if r and r[0] in premises and r[-1]==tokens['circuit-a']]
        fuse=sum(tokens['protective-a'] in p for p in paths)
        transformer=sum(tokens['transformer-a'] in p for p in paths)
        self.assertEqual((len(paths),fuse,transformer),(1563,4,1))
        priority=self.base.restoration.priority
        self.assertEqual((priority.circuit_customer_paths, priority.dependent_customer_paths, priority.paths_outside_declared_damage),(len(paths),fuse,len(paths)-fuse))
        self.assertEqual([s.newly_eligible_customers for s in self.base.restoration.repair_stages],[fuse-transformer,transformer])
        self.assertEqual(priority.recommended_first_task,'fuse-task')
        self.assertIsNone(priority.priority_score)
        self.assertIsNone(priority.affected_critical_facilities)
        self.assertIsNone(priority.arcos_affected_customers)
        self.assertIsNone(priority.sectionalization_restorable_customers)
        self.assertEqual(priority.arcos_asset_match, 'unavailable')
        for item in priority.asset_impacts:
            # Global raw membership BEFORE filtering to a circuit or customer.
            all_members={r[0] for r in rows if tokens[item.node_alias] in r[1:]}
            self.assertEqual(item.topology_path_count,len(all_members))
            self.assertEqual(item.dependent_customers,len(all_members))
            self.assertTrue(all_members <= premises)
            self.assertEqual(item.unresolved_path_count,0)
            self.assertEqual(item.identity_basis,'exact_typed_GIS_and_topology')

    def test_reverse_index_is_asset_centric_preserves_strings_and_all_branches(self):
        lines=['001\ttransformer*01*Distribution*T1\tfuse*1*Fuse*F1\tcircuit*A*Circuit Breaker*A',
               '002\ttransformer*02*Distribution*T2\tfuse*1*Fuse*F1\tcircuit*A*Circuit Breaker*A',
               '003\ttransformer*03*Distribution*T3\tcircuit*A*Circuit Breaker*A',
               '004\ttransformer*04*Distribution*T4\tfuse*2*Fuse*F2\tcircuit*B*Circuit Breaker*B']
        index=parse_topology(lines)
        self.assertEqual(index.premises_by_asset[('fuse','1')],frozenset({'001','002'}))
        self.assertEqual(index.premises_by_asset[('transformer','01')],frozenset({'001'}))
        self.assertIsNone(index.premises_by_asset.get(('fuse','missing')))
        self.assertEqual(index.premises_by_asset,parse_topology(reversed(lines)).premises_by_asset)

    def test_incomplete_reverse_evidence_withholds_whole_impact_not_partial_count(self):
        failed=self.context.impact.asset_impacts[1].model_copy(update={'status':'unavailable','dependent_customers':None,'unresolved_path_count':1,'dependency_classification':'unavailable'})
        impact=replace(self.context.impact,asset_impacts=(self.context.impact.asset_impacts[0],failed))
        context=replace(self.context,impact=impact)
        result=evaluate(context,default_scenario(context))
        self.assertIsNone(result.restoration.priority.dependent_customer_paths)
        self.assertIsNone(result.restoration.priority.paths_outside_declared_damage)
        self.assertTrue(all(s.newly_eligible_customers is None for s in result.restoration.repair_stages))
        self.assertIn('withheld',result.restoration.priority.reasoning)

    def test_reverse_gis_join_does_not_silently_drop_unmatched_premise(self):
        with zipfile.ZipFile(RAW/'matched_upstream.zip') as z:
            lines=z.read('matched_upstream.txt').decode().splitlines()
        golden=next(line for line in lines if line.split('\t')[0]==self.context.private_premise)
        # Explicit test-only unmatched premise; no source files are altered.
        index=parse_topology(lines+['synthetic-unmatched\t'+golden.split('\t',1)[1]])
        impact=prepare_impact(RAW,index,self.context.assets)
        fuse=next(i for i in impact.asset_impacts if i.node_alias=='protective-a')
        self.assertEqual(fuse.topology_path_count,5)
        self.assertEqual(fuse.unresolved_path_count,1)
        self.assertEqual(fuse.dependency_classification,'unavailable')
        self.assertIsNone(fuse.dependent_customers)

    def test_critical_facilities_are_supplied_3857_points_not_inferred_connections(self):
        transformer=self.context.assets[0]
        with zipfile.ZipFile(RAW/'Data1.zip') as z:
            with shapefile.Reader(shp=io.BytesIO(z.read('Primary_ExportFeatures.shp')),shx=io.BytesIO(z.read('Primary_ExportFeatures.shx')),dbf=io.BytesIO(z.read('Primary_ExportFeatures.dbf'))) as r:
                boxes=[r.shape(i).bbox for i,row in enumerate(r.iterRecords(fields=['circuit_id','aep_circui','aep_statio'])) if (row['circuit_id'],row['aep_circui'],row['aep_statio'])==(transformer.circuit_id,transformer.circuit_alias,transformer.station_alias)]
            extent=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
            convert=Transformer.from_crs(3857,4326,always_xy=True)
            for f in self.base.restoration.priority.facilities:
                with shapefile.Reader(shp=io.BytesIO(z.read(f.source_layer+'.shp')),shx=io.BytesIO(z.read(f.source_layer+'.shx')),dbf=io.BytesIO(z.read(f.source_layer+'.dbf'))) as r:
                    points=[convert.transform(*s.points[0][:2]) for s in r.iterShapes()]
                self.assertEqual(f.regional_features,len(points))
                self.assertEqual(f.within_primary_extent,sum(extent[0]<=x<=extent[2] and extent[1]<=y<=extent[3] for x,y in points))
        self.assertEqual([f.within_primary_extent for f in self.base.restoration.priority.facilities],[0,1,0])
        self.assertIn('Confirm their electrical supply',self.base.restoration.priority.criticality_action)
        self.assertNotIn('position',self.base.restoration.priority.model_dump_json())

    def test_declarations_are_explicit_optional_and_do_not_change_numerical_result(self):
        with TestClient(create_app(lambda:self.context,lambda:None)) as client:
            baseline=client.post('/api/evaluate',json={}).json()
            self.assertEqual(baseline['customer_journey']['declared_needs']['selections'],[])
            for need in ('medical','accessibility','critical_responsibility'):
                data=client.post('/api/evaluate',json={'declared_needs':{'selections':[need]}}).json()
                self.assertEqual(data['result'],baseline['result'])
                journey=data['customer_journey']
                self.assertTrue(journey['alerts']['priority_needs_declared'])
                self.assertEqual(len(journey['preparation']['declared_actions']),1)
                self.assertIn('phone_call',journey['alerts']['suggested_channels'])
                self.assertIn('No contact or dispatch',journey['alerts']['escalation_guidance'])
            cleared=client.post('/api/evaluate',json={}).json()
            self.assertEqual(cleared,baseline)

    def test_blocked_declared_needs_keep_unknown_duration_and_support_guidance(self):
        journey=customer_journey(self.result(access='blocked'),declared_needs=DeclaredNeeds(selections=('medical','accessibility')))
        self.assertFalse(journey.preparation.duration_known)
        self.assertEqual(len(journey.preparation.declared_actions),2)
        self.assertIn('phone_call',journey.alerts.suggested_channels)
        self.assertTrue(_eligibility('Low',None,'Low',True).eligible)
        self.assertNotIn('on file',' '.join(journey.preparation.declared_actions))

    def test_declared_needs_never_reach_any_provider_context(self):
        baseline=build_context(self.base,customer_journey(self.base))
        for need in ('medical','accessibility','critical_responsibility'):
            personalized=customer_journey(self.base,declared_needs=DeclaredNeeds(selections=(need,)))
            context=build_context(self.base,personalized)
            self.assertEqual(context,baseline)
            provider=FakeProvider()
            response=asyncio.run(explain(context,'What should I prepare for?',provider))
            self.assertEqual(response.mode,'ai_assisted')
            for action in personalized.preparation.declared_actions:
                self.assertNotIn(action,context.model_dump_json())

    def test_elapsed_alert_threshold_does_not_use_person_hours(self):
        a=self.result(crew_size=8,access='restricted')
        b=self.result(crew_size=2,access='restricted')
        self.assertEqual(a.restoration.total_person_hours,b.restoration.total_person_hours)
        self.assertTrue(customer_journey(b,a,compare_scenarios(a,b)).estimate_update_eligible) # elapsed lower moves 6.0885
        self.assertFalse(customer_journey(self.result(access='restricted'),self.base,compare_scenarios(self.base,self.result(access='restricted'))).estimate_update_eligible)

    def test_ai_distinguishes_effort_duration_and_unknown_switching(self):
        context=build_context(self.base,customer_journey(self.base))
        for question in ('How is repair effort calculated?','Why is restoration 2.5–12 hours?'):
            response=asyncio.run(explain(context,question,FakeProvider()))
            text=response.answer+' '.join(f.text for f in response.supporting_factors)
            self.assertIn('11.736',text)
            self.assertIn('person-hours',text)
            self.assertIn('elapsed',text)
        sequence=asyncio.run(explain(context,'Why this repair sequence?',FakeProvider()))
        self.assertIn('unavailable',' '.join(f.text for f in sequence.supporting_factors))
        bad=json.dumps({'result_id':context.result_id,'intent':'labor','supporting_refs':['labor-allowance'],'answer':'Repair effort is 1 person-hour.'})
        self.assertEqual(asyncio.run(explain(context,'How is repair effort calculated?',FakeProvider(bad))).mode,'standard')

    def test_api_previous_crew_size_and_explanation_binding(self):
        with TestClient(create_app(lambda:self.context,lambda:FakeProvider())) as client:
            body={'crew_size':8,'scenario_revision':2,'previous':{'access':'clear','crew_size':2,'scenario_revision':1}}
            data=client.post('/api/evaluate',json=body).json()
            self.assertEqual(data['comparison']['changed_inputs'],['crew_size'])
            request={**body,'result_id':data['result']['result_id'],'previous_result_id':data['comparison']['before_result_id'],'question':'Why did my estimate change?'}
            self.assertEqual(client.post('/api/explain',json=request).json()['mode'],'ai_assisted')
            self.assertEqual(client.post('/api/explain',json={**request,'crew_size':4}).status_code,409)

    def test_every_model_rule_has_one_evidence_class_and_unknowns_stay_null(self):
        classes={'AEP-specified','source-derived','scenario assumption','prototype policy','user-declared','unavailable'}
        for item in (*self.base.assumptions,*self.base.risk.factors,*self.base.restoration.factors):
            self.assertIn(item.classification,classes)
        for rule in self.base.assumptions:
            if rule.classification=='unavailable': self.assertIsNone(rule.value)
        self.assertEqual(next(a.classification for a in self.base.assumptions if a.id=='elapsed-envelope'),'prototype policy')

    def test_missing_facility_extent_is_unknown_not_zero(self):
        impact = replace(self.context.impact, facilities=tuple(f.model_copy(update={'within_primary_extent':None}) for f in self.context.impact.facilities))
        context = replace(self.context, impact=impact)
        result = evaluate(context, default_scenario(context))
        self.assertIn('counts within the primary-line extent are unavailable', result.restoration.priority.criticality_action)
        self.assertIsNone(result.restoration.priority.affected_critical_facilities)


if __name__=='__main__': unittest.main()
