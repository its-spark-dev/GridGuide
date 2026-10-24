"""Source pins and explicit team assumptions, never precomputed demo results."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SNAPSHOT = "aep-hack26-28a5520"
SNAPSHOT_DATE = date(2026, 10, 24)
GOLDEN_ALIAS = "demo-a"
GOLDEN_CUSTOMER_RECORD = 1077  # 1-based locator, valid only for the pinned Data1.
SOURCE_SHA256 = {
    "Data1.zip": "08ac47b7dd7f43cde56509644d7292d0b6978dcd62300912b4ecf0a2c3c6eca3",
    "Data2.zip": "13bea1c84636989a6475f481d67f25b25a17fcac8b77f674a5157e3a1d105f00",
    "matched_upstream.zip": "13f8d9da49843c959059b4074417c47671105131cdc4bfe9daf7b534e5f522c3",
    "Install_Labor_HackOHIO.xlsx": "e11fb199592bf26ef7f6e0bd11fab3de00265cde7649fc9b9a0cd54fc2e96e3b",
}
RISK_VERSION = "scenario-risk-v1"
RESTORATION_VERSION = "serial-path-v1"


@dataclass(frozen=True)
class Assumptions:
    """Change this version and rerun golden tests when the unit basis is clarified."""

    version: str = "provisional-crew-unit-v1"
    reference_crew_hours_per_labor_hour: Decimal = Decimal("1")
    upper_scope_multiplier: Decimal = Decimal("1.5")
    worksite_radius_m: float = 50.0

    def __post_init__(self):
        if not self.reference_crew_hours_per_labor_hour.is_finite() or self.reference_crew_hours_per_labor_hour <= 0:
            raise ValueError("Labor conversion must be finite and positive")
        if not self.upper_scope_multiplier.is_finite() or self.upper_scope_multiplier < 1:
            raise ValueError("Upper scope multiplier must be finite and at least one")
        if not 0 < self.worksite_radius_m <= 1000:
            raise ValueError("Worksite radius must be finite and positive")


ASSUMPTIONS = Assumptions()


def risk_band_for_score(score: int) -> str:
    if score == 0:
        return "LOW"
    if 1 <= score <= 2:
        return "MODERATE"
    if 3 <= score <= 4:
        return "HIGH"
    if score == 5:
        return "SEVERE"
    raise ValueError("Risk score is outside the v1 range")
