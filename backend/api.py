"""Thin HTTP boundary around the unchanged checkpoint engine."""
from contextlib import asynccontextmanager
from typing import Annotated, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, model_validator

from .config import GOLDEN_ALIAS, RISK_VERSION, RESTORATION_VERSION, SNAPSHOT
from .contracts import Access, CrewSize, DeclaredNeeds, Comparison, Contract, CustomerJourney, Evaluation, ExplanationResponse, GeographicMap, Location
from .ai_provider import configured_provider
from .customer import customer_journey
from .data import CheckpointError, PreparedContext, prepare_context
from .engine import compare_scenarios, default_scenario, evaluate
from .geography import prepare_map
from .explanations import ExplanationService, build_context

Revision = Annotated[int, Field(strict=True, ge=1)]


class PreviousSelection(Contract):
    access: Access
    crew_size: CrewSize = 4
    scenario_revision: Revision


class AnalysisRequest(Contract):
    location_alias: str = GOLDEN_ALIAS
    access: Access = "clear"
    crew_size: CrewSize = 4
    declared_needs: DeclaredNeeds = DeclaredNeeds()
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


class ExplanationRequest(AnalysisRequest):
    result_id: Annotated[str, Field(min_length=1, max_length=128)]
    previous_result_id: Annotated[str, Field(min_length=1, max_length=128)] | None = None
    question: Annotated[str, Field(min_length=1, max_length=240)]


def analyze_selection(context: PreparedContext, body: AnalysisRequest) -> AnalysisResponse:
    result = evaluate(context, default_scenario(context, location_alias=body.location_alias,
        access=body.access, crew_size=body.crew_size, scenario_revision=body.scenario_revision))
    comparison = None
    previous = None
    if body.previous:
        previous = evaluate(context, default_scenario(context, location_alias=body.location_alias,
            access=body.previous.access, crew_size=body.previous.crew_size, scenario_revision=body.previous.scenario_revision))
        comparison = compare_scenarios(previous, result)
    return AnalysisResponse(result=result, comparison=comparison, customer_journey=customer_journey(result, previous, comparison, body.declared_needs))


def create_app(context_loader: Callable[[], PreparedContext] = prepare_context,
               provider_loader: Callable = configured_provider) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Verify source pins and joins once. Failure prevents readiness entirely.
        app.state.context = context_loader()
        app.state.explanation_provider = provider_loader()
        app.state.explanation_service = ExplanationService(app.state.explanation_provider)
        try:
            app.state.geographic_map = prepare_map(app.state.context)
        except Exception:
            # Optional geography must not prevent the verified analysis from starting.
            # The map endpoint returns a safe unavailable response without private details.
            app.state.geographic_map = None
        yield
        del app.state.geographic_map
        del app.state.context
        del app.state.explanation_provider
        del app.state.explanation_service

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

    @app.get("/api/map", response_model=GeographicMap)
    def geographic_map(request: Request, location_alias: str = GOLDEN_ALIAS):
        if location_alias != GOLDEN_ALIAS:
            raise CheckpointError("unsupported_location", "Only the audited demo location is supported.")
        if request.app.state.geographic_map is None:
            return JSONResponse(status_code=503, content={"error": {
                "code": "map_unavailable", "message": "Geographic context is unavailable. The dependency schematic and analysis remain available."}})
        return request.app.state.geographic_map

    @app.post("/api/evaluate", response_model=AnalysisResponse)
    def analysis(body: AnalysisRequest, request: Request):
        return analyze_selection(request.app.state.context, body)

    @app.post("/api/explain", response_model=ExplanationResponse)
    async def explanation(body: ExplanationRequest, request: Request):
        # Recompute from validated selections. Never accept client-supplied facts.
        analysis = analyze_selection(request.app.state.context, body)
        previous_id = analysis.comparison.before_result_id if analysis.comparison else None
        if analysis.result.result_id != body.result_id or previous_id != body.previous_result_id:
            return JSONResponse(status_code=409, content={"error": {
                "code": "stale_result", "message": "Reload the current scenario before asking for an explanation."}})
        context = build_context(analysis.result, analysis.customer_journey, analysis.comparison)
        return await request.app.state.explanation_service.answer(context, body.question)

    return app


app = create_app()
