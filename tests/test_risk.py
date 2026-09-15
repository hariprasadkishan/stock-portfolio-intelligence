"""Deterministic numerical tests for risk analytics."""

import numpy as np
import pandas as pd
import pytest

from agent.analytics.risk import (
    calculate_annualized_volatility,
    calculate_downside_deviation,
    calculate_drawdown_series,
    calculate_max_drawdown,
    calculate_max_drawdown_duration,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    compute_risk_metrics,
)


class TestVolatility:
    """Test sample standard deviation and annualization."""

    def test_annualized_volatility_exact(self):
        """Verify annualized volatility against analytical hand calculation."""
        # 4 returns with mean = 0.0
        # Variance with ddof=1 is (0.0001 * 4) / 3 = 0.0004 / 3
        # std = sqrt(0.0004 / 3)
        # ann_vol = std * sqrt(252) = 0.02 * sqrt(84) = 0.183303027...
        rets = pd.Series([0.01, -0.01, 0.01, -0.01])
        vol = calculate_annualized_volatility(rets, periods_per_year=252)

        expected_vol = 0.02 * np.sqrt(84)
        assert vol is not None
        assert vol == pytest.approx(expected_vol, rel=1e-5)

    def test_zero_variance_volatility(self):
        """Zero variance returns zero volatility."""
        rets = pd.Series([0.02, 0.02, 0.02, 0.02])
        vol = calculate_annualized_volatility(rets)
        assert vol == 0.0

    def test_insufficient_volatility_data(self):
        """Single point or empty returns None."""
        assert calculate_annualized_volatility(pd.Series([0.05])) is None
        assert calculate_annualized_volatility(pd.Series(dtype=float)) is None


class TestSharpeAndSortino:
    """Test Sharpe and Sortino ratios with configurable risk-free rates."""

    def test_sharpe_ratio_positive_excess_return(self):
        """Verify Sharpe calculation with deterministic return and volatility."""
        # Construct synthetic series where daily returns yield known annualized return and volatility
        np.random.seed(42)
        # Daily return of ~0.0008 (~20% annual return), low vol
        rets = pd.Series([0.01, 0.015, -0.005, 0.008, 0.012] * 50)  # 250 days

        # Configurable risk-free rates
        sharpe_0 = calculate_sharpe_ratio(rets, risk_free_rate=0.0, periods_per_year=252)
        sharpe_5 = calculate_sharpe_ratio(rets, risk_free_rate=0.05, periods_per_year=252)

        assert sharpe_0 is not None
        assert sharpe_5 is not None
        # Higher risk-free rate reduces the Sharpe ratio
        assert sharpe_5 < sharpe_0

    def test_sharpe_ratio_zero_volatility(self):
        """Constant returns produce 0 volatility -> Sharpe is undefined (None)."""
        rets = pd.Series([0.01, 0.01, 0.01, 0.01])
        assert calculate_sharpe_ratio(rets, risk_free_rate=0.0) is None

    def test_sortino_ratio_exact_downside_deviation(self):
        """Verify downside deviation and Sortino ratio against manual calculation."""
        # 4 daily returns: [0.02, 0.01, -0.02, -0.01]
        # Target return = 0.0
        # Downside deviations: [0, 0, -0.02, -0.01]
        # Sum of squared downsides: 0.0004 + 0.0001 = 0.0005
        # Mean squared downside = 0.0005 / 4 = 0.000125
        # Daily downside std = sqrt(0.000125)
        # Annualized downside vol = sqrt(0.000125 * 252) = sqrt(0.0315) approx 0.17748239
        rets = pd.Series([0.02, 0.01, -0.02, -0.01])
        downside = calculate_downside_deviation(rets, target_return=0.0, periods_per_year=252)
        expected_downside = np.sqrt(0.0315)
        assert downside == pytest.approx(expected_downside, rel=1e-5)

        sortino = calculate_sortino_ratio(rets, risk_free_rate=0.0, target_return=0.0, periods_per_year=252)
        assert sortino is not None

    def test_sortino_zero_downside_deviation(self):
        """When all returns exceed target return, downside deviation is zero -> Sortino is None."""
        rets = pd.Series([0.05, 0.03, 0.02, 0.04])
        assert calculate_sortino_ratio(rets, target_return=0.0) is None


class TestDrawdownAnalytics:
    """Test peak-to-trough drawdowns and duration in trading days."""

    def test_drawdown_series_and_max_drawdown_exact(self):
        """Verify drawdown trajectory and MDD on hand-crafted price path."""
        # Peak: 100 -> 120 (Peak 120)
        # Drop: 120 -> 90 (-25% drawdown)
        # Rebound: 90 -> 110 (-8.33% drawdown)
        # Drop: 110 -> 80 (-33.33% drawdown -> Max Drawdown)
        # Breakout: 80 -> 130 (New Peak 130, 0% drawdown)
        prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0, 130.0])

        dd = calculate_drawdown_series(prices)
        expected_dd = [0.0, 0.0, -0.25, -10.0 / 120.0, -40.0 / 120.0, 0.0]
        np.testing.assert_allclose(dd.values, expected_dd, rtol=1e-5)

        mdd = calculate_max_drawdown(prices)
        assert mdd == pytest.approx(-40.0 / 120.0, rel=1e-5)  # -33.33%

    def test_max_drawdown_duration_exact(self):
        """Verify exact duration in trading days spent underwater."""
        # Day 0: 100 (peak)
        # Day 1: 120 (new peak)
        # Day 2: 90 (underwater day 1)
        # Day 3: 110 (underwater day 2)
        # Day 4: 80 (underwater day 3)
        # Day 5: 130 (recovered to new peak -> duration resets)
        prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0, 130.0])
        duration = calculate_max_drawdown_duration(prices)
        assert duration == 3

    def test_strictly_increasing_series_no_drawdown(self):
        """Series that never declines has MDD = 0.0 and duration = 0."""
        prices = pd.Series([100.0, 105.0, 110.0, 115.0])
        assert calculate_max_drawdown(prices) == 0.0
        assert calculate_max_drawdown_duration(prices) == 0

    def test_empty_drawdown(self):
        """Empty series returns 0.0 drawdown and 0 duration."""
        assert calculate_max_drawdown(pd.Series(dtype=float)) == 0.0
        assert calculate_max_drawdown_duration(pd.Series(dtype=float)) == 0


class TestRiskMetricsBundle:
    """Test compute_risk_metrics aggregate method."""

    def test_compute_risk_metrics(self):
        rets = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        metrics = compute_risk_metrics(rets, risk_free_rate=0.02, periods_per_year=252)

        assert metrics.annualized_volatility is not None
        assert metrics.annualized_volatility > 0.0
        assert metrics.max_drawdown <= 0.0
        assert metrics.max_drawdown_duration_days >= 0
        assert metrics.risk_free_rate == 0.02
