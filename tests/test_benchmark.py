"""Deterministic tests for benchmark comparative metrics (correlation, covariance, beta, alpha, TE, IR)."""

from datetime import date
import numpy as np
import pandas as pd
import pytest

from agent.analytics.benchmark import (
    align_returns,
    calculate_beta,
    calculate_correlation,
    calculate_covariance,
    calculate_information_ratio,
    calculate_jensens_alpha,
    calculate_tracking_error,
    compute_benchmark_metrics,
)


class TestAlignment:
    """Test date-based alignment of portfolio and benchmark time-series."""

    def test_align_returns_inner_join_no_silent_fill(self):
        """Verify mismatched dates are dropped strictly without synthetic filling."""
        p_dates = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-04", "2025-01-07"])
        b_dates = pd.to_datetime(["2025-01-03", "2025-01-04", "2025-01-05", "2025-01-07"])

        rp = pd.Series([0.01, 0.02, -0.01, 0.03], index=p_dates)
        rb = pd.Series([0.015, -0.005, 0.02, 0.025], index=b_dates)

        aligned = align_returns(rp, rb)
        # Expected intersection: 2025-01-03, 2025-01-04, 2025-01-07 (3 dates)
        assert len(aligned) == 3
        assert list(aligned.index) == [
            pd.Timestamp("2025-01-03"),
            pd.Timestamp("2025-01-04"),
            pd.Timestamp("2025-01-07"),
        ]
        assert aligned["portfolio"].iloc[0] == 0.02
        assert aligned["benchmark"].iloc[0] == 0.015

    def test_align_empty_series(self):
        """Empty series returns empty aligned dataframe."""
        aligned = align_returns(pd.Series(dtype=float), pd.Series([0.01]))
        assert aligned.empty


class TestCorrelationAndCovariance:
    """Test Pearson correlation and sample covariance."""

    def test_perfect_correlation(self):
        """Identical or scaled returns have correlation = 1.0."""
        dates = pd.date_range("2025-01-01", periods=5)
        rb = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02], index=dates)
        rp = rb * 2.0  # Perfect linear relationship

        corr = calculate_correlation(rp, rb)
        assert corr is not None
        assert corr == pytest.approx(1.0, rel=1e-5)

    def test_perfect_negative_correlation(self):
        """Inversely proportional returns have correlation = -1.0."""
        dates = pd.date_range("2025-01-01", periods=5)
        rb = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02], index=dates)
        rp = -rb

        corr = calculate_correlation(rp, rb)
        assert corr is not None
        assert corr == pytest.approx(-1.0, rel=1e-5)

    def test_covariance_analytical(self):
        """Verify sample covariance matches analytical computation."""
        dates = pd.date_range("2025-01-01", periods=3)
        rp = pd.Series([0.02, 0.04, 0.06], index=dates)  # mean = 0.04, diffs = [-0.02, 0.0, 0.02]
        rb = pd.Series([0.01, 0.02, 0.03], index=dates)  # mean = 0.02, diffs = [-0.01, 0.0, 0.01]
        # Sum of products: (-0.02 * -0.01) + (0) + (0.02 * 0.01) = 0.0002 + 0.0002 = 0.0004
        # Covariance (ddof=1) = 0.0004 / 2 = 0.0002
        cov = calculate_covariance(rp, rb, annualize=False)
        assert cov == pytest.approx(0.0002, rel=1e-6)

        cov_ann = calculate_covariance(rp, rb, annualize=True, periods_per_year=252)
        assert cov_ann == pytest.approx(0.0002 * 252, rel=1e-6)


class TestBetaAndAlpha:
    """Test Portfolio Beta and Jensen's Alpha."""

    def test_beta_exact_linear_multiple(self):
        """If Rp = 1.5 * Rb + epsilon where epsilon is orthogonal, Beta = 1.5."""
        dates = pd.date_range("2025-01-01", periods=5)
        rb = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02], index=dates)
        rp = 1.5 * rb

        beta = calculate_beta(rp, rb)
        assert beta is not None
        assert beta == pytest.approx(1.5, rel=1e-5)

    def test_beta_zero_benchmark_variance(self):
        """Constant benchmark returns have 0 variance -> Beta is None."""
        dates = pd.date_range("2025-01-01", periods=4)
        rb = pd.Series([0.01, 0.01, 0.01, 0.01], index=dates)
        rp = pd.Series([0.02, -0.01, 0.03, 0.01], index=dates)

        beta = calculate_beta(rp, rb)
        assert beta is None

    def test_jensens_alpha_exact(self):
        """Verify Jensen's Alpha against hand-calculated analytical result.
        
        Using arithmetic return method:
        Suppose Rp mean = 0.001 (annualized 0.252 = 25.2%)
        Suppose Rb mean = 0.0005 (annualized 0.126 = 12.6%)
        Suppose Beta = 1.2
        Rf = 0.03 (3.0%)
        Expected return = 0.03 + 1.2 * (0.126 - 0.03) = 0.03 + 1.2 * 0.096 = 0.03 + 0.1152 = 0.1452 (14.52%)
        Alpha = 0.252 - 0.1452 = 0.1068 (10.68%)
        """
        dates = pd.date_range("2025-01-01", periods=5)
        # Synthetic data with exact known beta and means
        rb = pd.Series([0.0005 + 0.01, 0.0005 - 0.01, 0.0005 + 0.01, 0.0005 - 0.01, 0.0005], index=dates)
        # Rp = 1.2 * (Rb - mean_b) + mean_p
        diff_b = rb - rb.mean()
        rp = 1.2 * diff_b + 0.001

        beta = calculate_beta(rp, rb)
        assert beta == pytest.approx(1.2, rel=1e-4)

        alpha = calculate_jensens_alpha(
            rp, rb, risk_free_rate=0.03, periods_per_year=252, return_method="arithmetic"
        )
        assert alpha is not None
        expected_alpha = (0.001 * 252) - (0.03 + 1.2 * ((0.0005 * 252) - 0.03))
        assert alpha == pytest.approx(expected_alpha, rel=1e-4)


class TestTrackingErrorAndInformationRatio:
    """Test Tracking Error and Information Ratio."""

    def test_tracking_error_analytical(self):
        """Verify tracking error of active return spread."""
        dates = pd.date_range("2025-01-01", periods=4)
        # Active spread: Rp - Rb = [0.01, -0.01, 0.01, -0.01]
        # Active mean = 0.0. Sample std = sqrt(0.0004 / 3)
        # Annualized TE = sqrt(0.0004 / 3 * 252) = 0.02 * sqrt(84) = 0.183303...
        rb = pd.Series([0.0, 0.0, 0.0, 0.0], index=dates)
        rp = pd.Series([0.01, -0.01, 0.01, -0.01], index=dates)

        te = calculate_tracking_error(rp, rb, periods_per_year=252)
        expected_te = 0.02 * np.sqrt(84)
        assert te is not None
        assert te == pytest.approx(expected_te, rel=1e-5)

    def test_information_ratio_zero_tracking_error(self):
        """Zero tracking error returns None (safe from ZeroDivisionError)."""
        dates = pd.date_range("2025-01-01", periods=4)
        rb = pd.Series([0.01, 0.02, 0.03, 0.04], index=dates)
        rp = rb.copy()

        ir = calculate_information_ratio(rp, rb)
        assert ir is None


class TestBenchmarkMetricsBundle:
    """Test compute_benchmark_metrics aggregator."""

    def test_compute_benchmark_metrics(self):
        dates = pd.date_range("2025-01-01", periods=10)
        np.random.seed(123)
        rb = pd.Series(np.random.normal(0.0005, 0.01, 10), index=dates)
        rp = 1.1 * rb + np.random.normal(0.0002, 0.005, 10)

        metrics = compute_benchmark_metrics(rp, rb, risk_free_rate=0.02, periods_per_year=252)
        assert metrics.aligned_observations == 10
        assert metrics.beta is not None
        assert metrics.correlation is not None
        assert metrics.tracking_error is not None
        assert metrics.alpha is not None
