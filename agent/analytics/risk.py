"""Deterministic risk analytics for asset and portfolio time-series.

Mathematical Formulas:
1. Annualized Volatility:
   s = \\sqrt{ \\frac{1}{N - 1} \\sum_{t=1}^N (R_t - \\bar{R})^2 }
   \\sigma_{ann} = s \\times \\sqrt{periods_per_year}

2. Sharpe Ratio:
   Sharpe = \\frac{R_{ann} - R_f}{\\sigma_{ann}}
   where R_{ann} is annualized return, R_f is annual risk-free rate, \\sigma_{ann} is annualized volatility.

3. Downside Deviation:
   \\sigma_{downside, daily} = \\sqrt{ \\frac{1}{N} \\sum_{t=1}^N \\min(R_t - MAR, 0)^2 }
   \\sigma_{downside, ann} = \\sigma_{downside, daily} \\times \\sqrt{periods_per_year}
   where MAR is Minimum Acceptable Return (default: R_f / periods_per_year or 0.0).

4. Sortino Ratio:
   Sortino = \\frac{R_{ann} - R_f}{\\sigma_{downside, ann}}

5. Maximum Drawdown (MDD):
   Peak_t = \\max_{0 \\le s \\le t} P_s
   DD_t = \\frac{P_t - Peak_t}{Peak_t}
   MDD = \\min_{0 \\le t \\le N} DD_t  (reported as non-positive float, e.g. -0.20 for -20%)

6. Maximum Drawdown Duration:
   The maximum count of consecutive trading days spent below the prior high-water mark (underwater).
"""

from typing import Optional, Union
import numpy as np
import pandas as pd

from agent.analytics.returns import calculate_annualized_return
from agent.analytics.types import RiskMetrics


def calculate_annualized_volatility(
    daily_returns: pd.Series,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate annualized sample standard deviation of daily returns.

    Formula:
        \\sigma_{ann} = \\text{std}(R, \\text{ddof}=1) \\times \\sqrt{periods_per_year}

    Parameters:
        daily_returns: pd.Series of simple daily returns.
        periods_per_year: Trading days per year (default 252).

    Returns:
        Annualized volatility as float, or None if fewer than 2 valid observations.
    """
    if daily_returns is None or daily_returns.empty:
        return None

    clean_returns = daily_returns.dropna()
    if len(clean_returns) < 2:
        return None

    daily_std = float(clean_returns.std(ddof=1))
    if np.isnan(daily_std):
        return None

    annualized_vol = daily_std * np.sqrt(periods_per_year)
    return float(annualized_vol)


def calculate_downside_deviation(
    daily_returns: pd.Series,
    target_return: float = 0.0,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate annualized downside deviation (semi-deviation below target return).

    Formula:
        \\sigma_{downside} = \\sqrt{ \\frac{1}{N} \\sum_{t=1}^N \\min(R_t - target, 0)^2 } \\times \\sqrt{periods_per_year}

    Parameters:
        daily_returns: pd.Series of daily returns.
        target_return: Minimum acceptable daily return (MAR), default 0.0.
        periods_per_year: Trading days per year (default 252).

    Returns:
        Annualized downside deviation, or None if insufficient observations.
    """
    if daily_returns is None or daily_returns.empty:
        return None

    clean = daily_returns.dropna()
    n = len(clean)
    if n < 2:
        return None

    downside_diff = np.minimum(clean - target_return, 0.0)
    downside_variance = np.sum(downside_diff ** 2) / n
    daily_downside_std = np.sqrt(downside_variance)

    return float(daily_downside_std * np.sqrt(periods_per_year))


def calculate_sharpe_ratio(
    daily_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate annualized Sharpe Ratio.

    Formula:
        Sharpe = (R_{ann} - R_f) / \\sigma_{ann}

    Parameters:
        daily_returns: pd.Series of daily returns.
        risk_free_rate: Annualized risk-free rate (e.g. 0.04 for 4%, default 0.0).
        periods_per_year: Trading days per year (default 252).

    Returns:
        Sharpe ratio as float, or None if volatility is zero/undefined or insufficient data.
    """
    if daily_returns is None or daily_returns.empty:
        return None

    clean = daily_returns.dropna()
    if len(clean) < 2:
        return None

    ann_return = calculate_annualized_return(
        clean, periods_per_year=periods_per_year, is_prices=False
    )
    if ann_return is None:
        return None

    ann_vol = calculate_annualized_volatility(clean, periods_per_year=periods_per_year)
    if ann_vol is None or ann_vol <= 1e-12:
        # Zero variance / volatility means Sharpe ratio is undefined
        return None

    sharpe = (ann_return - risk_free_rate) / ann_vol
    if np.isnan(sharpe) or np.isinf(sharpe):
        return None

    return float(sharpe)


def calculate_sortino_ratio(
    daily_returns: pd.Series,
    risk_free_rate: float = 0.0,
    target_return: Optional[float] = None,
    periods_per_year: int = 252,
) -> Optional[float]:
    """Calculate annualized Sortino Ratio.

    Formula:
        Sortino = (R_{ann} - R_f) / \\sigma_{downside, ann}

    Parameters:
        daily_returns: pd.Series of daily returns.
        risk_free_rate: Annualized risk-free rate (e.g. 0.02 for 2%, default 0.0).
        target_return: Minimum acceptable daily return (MAR). If None, defaults to risk_free_rate / periods_per_year.
        periods_per_year: Trading days per year (default 252).

    Returns:
        Sortino ratio as float, or None if downside deviation is zero or insufficient data.
    """
    if daily_returns is None or daily_returns.empty:
        return None

    clean = daily_returns.dropna()
    if len(clean) < 2:
        return None

    ann_return = calculate_annualized_return(
        clean, periods_per_year=periods_per_year, is_prices=False
    )
    if ann_return is None:
        return None

    daily_mar = (
        target_return
        if target_return is not None
        else risk_free_rate / float(periods_per_year)
    )

    downside_vol = calculate_downside_deviation(
        clean, target_return=daily_mar, periods_per_year=periods_per_year
    )
    if downside_vol is None or downside_vol <= 1e-12:
        # No downside deviation (all returns above MAR) -> Sortino is undefined
        return None

    sortino = (ann_return - risk_free_rate) / downside_vol
    if np.isnan(sortino) or np.isinf(sortino):
        return None

    return float(sortino)


def calculate_drawdown_series(prices_or_values: pd.Series) -> pd.Series:
    """Calculate the continuous percentage drawdown series from historical peaks.

    Formula:
        Peak_t = \\max_{0 \\le s \\le t} P_s
        DD_t = (P_t - Peak_t) / Peak_t

    Parameters:
        prices_or_values: Time series of asset prices or portfolio values.

    Returns:
        pd.Series of drawdowns (values <= 0.0).
    """
    if prices_or_values is None or prices_or_values.empty:
        return pd.Series(dtype=float)

    clean = prices_or_values.dropna()
    if clean.empty:
        return pd.Series(dtype=float)

    # Calculate cumulative high-water mark (expanding maximum)
    peaks = clean.cummax()

    # Prevent division by zero if peak is 0 or negative
    drawdown = (clean - peaks) / peaks.replace(0, np.nan)
    drawdown = drawdown.fillna(0.0)

    # Ensure drawdown is strictly <= 0
    drawdown = drawdown.clip(upper=0.0)
    return drawdown


def calculate_max_drawdown(prices_or_values: pd.Series) -> float:
    """Calculate maximum peak-to-trough drawdown (MDD).

    Formula:
        MDD = \\min_t DD_t

    Returns:
        Maximum drawdown as non-positive float (e.g. -0.22 for a 22% loss).
        Returns 0.0 if empty, single point, or strictly increasing series.
    """
    dd_series = calculate_drawdown_series(prices_or_values)
    if dd_series.empty:
        return 0.0

    mdd = float(dd_series.min())
    return mdd if not np.isnan(mdd) else 0.0


def calculate_max_drawdown_duration(prices_or_values: pd.Series) -> int:
    """Calculate maximum drawdown duration in trading days.

    The duration represents the longest contiguous sequence of trading days
    that the asset/portfolio remained below its prior peak before making a new high.

    Parameters:
        prices_or_values: Time series of asset prices or portfolio values.

    Returns:
        Integer count of trading days for the longest drawdown period.
    """
    dd_series = calculate_drawdown_series(prices_or_values)
    if dd_series.empty:
        return 0

    max_duration = 0
    current_duration = 0

    for dd in dd_series:
        if dd < 0.0:
            current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
        else:
            current_duration = 0

    return max_duration


def compute_risk_metrics(
    daily_returns: pd.Series,
    prices_or_values: Optional[pd.Series] = None,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> RiskMetrics:
    """Compute structured risk analytics package for asset or portfolio series.

    Parameters:
        daily_returns: pd.Series of simple daily returns.
        prices_or_values: Optional price or portfolio equity value series. If omitted,
                          a synthetic price series is constructed from daily returns.
        risk_free_rate: Annualized risk-free rate (default 0.0).
        periods_per_year: Trading days per year (default 252).

    Returns:
        RiskMetrics dataclass.
    """
    clean_returns = daily_returns.dropna() if daily_returns is not None else pd.Series(dtype=float)

    # Determine prices/values for drawdown calculation
    if prices_or_values is not None and not prices_or_values.empty:
        val_series = prices_or_values.dropna()
    elif not clean_returns.empty:
        val_series = (1.0 + clean_returns).cumprod()
    else:
        val_series = pd.Series(dtype=float)

    ann_vol = calculate_annualized_volatility(clean_returns, periods_per_year=periods_per_year)
    sharpe = calculate_sharpe_ratio(
        clean_returns, risk_free_rate=risk_free_rate, periods_per_year=periods_per_year
    )
    sortino = calculate_sortino_ratio(
        clean_returns, risk_free_rate=risk_free_rate, periods_per_year=periods_per_year
    )
    downside_dev = calculate_downside_deviation(
        clean_returns,
        target_return=risk_free_rate / float(periods_per_year),
        periods_per_year=periods_per_year,
    )
    mdd = calculate_max_drawdown(val_series)
    mdd_days = calculate_max_drawdown_duration(val_series)

    return RiskMetrics(
        annualized_volatility=ann_vol,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=mdd,
        max_drawdown_duration_days=mdd_days,
        downside_deviation=downside_dev,
        risk_free_rate=risk_free_rate,
    )
