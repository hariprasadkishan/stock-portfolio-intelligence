"""Deterministic financial analytics package for Stock Portfolio Intelligence & Risk Analytics."""

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
from agent.analytics.portfolio import (
    calculate_portfolio_value_series,
    compute_portfolio_analytics,
)
from agent.analytics.portfolio_intelligence import (
    calculate_asset_allocation,
    calculate_concentration_metrics,
    calculate_diversification_metrics,
    calculate_return_contributions,
    calculate_sector_exposure,
    compute_portfolio_intelligence,
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
from agent.analytics.tail_risk import (
    calculate_historical_cvar,
    calculate_historical_var,
    compute_tail_risk_metrics,
)
from agent.analytics.types import (
    BenchmarkMetrics,
    ConcentrationMetrics,
    DiversificationMetrics,
    HoldingAllocation,
    PortfolioAnalyticsSummary,
    PortfolioIntelligenceSummary,
    PortfolioSnapshot,
    ReturnContribution,
    ReturnMetrics,
    RiskMetrics,
    SectorExposure,
    TailRiskMetrics,
)

__all__ = [
    # Returns
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_annualized_return",
    "compute_return_metrics",
    # Risk
    "calculate_annualized_volatility",
    "calculate_downside_deviation",
    "calculate_drawdown_series",
    "calculate_max_drawdown",
    "calculate_max_drawdown_duration",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "compute_risk_metrics",
    # Benchmark
    "align_returns",
    "calculate_correlation",
    "calculate_covariance",
    "calculate_beta",
    "calculate_jensens_alpha",
    "calculate_tracking_error",
    "calculate_information_ratio",
    "compute_benchmark_metrics",
    # Tail Risk
    "calculate_historical_var",
    "calculate_historical_cvar",
    "compute_tail_risk_metrics",
    # Portfolio Valuation
    "calculate_portfolio_value_series",
    "compute_portfolio_analytics",
    # Portfolio Intelligence (Step 7)
    "calculate_asset_allocation",
    "calculate_sector_exposure",
    "calculate_concentration_metrics",
    "calculate_return_contributions",
    "calculate_diversification_metrics",
    "compute_portfolio_intelligence",
    # Types
    "ReturnMetrics",
    "RiskMetrics",
    "PortfolioSnapshot",
    "PortfolioAnalyticsSummary",
    "BenchmarkMetrics",
    "TailRiskMetrics",
    "HoldingAllocation",
    "SectorExposure",
    "ConcentrationMetrics",
    "ReturnContribution",
    "DiversificationMetrics",
    "PortfolioIntelligenceSummary",
]
