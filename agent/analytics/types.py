"""Data structures and types for financial analytics engine."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional
import pandas as pd


@dataclass(frozen=True)
class ReturnMetrics:
    """Calculated return metrics for an asset or portfolio."""

    daily_returns: pd.Series
    cumulative_return: float
    annualized_return: Optional[float]
    total_trading_days: int

    def to_dict(self) -> dict:
        return {
            "cumulative_return": self.cumulative_return,
            "annualized_return": self.annualized_return,
            "total_trading_days": self.total_trading_days,
        }


@dataclass(frozen=True)
class RiskMetrics:
    """Calculated risk metrics for an asset or portfolio."""

    annualized_volatility: Optional[float]
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    max_drawdown: float
    max_drawdown_duration_days: int
    downside_deviation: Optional[float]
    risk_free_rate: float

    def to_dict(self) -> dict:
        return {
            "annualized_volatility": self.annualized_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration_days": self.max_drawdown_duration_days,
            "downside_deviation": self.downside_deviation,
            "risk_free_rate": self.risk_free_rate,
        }


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Single point in time portfolio valuation snapshot."""

    snapshot_date: date
    equity_value: float
    cash_balance: float
    total_value: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None


@dataclass
class PortfolioAnalyticsSummary:
    """Comprehensive portfolio analytics summary."""

    initial_value: float
    ending_value: float
    total_profit_loss: float
    total_return_pct: float
    annualized_return: Optional[float]
    annualized_volatility: Optional[float]
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    max_drawdown: float
    max_drawdown_duration_days: int
    total_trading_days: int
    risk_free_rate: float
    value_history: pd.DataFrame = field(default_factory=pd.DataFrame)

    def to_dict(self) -> dict:
        return {
            "initial_value": self.initial_value,
            "ending_value": self.ending_value,
            "total_profit_loss": self.total_profit_loss,
            "total_return_pct": self.total_return_pct,
            "annualized_return": self.annualized_return,
            "annualized_volatility": self.annualized_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration_days": self.max_drawdown_duration_days,
            "total_trading_days": self.total_trading_days,
            "risk_free_rate": self.risk_free_rate,
        }
