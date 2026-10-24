"""Real-source map identity/privacy plus synthetic transformation/failure cases."""
from dataclasses import replace
import json
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from pyproj import Transformer
import shapefile

from backend.api import create_app
from backend.config import GOLDEN_CUSTOMER_RECORD, RAW
from backend.contracts import GeographicAsset
from backend.data import CheckpointError, layer, point_wgs84, prepare_context, public_point, source_hashes
from backend.geography import generalized_line_parts, prepare_map


class GeographyTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = source_hashes()
        cls.context = prepare_context()
        cls.map = prepare_map(cls.context)

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.before:
            raise AssertionError('Map tests changed raw data')

    def test_golden_point_identities_and_missing_terminal(self):
        assets = self.map.assets
        self.assertEqual([a.kind for a in assets], ['customer', 'transformer', 'fuse', 'circuit_terminal'])
        self.assertEqual(assets[0].position, public_point(self.context.private_customer_point))
        for public, private in zip(assets[1:], self.context.assets):
            self.assertEqual(public.position, public_point(private.point) if private.point else None)
        self.assertEqual(assets[0].position, assets[1].position)  # No fake visual offset.
        self.assertIsNone(assets[-1].position)
        self.assertIsNone(assets[-1].source_layer)
        self.assertEqual(assets[-1].geometry_status, 'unavailable')
        self.assertEqual(len([a for a in assets if a.position]), 3)

    def test_actual_source_geometry_and_axis_order(self):
        with layer(RAW, 'Data1.zip', 'Customer_Clip', geometry=True) as (reader, archive):
            point = point_wgs84(reader, archive, 'Customer_Clip', GOLDEN_CUSTOMER_RECORD-1)
        self.assertEqual(public_point(point), self.map.assets[0].position)
        self.assertTrue(-81 < point[0] < -79 and 36 < point[1] < 38)
        self.assertEqual(self.map.crs, 'EPSG:4326')

    def test_primary_lines_match_exact_circuit_not_nearest_geometry(self):
        lines = self.map.primary_lines
        self.assertEqual(lines.status, 'available')
        self.assertEqual(lines.source_segment_count, 1746)
        self.assertEqual(len(lines.paths), 165)
        self.assertEqual(lines.omitted_collapsed_parts, 1581)
        self.assertFalse(lines.topology_verified)
        with layer(RAW, 'Data1.zip', 'Primary_ExportFeatures', geometry=True) as (reader, _):
            expected = []
            target = self.context.assets[0]
            identity = Transformer.from_crs(4326, 4326, always_xy=True)
            for index, record in enumerate(reader.iterRecords(fields=['circuit_id', 'aep_circui', 'aep_statio'])):
                if record['circuit_id'] == target.circuit_id and record['aep_circui'] == target.circuit_alias and record['aep_statio'] == target.station_alias:
                    parts, _ = generalized_line_parts(reader.shape(index), identity)
                    expected.extend(parts)
        self.assertEqual(tuple(expected), lines.paths)

    def test_mercator_transformation_and_multipart_boundaries(self):
        to_meters = Transformer.from_crs(4326, 3857, always_xy=True)
        source = [(-80.071,37.191),(-80.051,37.211),(-80.101,37.221),(-80.091,37.241)]
        shape = shapefile.Shape(shapeType=shapefile.POLYLINE,
                               points=[to_meters.transform(*point) for point in source], parts=[0,2])
        paths, omitted = generalized_line_parts(shape, Transformer.from_crs(3857,4326,always_xy=True))
        self.assertEqual(paths, ((public_point(source[0]), public_point(source[1])),(public_point(source[2]), public_point(source[3]))))
        self.assertEqual(omitted,0)
        self.assertEqual(len(paths),2)  # Never join disconnected source parts.

    def test_collapsed_or_invalid_geometry_never_becomes_fake_line(self):
        shape = shapefile.Shape(shapeType=shapefile.POLYLINE,
                               points=[(-80.071,37.191),(-80.072,37.192)], parts=[0])
        transform=Transformer.from_crs(4326,4326,always_xy=True)
        self.assertEqual(generalized_line_parts(shape,transform),((),1))
        shape.points=[(float('nan'),37),(-80,37)]
        with self.assertRaises(CheckpointError):
            generalized_line_parts(shape,transform)
        shape.shapeType=shapefile.POINT
        with self.assertRaises(CheckpointError):
            generalized_line_parts(shape,transform)

    def test_missing_equipment_point_remains_null(self):
        assets = list(self.context.location.upstream_assets)
        assets[0] = assets[0].model_copy(update={'map_position':None})
        context=replace(self.context,location=self.context.location.model_copy(update={'upstream_assets':tuple(assets)}))
        with patch('backend.geography.primary_context',return_value=self.map.primary_lines):
            result=prepare_map(context)
        self.assertIsNone(result.assets[1].position)
        self.assertEqual(result.assets[1].geometry_status,'unavailable')
        terminal=self.map.assets[-1].model_dump()
        terminal.update(position=self.map.assets[0].position,geometry_status='verified_generalized')
        with self.assertRaises(ValidationError):
            GeographicAsset.model_validate(terminal)

    def test_ambiguous_circuit_withholds_lines_but_keeps_points(self):
        with patch('backend.geography.validate_crosswalk', side_effect=CheckpointError('ambiguous_circuit','Ambiguous circuit')):
            result=prepare_map(self.context)
        self.assertEqual(result.primary_lines.status,'unavailable')
        self.assertEqual(result.primary_lines.paths,())
        self.assertEqual(result.assets,self.map.assets)

    def test_public_map_is_allowlisted_and_generalized(self):
        payload=self.map.model_dump(mode='json')
        forbidden={'premise_nu','private_premise','id','circuit_id','aep_circui','aep_statio','critical_c','address','road_name','anno_strin','location_n'}
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for child in value.values(): inspect(child)
            elif isinstance(value,list):
                for child in value: inspect(child)
        inspect(payload)
        serialized=json.dumps(payload)
        for value in (self.context.private_premise,self.context.private_customer_id,*[a.token.identifier for a in self.context.assets]):
            self.assertNotIn(json.dumps(value),serialized)
        points=[a.position for a in self.map.assets if a.position]+[p for path in self.map.primary_lines.paths for p in path]
        for point in points:
            self.assertEqual(public_point((point.longitude,point.latitude)),point)
        for point in [self.context.private_customer_point,*[a.point for a in self.context.assets if a.point]]:
            self.assertNotIn(str(point[0]),serialized)
            self.assertNotIn(str(point[1]),serialized)
        self.assertLess(len(serialized),150000)

    def test_api_map_cached_and_source_failure_isolated(self):
        with patch('backend.api.prepare_map',return_value=self.map) as loader:
            with TestClient(create_app(lambda:self.context)) as client:
                for _ in range(2):
                    response=client.get('/api/map')
                    self.assertEqual(response.status_code,200)
                    self.assertEqual(response.json(),self.map.model_dump(mode='json'))
                loader.assert_called_once_with(self.context)
                response=client.get('/api/map?location_alias=private-value')
                self.assertEqual(response.status_code,404)
                self.assertNotIn('private-value',response.text)
                schema=client.get('/openapi.json').json()
                self.assertIn('/api/map',schema['paths'])
                self.assertIn('GeographicMap',schema['components']['schemas'])
        with patch('backend.api.prepare_map',side_effect=RuntimeError('private-source-error')):
            with TestClient(create_app(lambda:self.context)) as client:
                self.assertEqual(client.get('/api/map').status_code,503)
                self.assertNotIn('private-source-error',client.get('/api/map').text)
                self.assertEqual(client.post('/api/evaluate',json={'access':'clear'}).status_code,200)
