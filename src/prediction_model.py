"""FIRM Tool — Febrile Infant Rural Model.

Standalone prediction model with embedded coefficients from the derivation study.
No external data required. The coefficients were derived from logistic regression
on the PECARN Biosignatures complete-case cohort (n=4,434; 88 IBI events).

For derivation details, see the accompanying manuscript and analysis code:
https://doi.org/10.5281/zenodo.19649953
"""

import numpy as np
from dataclasses import dataclass, field

FEATURES = ["age_days", "temp_c", "wbc", "anc", "ua_pos", "yos_total", "age_young"]

# Embedded model coefficients (from derivation study, Table 2)
_COEFFICIENTS = np.array([
    -0.0232566655643762,    # age_days
    -0.09884938736162842,   # temp_c
    -0.15044829949342556,   # wbc
    0.23314800023694138,    # anc
    1.3198524072260749,     # ua_pos
    0.10229519456626301,    # yos_total
    0.30982788445199166,    # age_young
])
_INTERCEPT = -0.04785341790715337

# Median values for imputation when inputs are missing
_MEDIANS = {
    "age_days": 38.0,
    "temp_c": 38.36,
    "wbc": 9.81,
    "anc": 3.23,
    "ua_pos": 0.0,
    "yos_total": 6.0,
    "age_young": 0.0,
}

# Published rule performance for context
PUBLISHED_RULE_CONTEXT = {
    "Aronson": {"ibi_rate_in_low_risk": 0.006, "npv": 0.994, "source": "FIDO 2024"},
    "PECARN": {"ibi_rate_in_low_risk": 0.004, "npv": 0.996, "source": "Kuppermann 2019"},
    "Step-by-Step": {"ibi_rate_in_low_risk": 0.007, "npv": 0.993, "source": "Gomez 2016"},
    "Rochester": {"ibi_rate_in_low_risk": 0.017, "npv": 0.983, "source": "Gomez 2016"},
}


@dataclass
class PredictionResult:
    probability: float
    one_in_n: int
    risk_tier: str
    risk_description: str
    comparison_to_rules: str
    age_context: str
    features_used: list[str] = field(default_factory=list)
    n_missing_imputed: int = 0


def _risk_tier(prob: float, age_days: int) -> tuple[str, str, str, str]:
    """Assign risk tier with clinical description and rule comparison."""
    if prob < 0.005:
        tier = "very_low"
        desc = "Very low risk — below the residual IBI rate of all published decision rules."
        comp = ("Below the residual IBI rate in PECARN low-risk (0.4%), "
                "Aronson low-risk (0.6%), and Rochester low-risk (1.7%).")
    elif prob < 0.015:
        tier = "low"
        desc = ("Low risk — comparable to the residual IBI rate accepted by "
                "published decision rules for 'low-risk' classification.")
        comp = ("Comparable to Aronson low-risk (0.6% IBI rate, NPV 99.4%) "
                "and PECARN low-risk (0.4% IBI rate, NPV 99.6%). "
                "Published rules accept this level of residual risk for "
                "observation or discharge with follow-up.")
    elif prob < 0.03:
        tier = "moderate"
        desc = ("Moderate risk — above the residual IBI rate typically accepted "
                "by published low-risk rules.")
        comp = ("Above Aronson/PECARN low-risk thresholds. "
                "Consider further workup, observation period, or shared "
                "decision-making with family.")
    else:
        tier = "high"
        desc = "High risk — IBI workup recommended."
        comp = "Well above all published low-risk thresholds."

    if age_days <= 7:
        age_ctx = ("Age ≤7 days: highest baseline IBI risk. Most guidelines "
                   "recommend full workup and admission regardless of labs.")
    elif age_days <= 21:
        age_ctx = ("Age 8-21 days: high baseline IBI risk. AAP 2021 recommends "
                   "admission with empiric antibiotics for all infants in this group.")
    elif age_days <= 28:
        age_ctx = ("Age 22-28 days: AAP 2021 allows selective management if "
                   "all inflammatory markers are normal and follow-up is assured.")
    elif age_days <= 60:
        age_ctx = ("Age 29-60 days: lower baseline IBI risk (~1.2%). "
                   "Low-risk classification supported by multiple validated rules.")
    else:
        age_ctx = ("Age >60 days: limited validation data for this age group. "
                   "Interpret with caution.")

    return tier, desc, comp, age_ctx


def predict(
    age_days: float,
    temp_c: float,
    wbc: float = None,
    anc: float = None,
    ua_positive: bool = None,
    yos_total: float = None,
) -> PredictionResult:
    """Predict IBI probability using embedded model coefficients.

    Missing inputs are imputed with training-set medians.
    """
    ua_val = float(ua_positive) if ua_positive is not None else _MEDIANS["ua_pos"]
    yos_val = float(yos_total) if yos_total is not None else _MEDIANS["yos_total"]
    age_young_val = 1.0 if age_days <= 14 else 0.0

    n_missing = sum(1 for v in [wbc, anc, ua_positive, yos_total] if v is None)

    x = np.array([
        age_days,
        temp_c,
        wbc if wbc is not None else _MEDIANS["wbc"],
        anc if anc is not None else _MEDIANS["anc"],
        ua_val,
        yos_val,
        age_young_val,
    ])

    logit = np.dot(_COEFFICIENTS, x) + _INTERCEPT
    prob = 1.0 / (1.0 + np.exp(-logit))

    tier, desc, comp, age_ctx = _risk_tier(prob, int(age_days))

    if n_missing >= 3:
        desc = "Multiple inputs missing — probability estimate is uncertain. " + desc
        comp = ("Insufficient data for reliable comparison to published rules. "
                "Consider obtaining additional investigations.")

    one_in_n = int(round(1 / max(prob, 0.0001)))

    return PredictionResult(
        probability=prob,
        one_in_n=one_in_n,
        risk_tier=tier,
        risk_description=desc,
        comparison_to_rules=comp,
        age_context=age_ctx,
        features_used=list(FEATURES),
        n_missing_imputed=n_missing,
    )
