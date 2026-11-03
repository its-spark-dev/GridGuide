"""Legacy ordinal rule without source pins or filesystem dependencies."""


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
