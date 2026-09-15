"""Deterministic financial analytics package for Stock Portfolio Intelligence & Risk Analytics."""

from agent.analytics.portfolio import (
    calculate_portfolio_value_series,
    compute_portfolio_analytics,
)
from agent.analytics.returns import (
    calculate_annualized_return,
    calculate_cumulative_returns,
    calculate_daily_returns,
    compute_return_metrics,
)
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
from agent.analytics.types import (
    PortfolioAnalyticsSummary,
    PortfolioSnapshot,
    ReturnMetrics,
    RiskMetrics,
)

__all__ = [
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_annualized_return",
    "compute_return_metrics",
    "calculate_annualized_volatility",
    "calculate_downside_deviation",
    "calculate_drawdown_series",
    "calculate_max_drawdown",
    "calculate_max_drawdown_duration",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "compute_risk_metrics",
    "calculate_portfolio_value_series",
    "compute_portfolio_analytics",
    "ReturnMetrics",
    "RiskMetrics",
    "PortfolioSnapshot",
    "PortfolioAnalyticsSummary",
]
