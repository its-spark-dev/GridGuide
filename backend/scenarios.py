"""Immutable fictional catalog adapter. No imports of challenge preparation or AI."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .contracts import (ScenarioCatalogResponse, ScenarioDefinitionResponse,
                        ScenarioMetadata, ScenarioSummary, SyntheticCatalog, SyntheticScenario)

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "catalog.json"
CATALOG_SHA256 = "907aa9493c9650a875eafeb7fedd67267d320d9f0ba563407ca17851a6c5dee9"


class SyntheticCatalogError(ValueError):
    """Safe startup error; source contents and filenames are never echoed."""


@dataclass(frozen=True)
class SyntheticContext:
    catalog_sha256: str
    scenarios: Mapping[str, SyntheticScenario]
    metadata: Mapping[str, ScenarioMetadata]

    def definition(self, scenario_id: str) -> ScenarioDefinitionResponse:
        scenario = self.scenarios[scenario_id]
        missing = []
        if scenario.topology_status == "partial_by_construction":
            missing.append("complete_dependency_evidence")
        if any(r.repair_person_hours is None for r in scenario.repairs):
            missing.append("repair_effort")
        if any(r.access == "blocked" for r in scenario.repairs):
            missing.append("access_clearance_time")
        return ScenarioDefinitionResponse(
            metadata=self.metadata[scenario_id], definition=scenario,
            complete_dependency_customer_count=None if scenario.topology_status == "partial_by_construction" else len(scenario.customer_paths),
            missing_inputs=tuple(missing))

    def catalog(self) -> ScenarioCatalogResponse:
        summaries = []
        for scenario_id, scenario in self.scenarios.items():
            result = self.definition(scenario_id)
            summaries.append(ScenarioSummary(metadata=result.metadata, label=scenario.label,
                purpose=scenario.purpose, topology_status=scenario.topology_status,
                complete_dependency_customer_count=result.complete_dependency_customer_count,
                missing_inputs=result.missing_inputs))
        return ScenarioCatalogResponse(catalog_sha256=self.catalog_sha256, scenarios=tuple(summaries))


def prepare_synthetic(path: Path = CATALOG_PATH) -> SyntheticContext:
    try:
        if path.is_symlink() or path.stat().st_size > 1_000_000:
            raise ValueError("Invalid catalog file")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != CATALOG_SHA256:
            raise ValueError("Catalog pin mismatch")
        catalog = SyntheticCatalog.model_validate_json(payload)
    except (OSError, ValueError):
        raise SyntheticCatalogError("Synthetic catalog failed integrity or schema validation; startup is withheld.") from None
    scenarios = {s.id: s for s in catalog.scenarios}
    metadata = {}
    for scenario in catalog.scenarios:
        canonical = json.dumps({"definition": scenario.model_dump(mode="json"), "catalog_version": catalog.version,
                                "generator_version": catalog.generator_version, "catalog_sha256": CATALOG_SHA256},
                               sort_keys=True, separators=(",", ":"), allow_nan=False)
        metadata[scenario.id] = ScenarioMetadata(scenario_id=scenario.id, scenario_revision=scenario.revision,
                                                 input_fingerprint=hashlib.sha256(canonical.encode()).hexdigest())
    return SyntheticContext(CATALOG_SHA256, MappingProxyType(scenarios), MappingProxyType(metadata))
