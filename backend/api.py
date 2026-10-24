"""Thin HTTP boundary around the unchanged checkpoint engine."""
from contextlib import asynccontextmanager
from typing import Annotated, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, model_validator

from .config import GOLDEN_ALIAS, RISK_VERSION, RESTORATION_VERSION, SNAPSHOT
from .contracts import Access, Comparison, Contract, CustomerJourney, Evaluation, Location
from .customer import customer_journey
from .data import CheckpointError, PreparedContext, prepare_context
from .engine import compare_access, default_scenario, evaluate

Revision = Annotated[int, Field(strict=True, ge=1)]


class PreviousSelection(Contract):
    access: Access
    scenario_revision: Revision


class AnalysisRequest(Contract):
    location_alias: str = GOLDEN_ALIAS
    access: Access = "clear"
    scenario_revision: Revision = 1
    previous: PreviousSelection | None = None

    @model_validator(mode="after")
    def ordered_revisions(self):
        if self.previous and self.previous.scenario_revision >= self.scenario_revision:
            raise ValueError("Previous revision must precede the requested revision")
        return self


class AnalysisResponse(Contract):
    result: Evaluation
    comparison: Comparison | None = None
    customer_journey: CustomerJourney


def create_app(context_loader: Callable[[], PreparedContext] = prepare_context) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Verify source pins and joins once. Failure prevents readiness entirely.
        app.state.context = context_loader()
        yield
        del app.state.context

    app = FastAPI(title="GridGuide", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def no_stale_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError):
        # Do not return Pydantic's input echo or arbitrary submitted private fields.
        return JSONResponse(status_code=422, content={"error": {
            "code": "invalid_input", "message": "Choose a supported location and access condition with a valid revision."}})

    @app.exception_handler(CheckpointError)
    async def checkpoint_error(request: Request, error: CheckpointError):
        return JSONResponse(status_code=404 if error.code == "unsupported_location" else 422,
            content={"error": {"code": error.code, "message": str(error)}})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        return JSONResponse(status_code=500, content={"error": {
            "code": "analysis_unavailable", "message": "Analysis could not be completed. Please try again."}})

    @app.get("/api/health")
    def health(request: Request):
        # Accessing context ensures the lifespan preparation ran successfully.
        return {"ready": bool(request.app.state.context), "data_snapshot": SNAPSHOT,
                "model_versions": {"risk": RISK_VERSION, "restoration": RESTORATION_VERSION}}

    @app.get("/api/locations", response_model=tuple[Location, ...])
    def locations(request: Request):
        return (request.app.state.context.location,)

    @app.post("/api/evaluate", response_model=AnalysisResponse)
    def analysis(body: AnalysisRequest, request: Request):
        context = request.app.state.context
        result = evaluate(context, default_scenario(context, location_alias=body.location_alias,
            access=body.access, scenario_revision=body.scenario_revision))
        comparison = None
        previous = None
        if body.previous:
            previous = evaluate(context, default_scenario(context, location_alias=body.location_alias,
                access=body.previous.access, scenario_revision=body.previous.scenario_revision))
            comparison = compare_access(previous, result)
        return AnalysisResponse(result=result, comparison=comparison, customer_journey=customer_journey(result, previous, comparison))

    return app


app = create_app()
