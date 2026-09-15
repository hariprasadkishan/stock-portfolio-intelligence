"""Data structures and types for financial analytics engine."""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple
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


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Calculated benchmark comparison metrics for a portfolio."""

    correlation: Optional[float]
    covariance: Optional[float]
    beta: Optional[float]
    alpha: Optional[float]
    tracking_error: Optional[float]
    information_ratio: Optional[float]
    aligned_observations: int
    risk_free_rate: float

    def to_dict(self) -> dict:
        return {
            "correlation": self.correlation,
            "covariance": self.covariance,
            "beta": self.beta,
            "alpha": self.alpha,
            "tracking_error": self.tracking_error,
            "information_ratio": self.information_ratio,
            "aligned_observations": self.aligned_observations,
            "risk_free_rate": self.risk_free_rate,
        }


@dataclass(frozen=True)
class TailRiskMetrics:
    """Historical Value at Risk (VaR) and Conditional VaR (Expected Shortfall).

    Sign convention:
    Positive numbers denote loss magnitudes (e.g. 0.025 denotes a 2.5% loss).
    """

    var_95: Optional[float]
    cvar_95: Optional[float]
    confidence_level: float
    var_custom: Optional[float]
    cvar_custom: Optional[float]
    total_observations: int

    def to_dict(self) -> dict:
        return {
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "confidence_level": self.confidence_level,
            "var_custom": self.var_custom,
            "cvar_custom": self.cvar_custom,
            "total_observations": self.total_observations,
        }


@dataclass(frozen=True)
class HoldingAllocation:
    """Individual holding allocation details."""

    ticker: str
    shares: float
    current_price: float
    market_value: float
    portfolio_weight: float
    sector: Optional[str] = None


@dataclass(frozen=True)
class SectorExposure:
    """Aggregated portfolio exposure by sector."""

    sector: str
    market_value: float
    portfolio_weight: float


@dataclass(frozen=True)
class ConcentrationMetrics:
    """Portfolio concentration metrics including HHI and top holdings."""

    hhi: float
    largest_holding_ticker: Optional[str]
    largest_holding_weight: float
    top_3_weight: float
    top_5_weight: float
    total_holdings_count: int

    def to_dict(self) -> dict:
        return {
            "hhi": self.hhi,
            "largest_holding_ticker": self.largest_holding_ticker,
            "largest_holding_weight": self.largest_holding_weight,
            "top_3_weight": self.top_3_weight,
            "top_5_weight": self.top_5_weight,
            "total_holdings_count": self.total_holdings_count,
        }


@dataclass(frozen=True)
class ReturnContribution:
    """Individual asset contribution to total portfolio return."""

    ticker: str
    portfolio_weight: float
    asset_return: float
    contribution: float
    contribution_pct: Optional[float]


@dataclass(frozen=True)
class DiversificationMetrics:
    """Asset-level return correlation and diversification metrics."""

    correlation_matrix: pd.DataFrame
    average_pairwise_correlation: Optional[float]
    highest_pairwise_correlation: Optional[float]
    highest_correlation_pair: Optional[Tuple[str, str]]
    lowest_pairwise_correlation: Optional[float]
    lowest_correlation_pair: Optional[Tuple[str, str]]
    total_pairs_count: int


@dataclass
class PortfolioIntelligenceSummary:
    """Comprehensive portfolio intelligence summary combining allocation, exposure, concentration, and diversification."""

    total_market_value: float
    allocations: List[HoldingAllocation]
    sector_exposures: List[SectorExposure]
    concentration: ConcentrationMetrics
    return_contributions: List[ReturnContribution]
    diversification: DiversificationMetrics
    portfolio_return: Optional[float]
    allocation_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    sector_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    contribution_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    def to_dict(self) -> dict:
        return {
            "total_market_value": self.total_market_value,
            "portfolio_return": self.portfolio_return,
            "concentration": self.concentration.to_dict(),
            "allocations_count": len(self.allocations),
            "sectors_count": len(self.sector_exposures),
            "average_pairwise_correlation": self.diversification.average_pairwise_correlation,
        }
