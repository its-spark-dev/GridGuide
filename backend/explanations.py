"""Grounded reference selection. The engine and reviewed copy own every claim."""
import asyncio
import json
import hashlib
import time
from collections import OrderedDict
from typing import Protocol

from pydantic import ValidationError

from .contracts import (Comparison, CustomerJourney, Evaluation, ExplanationClause,
                        ExplanationContext, ExplanationIntent, ExplanationResponse,
                        ModelSelection)

DATASET_NOTE = "Anonymized demo location in Virginia, using AEP-provided challenge data; no live utility connection."
UNCERTAINTY = ("Predictive confidence is LOW. Risk is an ordinal modeled concern band, not an outage probability. "
               "Restoration is conditional on simulated repairs and access, with provisional labor units; "
               "it is not an official AEP ETR. No alert has been sent.")
PROVIDER_TIMEOUT_SECONDS = 8.0


class ExplanationProvider(Protocol):
    async def select(self, context: ExplanationContext, intent: ExplanationIntent,
                     allowed_refs: tuple[str, ...]) -> str: ...


def build_context(result: Evaluation, journey: CustomerJourney,
                  comparison: Comparison | None = None) -> ExplanationContext:
    if journey.result_id != result.result_id or (comparison and comparison.after_result_id != result.result_id):
        raise ValueError("Explanation context must describe the same validated result")
    clauses = []
    def add(identifier, text, source="modeled"):
        clauses.append(ExplanationClause(id=identifier, text=text, source_type=source))

    risk = result.risk
    restoration = result.restoration
    access = result.simulated_inputs.access
    bounds = restoration.display_hours
    add("risk-summary", f"{risk.band} is an ordinal modeled concern band under this storm scenario, not an outage probability. "
        "It reflects the selected storm concern, transformer mounting and historical circuit evidence. Predictive confidence is LOW."
        if risk.band else "There is not enough verified information to assign a risk band.")
    for factor in risk.factors:
        value = ("present in the historical extract" if factor.value is True else "not found in this extract; coverage is unknown" if factor.value is False else str(factor.value) if factor.value is not None else "unavailable")
        add(f"risk-{factor.id}", f"{factor.label}: {value}.", "verified" if factor.provenance == "source_fact" else "simulated")
    if bounds:
        add("restoration-summary", f"The current provisional modeled range is {bounds.lower:g}–{bounds.upper:g} hours "
            "from when an assigned crew begins its response. It covers the declared replacement work and access conditions, not a clock-time promise.")
    elif restoration.status == "pending_clearance":
        add("restoration-summary", "A modeled restoration range is unavailable. Access must be cleared before a credible modeled range can be provided. "
            "The clearance time is unknown, so GridGuide cannot say when power will be restored.")
    else:
        add("restoration-summary", "A modeled restoration range is unavailable because required resources or information are missing. GridGuide cannot provide a time estimate.")
    add("repair-scope", "Simulated replacement scope: " + "; ".join(f"{work.quantity} × {work.recipe.replace('-', ' ')}" for work in restoration.labor_contributions) + ". These are declared repairs, not observed current damage.", "simulated")
    add("serial-work", "The model sequences repairs along the verified dependency path. Additional crews do not divide this serial repair duration.", "mixed")
    add("labor-allowance", f"The engine applies the workbook's {restoration.indirect_labor_multiplier:g} indirect-work multiplier once. "
        "The upper allowance and reference-crew conversion are disclosed team assumptions.", "mixed")
    if access == "blocked":
        add("access-detail", "Simulated access is blocked. Clearance is a prerequisite with unknown duration, so both restoration bounds stay unavailable.", "simulated")
    elif access == "restricted":
        add("access-detail", f"Simulated restricted access adds work at {restoration.worksite_count} validated repair worksites before repairs can finish.", "mixed")
    else:
        add("access-detail", "Simulated access is clear, so the engine adds no restricted-access work.", "simulated")
    # The engine owns all deltas. No comparison math is repeated here.
    add("comparison-summary", comparison.explanation if comparison else
        "No previous scenario is selected for comparison. Change access to compare with the last completed scenario.")
    topology = ("Customer", *["Distribution transformer" if asset.kind == "Distribution" else asset.kind for asset in result.location.upstream_assets])
    add("topology-summary", "Verified dependency order: " + " → ".join(topology) +
        ". The Circuit Breaker terminal is abstract and has no supplied geometry; this is not live switching status.", "verified")
    add("preparation-summary", journey.preparation.note)
    for index, action in enumerate(journey.preparation.actions):
        add(f"preparation-{index}", action)
    # Safety wording is never authored by the model; the existing guidance section
    # remains authoritative and visible regardless of explanation availability.
    eligibility = "eligible" if journey.alerts.eligible is True else "not eligible" if journey.alerts.eligible is False else "undetermined"
    add("alerts-summary", f"Demo alert eligibility is {eligibility}. {journey.alerts.reason} "
        "These are team preview rules, not utility enrollment. No alert has been sent.")
    return ExplanationContext(result_id=result.result_id, scenario_revision=result.scenario_revision,
        location_label=result.location.label, dataset_note=DATASET_NOTE,
        risk_band=risk.band, risk_confidence=risk.predictive_confidence,
        restoration_status=restoration.status, restoration_bounds=bounds, access=access,
        topology=topology, alert_eligible=journey.alerts.eligible,
        assumptions=tuple(f"{a.description} Assumed value: {a.value}." for a in result.assumptions),
        limitations=(*risk.limitations, *restoration.limitations), clauses=tuple(clauses))


def question_intent(question: str, context: ExplanationContext) -> ExplanationIntent:
    """Curated questions only. Arbitrary user text never reaches the provider."""
    normalized = " ".join(question.lower().replace("’", "'").replace("–", "-").strip().rstrip("?.").split())
    questions = {
        "why is my outage risk high": "risk", "what does high mean": "risk",
        "why did my estimate change": "change", "why did my restoration estimate change": "change",
        "why did my restoration outlook change": "change",
        "what is making restoration take longer": "restoration",
        "what should i prepare for": "preparation",
        "when will my power be restored": "availability",
        "why can't gridguide estimate restoration right now": "availability",
        "how is my location connected": "topology", "am i eligible for demo alerts": "alerts",
    }
    if context.restoration_bounds:
        b = context.restoration_bounds
        questions[f"why is restoration {b.lower:g}-{b.upper:g} hours"] = "restoration"
    return questions.get(normalized, "unsupported")


def explanation_plan(context: ExplanationContext, intent: ExplanationIntent) -> tuple[str, tuple[str, ...]]:
    risk_refs = tuple(c.id for c in context.clauses if c.id.startswith("risk-") and c.id != "risk-summary")
    prep_refs = tuple(c.id for c in context.clauses if c.id.startswith("preparation-") and c.id != "preparation-summary")
    # A blocked change answer must not reintroduce old finite bounds, even if a
    # future comparison template contains them. Current availability always leads.
    plans = {
        "risk": ("risk-summary", risk_refs),
        "restoration": ("restoration-summary", ("access-detail", "repair-scope", "labor-allowance", "serial-work")),
        "availability": ("restoration-summary", ("access-detail", "repair-scope", "serial-work")),
        "change": ("restoration-summary", ("access-detail", "serial-work")) if context.restoration_bounds is None else
                  ("restoration-summary", ("comparison-summary", "access-detail", "serial-work")),
        "preparation": ("preparation-summary", prep_refs),
        "topology": ("topology-summary", ("serial-work",)),
        "alerts": ("alerts-summary", ("preparation-summary",)),
    }
    return plans[intent]


async def explain(context: ExplanationContext, question: str, provider: ExplanationProvider | None) -> ExplanationResponse:
    intent = question_intent(question, context)
    common = dict(result_id=context.result_id, scenario_revision=context.scenario_revision,
                  intent=intent, uncertainty_note=UNCERTAINTY, dataset_note=context.dataset_note)
    if intent == "unsupported":
        return ExplanationResponse(**common, answer="GridGuide does not have enough verified information to answer that question. "
            "Choose a question about this demo's risk, restoration, preparation or grid context.",
            supporting_factors=(), source_type="mixed", mode="unsupported", fallback_reason="unsupported_question")
    lead, allowed = explanation_plan(context, intent)
    references = allowed[:3]
    reason = "not_configured"
    if provider is not None:
        try:
            raw = await asyncio.wait_for(provider.select(context, intent, allowed), timeout=PROVIDER_TIMEOUT_SECONDS)
            if not isinstance(raw, str) or len(raw) > 4096:
                raise ValueError("Invalid model response")
            # Strict decoding rejects duplicate keys rather than silently accepting
            # an overwritten result binding or hidden extra field.
            def unique_keys(pairs):
                obj = {}
                for key, value in pairs:
                    if key in obj: raise ValueError("Duplicate model key")
                    obj[key] = value
                return obj
            selection = ModelSelection.model_validate(json.loads(raw, object_pairs_hook=unique_keys))
            if (selection.result_id != context.result_id or selection.intent != intent or
                len(set(selection.supporting_refs)) != len(selection.supporting_refs) or
                not set(selection.supporting_refs) <= set(allowed)):
                raise ValueError("Unsupported model reference")
            # Comparison causality must never be omitted for a finite change.
            if intent == "change" and "comparison-summary" in allowed and "comparison-summary" not in selection.supporting_refs:
                raise ValueError("Missing comparison reference")
            references = selection.supporting_refs
            reason = None
        except (TimeoutError, asyncio.TimeoutError):
            reason = "timeout"
        except (ValidationError, ValueError, TypeError):
            reason = "invalid_response"
        except Exception:
            # Never expose provider errors, prompts, credentials or raw responses.
            reason = "provider_unavailable"
    catalog = {clause.id: clause for clause in context.clauses}
    selected = tuple(catalog[ref] for ref in references)
    types = {catalog[lead].source_type, *[clause.source_type for clause in selected]}
    return ExplanationResponse(**common, answer=catalog[lead].text, supporting_factors=selected,
        source_type=next(iter(types)) if len(types) == 1 else "mixed",
        mode="standard" if reason else "ai_assisted", fallback_reason=reason)


class ExplanationService:
    """Bounded process-local cache of validated answers; no persistence or raw questions."""
    def __init__(self, provider: ExplanationProvider | None, max_entries: int = 64, ttl: float = 300):
        self.provider, self.max_entries, self.ttl = provider, max_entries, ttl
        self._cache = OrderedDict()

    async def answer(self, context: ExplanationContext, question: str) -> ExplanationResponse:
        intent = question_intent(question, context)
        # Full context includes previous-comparison wording, revision and policy
        # version. Identical current result IDs alone are insufficient for caching.
        key = hashlib.sha256((context.model_dump_json() + intent).encode()).hexdigest()
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.ttl:
            self._cache.move_to_end(key)
            return cached[1]
        self._cache.pop(key, None)
        answer = await explain(context, question, self.provider)
        if answer.mode == "ai_assisted":
            self._cache[key] = (time.monotonic(), answer)
            while len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)
        return answer
