"""Tests for the FIRM prediction model."""
import pytest
from src.prediction_model import predict, _COEFFICIENTS, _INTERCEPT, _MEDIANS, FEATURES


class TestPredictBasic:
    """Core prediction functionality."""

    def test_returns_prediction_result(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert hasattr(r, "probability")
        assert hasattr(r, "risk_tier")
        assert hasattr(r, "one_in_n")

    def test_probability_between_0_and_1(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0

    def test_one_in_n_inverse_of_probability(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert r.one_in_n == round(1 / r.probability)

    def test_features_used_correct(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert r.features_used == FEATURES


class TestRiskTiers:
    """Risk tier assignment at known probability ranges."""

    def test_well_older_infant_low_risk(self):
        """Well-appearing 45d infant with normal labs should be low risk."""
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert r.risk_tier in ("very_low", "low")
        assert r.probability < 0.015

    def test_unwell_neonate_high_risk(self):
        """Unwell 10d neonate with abnormal labs should be high risk."""
        r = predict(age_days=10, temp_c=39.0, wbc=18.0, anc=12.0,
                    ua_positive=True, yos_total=16.0)
        assert r.risk_tier == "high"
        assert r.probability > 0.03

    def test_borderline_infant_moderate(self):
        """30d infant with borderline labs should be moderate risk."""
        r = predict(age_days=30, temp_c=38.5, wbc=12.0, anc=6.0,
                    ua_positive=False, yos_total=8.0)
        assert r.risk_tier in ("low", "moderate")

    def test_lowest_achievable_is_low(self):
        """Older well infant with very normal labs should be low risk."""
        r = predict(age_days=60, temp_c=38.0, wbc=4.0, anc=1.0,
                    ua_positive=False, yos_total=6.0)
        assert r.risk_tier == "low"
        assert r.probability < 0.01

    def test_tier_boundaries(self):
        """Verify the four tiers are exhaustive."""
        valid_tiers = {"very_low", "low", "moderate", "high"}
        for age in [5, 15, 30, 50]:
            for anc in [2.0, 8.0, 15.0]:
                r = predict(age_days=age, temp_c=38.5, wbc=10.0, anc=anc,
                            ua_positive=False, yos_total=6.0)
                assert r.risk_tier in valid_tiers


class TestMissingInputs:
    """Missing input handling via median imputation."""

    def test_missing_wbc_still_predicts(self):
        r = predict(age_days=45, temp_c=38.3, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0
        assert r.n_missing_imputed == 1

    def test_missing_anc_still_predicts(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0
        assert r.n_missing_imputed == 1

    def test_missing_ua_still_predicts(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    yos_total=6.0)
        assert 0.0 < r.probability < 1.0
        assert r.n_missing_imputed == 1

    def test_missing_yos_still_predicts(self):
        r = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                    ua_positive=False)
        assert 0.0 < r.probability < 1.0
        assert r.n_missing_imputed == 1

    def test_all_labs_missing(self):
        """Only age and temp provided — should still produce a result."""
        r = predict(age_days=45, temp_c=38.5)
        assert 0.0 < r.probability < 1.0
        assert r.n_missing_imputed == 4

    def test_many_missing_adds_uncertainty_warning(self):
        """3+ missing inputs should add uncertainty language."""
        r = predict(age_days=45, temp_c=38.5, wbc=9.0)
        assert r.n_missing_imputed == 3
        assert "uncertain" in r.risk_description.lower()

    def test_n_missing_count_correct(self):
        """Count only the 4 imputable inputs (wbc, anc, ua, yos)."""
        r_none = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0,
                         ua_positive=False, yos_total=6.0)
        assert r_none.n_missing_imputed == 0

        r_two = predict(age_days=45, temp_c=38.3, wbc=9.0, anc=3.0)
        assert r_two.n_missing_imputed == 2


class TestAgeContext:
    """Age-specific clinical context messages."""

    def test_age_leq_7(self):
        r = predict(age_days=5, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert "7 days" in r.age_context

    def test_age_8_to_21(self):
        r = predict(age_days=15, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert "AAP 2021" in r.age_context

    def test_age_29_to_60(self):
        r = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert "29-60" in r.age_context

    def test_age_over_60(self):
        r = predict(age_days=75, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert "limited" in r.age_context.lower()


class TestModelCoefficients:
    """Verify embedded model integrity."""

    def test_correct_number_of_coefficients(self):
        assert len(_COEFFICIENTS) == 7
        assert len(FEATURES) == 7

    def test_intercept_is_negative(self):
        assert _INTERCEPT < 0

    def test_ua_positive_strongest_predictor(self):
        """Urinalysis positive should have the largest absolute coefficient."""
        ua_idx = FEATURES.index("ua_pos")
        assert abs(_COEFFICIENTS[ua_idx]) == max(abs(c) for c in _COEFFICIENTS)

    def test_medians_all_present(self):
        for feat in FEATURES:
            assert feat in _MEDIANS

    def test_positive_ua_increases_risk(self):
        """UA positive should substantially increase predicted probability."""
        r_neg = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=4.0,
                        ua_positive=False, yos_total=6.0)
        r_pos = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=4.0,
                        ua_positive=True, yos_total=6.0)
        assert r_pos.probability > r_neg.probability * 2

    def test_higher_anc_increases_risk(self):
        r_low = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=2.0,
                        ua_positive=False, yos_total=6.0)
        r_high = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=12.0,
                         ua_positive=False, yos_total=6.0)
        assert r_high.probability > r_low.probability

    def test_higher_yos_increases_risk(self):
        r_well = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=4.0,
                         ua_positive=False, yos_total=6.0)
        r_unwell = predict(age_days=45, temp_c=38.5, wbc=10.0, anc=4.0,
                           ua_positive=False, yos_total=18.0)
        assert r_unwell.probability > r_well.probability


class TestEdgeCases:
    """Boundary and edge case handling."""

    def test_age_zero(self):
        r = predict(age_days=0, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0

    def test_age_89(self):
        r = predict(age_days=89, temp_c=38.5, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0

    def test_extreme_temp_high(self):
        r = predict(age_days=45, temp_c=41.0, wbc=10.0, anc=3.0,
                    ua_positive=False, yos_total=6.0)
        assert 0.0 < r.probability < 1.0

    def test_extreme_wbc(self):
        r = predict(age_days=45, temp_c=38.5, wbc=40.0, anc=20.0,
                    ua_positive=True, yos_total=20.0)
        assert 0.0 < r.probability < 1.0
