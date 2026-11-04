"""Source-free one-origin composition. No challenge or hosted-provider entrypoint."""
import json
import os
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .operator_api import create_operator_app
from . import review

ROOT = Path(__file__).resolve().parents[1]
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'; object-src 'none'"


def create_public_app(root: Path = ROOT):
    if os.environ.get('GRIDGUIDE_MODE', 'synthetic-demo') != 'synthetic-demo':
        raise RuntimeError('Public distribution requires synthetic-demo mode')
    if os.environ.get('GRIDGUIDE_AI_PROVIDER', 'none') != 'none':
        raise RuntimeError('External AI is disabled in the public distribution')
    app = create_operator_app()
    app.title = 'GridGuide fictional demonstration'
    app.version = '1.1.0'
    app.add_middleware(TrustedHostMiddleware,
        allowed_hosts=os.environ.get('GRIDGUIDE_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(','))
    # No interactive Swagger/ReDoc third-party scripts or schema browsing endpoint.
    app.router.routes[:] = [r for r in app.router.routes if r.path not in ('/docs','/redoc','/openapi.json','/docs/oauth2-redirect')]
    manifest_path = root/'PUBLIC_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    static = {name.removeprefix('static/'): root/name for name in manifest['files'] if name.startswith('static/')}
    from .public_integrity import verify_tree
    verify_tree(root)
    review.catalog()  # Pin the operator input as well as the G1 lifespan catalog.

    @app.middleware('http')
    async def boundaries(request, call_next):
        async def response():
            if not request.scope['path'].startswith('/'):
                return JSONResponse({'error': 'Invalid path'}, status_code=400)
            if request.method not in ('GET', 'HEAD', 'POST'):
                return JSONResponse({'error': 'Method not allowed'}, status_code=405)
            # These small immutable demo files never require partial content.
            if 'range' in request.headers:
                return JSONResponse({'error': 'Range requests unsupported'}, status_code=416)
            # Limit every body before JSON parsing, including unknown routes and chunked requests.
            chunks, size = [], 0
            async for part in request.stream():
                size += len(part)
                if size > 32768:
                    return JSONResponse({'error': 'Request too large'}, status_code=413)
                chunks.append(part)
            request._body = b''.join(chunks)
            return await call_next(request)
        result = await response()
        result.headers.update({'Content-Security-Policy': CSP, 'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
            'Permissions-Policy': 'geolocation=(), camera=(), microphone=()', 'Cache-Control': 'no-store'})
        return result

    @app.get('/ready')
    def ready():
        return {'ready': True, 'mode': 'synthetic-demo', 'version': 'public-package-v1',
                'product_version': app.version, 'release_status': 'release-candidate',
                'external_ai': False, 'interactive_solver': False}

    @app.get('/')
    def home():
        return RedirectResponse('/preparedness/', status_code=307)

    @app.get('/{path:path}', include_in_schema=False)
    def asset(path: str):
        if path.endswith('/'): path += 'index.html'
        target = static.get(path)
        if target is None or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
            raise HTTPException(404, 'Not found')
        return FileResponse(target)
    return app
