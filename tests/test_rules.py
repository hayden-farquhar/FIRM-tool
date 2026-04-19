"""Tests for published decision rule implementations."""
import pytest
from src.rules.aronson import AronsonInputs, apply as aronson_apply
from src.rules.pecarn import PECARNInputs, apply as pecarn_apply
from src.rules.step_by_step import StepByStepInputs, apply as sbs_apply
from src.rules.aap_2021 import AAP2021Inputs, apply as aap_apply
from src.rules.rochester import RochesterInputs, apply as rochester_apply


class TestAronson:
    """Aronson criteria (Aronson et al. 2019)."""

    def test_low_risk_older_infant(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert r.prediction == 0
        assert r.applicable

    def test_high_risk_young_age(self):
        r = aronson_apply(AronsonInputs(
            age_days=15, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert r.prediction == 1
        assert "age_leq_21d" in r.triggered_criteria

    def test_high_risk_elevated_temp(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=39.0, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert r.prediction == 1
        assert "temp_geq_38.5" in r.triggered_criteria

    def test_high_risk_positive_ua(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, ua_le_positive=True,
            ua_nitrites_positive=False, anc=3.0))
        assert r.prediction == 1
        assert "ua_positive" in r.triggered_criteria

    def test_high_risk_elevated_anc(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False, anc=6.0))
        assert r.prediction == 1
        assert "anc_elevated" in r.triggered_criteria

    def test_not_applicable_over_60d(self):
        r = aronson_apply(AronsonInputs(
            age_days=75, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert not r.applicable

    def test_not_applicable_missing_ua(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, anc=3.0))
        assert not r.applicable

    def test_not_applicable_missing_anc(self):
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False))
        assert not r.applicable

    def test_anc_boundary(self):
        """ANC exactly at 5.185 should trigger."""
        r = aronson_apply(AronsonInputs(
            age_days=45, temp_c=38.2, ua_le_positive=False,
            ua_nitrites_positive=False, anc=5.185))
        assert r.prediction == 1


class TestPECARN:
    """PECARN febrile infant rule (Kuppermann et al. 2019)."""

    def test_low_risk_older_infant(self):
        r = pecarn_apply(PECARNInputs(
            age_days=45, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert r.prediction == 0
        assert r.age_stratum == "29-60d"

    def test_low_risk_young_with_pct(self):
        r = pecarn_apply(PECARNInputs(
            age_days=20, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0, pct=0.5))
        assert r.prediction == 0
        assert r.age_stratum == "7-28d"

    def test_not_applicable_under_7d(self):
        r = pecarn_apply(PECARNInputs(
            age_days=3, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0))
        assert not r.applicable

    def test_young_requires_pct(self):
        """7-28d stratum requires PCT — missing PCT makes rule inapplicable."""
        r = pecarn_apply(PECARNInputs(
            age_days=20, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0, pct=None))
        assert not r.applicable

    def test_older_does_not_require_pct(self):
        """29-60d stratum does NOT require PCT."""
        r = pecarn_apply(PECARNInputs(
            age_days=45, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0, pct=None))
        assert r.applicable
        assert r.prediction == 0

    def test_elevated_pct_triggers(self):
        r = pecarn_apply(PECARNInputs(
            age_days=20, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=3.0, pct=2.0))
        assert r.prediction == 1
        assert "pct_elevated" in r.triggered_criteria

    def test_elevated_anc_triggers(self):
        r = pecarn_apply(PECARNInputs(
            age_days=45, temp_c=38.5, ua_le_positive=False,
            ua_nitrites_positive=False, anc=5.0))
        assert r.prediction == 1
        assert "anc_elevated" in r.triggered_criteria


class TestStepByStep:
    """Step-by-Step algorithm (Gomez et al. 2016)."""

    def test_not_applicable_without_ua(self):
        r = sbs_apply(StepByStepInputs(
            age_days=45, temp_c=38.5, well_appearing=True))
        assert not r.applicable

    def test_applicable_with_basic_inputs(self):
        r = sbs_apply(StepByStepInputs(
            age_days=45, temp_c=38.5, well_appearing=True,
            ua_le_positive=False, ua_nitrites_positive=False,
            pct=0.3, crp=5.0, anc=3.0))
        assert r.applicable


class TestAAP2021:
    """AAP 2021 guideline (Pantell et al. 2021)."""

    def test_applicable_with_ua(self):
        r = aap_apply(AAP2021Inputs(
            age_days=45, temp_c=38.5, well_appearing=True,
            ua_le_positive=False, ua_nitrites_positive=False,
            pct=0.3, anc=3.0, crp=5.0))
        assert r.applicable

    def test_not_applicable_without_ua(self):
        r = aap_apply(AAP2021Inputs(
            age_days=45, temp_c=38.5, well_appearing=True))
        assert not r.applicable
