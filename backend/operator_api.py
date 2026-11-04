"""Opt-in composition: one synthetic FastAPI service with bounded operator routes.

The original catalog-only distribution and challenge app stay unchanged.
"""
import threading
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .synthetic_api import create_synthetic_app
from .review_contracts import CompareRequest, OperatorComparison, ReviewRequest, ReviewExport, ReviewCatalog
from . import review


def create_operator_app():
    app=create_synthetic_app()
    app.title='GridGuide fictional operator review'
    app.version='1.1.0-phase7'
    gate=threading.BoundedSemaphore(2)

    @app.middleware('http')
    async def bounded_body(request, call_next):
        if request.url.path.startswith('/api/v2/operator/'):
            size=0
            chunks=[]
            async for chunk in request.stream():
                size+=len(chunk)
                chunks.append(chunk)
                if size>32768:return JSONResponse(status_code=413,content={'error':{'message':'Review request is too large.'}})
            # Restore the bounded body for Starlette's downstream request wrapper.
            request._body=b''.join(chunks)
        return await call_next(request)

    def invoke(fn,*args):
        if not gate.acquire(blocking=False):raise HTTPException(503,'Review capacity unavailable; retry.')
        try:return fn(*args)
        except Exception:raise HTTPException(422,'Review could not be validated. Refresh the scenario and check constraints.') from None
        finally:gate.release()

    @app.get('/api/v2/operator/scenarios',response_model=ReviewCatalog)
    def scenarios():return invoke(review.catalog)

    @app.post('/api/v2/operator/compare',response_model=OperatorComparison)
    def compare(body:CompareRequest):return invoke(review.compare,body)

    @app.post('/api/v2/operator/review-export',response_model=ReviewExport)
    def export(body:ReviewRequest):return invoke(review.export_review,body)
    return app

app=create_operator_app()
