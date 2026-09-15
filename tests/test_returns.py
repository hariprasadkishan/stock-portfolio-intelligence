"""Deterministic numerical tests for return analytics."""

from datetime import date
import numpy as np
import pandas as pd
import pytest

from agent.analytics.returns import (
    calculate_annualized_return,
    calculate_cumulative_returns,
    calculate_daily_returns,
    compute_return_metrics,
)


class TestDailyReturns:
    """Test daily simple return calculation with precise expected numerical results."""

    def test_daily_returns_exact_numerical_values(self):
        """Verify daily returns match hand-calculated percentage changes."""
        dates = pd.date_range("2025-01-01", periods=4, freq="D")
        # 100 -> 105 (+5%) -> 102.9 (-2%) -> 113.19 (+10%)
        prices = pd.Series([100.0, 105.0, 102.9, 113.19], index=dates)

        rets = calculate_daily_returns(prices, dropna=True)
        assert len(rets) == 3
        expected = [0.05, -0.02, 0.10]
        np.testing.assert_allclose(rets.values, expected, rtol=1e-5)

    def test_daily_returns_without_dropna(self):
        """Verify dropna=False retains leading NaN."""
        prices = pd.Series([100.0, 110.0])
        rets = calculate_daily_returns(prices, dropna=False)
        assert len(rets) == 2
        assert np.isnan(rets.iloc[0])
        assert rets.iloc[1] == pytest.approx(0.10)

    def test_daily_returns_with_missing_values_ffill(self):
        """Verify forward fill handles intermittent missing prices."""
        prices = pd.Series([100.0, np.nan, 110.0])
        rets = calculate_daily_returns(prices, dropna=True, fill_method="ffill")
        # 100 -> ffill 100 (0.0) -> 110 (+10%)
        assert len(rets) == 2
        assert rets.iloc[0] == 0.0
        assert rets.iloc[1] == pytest.approx(0.10)

    def test_daily_returns_empty_and_single_element(self):
        """Verify handling of empty or 1-element series."""
        assert calculate_daily_returns(pd.Series(dtype=float)).empty
        assert calculate_daily_returns(pd.Series([100.0])).empty


class TestCumulativeReturns:
    """Test cumulative return calculations."""

    def test_cumulative_returns_from_prices(self):
        """Verify cumulative returns derived directly from price series."""
        dates = pd.date_range("2025-01-01", periods=4, freq="D")
        prices = pd.Series([100.0, 110.0, 105.0, 120.0], index=dates)

        cum_rets = calculate_cumulative_returns(prices, is_prices=True)
        expected = [0.0, 0.10, 0.05, 0.20]
        np.testing.assert_allclose(cum_rets.values, expected, rtol=1e-5)

    def test_cumulative_returns_from_daily_returns(self):
        """Verify cumulative compounding from periodic daily returns."""
        # Day 1: +10% (1.10)
        # Day 2: -5%  (1.10 * 0.95 = 1.045 -> +4.5%)
        # Day 3: +10% (1.045 * 1.10 = 1.1495 -> +14.95%)
        rets = pd.Series([0.10, -0.05, 0.10])
        cum_rets = calculate_cumulative_returns(rets, is_prices=False)

        expected = [0.10, 0.045, 0.1495]
        np.testing.assert_allclose(cum_rets.values, expected, rtol=1e-5)

    def test_cumulative_returns_empty_series(self):
        """Verify edge case of empty series."""
        assert calculate_cumulative_returns(pd.Series(dtype=float)).empty


class TestAnnualizedReturn:
    """Test CAGR / Annualized Return calculations."""

    def test_annualized_return_exact_one_year(self):
        """A series spanning exactly 252 trading days with +21% total return."""
        prices = pd.Series(np.linspace(100.0, 121.0, 253))  # 253 points = 252 intervals
        ann_ret = calculate_annualized_return(prices, periods_per_year=252, is_prices=True)
        assert ann_ret is not None
        assert ann_ret == pytest.approx(0.21, rel=1e-4)

    def test_annualized_return_exact_two_years(self):
        """A series spanning exactly 504 trading days with +44% total return -> 20% CAGR."""
        # (1 + 0.44)^(252 / 504) - 1 = sqrt(1.44) - 1 = 1.20 - 1 = 0.20 (20%)
        prices = pd.Series(np.linspace(100.0, 144.0, 505))  # 504 intervals
        ann_ret = calculate_annualized_return(prices, periods_per_year=252, is_prices=True)
        assert ann_ret is not None
        assert ann_ret == pytest.approx(0.20, rel=1e-4)

    def test_annualized_return_complete_loss(self):
        """Total loss of capital returns -1.0 (-100%)."""
        prices = pd.Series([100.0, 50.0, 0.0])
        ann_ret = calculate_annualized_return(prices, periods_per_year=252, is_prices=True)
        assert ann_ret == -1.0

    def test_annualized_return_insufficient_data(self):
        """Single price point or empty series returns None."""
        assert calculate_annualized_return(pd.Series([100.0]), is_prices=True) is None
        assert calculate_annualized_return(pd.Series(dtype=float)) is None


class TestReturnMetricsBundle:
    """Test aggregate ReturnMetrics container."""

    def test_compute_return_metrics(self):
        prices = pd.Series([100.0, 105.0, 110.0])
        metrics = compute_return_metrics(prices, periods_per_year=252)

        assert metrics.total_trading_days == 3
        assert metrics.cumulative_return == pytest.approx(0.10)
        assert len(metrics.daily_returns) == 2
        assert metrics.annualized_return is not None
        assert metrics.annualized_return > 0.0
