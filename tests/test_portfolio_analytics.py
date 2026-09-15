"""Deterministic tests for portfolio value time-series and aggregate analytics."""

from datetime import date
import pandas as pd
import pytest

from agent.analytics.portfolio import (
    calculate_portfolio_value_series,
    compute_portfolio_analytics,
)


class TestPortfolioValuation:
    """Test multi-asset portfolio valuation time-series."""

    def test_multi_asset_portfolio_valuation(self):
        """Verify daily equity and total valuation from holdings and price matrix."""
        dates = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-04"])
        prices = pd.DataFrame(
            {
                "AAPL": [150.0, 160.0, 155.0],
                "MSFT": [300.0, 310.0, 320.0],
            },
            index=dates,
        )
        holdings = {"AAPL": 10.0, "MSFT": 5.0}
        cash = 1000.0

        # Day 0: Equity = (10 * 150) + (5 * 300) = 1500 + 1500 = 3000. Total = 4000.
        # Day 1: Equity = (10 * 160) + (5 * 310) = 1600 + 1550 = 3150. Total = 4150.
        #        Daily return = (4150 - 4000) / 4000 = 0.0375 (+3.75%).
        # Day 2: Equity = (10 * 155) + (5 * 320) = 1550 + 1600 = 3150. Total = 4150.
        #        Daily return = 0.0.
        df_val = calculate_portfolio_value_series(holdings, prices, cash_balance=cash)

        assert len(df_val) == 3
        assert list(df_val["equity_value"]) == [3000.0, 3150.0, 3150.0]
        assert list(df_val["cash_balance"]) == [1000.0, 1000.0, 1000.0]
        assert list(df_val["total_value"]) == [4000.0, 4150.0, 4150.0]
        assert df_val["daily_return"].iloc[1] == pytest.approx(0.0375)
        assert df_val["cumulative_return"].iloc[1] == pytest.approx(0.0375)

    def test_cash_only_portfolio(self):
        """Zero holdings yields constant total value equal to cash balance."""
        dates = pd.date_range("2025-01-01", periods=3)
        prices = pd.DataFrame({"AAPL": [100.0, 110.0, 120.0]}, index=dates)
        holdings = {"AAPL": 0.0}
        cash = 50000.0

        df_val = calculate_portfolio_value_series(holdings, prices, cash_balance=cash)
        assert (df_val["equity_value"] == 0.0).all()
        assert (df_val["total_value"] == 50000.0).all()
        assert df_val["cumulative_return"].iloc[-1] == 0.0

    def test_empty_prices_returns_empty_dataframe(self):
        """Empty price matrix yields structured empty dataframe."""
        df_val = calculate_portfolio_value_series({"AAPL": 10.0}, pd.DataFrame())
        assert df_val.empty
        assert "equity_value" in df_val.columns
        assert "total_value" in df_val.columns


class TestPortfolioAnalyticsSummary:
    """Test comprehensive aggregate portfolio performance analytics."""

    def test_portfolio_analytics_summary_exact_values(self):
        """Verify profit/loss, returns, and risk stats match known inputs."""
        dates = pd.date_range("2025-01-01", periods=4)
        # Value path: 10,000 -> 10,500 (+5%) -> 10,200 (-2.86%) -> 11,000 (+7.84%)
        values = pd.Series([10000.0, 10500.0, 10200.0, 11000.0], index=dates)

        summary = compute_portfolio_analytics(
            values, initial_capital=10000.0, risk_free_rate=0.02, periods_per_year=252
        )

        assert summary.initial_value == 10000.0
        assert summary.ending_value == 11000.0
        assert summary.total_profit_loss == 1000.0
        assert summary.total_return_pct == pytest.approx(0.10)
        assert summary.total_trading_days == 4
        assert summary.max_drawdown == pytest.approx((10200.0 - 10500.0) / 10500.0)
        assert summary.max_drawdown_duration_days == 1
        assert summary.annualized_return is not None
        assert summary.annualized_volatility is not None
        assert summary.sharpe_ratio is not None

    def test_portfolio_analytics_empty_series(self):
        """Edge case: empty series returns clean zero-filled summary."""
        summary = compute_portfolio_analytics(pd.Series(dtype=float))
        assert summary.initial_value == 0.0
        assert summary.ending_value == 0.0
        assert summary.total_profit_loss == 0.0
        assert summary.total_return_pct == 0.0
        assert summary.annualized_return is None
        assert summary.max_drawdown == 0.0
