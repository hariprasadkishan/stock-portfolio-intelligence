"""Deterministic tests for Historical Value at Risk (VaR) and Conditional VaR (Expected Shortfall)."""

import numpy as np
import pandas as pd
import pytest

from agent.analytics.tail_risk import (
    calculate_historical_cvar,
    calculate_historical_var,
    compute_tail_risk_metrics,
)


class TestHistoricalVaR:
    """Test Historical VaR calculation and positive loss magnitude convention."""

    def test_historical_var_exact_linear_quantile(self):
        """Verify VaR against manual linear interpolation quantile.
        
        Given 10 returns:
        [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07]
        Confidence level = 0.95 -> alpha = 0.05.
        Quantile index = (10 - 1) * 0.05 = 0.45.
        Interpolated quantile = -0.05 + 0.45 * (-0.03 - (-0.05)) = -0.05 + 0.009 = -0.041 (-4.1%).
        VaR (positive loss magnitude) = +0.041 (+4.1%).
        """
        rets = pd.Series([-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07])
        var_95 = calculate_historical_var(rets, confidence_level=0.95)

        assert var_95 is not None
        assert var_95 == pytest.approx(0.041, rel=1e-5)

    def test_historical_var_80_confidence(self):
        """Verify 80% confidence VaR (20th percentile)."""
        rets = pd.Series([-0.08, -0.06, -0.04, -0.02, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
        # Quantile index = 9 * 0.20 = 1.8 -> -0.06 + 0.8 * (-0.04 - (-0.06)) = -0.06 + 0.016 = -0.044
        var_80 = calculate_historical_var(rets, confidence_level=0.80)
        assert var_80 is not None
        assert var_80 == pytest.approx(0.044, rel=1e-5)

    def test_historical_var_invalid_confidence_levels(self):
        """Invalid confidence levels (<0, >1, 0, 1) return None."""
        rets = pd.Series([0.01, -0.02, 0.03])
        assert calculate_historical_var(rets, confidence_level=0.0) is None
        assert calculate_historical_var(rets, confidence_level=1.0) is None
        assert calculate_historical_var(rets, confidence_level=-0.5) is None
        assert calculate_historical_var(rets, confidence_level=1.5) is None

    def test_historical_var_empty_and_insufficient_data(self):
        """Empty or single observation series returns None."""
        assert calculate_historical_var(pd.Series(dtype=float)) is None
        assert calculate_historical_var(pd.Series([-0.02])) is None


class TestHistoricalCVaR:
    """Test Historical Conditional VaR (Expected Shortfall) calculation."""

    def test_historical_cvar_exact_tail_mean(self):
        """Verify CVaR computes the exact mean of observations in the tail beyond VaR.
        
        Given:
        [-0.08, -0.06, -0.04, -0.02, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05]
        For 80% confidence:
        Quantile threshold = -0.044.
        Tail observations <= -0.044: [-0.08, -0.06].
        Expected Shortfall = mean([-0.08, -0.06]) = -0.07.
        CVaR (positive loss magnitude) = +0.07 (7.0% expected loss).
        """
        rets = pd.Series([-0.08, -0.06, -0.04, -0.02, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
        cvar_80 = calculate_historical_cvar(rets, confidence_level=0.80)

        assert cvar_80 is not None
        assert cvar_80 == pytest.approx(0.07, rel=1e-5)

    def test_cvar_always_greater_than_or_equal_to_var(self):
        """By definition, Expected Shortfall in the loss tail must be >= VaR threshold."""
        np.random.seed(42)
        rets = pd.Series(np.random.normal(-0.0005, 0.02, 200))

        var_95 = calculate_historical_var(rets, confidence_level=0.95)
        cvar_95 = calculate_historical_cvar(rets, confidence_level=0.95)

        assert var_95 is not None
        assert cvar_95 is not None
        assert cvar_95 >= var_95

    def test_historical_cvar_insufficient_data(self):
        """Empty or single-element series returns None."""
        assert calculate_historical_cvar(pd.Series(dtype=float)) is None
        assert calculate_historical_cvar(pd.Series([-0.05])) is None


class TestTailRiskBundle:
    """Test compute_tail_risk_metrics aggregator."""

    def test_compute_tail_risk_metrics(self):
        np.random.seed(42)
        rets = pd.Series(np.random.normal(0.0, 0.01, 100))

        metrics = compute_tail_risk_metrics(rets, custom_confidence=0.99)
        assert metrics.total_observations == 100
        assert metrics.var_95 is not None
        assert metrics.cvar_95 is not None
        assert metrics.var_custom is not None
        assert metrics.cvar_custom is not None
        assert metrics.confidence_level == 0.99
        # Higher confidence yields higher loss magnitude
        assert metrics.var_custom >= metrics.var_95
        assert metrics.cvar_custom >= metrics.cvar_95
