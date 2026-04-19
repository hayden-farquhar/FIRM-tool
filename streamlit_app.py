"""FIRM Tool — Febrile Infant Rural Model.

Interactive decision support for febrile infants aged 0-89 days.
Generates continuous IBI probability estimates using clinical and
laboratory data available in rural emergency departments.

DISCLAIMER: Research tool only. Not for clinical use without prospective
local validation.
"""

import streamlit as st
from src.prediction_model import predict
from src.rules.aronson import AronsonInputs, apply as aronson_apply
from src.rules.pecarn import PECARNInputs, apply as pecarn_apply
from src.rules.step_by_step import StepByStepInputs, apply as sbs_apply
from src.rules.aap_2021 import AAP2021Inputs, apply as aap_apply
from src.rules.rochester import RochesterInputs, apply as rochester_apply

st.set_page_config(
    page_title="FIRM Tool — Febrile Infant Rural Model",
    page_icon="🏥",
    layout="wide",
)

st.error(
    "**RESEARCH TOOL ONLY** — Not for clinical use without prospective "
    "local validation. This tool does not replace clinical judgement. "
    "Always follow local guidelines and consult senior clinicians."
)

st.title("FIRM Tool — Febrile Infant Rural Model")
st.caption(
    "Continuous IBI probability for febrile infants <90 days "
    "with incomplete clinical inputs. "
    "[Pre-registration](https://osf.io/dq5n8/) | "
    "[Derivation study](https://doi.org/10.5281/zenodo.19649953)"
)

# ── Sidebar: Clinical inputs ─────────────────────────────────

st.sidebar.header("Patient Details")

age_days = st.sidebar.number_input(
    "Age (days)", min_value=0, max_value=89, value=30, step=1
)
temp_c = st.sidebar.number_input(
    "Temperature (°C)", min_value=36.0, max_value=42.0, value=38.5, step=0.1,
    format="%.1f"
)
appearance = st.sidebar.selectbox(
    "Clinical appearance", ["Well-appearing", "Unwell / ill-appearing"]
)
well_appearing = appearance == "Well-appearing"

yos_total = st.sidebar.number_input(
    "Yale Observation Scale (6-30)", min_value=6, max_value=30, value=6, step=2,
    help="Sum of 6 components (cry, reaction, state, colour, hydration, response). "
         "Each scored 1-3-5. Total 6 = well, ≤10 = normal, >10 = concerning."
)

st.sidebar.header("Laboratory Results")
st.sidebar.caption("Leave unchecked if not available")

has_wbc = st.sidebar.checkbox("WBC available")
wbc = st.sidebar.number_input(
    "WBC (×10³/µL)", min_value=0.0, max_value=50.0, value=10.0, step=0.5,
    disabled=not has_wbc
) if has_wbc else None

has_anc = st.sidebar.checkbox("ANC available")
anc = st.sidebar.number_input(
    "ANC (×10³/µL)", min_value=0.0, max_value=40.0, value=4.0, step=0.5,
    disabled=not has_anc
) if has_anc else None

has_pct = st.sidebar.checkbox("PCT available")
pct = st.sidebar.number_input(
    "PCT (ng/mL)", min_value=0.0, max_value=200.0, value=0.3, step=0.1,
    format="%.2f", disabled=not has_pct
) if has_pct else None

has_crp = st.sidebar.checkbox("CRP available")
crp = st.sidebar.number_input(
    "CRP (mg/L)", min_value=0.0, max_value=500.0, value=5.0, step=1.0,
    disabled=not has_crp
) if has_crp else None

has_ua = st.sidebar.checkbox("Urinalysis available")
if has_ua:
    ua_le = st.sidebar.selectbox("Leukocyte esterase", ["Negative", "Positive"])
    ua_nitrites = st.sidebar.selectbox("Nitrites", ["Negative", "Positive"])
    ua_le_positive = ua_le == "Positive"
    ua_nitrites_positive = ua_nitrites == "Positive"
else:
    ua_le_positive = None
    ua_nitrites_positive = None

# ── Missing inputs ───────────────────────────────────────────

missing_inputs = []
if not has_pct:
    missing_inputs.append("PCT")
if not has_crp:
    missing_inputs.append("CRP")
if not has_ua:
    missing_inputs.append("UA")
if not has_anc:
    missing_inputs.append("ANC")

# ── Apply decision rules ──────────────────────────────────────

def apply_rules():
    """Apply published decision rules and return results."""
    results = {}

    if has_anc and has_ua:
        r = aronson_apply(AronsonInputs(
            age_days=age_days, temp_c=temp_c,
            ua_le_positive=ua_le_positive,
            ua_nitrites_positive=ua_nitrites_positive,
            anc=anc,
        ))
        if r.applicable:
            results["Aronson"] = r

    if has_wbc and has_ua:
        r = rochester_apply(RochesterInputs(
            age_days=age_days, temp_c=temp_c,
            well_appearing=well_appearing,
            previously_healthy=True, no_focal_infection=True,
            wbc=wbc, band_count=None,
            ua_wbc_hpf=None,
        ))
        results["Rochester"] = r

    if has_ua:
        r = sbs_apply(StepByStepInputs(
            age_days=age_days, temp_c=temp_c,
            well_appearing=well_appearing,
            ua_le_positive=ua_le_positive,
            ua_nitrites_positive=ua_nitrites_positive,
            pct=pct, crp=crp, anc=anc,
        ))
        results["Step-by-Step"] = r

    if has_ua and has_anc:
        r = pecarn_apply(PECARNInputs(
            age_days=age_days, temp_c=temp_c,
            ua_le_positive=ua_le_positive,
            ua_nitrites_positive=ua_nitrites_positive,
            anc=anc, pct=pct,
        ))
        results["PECARN"] = r

    if has_ua:
        r = aap_apply(AAP2021Inputs(
            age_days=age_days, temp_c=temp_c,
            well_appearing=well_appearing,
            ua_le_positive=ua_le_positive,
            ua_nitrites_positive=ua_nitrites_positive,
            pct=pct, anc=anc, crp=crp,
        ))
        results["AAP 2021"] = r

    return results


# ── Main display ──────────────────────────────────────────────

col1, col2 = st.columns([2, 1])

with col1:
    if missing_inputs:
        missing_str = ", ".join(missing_inputs)
        st.warning(f"**Missing inputs:** {missing_str} — imputed with training-set medians.")
    else:
        st.success("**All inputs available** — full assessment possible.")

    pred = predict(
        age_days=age_days,
        temp_c=temp_c,
        wbc=wbc if has_wbc else None,
        anc=anc if has_anc else None,
        ua_positive=ua_le_positive if has_ua else None,
        yos_total=float(yos_total),
    )

    tier_map = {
        "very_low": ("Very low risk", "green"),
        "low": ("Low risk — comparable to published decision rules", "blue"),
        "moderate": ("Moderate risk — above published low-risk thresholds", "orange"),
        "high": ("High risk — IBI workup recommended", "red"),
    }
    decision_text, decision_color = tier_map.get(pred.risk_tier, ("Assess further", "orange"))

    st.markdown("---")
    st.subheader("Assessment")

    if decision_color == "green":
        st.success(f"### {decision_text}")
    elif decision_color == "blue":
        st.info(f"### {decision_text}")
    elif decision_color == "red":
        st.error(f"### {decision_text}")
    else:
        st.warning(f"### {decision_text}")

    mcol1, mcol2, mcol3 = st.columns(3)
    with mcol1:
        st.metric("IBI Probability", f"{pred.probability:.2%}")
    with mcol2:
        st.metric("Risk", f"1 in {pred.one_in_n}")
    with mcol3:
        st.metric("Missing Inputs Imputed", f"{pred.n_missing_imputed}")

    st.markdown(f"**{pred.risk_description}**")
    st.markdown(f"*{pred.comparison_to_rules}*")

    with st.expander("Age-specific context", expanded=True):
        st.markdown(pred.age_context)

    rule_results = apply_rules()

with col2:
    st.subheader("Per-Rule Breakdown")

    if not rule_results:
        st.info("No rules applicable with current inputs.")
    else:
        for name, result in rule_results.items():
            if not result.applicable:
                st.markdown(f"**{name}:** ⚪ Not applicable (missing inputs)")
            elif result.prediction == 0:
                st.markdown(f"**{name}:** 🟢 Low-risk")
            else:
                triggers = ", ".join(result.triggered_criteria)
                st.markdown(f"**{name}:** 🔴 Not low-risk ({triggers})")

    st.markdown("---")
    st.subheader("Risk Tiers")
    st.markdown(
        "| Tier | P(IBI) | Interpretation |\n"
        "|------|--------|----------------|\n"
        "| Very low | <0.5% | Below all published rule residual rates |\n"
        "| Low | 0.5-1.5% | Comparable to published low-risk groups |\n"
        "| Moderate | 1.5-3% | Above published low-risk thresholds |\n"
        "| High | >3% | IBI workup recommended |"
    )

# ── Footer ────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "*FIRM Tool (Febrile Infant Rural Model). "
    "[Pre-registration](https://osf.io/dq5n8/) | "
    "[Derivation study](https://doi.org/10.5281/zenodo.19649953) | "
    "PRISMA-DTA + TRIPOD+AI*"
)
st.caption(
    "Research tool only. Not validated for clinical use. "
    "Prospective validation via PREDICT network invited."
)
