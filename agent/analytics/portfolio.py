"""Portfolio value and performance analytics.

Mathematical Formulas:
1. Daily Equity Value:
   Equity_t = \\sum_{i \\in Assets} (Shares_i \\times Price_{i, t})

2. Total Portfolio Value:
   V_t = Equity_t + Cash_t

3. Profit & Loss (PnL):
   PnL_{abs} = V_{ending} - V_{initial}
   PnL_{\\%} = \\frac{V_{ending} - V_{initial}}{V_{initial}}

4. Portfolio Return:
   R_{port, t} = \\frac{V_t - V_{t-1}}{V_{t-1}}
"""

from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

from agent.analytics.returns import (
    calculate_annualized_return,
    calculate_cumulative_returns,
    calculate_daily_returns,
)
from agent.analytics.risk import (
    calculate_annualized_volatility,
    calculate_max_drawdown,
    calculate_max_drawdown_duration,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
)
from agent.analytics.types import PortfolioAnalyticsSummary, PortfolioSnapshot


def calculate_portfolio_value_series(
    holdings: Dict[str, float],
    price_matrix: pd.DataFrame,
    cash_balance: float = 0.0,
) -> pd.DataFrame:
    """Calculate the daily equity, cash, and total portfolio valuation time-series.

    Parameters:
        holdings: Dictionary mapping ticker symbol to share count. E.g. {"AAPL": 10.0, "SPY": 5.0}.
        price_matrix: DataFrame of asset prices indexed by date with ticker columns.
        cash_balance: Cash amount held in portfolio (assumed constant or base cash).

    Returns:
        pd.DataFrame containing columns:
        - equity_value: Sum of (shares * price)
        - cash_balance: Cash amount
        - total_value: equity_value + cash_balance
        - daily_return: Daily percentage return of total_value
        - cumulative_return: Cumulative return from inception
    """
    if price_matrix is None or price_matrix.empty:
        return pd.DataFrame(
            columns=["equity_value", "cash_balance", "total_value", "daily_return", "cumulative_return"]
        )

    clean_prices = price_matrix.copy().ffill().dropna(how="all")
    if clean_prices.empty:
        return pd.DataFrame(
            columns=["equity_value", "cash_balance", "total_value", "daily_return", "cumulative_return"]
        )

    # Calculate equity value for each date
    equity = pd.Series(0.0, index=clean_prices.index)
    for ticker, shares in holdings.items():
        clean_ticker = ticker.strip().upper()
        if clean_ticker in clean_prices.columns and shares > 0:
            equity += clean_prices[clean_ticker] * float(shares)

    total_value = equity + float(cash_balance)
    daily_returns = calculate_daily_returns(total_value, dropna=False)
    cum_returns = calculate_cumulative_returns(total_value, is_prices=True)

    df_result = pd.DataFrame(
        {
            "equity_value": equity.round(4),
            "cash_balance": round(float(cash_balance), 4),
            "total_value": total_value.round(4),
            "daily_return": daily_returns.round(6),
            "cumulative_return": cum_returns.round(6),
        },
        index=clean_prices.index,
    )
    df_result.index.name = "date"
    return df_result


def compute_portfolio_analytics(
    value_series: pd.Series,
    initial_capital: Optional[float] = None,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> PortfolioAnalyticsSummary:
    """Compute comprehensive portfolio analytics from a total value series.

    Parameters:
        value_series: Time-series of total portfolio values indexed by date.
        initial_capital: Optional initial capital base. If None, uses value_series.iloc[0].
        risk_free_rate: Annualized risk-free rate for Sharpe and Sortino (default 0.0).
        periods_per_year: Trading days per year (default 252).

    Returns:
        PortfolioAnalyticsSummary dataclass.
    """
    if value_series is None or value_series.empty:
        return PortfolioAnalyticsSummary(
            initial_value=0.0,
            ending_value=0.0,
            total_profit_loss=0.0,
            total_return_pct=0.0,
            annualized_return=None,
            annualized_volatility=None,
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=0.0,
            max_drawdown_duration_days=0,
            total_trading_days=0,
            risk_free_rate=risk_free_rate,
            value_history=pd.DataFrame(),
        )

    clean_vals = value_series.dropna()
    if clean_vals.empty:
        return PortfolioAnalyticsSummary(
            initial_value=0.0,
            ending_value=0.0,
            total_profit_loss=0.0,
            total_return_pct=0.0,
            annualized_return=None,
            annualized_volatility=None,
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=0.0,
            max_drawdown_duration_days=0,
            total_trading_days=0,
            risk_free_rate=risk_free_rate,
            value_history=pd.DataFrame(),
        )

    v_start = float(initial_capital) if initial_capital is not None else float(clean_vals.iloc[0])
    v_end = float(clean_vals.iloc[-1])
    n_days = len(clean_vals)

    pnl_abs = v_end - v_start
    total_ret_pct = (pnl_abs / v_start) if v_start > 0 else 0.0

    daily_rets = calculate_daily_returns(clean_vals, dropna=True)
    ann_ret = calculate_annualized_return(
        clean_vals, periods_per_year=periods_per_year, is_prices=True
    )
    ann_vol = calculate_annualized_volatility(daily_rets, periods_per_year=periods_per_year)
    sharpe = calculate_sharpe_ratio(
        daily_rets, risk_free_rate=risk_free_rate, periods_per_year=periods_per_year
    )
    sortino = calculate_sortino_ratio(
        daily_rets, risk_free_rate=risk_free_rate, periods_per_year=periods_per_year
    )
    mdd = calculate_max_drawdown(clean_vals)
    mdd_days = calculate_max_drawdown_duration(clean_vals)

    # Construct valuation history dataframe
    cum_rets = calculate_cumulative_returns(clean_vals, is_prices=True)
    history_df = pd.DataFrame(
        {
            "total_value": clean_vals,
            "daily_return": calculate_daily_returns(clean_vals, dropna=False),
            "cumulative_return": cum_rets,
        },
        index=clean_vals.index,
    )

    return PortfolioAnalyticsSummary(
        initial_value=float(v_start),
        ending_value=float(v_end),
        total_profit_loss=float(pnl_abs),
        total_return_pct=float(total_ret_pct),
        annualized_return=float(ann_ret) if ann_ret is not None else None,
        annualized_volatility=float(ann_vol) if ann_vol is not None else None,
        sharpe_ratio=float(sharpe) if sharpe is not None else None,
        sortino_ratio=float(sortino) if sortino is not None else None,
        max_drawdown=float(mdd),
        max_drawdown_duration_days=mdd_days,
        total_trading_days=n_days,
        risk_free_rate=risk_free_rate,
        value_history=history_df,
    )
