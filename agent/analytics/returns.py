"""Deterministic return calculations for asset and portfolio time-series.

Mathematical Formulas:
1. Daily Simple Return:
   R_t = (P_t / P_{t-1}) - 1

2. Cumulative Return:
   From prices:
     R_{cum, t} = (P_t - P_0) / P_0 = (P_t / P_0) - 1
   From daily returns:
     R_{cum, t} = \\prod_{i=1}^t (1 + R_i) - 1

3. Annualized Return (CAGR - Compound Annual Growth Rate):
   Given N trading periods and trading periods per year (default 252):
     R_{ann} = (1 + R_{total})^{(252 / N)} - 1
   where R_{total} is the total cumulative return across the entire span.
"""

from typing import Optional, Union
import numpy as np
import pandas as pd

from agent.analytics.types import ReturnMetrics


def calculate_daily_returns(
    prices: pd.Series,
    dropna: bool = True,
    fill_method: Optional[str] = "ffill",
) -> pd.Series:
    """Calculate simple daily percentage returns from a price series.

    Formula:
        R_t = (P_t - P_{t-1}) / P_{t-1} = (P_t / P_{t-1}) - 1

    Parameters:
        prices: Series of asset or portfolio prices indexed by date.
        dropna: If True, drop the leading NaN from the diff/shift operation.
        fill_method: Optional fill method for missing prices before return calculation (default: 'ffill').

    Returns:
        pd.Series of daily simple returns.
    """
    if prices is None or prices.empty:
        return pd.Series(dtype=float)

    clean_prices = prices.copy()
    if fill_method == "ffill":
        clean_prices = clean_prices.ffill()

    # Drop any remaining NaNs or invalid values
    clean_prices = clean_prices.dropna()

    if len(clean_prices) < 2:
        return pd.Series(dtype=float)

    # Avoid division by zero or negative base price
    prev_prices = clean_prices.shift(1)
    valid_mask = prev_prices > 0

    daily_returns = (clean_prices - prev_prices) / prev_prices
    daily_returns[~valid_mask] = np.nan

    if dropna:
        daily_returns = daily_returns.dropna()

    return daily_returns


def calculate_cumulative_returns(
    series: pd.Series,
    is_prices: bool = False,
) -> pd.Series:
    """Calculate cumulative return series.

    Formula:
        From prices:
            R_{cum, t} = (P_t - P_0) / P_0
        From returns:
            R_{cum, t} = \\prod_{i=1}^t (1 + R_i) - 1

    Parameters:
        series: Price series (if is_prices=True) or daily return series (if is_prices=False).
        is_prices: Flag indicating whether input is price series or return series.

    Returns:
        pd.Series of cumulative returns as decimal percentages (e.g. 0.15 for +15%).
    """
    if series is None or series.empty:
        return pd.Series(dtype=float)

    clean_series = series.dropna()
    if clean_series.empty:
        return pd.Series(dtype=float)

    if is_prices:
        p0 = clean_series.iloc[0]
        if p0 <= 0:
            return pd.Series(np.nan, index=clean_series.index)
        return (clean_series - p0) / p0
    else:
        # Input is daily returns
        compounded = (1.0 + clean_series).cumprod() - 1.0
        return compounded


def calculate_annualized_return(
    prices_or_returns: pd.Series,
    periods_per_year: int = 252,
    is_prices: bool = False,
) -> Optional[float]:
    """Calculate Compound Annual Growth Rate (CAGR) / Annualized Return.

    Formula:
        R_{ann} = (1 + R_{total})^{(periods_per_year / N)} - 1

    Parameters:
        prices_or_returns: Price series or daily returns series.
        periods_per_year: Annualization factor (default 252 for daily trading days).
        is_prices: True if input series represents prices, False if daily returns.

    Returns:
        Annualized return as float, or None if insufficient observations.
    """
    if prices_or_returns is None or prices_or_returns.empty:
        return None

    clean = prices_or_returns.dropna()
    if clean.empty:
        return None

    if is_prices:
        if len(clean) < 2:
            return None
        p_start = clean.iloc[0]
        p_end = clean.iloc[-1]
        if p_start <= 0:
            return None
        total_return = (p_end - p_start) / p_start
        n_periods = len(clean) - 1
    else:
        if len(clean) < 1:
            return None
        total_return = float((1.0 + clean).prod() - 1.0)
        n_periods = len(clean)

    if n_periods <= 0:
        return None

    # Handle total wipeout (capital loss >= 100%)
    if 1.0 + total_return <= 0.0:
        return -1.0

    exponent = float(periods_per_year) / float(n_periods)
    annualized = float((1.0 + total_return) ** exponent - 1.0)

    if np.isnan(annualized) or np.isinf(annualized):
        return None

    return annualized


def compute_return_metrics(
    prices: pd.Series,
    periods_per_year: int = 252,
) -> ReturnMetrics:
    """Compute structured return analytics from a historical price series.

    Parameters:
        prices: Daily price series (preferably adjusted close).
        periods_per_year: Trading periods per year (default 252).

    Returns:
        ReturnMetrics dataclass containing daily returns, cumulative return,
        annualized return, and total observations.
    """
    if prices is None or prices.empty:
        return ReturnMetrics(
            daily_returns=pd.Series(dtype=float),
            cumulative_return=0.0,
            annualized_return=None,
            total_trading_days=0,
        )

    clean_prices = prices.dropna()
    daily_rets = calculate_daily_returns(clean_prices, dropna=True)
    cum_series = calculate_cumulative_returns(clean_prices, is_prices=True)

    cum_return = float(cum_series.iloc[-1]) if not cum_series.empty else 0.0
    ann_return = calculate_annualized_return(
        clean_prices, periods_per_year=periods_per_year, is_prices=True
    )

    return ReturnMetrics(
        daily_returns=daily_rets,
        cumulative_return=cum_return,
        annualized_return=ann_return,
        total_trading_days=len(clean_prices),
    )
