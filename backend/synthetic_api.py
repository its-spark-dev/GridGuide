"""Phase 1 read-only synthetic boundary. Numerical endpoints await later gates."""
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .contracts import ScenarioCatalogResponse, ScenarioDefinitionResponse, SyntheticHealth
from .scenarios import SyntheticContext, prepare_synthetic


def create_synthetic_app(loader: Callable[[], SyntheticContext] = prepare_synthetic) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        app.state.synthetic = loader()  # Fail closed; never fall back to challenge data.
        yield
        del app.state.synthetic

    app = FastAPI(title="GridGuide synthetic catalog", version="1.1.0-phase1", lifespan=lifespan)

    @app.middleware("http")
    async def no_stale_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_input", "message": "Choose an available fictional scenario."}})

    @app.exception_handler(Exception)
    async def unavailable(request, error):
        return JSONResponse(status_code=500, content={"error": {"code": "catalog_unavailable", "message": "The fictional catalog is unavailable."}})

    @app.get("/api/health", response_model=SyntheticHealth, include_in_schema=False)
    @app.get("/api/v2/health", response_model=SyntheticHealth)
    def health(request: Request):
        context = request.app.state.synthetic
        return SyntheticHealth(ready=True, catalog_sha256=context.catalog_sha256)

    @app.get("/api/v2/scenarios", response_model=ScenarioCatalogResponse)
    def scenarios(request: Request):
        return request.app.state.synthetic.catalog()

    @app.get("/api/v2/scenarios/{scenario_id}", response_model=ScenarioDefinitionResponse)
    def scenario(scenario_id: str, request: Request):
        context = request.app.state.synthetic
        if scenario_id not in context.scenarios:
            return JSONResponse(status_code=404, content={"error": {"code": "unknown_scenario", "message": "Choose an available fictional scenario."}})
        return context.definition(scenario_id)

    return app
