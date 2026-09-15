"""Deterministic unit tests for Portfolio Intelligence analytics layer.

Tests:
- Asset Allocation (market values, decimal weights, validation)
- Sector Exposure (grouping, 'Unknown' handling, reconciliation)
- Concentration (HHI, largest holding, top-3, top-5)
- Return Contribution (weights * returns, percentage of portfolio return, zero return safety)
- Diversification / Correlation (pairwise correlation, diagonal exclusion, pair identification)
- Portfolio Intelligence Summary (bundle integration and empty/invalid input handling)
"""

import numpy as np
import pandas as pd
import pytest

from agent.analytics.portfolio_intelligence import (
    calculate_asset_allocation,
    calculate_concentration_metrics,
    calculate_diversification_metrics,
    calculate_return_contributions,
    calculate_sector_exposure,
    compute_portfolio_intelligence,
)


class TestAssetAllocation:
    """Test asset allocation, market values, and decimal portfolio weights."""

    def test_two_asset_allocation_exact_weights(self):
        """Verify 2 assets with equal market values produce 0.50 weights."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "shares": [10.0, 20.0],
                "current_price": [100.0, 50.0],
            }
        )
        # AAPL: 10 * 100 = 1000
        # MSFT: 20 * 50 = 1000
        # Total = 2000. Weight each = 0.50.
        df_alloc = calculate_asset_allocation(holdings)

        assert len(df_alloc) == 2
        assert list(df_alloc["ticker"]) == ["AAPL", "MSFT"]
        assert list(df_alloc["market_value"]) == [1000.0, 1000.0]
        assert list(df_alloc["portfolio_weight"]) == [0.50, 0.50]
        assert df_alloc["portfolio_weight"].sum() == pytest.approx(1.0)

    def test_allocation_weights_sum_to_one(self):
        """Verify weights sum to 1.0 across arbitrary holdings."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "NVDA", "AMZN"],
                "shares": [15.0, 25.0, 10.0],
                "current_price": [220.0, 120.0, 180.0],
            }
        )
        df_alloc = calculate_asset_allocation(holdings)
        assert df_alloc["portfolio_weight"].sum() == pytest.approx(1.0, rel=1e-6)

    def test_empty_holdings(self):
        """Empty holdings DataFrame returns empty structured DataFrame."""
        df_alloc = calculate_asset_allocation(pd.DataFrame())
        assert df_alloc.empty
        assert list(df_alloc.columns) == [
            "ticker",
            "shares",
            "current_price",
            "market_value",
            "portfolio_weight",
        ]

    def test_missing_or_invalid_prices_and_shares(self):
        """Invalid shares (<=0) or prices (<=0, NaN) are dropped; valid rows retained."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "BAD_PRICE", "ZERO_SHARES", "NEG_PRICE", "VALID_ETF"],
                "shares": [10.0, 5.0, 0.0, 8.0, 20.0],
                "current_price": [150.0, np.nan, 200.0, -10.0, 50.0],
            }
        )
        df_alloc = calculate_asset_allocation(holdings)

        # Only AAPL (10 * 150 = 1500) and VALID_ETF (20 * 50 = 1000) are valid
        assert len(df_alloc) == 2
        assert set(df_alloc["ticker"]) == {"AAPL", "VALID_ETF"}
        assert df_alloc["portfolio_weight"].sum() == pytest.approx(1.0)

    def test_zero_total_portfolio_value(self):
        """If all rows have 0 value or invalid data, returns empty dataframe."""
        holdings = pd.DataFrame(
            {
                "ticker": ["A", "B"],
                "shares": [0.0, -5.0],
                "current_price": [10.0, 20.0],
            }
        )
        df_alloc = calculate_asset_allocation(holdings)
        assert df_alloc.empty


class TestSectorExposure:
    """Test portfolio exposure aggregation by sector."""

    def test_multiple_assets_in_same_sector(self):
        """Assets in same sector are aggregated and reconciled against total."""
        alloc = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT", "JNJ"],
                "market_value": [3000.0, 2000.0, 5000.0],
                "sector": ["Technology", "Technology", "Healthcare"],
            }
        )
        df_sector = calculate_sector_exposure(alloc)

        assert len(df_sector) == 2
        # Technology: 3000 + 2000 = 5000 (50%)
        # Healthcare: 5000 (50%)
        tech_row = df_sector[df_sector["sector"] == "Technology"].iloc[0]
        health_row = df_sector[df_sector["sector"] == "Healthcare"].iloc[0]

        assert tech_row["market_value"] == 5000.0
        assert tech_row["portfolio_weight"] == pytest.approx(0.50)
        assert health_row["market_value"] == 5000.0
        assert health_row["portfolio_weight"] == pytest.approx(0.50)
        assert df_sector["portfolio_weight"].sum() == pytest.approx(1.0)

    def test_missing_sector_explicit_unknown(self):
        """Missing or None sector is assigned explicit 'Unknown' without dropping asset."""
        alloc = pd.DataFrame(
            {
                "ticker": ["AAPL", "MYSTERY_ETF", "UNKNOWN_CORP"],
                "market_value": [4000.0, 4000.0, 2000.0],
                "sector": ["Technology", None, np.nan],
            }
        )
        df_sector = calculate_sector_exposure(alloc)

        # Sectors should be Technology (4000) and Unknown (4000 + 2000 = 6000)
        assert set(df_sector["sector"]) == {"Technology", "Unknown"}
        unknown_row = df_sector[df_sector["sector"] == "Unknown"].iloc[0]
        assert unknown_row["market_value"] == 6000.0
        assert unknown_row["portfolio_weight"] == pytest.approx(0.60)
        assert df_sector["portfolio_weight"].sum() == pytest.approx(1.0)

    def test_sector_mapping_dictionary(self):
        """Sector map fills missing sectors in allocation dataframe."""
        alloc = pd.DataFrame(
            {
                "ticker": ["AAPL", "SPY"],
                "market_value": [6000.0, 4000.0],
            }
        )
        sector_map = {"AAPL": "Technology", "SPY": "Broad Market ETF"}
        df_sector = calculate_sector_exposure(alloc, sector_map=sector_map)

        assert len(df_sector) == 2
        assert set(df_sector["sector"]) == {"Technology", "Broad Market ETF"}


class TestConcentrationAnalytics:
    """Test HHI and top holding concentration."""

    def test_exact_hhi_example_50_30_20(self):
        """Verify HHI = 0.50^2 + 0.30^2 + 0.20^2 = 0.25 + 0.09 + 0.04 = 0.38."""
        weights = {"AAPL": 0.50, "MSFT": 0.30, "GOOGL": 0.20}
        conc = calculate_concentration_metrics(weights)

        assert conc.hhi == pytest.approx(0.38, rel=1e-5)
        assert conc.largest_holding_ticker == "AAPL"
        assert conc.largest_holding_weight == pytest.approx(0.50)
        assert conc.top_3_weight == pytest.approx(1.0)
        assert conc.top_5_weight == pytest.approx(1.0)
        assert conc.total_holdings_count == 3

    def test_concentration_top_n_with_fewer_holdings(self):
        """Top-3 and top-5 with only 2 holdings sums all available."""
        weights = pd.Series({"AAPL": 0.75, "MSFT": 0.25})
        conc = calculate_concentration_metrics(weights)

        assert conc.hhi == pytest.approx(0.75**2 + 0.25**2)  # 0.5625 + 0.0625 = 0.625
        assert conc.largest_holding_ticker == "AAPL"
        assert conc.largest_holding_weight == pytest.approx(0.75)
        assert conc.top_3_weight == pytest.approx(1.0)
        assert conc.top_5_weight == pytest.approx(1.0)
        assert conc.total_holdings_count == 2

    def test_concentration_from_dataframe(self):
        """Extracts concentration directly from DataFrame with 'ticker' and 'portfolio_weight'."""
        df = pd.DataFrame(
            {
                "ticker": ["A", "B", "C", "D", "E", "F"],
                "portfolio_weight": [0.40, 0.20, 0.15, 0.10, 0.10, 0.05],
            }
        )
        conc = calculate_concentration_metrics(df)

        assert conc.largest_holding_ticker == "A"
        assert conc.largest_holding_weight == pytest.approx(0.40)
        # Top 3: 0.40 + 0.20 + 0.15 = 0.75
        assert conc.top_3_weight == pytest.approx(0.75)
        # Top 5: 0.40 + 0.20 + 0.15 + 0.10 + 0.10 = 0.95
        assert conc.top_5_weight == pytest.approx(0.95)
        assert conc.total_holdings_count == 6

    def test_concentration_empty_portfolio(self):
        """Empty weights returns clean zero-filled metrics."""
        conc = calculate_concentration_metrics({})
        assert conc.hhi == 0.0
        assert conc.largest_holding_ticker is None
        assert conc.largest_holding_weight == 0.0
        assert conc.top_3_weight == 0.0
        assert conc.top_5_weight == 0.0
        assert conc.total_holdings_count == 0


class TestReturnContribution:
    """Test return contribution calculations and reconciliation."""

    def test_exact_weighted_contribution_and_sum(self):
        """Verify contributions reconcile with total portfolio return.
        
        AAPL: weight 0.60, return +10% -> contribution = +0.06
        MSFT: weight 0.40, return -5%  -> contribution = -0.02
        Total portfolio return = +0.04 (+4%)
        Contribution pct:
        AAPL: 0.06 / 0.04 = 1.50 (150%)
        MSFT: -0.02 / 0.04 = -0.50 (-50%)
        """
        weights = {"AAPL": 0.60, "MSFT": 0.40}
        returns = {"AAPL": 0.10, "MSFT": -0.05}

        df_contrib = calculate_return_contributions(weights, returns)
        assert len(df_contrib) == 2

        aapl_row = df_contrib[df_contrib["ticker"] == "AAPL"].iloc[0]
        msft_row = df_contrib[df_contrib["ticker"] == "MSFT"].iloc[0]

        assert aapl_row["contribution"] == pytest.approx(0.06)
        assert aapl_row["contribution_pct"] == pytest.approx(1.50)

        assert msft_row["contribution"] == pytest.approx(-0.02)
        assert msft_row["contribution_pct"] == pytest.approx(-0.50)

        # Sum of contributions must equal weighted return: 0.06 - 0.02 = 0.04
        assert df_contrib["contribution"].sum() == pytest.approx(0.04)

    def test_zero_portfolio_return_safety(self):
        """Zero portfolio return sets contribution_pct to None rather than raising ZeroDivisionError."""
        weights = {"AAPL": 0.50, "MSFT": 0.50}
        returns = {"AAPL": 0.10, "MSFT": -0.10}  # Net portfolio return = 0.0

        df_contrib = calculate_return_contributions(weights, returns)
        assert df_contrib["contribution"].sum() == pytest.approx(0.0)
        assert df_contrib["contribution_pct"].isna().all()

    def test_non_overlapping_tickers(self):
        """Only matching tickers are evaluated."""
        weights = {"AAPL": 1.0}
        returns = {"MSFT": 0.10}
        df_contrib = calculate_return_contributions(weights, returns)
        assert df_contrib.empty


class TestDiversificationAnalytics:
    """Test correlation matrix and pairwise summary statistics."""

    def test_perfect_correlations_matrix_and_summary(self):
        """Verify correlation matrix and pairwise stats on synthetic paths."""
        dates = pd.date_range("2025-01-01", periods=5)
        # R1, R2 = 2 * R1 (corr = 1.0), R3 = -R1 (corr = -1.0)
        r1 = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02], index=dates)
        r2 = r1 * 2.0
        r3 = -r1

        df_returns = pd.DataFrame({"A": r1, "B": r2, "C": r3})
        div = calculate_diversification_metrics(df_returns)

        assert div.total_pairs_count == 3  # (A,B), (A,C), (B,C)
        # Pairs:
        # corr(A, B) = 1.0
        # corr(A, C) = -1.0
        # corr(B, C) = -1.0
        # Average = (1.0 - 1.0 - 1.0) / 3 = -1.0 / 3 = -0.333333
        assert div.highest_pairwise_correlation == pytest.approx(1.0, rel=1e-5)
        assert set(div.highest_correlation_pair) == {"A", "B"}
        assert div.lowest_pairwise_correlation == pytest.approx(-1.0, rel=1e-5)
        assert div.average_pairwise_correlation == pytest.approx(-1.0 / 3.0, rel=1e-5)

    def test_diagonal_excluded_from_pairwise_average(self):
        """Diagonal self-correlations (1.0) must NOT inflate average pairwise correlation."""
        dates = pd.date_range("2025-01-01", periods=5)
        # Two assets with correlation 0.40
        r1 = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02], index=dates)
        # Add orthogonal component
        r2 = pd.Series([0.02, 0.01, 0.02, 0.01, -0.01], index=dates)

        df = pd.DataFrame({"X": r1, "Y": r2})
        div = calculate_diversification_metrics(df)

        expected_corr = float(r1.corr(r2))
        assert div.total_pairs_count == 1
        assert div.average_pairwise_correlation == pytest.approx(expected_corr, rel=1e-5)
        assert div.highest_pairwise_correlation == pytest.approx(expected_corr, rel=1e-5)

    def test_single_asset_or_empty_returns_matrix(self):
        """Single asset returns no pairwise stats."""
        df_single = pd.DataFrame({"AAPL": [0.01, 0.02, -0.01]})
        div = calculate_diversification_metrics(df_single)
        assert div.average_pairwise_correlation is None
        assert div.highest_pairwise_correlation is None
        assert div.total_pairs_count == 0

        div_empty = calculate_diversification_metrics(pd.DataFrame())
        assert div_empty.total_pairs_count == 0


class TestPortfolioIntelligenceSummary:
    """Test full integration bundle compute_portfolio_intelligence."""

    def test_compute_portfolio_intelligence_complete(self):
        """Verify all subcomponents assemble properly into PortfolioIntelligenceSummary."""
        holdings = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT", "SPY"],
                "shares": [10.0, 5.0, 4.0],
                "current_price": [150.0, 300.0, 500.0],
                "sector": ["Technology", "Technology", "ETF"],
            }
        )
        # AAPL: 1500 (30%), MSFT: 1500 (30%), SPY: 2000 (40%). Total = 5000.
        asset_returns = {"AAPL": 0.10, "MSFT": 0.05, "SPY": 0.02}

        dates = pd.date_range("2025-01-01", periods=6)
        returns_matrix = pd.DataFrame(
            {
                "AAPL": [0.01, -0.01, 0.02, -0.01, 0.01, 0.02],
                "MSFT": [0.015, -0.005, 0.01, -0.02, 0.01, 0.015],
                "SPY": [0.005, -0.002, 0.008, -0.005, 0.004, 0.006],
            },
            index=dates,
        )

        summary = compute_portfolio_intelligence(
            holdings_df=holdings,
            asset_returns=asset_returns,
            returns_matrix=returns_matrix,
        )

        assert summary.total_market_value == 5000.0
        assert len(summary.allocations) == 3
        assert len(summary.sector_exposures) == 2  # Technology, ETF
        assert summary.concentration.total_holdings_count == 3
        assert summary.concentration.largest_holding_ticker == "SPY"
        assert summary.concentration.largest_holding_weight == pytest.approx(0.40)
        assert summary.portfolio_return is not None
        # Portfolio return = 0.30*0.10 + 0.30*0.05 + 0.40*0.02 = 0.03 + 0.015 + 0.008 = 0.053 (+5.3%)
        assert summary.portfolio_return == pytest.approx(0.053, rel=1e-5)
        assert summary.diversification.total_pairs_count == 3
        assert summary.diversification.average_pairwise_correlation is not None

    def test_compute_portfolio_intelligence_empty_inputs(self):
        """Gracefully handle empty holdings."""
        summary = compute_portfolio_intelligence(pd.DataFrame())
        assert summary.total_market_value == 0.0
        assert len(summary.allocations) == 0
        assert summary.concentration.total_holdings_count == 0
        assert summary.portfolio_return is None
