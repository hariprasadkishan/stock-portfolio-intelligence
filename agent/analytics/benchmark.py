"""Benchmark comparative analytics for portfolio evaluation.

Mathematical Formulas:
1. Pearson Correlation:
   r = \\frac{Cov(R_p, R_b)}{s_p \\times s_b}

2. Sample Covariance:
   Cov(R_p, R_b) = \\frac{1}{N - 1} \\sum_{t=1}^N (R_{p, t} - \\bar{R}_p)(R_{b, t} - \\bar{R}_b)

3. Portfolio Beta:
   \\beta = \\frac{Cov(R_p, R_b)}{Var(R_b)}

4. Jensen's Alpha:
   \\alpha = R_{p, ann} - [R_f + \\beta \\times (R_{b, ann} - R_f)]
   where R_{p, ann} and R_{b, ann} are annualized returns over the aligned period,
   and R_f is the annualized risk-free rate.

5. Tracking Error:
   R_{active, t} = R_{p, t} - R_{b, t}
   TE = \\text{std}(R_{active}, \\text{ddof}=1) \\times \\sqrt{periods_per_year}

6. Information Ratio:
   IR = \\frac{R_{active, ann}}{TE} = \\frac{R_{p, ann} - R_{b, ann}}{TE}
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd

from agent.analytics.returns import calculate_annualized_return
from agent.analytics.types import BenchmarkMetrics


def align_returns(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> pd.DataFrame:
    """Align portfolio and benchmark daily returns strictly by date index.

    Drops missing dates without filling with artificial or forward-filled values.

    Returns:
        pd.DataFrame with columns ['portfolio', 'benchmark'] and matched datetime index.
    """
    if portfolio_returns is None or benchmark_returns is None:
        return pd.DataFrame(columns=["portfolio", "benchmark"])
    if portfolio_returns.empty or benchmark_returns.empty:
        return pd.DataFrame(columns=["portfolio", "benchmark"])

    p_clean = portfolio_returns.dropna()
    b_clean = benchmark_returns.dropna()

    aligned = pd.concat([p_clean, b_clean], axis=1, join="inner").dropna()
    aligned.columns = ["portfolio", "benchmark"]
    return aligned


def calculate_correlation(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> Optional[float]:
    """Calculate Pearson correlation coefficient between aligned portfolio and benchmark returns.

    Returns:
        Correlation in range [-1.0, 1.0], or None if insufficient data or zero variance.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    rp = aligned["portfolio"]
    rb = aligned["benchmark"]

    var_p = float(rp.var(ddof=1))
    var_b = float(rb.var(ddof=1))

    if var_p <= 1e-12 or var_b <= 1e-12 or np.isnan(var_p) or np.isnan(var_b):
        return None

    corr = float(rp.corr(rb))
    if np.isnan(corr) or np.isinf(corr):
        return None

    return max(-1.0, min(1.0, corr))


def calculate_covariance(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    annualize: bool = False,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate sample covariance (ddof=1) between portfolio and benchmark returns.

    Parameters:
        annualize: If True, scale by periods_per_year.
        periods_per_year: Annualization factor (default 252).

    Returns:
        Covariance as float, or None if fewer than 2 aligned observations.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    cov = float(aligned["portfolio"].cov(aligned["benchmark"]))
    if np.isnan(cov) or np.isinf(cov):
        return None

    if annualize:
        cov *= periods_per_year

    return cov


def calculate_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> Optional[float]:
    """Calculate portfolio Beta relative to a benchmark index.

    Formula:
        Beta = Cov(R_p, R_b) / Var(R_b)

    Returns:
        Beta as float, or None if benchmark variance is zero or insufficient data.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    rb = aligned["benchmark"]
    rp = aligned["portfolio"]

    var_b = float(rb.var(ddof=1))
    if var_b <= 1e-12 or np.isnan(var_b):
        return None

    cov_pb = float(rp.cov(rb))
    if np.isnan(cov_pb):
        return None

    beta = cov_pb / var_b
    if np.isnan(beta) or np.isinf(beta):
        return None

    return float(beta)


def calculate_jensens_alpha(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    return_method: str = "cagr",
) -> Optional[float]:
    """Calculate annualized Jensen's Alpha relative to the benchmark.

    Formula:
        Alpha = R_{p, ann} - [R_f + Beta * (R_{b, ann} - R_f)]

    Methodology:
        - return_method="cagr": Uses geometric CAGR for R_{p, ann} and R_{b, ann},
          consistent with Step 6A portfolio reporting.
        - return_method="arithmetic": Uses annualized mean daily return (mean * periods_per_year),
          consistent with classical single-period CAPM.

    Returns:
        Annualized alpha as float, or None if beta or returns cannot be determined.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    rp = aligned["portfolio"]
    rb = aligned["benchmark"]

    beta = calculate_beta(rp, rb)
    if beta is None:
        return None

    if return_method.lower() == "arithmetic":
        rp_ann = float(rp.mean() * periods_per_year)
        rb_ann = float(rb.mean() * periods_per_year)
    else:
        # Default: CAGR geometric compounding
        rp_ann_opt = calculate_annualized_return(
            rp, periods_per_year=periods_per_year, is_prices=False
        )
        rb_ann_opt = calculate_annualized_return(
            rb, periods_per_year=periods_per_year, is_prices=False
        )
        if rp_ann_opt is None or rb_ann_opt is None:
            return None
        rp_ann = rp_ann_opt
        rb_ann = rb_ann_opt

    expected_return = risk_free_rate + beta * (rb_ann - risk_free_rate)
    alpha = rp_ann - expected_return

    if np.isnan(alpha) or np.isinf(alpha):
        return None

    return float(alpha)


def calculate_tracking_error(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate annualized tracking error (standard deviation of excess active returns).

    Formula:
        TE = std(R_p - R_b, ddof=1) * sqrt(periods_per_year)

    Returns:
        Annualized tracking error as float, or None if fewer than 2 aligned observations.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    active_returns = aligned["portfolio"] - aligned["benchmark"]
    daily_te = float(active_returns.std(ddof=1))

    if np.isnan(daily_te):
        return None

    annualized_te = daily_te * np.sqrt(periods_per_year)
    return float(annualized_te)


def calculate_information_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252,
    return_method: str = "cagr",
) -> Optional[float]:
    """Calculate annualized Information Ratio (Active Return / Tracking Error).

    Formula:
        IR = (R_{p, ann} - R_{b, ann}) / Tracking_Error

    Returns:
        Information ratio as float, or None if tracking error is zero or undefined.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    if len(aligned) < 2:
        return None

    te = calculate_tracking_error(
        aligned["portfolio"], aligned["benchmark"], periods_per_year=periods_per_year
    )
    if te is None or te <= 1e-12:
        return None

    rp = aligned["portfolio"]
    rb = aligned["benchmark"]

    if return_method.lower() == "arithmetic":
        active_return_ann = float((rp.mean() - rb.mean()) * periods_per_year)
    else:
        rp_ann = calculate_annualized_return(
            rp, periods_per_year=periods_per_year, is_prices=False
        )
        rb_ann = calculate_annualized_return(
            rb, periods_per_year=periods_per_year, is_prices=False
        )
        if rp_ann is None or rb_ann is None:
            return None
        active_return_ann = rp_ann - rb_ann

    ir = active_return_ann / te
    if np.isnan(ir) or np.isinf(ir):
        return None

    return float(ir)


def compute_benchmark_metrics(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    return_method: str = "cagr",
) -> BenchmarkMetrics:
    """Compute comprehensive benchmark comparative metrics bundle.

    Returns:
        BenchmarkMetrics dataclass.
    """
    aligned = align_returns(portfolio_returns, benchmark_returns)
    n_aligned = len(aligned)

    if n_aligned < 2:
        return BenchmarkMetrics(
            correlation=None,
            covariance=None,
            beta=None,
            alpha=None,
            tracking_error=None,
            information_ratio=None,
            aligned_observations=n_aligned,
            risk_free_rate=risk_free_rate,
        )

    rp = aligned["portfolio"]
    rb = aligned["benchmark"]

    corr = calculate_correlation(rp, rb)
    cov = calculate_covariance(rp, rb, annualize=False, periods_per_year=periods_per_year)
    beta = calculate_beta(rp, rb)
    alpha = calculate_jensens_alpha(
        rp, rb, risk_free_rate=risk_free_rate, periods_per_year=periods_per_year, return_method=return_method
    )
    te = calculate_tracking_error(rp, rb, periods_per_year=periods_per_year)
    ir = calculate_information_ratio(
        rp, rb, periods_per_year=periods_per_year, return_method=return_method
    )

    return BenchmarkMetrics(
        correlation=corr,
        covariance=cov,
        beta=beta,
        alpha=alpha,
        tracking_error=te,
        information_ratio=ir,
        aligned_observations=n_aligned,
        risk_free_rate=risk_free_rate,
    )
