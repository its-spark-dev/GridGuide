"""Versioned evidence register. Metadata discovery is not data-use clearance."""
from dataclasses import asdict, dataclass
import json
from typing import Literal

from backend.config import SOURCE_SHA256, SNAPSHOT
from backend.scenarios import CATALOG_SHA256

REGISTER_VERSION = "phase1-evidence-v1"
REVIEW_DATE = "2026-11-03"


@dataclass(frozen=True)
class SourceFile:
    name: str
    sha256: str | None
    checksum_status: Literal["pinned_local_bytes", "not_acquired"]

    def __post_init__(self):
        if (self.sha256 is None) != (self.checksum_status == "not_acquired"):
            raise ValueError("Unacquired sources cannot have invented checksums")
        if self.sha256 is not None and (len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256)):
            raise ValueError("Invalid SHA-256")


@dataclass(frozen=True)
class DatasetRecord:
    id: str
    version: str
    classification: Literal["source-derived", "scenario assumption", "unavailable"]
    availability: Literal["local_pinned", "metadata_only", "not_provided"]
    sources: tuple[str, ...]
    files: tuple[SourceFile, ...]
    schema_and_units: tuple[str, ...]
    spatial_resolution: str
    temporal_resolution: str
    observation_process: str
    coverage: str
    missingness: str
    license_status: str
    license_evidence: tuple[str, ...]
    data_use_feasibility: str
    included_in_public_artifact: bool
    permitted_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    unresolved_requirements: tuple[str, ...]


UPSTREAM = "https://github.com/hackohio/aep_challenge_hack26/tree/28a5520262b71a9fbf753b3031abf67781ca66ff"
ORNL = "https://doi.ccs.ornl.gov/dataset/ccec86f0-e144-5de8-aee0-fb26028b26e1"
NOAA = "https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc:C00510/html"
NOAA_FORMAT = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf"

DATASETS = (
    DatasetRecord(
        id="aep-challenge", version=SNAPSHOT, classification="source-derived", availability="local_pinned",
        sources=(UPSTREAM, "docs/DATA_AUDIT.md", "docs/MODEL_SPEC.md"),
        files=tuple(SourceFile(name, digest, "pinned_local_bytes") for name, digest in sorted(SOURCE_SHA256.items())),
        schema_and_units=("Typed string equipment/premise identifiers and ordered upstream paths", "Mixed EPSG:4326 and EPSG:3857 geometry; no inferred electrical edges", "Historical damage dates and status flags; no validated outage target", "Workbook direct labor multiplied by 4.5 once gives person-hours, not elapsed time"),
        spatial_resolution="Precise source customer/equipment/facility geometry remains private to local processing.",
        temporal_resolution="Static inventory; damage report and repair dates have day precision, not outage timestamps.",
        observation_process="Selected historical damage reports plus inventory; reporting completeness and exposed non-outage population are unknown.",
        coverage="117599 indexed paths; 40779 completely validated; 8093 physical assets have complete reverse membership. 1659 damage reports, 139 spatial candidates, 28 with complete reverse membership. See regenerated coverage report.",
        missingness="534 unresolved non-circuit topology nodes in original audit; 60 multiparent nodes; contradictory crosswalks. Failure categories overlap. 76 unrepaired flags have repair dates; 1659 outage/incident IDs are zero.",
        license_status="No explicit redistribution grant established; existing owner retention decision is not a license grant.",
        license_evidence=(UPSTREAM, "docs/releases/PUBLIC_RELEASE_AUDIT.md", "THIRD_PARTY_NOTICES.md"),
        data_use_feasibility="GO for existing owner-authorized local regression and explicitly declared scenarios only; exclude from new synthetic publication artifacts.",
        included_in_public_artifact=False,
        permitted_claims=("Pinned-source integrity and bounded validated dependency coverage", "Conditional effort under declared replacement scope"),
        prohibited_claims=("Observed current outages", "Damage reports as outage-positive/negative labels", "Date differences as repair or customer restoration duration", "Spatial matches as electrical truth"),
        unresolved_requirements=("Redistribution permission for any new data distribution", "Observed outage/negative exposure panel", "Verified restoration/crew/task timestamps", "Original challenge PDF and Data Guide attachments are not present in checkout")),
    DatasetRecord(
        id="synthetic-fixtures", version="synthetic-catalog-v1", classification="scenario assumption", availability="local_pinned",
        sources=("scripts/generate_synthetic.py", "data/synthetic/README.md"),
        files=(SourceFile("catalog.json", CATALOG_SHA256, "pinned_local_bytes"),),
        schema_and_units=("SyntheticScenario v1; fictional string identities and explicit path/repair relations", "Independent total repair person-hours; no source workbook or duration labels"),
        spatial_resolution="No coordinates or real geography.", temporal_resolution="No real observation dates; crew availability is a modeled response-origin assumption.",
        observation_process="Independently authored literal examples, not observations, samples, or transformations of challenge data.",
        coverage="Six boundary fixtures: simple, branching, overlap, blocked, missing evidence, critical-service tradeoff. Not a representative benchmark or population.",
        missingness="One deliberately unresolved topology case and missing effort; blocked access retains unknown clearance; actual efficiency and outcomes are always null.",
        license_status="Project-authored fixtures under the owner's implementation authorization. No new project-wide license or third-party grant is asserted.",
        license_evidence=("data/synthetic/README.md", "THIRD_PARTY_NOTICES.md"),
        data_use_feasibility="GO for fictional contract/isolation testing and the Phase 1 catalog artifact; no predictive or operational validation.",
        included_in_public_artifact=True,
        permitted_claims=("Valid-by-construction fictional definitions", "Unavailable evidence remains explicit"),
        prohibited_claims=("Observed outages or restoration outcomes", "Utility topology validation", "Empirical model performance"),
        unresolved_requirements=("Later benchmark preregistration is separate from these boundary fixtures",)),
    DatasetRecord(
        id="ornl-eagle-i", version="DOI 10.13139/ORNLNCCS/1975202; 2014-2022 release", classification="source-derived", availability="metadata_only",
        sources=(ORNL, "https://doi.org/10.1038/s41597-024-03095-5"),
        files=(SourceFile("county observations and coverage files", None, "not_acquired"),),
        schema_and_units=("Documented FIPS/county/state, customers without power, timestamp", "Counts of reported customers, not individual outage identities"),
        spatial_resolution="County aggregates; no premise/equipment crosswalk.", temporal_resolution="Documented 15-minute observations during 2014-2022.",
        observation_process="ETL from utilities' public outage maps; coverage varies and acquisition failures can resemble missing/zero reports.",
        coverage="Landing-page metadata reviewed; no observation files or target county/window coverage validated in Phase 1. Annual state coverage does not prove a complete county target window.",
        missingness="Unverified county-time observation completeness, reporting changes, missing-versus-zero semantics and publication latency. No negative labels inferred.",
        license_status="Dataset redistribution/use terms for the exact downloadable payload remain unverified; article terms are not substituted for dataset terms.",
        license_evidence=(ORNL, "https://api.datacite.org/dois/10.13139/ORNLNCCS/1975202"),
        data_use_feasibility="CONDITIONAL, NOT CLEARED: promising county research candidate only. Metadata/Globus discovery is not validated acquisition, license clearance, or label feasibility.",
        included_in_public_artifact=False,
        permitted_claims=("A county-level research candidate exists",),
        prohibited_claims=("Verified negative windows", "Premise outage probabilities", "Repair-task durations", "Empirical validation before acquisition and coverage audit"),
        unresolved_requirements=("Exact files/checksums and payload terms", "County-time quality masks and zero semantics", "As-of latency and event grouping", "Complete target windows and adequate held-out events")),
    DatasetRecord(
        id="noaa-storm-events", version="C00510 metadata and bulk-format documentation reviewed 2026-11-03; observation snapshot not acquired", classification="source-derived", availability="metadata_only",
        sources=(NOAA, NOAA_FORMAT), files=(SourceFile("StormEvents details/locations/fatalities snapshot", None, "not_acquired"),),
        schema_and_units=("EPISODE_ID and EVENT_ID connect retrospective storm records", "CZ_TYPE distinguishes counties, forecast zones and marine areas; CZ_FIPS is not always a county FIPS", "BEGIN/END_DATE_TIME and CZ_TIMEZONE require timezone validation"),
        spatial_resolution="County, forecast-zone or marine report geography; explicit crosswalk required.",
        temporal_resolution="Event start/end times; retrospective monthly product, metadata notes up to 120-day delay.",
        observation_process="Reported significant weather phenomena from NWS and other credited sources; not an exhaustive exposure or outage panel.",
        coverage="Metadata/schema inspected only. No selected period/geography observation completeness established.",
        missingness="Unreported events and revised narratives; reports can be unverified. No outage negatives or real-time availability implied.",
        license_status="NCEI open-data policy describes US public-domain data; dataset metadata requires citation and cautions about third-party source information. Exact snapshot review still required.",
        license_evidence=(NOAA, "https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf"),
        data_use_feasibility="CONDITIONAL for retrospective grouping/context after acquisition, attribution and zone/time audits; NO-GO as standalone outage labels or future-available predictors.",
        included_in_public_artifact=False, permitted_claims=("Potential retrospective episode grouping",),
        prohibited_claims=("Storm report implies a verified outage", "Post-event severity available before prediction", "County FIPS inferred from every zone identifier"),
        unresolved_requirements=("Pinned observation snapshot and source-specific terms", "Zone-to-county and time conversion validation", "Outage observations from an independent compatible source")),
    DatasetRecord(
        id="doe-417", version="Reporting-program reference reviewed 2026-11-03; no data release acquired", classification="source-derived", availability="metadata_only",
        sources=("https://doe417.energy.gov/",), files=(SourceFile("public incident-report snapshot", None, "not_acquired"),),
        schema_and_units=("Incident/emergency reporting context; exact downloadable schema not verified",),
        spatial_resolution="Incident/report geography, not premise membership.", temporal_resolution="Incident reporting; exact timestamp semantics not verified.",
        observation_process="Reportable electric incidents/emergencies, not all interruptions or a complete non-outage denominator.",
        coverage="Program landing page identified; rendered page supplied no readable report table during this review. No records or observation coverage validated.",
        missingness="Reporting thresholds, revisions and omissions prevent interpreting absent reports as no outage.",
        license_status="Exact public report payload terms not established; no blanket permission inferred from a government-hosted landing page.",
        license_evidence=("https://doe417.energy.gov/",), data_use_feasibility="NOT CLEARED; corroborating incident context only after source/schema/terms review.",
        included_in_public_artifact=False, permitted_claims=("Potential corroborating incident source",),
        prohibited_claims=("Complete outage/non-outage panel", "Customer restoration observations",),
        unresolved_requirements=("Accessible pinned public report files and terms", "Report scope and timestamp semantics",)),
    DatasetRecord(
        id="optional-partner", version="none", classification="unavailable", availability="not_provided", sources=(),
        files=(SourceFile("partner observations", None, "not_acquired"),), schema_and_units=("Required schema specified in feasibility document; no supplied data",),
        spatial_resolution="Unavailable", temporal_resolution="Unavailable", observation_process="Unavailable",
        coverage="No partner observations supplied.", missingness="All prerequisites unavailable.", license_status="No access agreement or data-use permission supplied.",
        license_evidence=(), data_use_feasibility="NO-GO now; optional and never a release dependency.", included_in_public_artifact=False,
        permitted_claims=("Missing-data requirements can be documented",), prohibited_claims=("Utility partnership, access or deployment",),
        unresolved_requirements=("Written permitted uses and retention/export rules", "Stable event/asset identities and explicit observation coverage", "Outage onset/restoration, task and crew timestamps with censoring", "Privacy-reviewed crosswalks and exposed non-outage controls")),
)


@dataclass(frozen=True)
class FeasibilityDecision:
    target: str
    decision: Literal["go_synthetic_only", "no_go_current_data", "conditional_not_cleared"]
    unit: str
    horizon_and_origin: str
    observation_process: str
    inclusion_rule: str
    licensing_gate: str
    coverage_gate: str
    evidence: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]


DECISIONS = (
    FeasibilityDecision("premise_outage_risk", "no_go_current_data", "probability per premise/window",
        "24 hours after a declared prediction issue time; unavailable in the challenge extract",
        "Damage reporting is not premise outage surveillance.",
        "Requires verified positives AND observed non-outage windows with known exposure and event grouping.",
        "Challenge local analysis only; no new redistribution permission.",
        "No eligible labeled observation panel.", ("aep-challenge",),
        ("Confirmed premise outages", "Verified non-outage controls and coverage", "Prediction-time features and timestamps")),
    FeasibilityDecision("county_reported_outage_risk", "conditional_not_cleared", "probability per county/24-hour window",
        "Next 24 hours; more than 100 reported customers without power for at least one hour",
        "Candidate utility-map aggregate observations; acquisition gaps are not negatives.",
        "Complete quality-audited target windows, stable county mapping, event-separated temporal splits; missing windows excluded with counts.",
        "Exact EAGLE-I payload terms remain unverified; no observations redistributed.",
        "No local observation snapshot or quality mask; county/time completeness and as-of latency unvalidated.",
        ("ornl-eagle-i", "noaa-storm-events", "doe-417"),
        ("Pinned permitted files", "Validated zero/missing semantics and coverage", "Independent event clusters and available-at-time features")),
    FeasibilityDecision("repair_task_duration", "no_go_current_data", "elapsed hours per task",
        "Actual task start to actual task completion, distinct from report-to-repair dates",
        "No task execution timeline or measured productivity is supplied.",
        "Requires linked task/asset/crew records, start/finish, pauses and censoring; labor rates alone are not labels.",
        "Optional partner terms absent.", "No compatible measured task outcomes.", ("aep-challenge", "optional-partner"),
        ("Task timestamps and scope", "Crew composition and interruptions", "Observed completed and censored work")),
    FeasibilityDecision("customer_restoration_time", "no_go_current_data", "elapsed hours per premise outage",
        "Observed outage onset to confirmed restoration; not modeled crew response time",
        "No premise outage-onset/restoration linkage is supplied.",
        "Requires verified service identity, event membership, onset/restoration and unresolved/censored outcomes.",
        "Partner permission and privacy-reviewed crosswalks absent.", "No observed premise outcomes.",
        ("aep-challenge", "optional-partner"), ("Verified outage and restoration timestamps", "Coverage/censoring definitions", "Permitted private linkage")),
    FeasibilityDecision("aggregate_outage_recovery", "conditional_not_cleared", "county reported-outage counts over elapsed hours",
        "Event-specific aggregate response origin and horizon must be preregistered after coverage validation",
        "Counts can decrease due to recovery, reporting changes or missing utilities; decreases are not individual restoration labels.",
        "Requires stable reporting coverage, event boundaries, missing-interval rules and explicit censoring.",
        "Exact external payload terms not established.", "No local audited aggregate time series.",
        ("ornl-eagle-i", "doe-417"), ("Pinned permitted observations", "Stable reporting coverage", "Event origin and censoring protocol")),
    FeasibilityDecision("synthetic_contract_isolation", "go_synthetic_only", "fictional scenario definition",
        "No elapsed-time outcome; response origin is an explicitly declared scenario assumption",
        "Literal independent fixture authoring, no observation process.",
        "Strict schema, unique fictional IDs, explicit graph links, classified evidence, immutable catalog hash.",
        "Owner-authorized new project fixtures; no third-party source data or new project license.",
        "Six defined boundary cases only; no statistical coverage claim.", ("synthetic-fixtures",), ()),
)


def register():
    return {"version": REGISTER_VERSION, "review_date": REVIEW_DATE,
            "scope": "Evidence and access feasibility only; no training or predictive validation performed.",
            "datasets": [asdict(record) for record in DATASETS],
            "feasibility_decisions": [asdict(decision) for decision in DECISIONS]}


if __name__ == "__main__":
    print(json.dumps(register(), indent=2, sort_keys=True, allow_nan=False))
