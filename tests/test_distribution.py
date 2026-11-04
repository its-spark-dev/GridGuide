"""Actual public package validation and HTTP boundary tests."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from backend.public_app import create_public_app
from backend.public_integrity import verify_tree
from scripts.package_demo import build, inspect, ROOT

class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/'frontend/dist-public/.vite/manifest.json').is_file():
            raise RuntimeError('Build public frontend before distribution tests; do not count an absent build as passing')

    def test_reproducible_archive_and_recursive_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);a=d/'a.zip';b=d/'b.zip';build(a);build(b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:z.extractall(d/'extracted')
            verify_tree(d/'extracted')
            self.assertEqual((d/'extracted'/'LICENSE').read_bytes(), (ROOT/'LICENSE').read_bytes())
            (d/'extracted'/'.env').write_text('canary')
            with self.assertRaises(ValueError):verify_tree(d/'extracted')
            with zipfile.ZipFile(a,'a') as z:z.writestr('unexpected.txt','canary')
            with self.assertRaises(ValueError):inspect(a)
            from scripts.verify_frozen_release import verify
            with self.assertRaises(ValueError):verify(a)

    def test_public_routes_security_headers_and_safe_static_scope(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'pkg';a=Path(d)/'pkg.zip';build(a)
            with zipfile.ZipFile(a) as z:z.extractall(root)
            with TestClient(create_public_app(root)) as c:
                self.assertEqual(c.get('/ready').json()['external_ai'],False)
                product=json.loads((ROOT/'frontend/package.json').read_text())['version']
                self.assertEqual(c.get('/ready').json()['product_version'],product)
                self.assertEqual(c.get('/ready').json()['release_status'],'stable')
                home=c.get('/',follow_redirects=False)
                self.assertEqual(home.status_code,200)
                self.assertIn('Your storm outlook',home.text)
                self.assertEqual(home.content,(root/'static/dashboard/index.html').read_bytes())
                self.assertEqual(c.get('/fonts/Barlow-Regular.woff2').status_code,200)
                self.assertEqual(c.get('/fonts/OFL.txt').status_code,200)
                cache=c.get('/preparedness/cache-manifest.json').json()['allowlist']
                self.assertNotIn('/',cache)
                self.assertNotIn('/operator/',cache)
                self.assertNotIn('/dashboard/index.html',cache)
                self.assertTrue(all('/api/' not in key and 'frames.json' not in key and '/fonts/' not in key for key in cache))
                for path in ['/docs','/openapi.json','/.env','/data/synthetic/catalog.json','/backend/public_app.py',
                             '/api/locations','/__test__/worker/1','/preparedness/../../deploy/serve.py','/%2e%2e/.env']:
                    self.assertEqual(c.get(path).status_code,404,path)
                self.assertEqual(c.get('/ready',headers={'host':'evil.invalid/ready'}).status_code,400)
                self.assertEqual(c.get('/preparedness/',headers={'range':'bytes='+'0'*20000+'-'}).status_code,416)
                self.assertEqual(c.post('/api/v2/operator/compare',content='x'*32769).status_code,413)
                self.assertEqual(c.request('_DO_DELETE','/ready').status_code,405)
                bad=c.post('/api/v2/operator/compare',json={'secret':'DO-NOT-ECHO'})
                self.assertNotIn('DO-NOT-ECHO',bad.text)
                for path in ['/preparedness/','/api/v2/operator/scenarios','/missing']:
                    r=c.get(path);self.assertIn("connect-src 'self'",r.headers['content-security-policy'])
                    self.assertEqual(r.headers['x-content-type-options'],'nosniff')
                    self.assertEqual(r.headers['cache-control'],'no-store')

    def test_mode_and_provider_cannot_be_enabled_by_environment(self):
        for key,value in [('GRIDGUIDE_MODE','challenge-local'),('GRIDGUIDE_AI_PROVIDER','gemini')]:
            with patch.dict(os.environ,{key:value}),self.assertRaises(RuntimeError):create_public_app()

    def test_two_calculation_slots_reject_saturation_and_recover_after_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'pkg';archive=Path(d)/'pkg.zip';build(archive)
            with zipfile.ZipFile(archive) as z:z.extractall(root)
            with TestClient(create_public_app(root)) as client:
                scenario=client.get('/api/v2/operator/scenarios').json()['scenarios'][0]
                body={k:scenario[k] for k in ('scenario_id','scenario_fingerprint')}
                entered=threading.Barrier(3);release=threading.Event()
                def delayed(_):
                    entered.wait(timeout=5)
                    if not release.wait(timeout=5):raise RuntimeError('Test did not release calculations')
                    raise ValueError('INTERNAL-DETAIL-MUST-NOT-LEAK')
                with ThreadPoolExecutor(max_workers=2) as pool,patch('backend.review.compare',side_effect=delayed):
                    futures=[pool.submit(client.post,'/api/v2/operator/compare',json=body) for _ in range(2)]
                    try:
                        entered.wait(timeout=5)
                        self.assertEqual(client.post('/api/v2/operator/compare',json=body).status_code,503)
                    finally:release.set()
                    for future in futures:
                        result=future.result(timeout=5)
                        self.assertEqual(result.status_code,422)
                        self.assertNotIn('INTERNAL-DETAIL',result.text)
                self.assertEqual(client.post('/api/v2/operator/compare',json=body).status_code,200)
