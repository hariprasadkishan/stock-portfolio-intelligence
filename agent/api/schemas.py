"""Pydantic v2 schemas for Portfolio Intelligence & Risk Analytics REST API."""

import math
from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


def clean_float(val: Any) -> Optional[float]:
    """Ensure floats are strictly finite (converting NaN and Inf to None)."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


class AllocationItem(BaseModel):
    """Individual holding allocation item."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    shares: float
    current_price: float
    market_value: float
    portfolio_weight: float


class PortfolioAllocationResponse(BaseModel):
    """Asset allocation breakdown."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    total_market_value: float
    allocations: List[AllocationItem] = Field(default_factory=list)


class SectorItem(BaseModel):
    """Aggregated sector exposure item."""

    model_config = ConfigDict(from_attributes=True)

    sector: str
    market_value: float
    portfolio_weight: float


class PortfolioSectorsResponse(BaseModel):
    """Sector exposure breakdown."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    total_market_value: float
    sectors: List[SectorItem] = Field(default_factory=list)


class ContributionItem(BaseModel):
    """Asset return contribution item."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    portfolio_weight: float
    asset_return: float
    contribution: float
    contribution_pct: Optional[float] = None


class PortfolioContributionsResponse(BaseModel):
    """Asset-level return contribution breakdown."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    portfolio_return: Optional[float] = None
    contributions: List[ContributionItem] = Field(default_factory=list)


class PortfolioCorrelationResponse(BaseModel):
    """Asset pairwise return correlation and diversification metrics."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    correlation_matrix: Dict[str, Dict[str, Optional[float]]] = Field(default_factory=dict)
    average_pairwise_correlation: Optional[float] = None
    highest_pairwise_correlation: Optional[float] = None
    lowest_pairwise_correlation: Optional[float] = None
    highest_correlated_pair: Optional[List[str]] = None
    lowest_correlated_pair: Optional[List[str]] = None


class PortfolioOverviewResponse(BaseModel):
    """High-level portfolio overview and valuation scorecard."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    portfolio_name: str
    base_currency: str = "USD"
    benchmark: Optional[str] = None
    initial_cash: float
    available_cash: float
    current_portfolio_value: float
    invested_value: float
    absolute_pnl: float
    percentage_pnl: float
    cumulative_return: Optional[float] = None
    annualized_return: Optional[float] = None
    annualized_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    maximum_drawdown: float = 0.0
    maximum_drawdown_duration: int = 0


class PortfolioRiskResponse(BaseModel):
    """Detailed risk analytics metrics."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    volatility: Optional[float] = None
    sharpe: Optional[float] = None
    sortino: Optional[float] = None
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None


class PortfolioBenchmarkResponse(BaseModel):
    """Benchmark comparative analytics."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    benchmark_symbol: Optional[str] = None
    correlation: Optional[float] = None
    covariance: Optional[float] = None
    beta: Optional[float] = None
    jensens_alpha: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    portfolio_cumulative_return: Optional[float] = None
    benchmark_cumulative_return: Optional[float] = None
    active_return: Optional[float] = None


class PerformanceObservation(BaseModel):
    """Single point in time observation for valuation and return curves."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    portfolio_value: float
    benchmark_value: Optional[float] = None
    daily_portfolio_return: Optional[float] = None
    cumulative_portfolio_return: Optional[float] = None
    daily_benchmark_return: Optional[float] = None
    cumulative_benchmark_return: Optional[float] = None


class PortfolioPerformanceResponse(BaseModel):
    """Valuation and return curve history."""

    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    observations_count: int
    performance: List[PerformanceObservation] = Field(default_factory=list)


class DashboardSummaryResponse(BaseModel):
    """Consolidated dashboard summary aggregating all analytics dimensions."""

    model_config = ConfigDict(from_attributes=True)

    overview: PortfolioOverviewResponse
    risk: PortfolioRiskResponse
    allocation: PortfolioAllocationResponse
    sectors: PortfolioSectorsResponse
    contributions: PortfolioContributionsResponse
    correlation: PortfolioCorrelationResponse
    benchmark: PortfolioBenchmarkResponse
    performance: List[PerformanceObservation] = Field(default_factory=list)
