"""Deterministic analytics context builder for AI Financial Analyst."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session


@dataclass
class PortfolioAnalyticsContext:
    """Structured, deterministic portfolio analytics evidence context."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    benchmark_symbol: Optional[str]
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
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    benchmark_return: Optional[float] = None
    active_return: Optional[float] = None
    holdings: List[Dict[str, Any]] = field(default_factory=list)
    sectors: List[Dict[str, Any]] = field(default_factory=list)
    concentration_hhi: Optional[float] = None
    largest_holding_ticker: Optional[str] = None
    largest_holding_weight: Optional[float] = None
    top_3_concentration: Optional[float] = None
    top_5_concentration: Optional[float] = None
    return_contributions: List[Dict[str, Any]] = field(default_factory=list)
    average_pairwise_correlation: Optional[float] = None
    highest_correlated_pair: Optional[List[str]] = None
    lowest_correlated_pair: Optional[List[str]] = None
    warnings: List[str] = field(default_factory=list)
    metrics_available: List[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        """Serialize deterministic context into an unambiguous, structured evidence block."""
        lines = []
        curr = self.base_currency.upper()

        lines.append(f"=== PORTFOLIO METADATA ===")
        lines.append(f"Portfolio ID: {self.portfolio_id}")
        lines.append(f"Portfolio Name: {self.portfolio_name}")
        lines.append(f"Base Currency: {curr}")
        lines.append(f"Benchmark Symbol: {self.benchmark_symbol or 'None'}")
        lines.append(f"Initial Cash: {self.initial_cash:,.2f} {curr}")
        lines.append(f"Available Cash: {self.available_cash:,.2f} {curr}")
        lines.append(f"Invested Capital: {self.invested_value:,.2f} {curr}")
        lines.append(f"Current Total Value: {self.current_portfolio_value:,.2f} {curr}")
        lines.append(f"Absolute P&L: {self.absolute_pnl:+,.2f} {curr}")
        lines.append(f"Percentage P&L: {self.percentage_pnl * 100:+.2f}%")

        lines.append("\n=== PERFORMANCE METRICS ===")
        if self.cumulative_return is not None:
            lines.append(f"Cumulative Portfolio Return: {self.cumulative_return * 100:+.2f}%")
        else:
            lines.append("Cumulative Portfolio Return: Not available (insufficient history)")

        if self.annualized_return is not None:
            lines.append(f"Annualized Return (CAGR): {self.annualized_return * 100:+.2f}%")
        else:
            lines.append("Annualized Return (CAGR): Not available")

        lines.append("\n=== QUANTITATIVE RISK METRICS ===")
        if self.annualized_volatility is not None:
            lines.append(f"Annualized Volatility: {self.annualized_volatility * 100:.2f}%")
        else:
            lines.append("Annualized Volatility: Not available")

        if self.sharpe_ratio is not None:
            lines.append(f"Sharpe Ratio: {self.sharpe_ratio:.2f}")
        else:
            lines.append("Sharpe Ratio: Not available")

        if self.sortino_ratio is not None:
            lines.append(f"Sortino Ratio: {self.sortino_ratio:.2f}")
        else:
            lines.append("Sortino Ratio: Not available")

        lines.append(f"Maximum Drawdown: {self.maximum_drawdown * 100:.2f}%")
        lines.append(f"Maximum Drawdown Duration: {self.maximum_drawdown_duration} trading days")

        if self.var_95 is not None:
            lines.append(f"Historical VaR (95% 1-day): {self.var_95 * 100:.2f}%")
        else:
            lines.append("Historical VaR (95%): Not available")

        if self.cvar_95 is not None:
            lines.append(f"Historical CVaR / Expected Shortfall (95% 1-day): {self.cvar_95 * 100:.2f}%")
        else:
            lines.append("Historical CVaR (95%): Not available")

        lines.append("\n=== BENCHMARK COMPARATIVE ANALYTICS ===")
        if self.benchmark_symbol:
            lines.append(f"Benchmark: {self.benchmark_symbol}")
            if self.benchmark_return is not None:
                lines.append(f"Benchmark Cumulative Return: {self.benchmark_return * 100:+.2f}%")
            if self.active_return is not None:
                lines.append(f"Active Return Spread (Portfolio - Benchmark): {self.active_return * 100:+.2f}%")
            if self.beta is not None:
                lines.append(f"Beta relative to {self.benchmark_symbol}: {self.beta:.2f}")
            if self.alpha is not None:
                lines.append(f"Jensen's Alpha: {self.alpha * 100:+.2f}%")
            if self.tracking_error is not None:
                lines.append(f"Tracking Error: {self.tracking_error * 100:.2f}%")
            if self.information_ratio is not None:
                lines.append(f"Information Ratio: {self.information_ratio:.2f}")
        else:
            lines.append("No benchmark assigned to portfolio.")

        lines.append("\n=== ASSET ALLOCATION & HOLDINGS ===")
        if self.holdings:
            for h in self.holdings:
                lines.append(
                    f"- {h['ticker']}: {h['shares']} shares @ {h['current_price']:.2f} {curr} | "
                    f"Market Value: {h['market_value']:,.2f} {curr} | Weight: {h['portfolio_weight'] * 100:.2f}%"
                )
        else:
            lines.append("No active asset positions (portfolio is 100% cash).")

        lines.append("\n=== SECTOR EXPOSURE ===")
        if self.sectors:
            for s in self.sectors:
                lines.append(f"- {s['sector']}: {s['market_value']:,.2f} {curr} ({s['portfolio_weight'] * 100:.2f}%)")
        else:
            lines.append("No sector exposures.")

        lines.append("\n=== CONCENTRATION & DIVERSIFICATION ===")
        if self.concentration_hhi is not None:
            lines.append(f"Herfindahl-Hirschman Index (HHI): {self.concentration_hhi:.4f}")
        if self.largest_holding_ticker:
            lines.append(
                f"Largest Holding: {self.largest_holding_ticker} "
                f"({(self.largest_holding_weight or 0.0) * 100:.2f}%)"
            )
        if self.top_3_concentration is not None:
            lines.append(f"Top 3 Holdings Concentration: {self.top_3_concentration * 100:.2f}%")
        if self.top_5_concentration is not None:
            lines.append(f"Top 5 Holdings Concentration: {self.top_5_concentration * 100:.2f}%")
        if self.average_pairwise_correlation is not None:
            lines.append(f"Average Pairwise Correlation: {self.average_pairwise_correlation:.3f}")
        if self.highest_correlated_pair:
            lines.append(f"Highest Correlated Pair: {self.highest_correlated_pair[0]} / {self.highest_correlated_pair[1]}")
        if self.lowest_correlated_pair:
            lines.append(f"Lowest Correlated Pair: {self.lowest_correlated_pair[0]} / {self.lowest_correlated_pair[1]}")

        lines.append("\n=== RETURN CONTRIBUTION ===")
        if self.return_contributions:
            for c in self.return_contributions:
                lines.append(
                    f"- {c['ticker']}: Asset Return {c['asset_return'] * 100:+.2f}%, Weight {c['portfolio_weight'] * 100:.2f}% -> "
                    f"Weighted Contribution {c['contribution'] * 100:+.2f}%"
                )
        else:
            lines.append("No return contribution data.")

        if self.warnings:
            lines.append("\n=== DATA ADVISORIES ===")
            for w in self.warnings:
                lines.append(f"Note: {w}")

        return "\n".join(lines)


def build_portfolio_analytics_context(
    session: Session,
    portfolio_id: uuid.UUID,
    risk_free_rate: float = 0.0,
) -> PortfolioAnalyticsContext:
    """Retrieve verified, deterministic analytics for a portfolio and build structured context."""
    from agent.api.routes import get_dashboard

    p_id_str = str(portfolio_id)
    dash = get_dashboard(p_id_str, risk_free_rate=risk_free_rate, db=session)

    ov = dash.overview
    rk = dash.risk
    al = dash.allocation
    sc = dash.sectors
    cb = dash.contributions
    cr = dash.correlation
    bm = dash.benchmark

    metrics_used = [
        "initial_cash",
        "available_cash",
        "current_portfolio_value",
        "invested_value",
        "absolute_pnl",
        "percentage_pnl",
    ]

    warnings = []

    if ov.cumulative_return is not None:
        metrics_used.append("cumulative_return")
    if ov.annualized_return is not None:
        metrics_used.append("annualized_return")
    if ov.annualized_volatility is not None:
        metrics_used.append("annualized_volatility")
    if ov.sharpe_ratio is not None:
        metrics_used.append("sharpe_ratio")
    if ov.sortino_ratio is not None:
        metrics_used.append("sortino_ratio")
    metrics_used.append("maximum_drawdown")
    metrics_used.append("maximum_drawdown_duration")

    if rk.var_95 is not None:
        metrics_used.append("var_95")
    if rk.cvar_95 is not None:
        metrics_used.append("cvar_95")
    if rk.beta is not None:
        metrics_used.append("beta")
    if rk.alpha is not None:
        metrics_used.append("alpha")
    if rk.tracking_error is not None:
        metrics_used.append("tracking_error")
    if rk.information_ratio is not None:
        metrics_used.append("information_ratio")

    if bm.portfolio_cumulative_return is not None:
        metrics_used.append("benchmark_portfolio_return")
    if bm.benchmark_cumulative_return is not None:
        metrics_used.append("benchmark_cumulative_return")
    if bm.active_return is not None:
        metrics_used.append("active_return")

    holdings_list = []
    if al.allocations:
        metrics_used.append("asset_allocation")
        for item in al.allocations:
            holdings_list.append(
                {
                    "ticker": item.ticker,
                    "shares": item.shares,
                    "current_price": item.current_price,
                    "market_value": item.market_value,
                    "portfolio_weight": item.portfolio_weight,
                }
            )
    else:
        warnings.append("Portfolio currently holds no active positions.")

    sectors_list = []
    if sc.sectors:
        metrics_used.append("sector_exposure")
        for s in sc.sectors:
            sectors_list.append(
                {
                    "sector": s.sector,
                    "market_value": s.market_value,
                    "portfolio_weight": s.portfolio_weight,
                }
            )

    conc_hhi = None
    largest_ticker = None
    largest_weight = None
    top_3 = None
    top_5 = None

    if al.concentration:
        metrics_used.append("concentration_analytics")
        conc_hhi = al.concentration.hhi
        largest_ticker = al.concentration.largest_holding_ticker
        largest_weight = al.concentration.largest_holding_weight
        top_3 = al.concentration.top_3_weight
        top_5 = al.concentration.top_5_weight

    contrib_list = []
    if cb.contributions:
        metrics_used.append("return_contribution")
        for c in cb.contributions:
            contrib_list.append(
                {
                    "ticker": c.ticker,
                    "portfolio_weight": c.portfolio_weight,
                    "asset_return": c.asset_return,
                    "contribution": c.contribution,
                    "contribution_pct": c.contribution_pct,
                }
            )

    avg_corr = cr.average_pairwise_correlation
    if avg_corr is not None:
        metrics_used.append("correlation_matrix")

    if not ov.benchmark:
        warnings.append("Portfolio has no benchmark symbol configured.")

    return PortfolioAnalyticsContext(
        portfolio_id=ov.portfolio_id,
        portfolio_name=ov.portfolio_name,
        base_currency=ov.base_currency,
        benchmark_symbol=ov.benchmark,
        initial_cash=ov.initial_cash,
        available_cash=ov.available_cash,
        current_portfolio_value=ov.current_portfolio_value,
        invested_value=ov.invested_value,
        absolute_pnl=ov.absolute_pnl,
        percentage_pnl=ov.percentage_pnl,
        cumulative_return=ov.cumulative_return,
        annualized_return=ov.annualized_return,
        annualized_volatility=ov.annualized_volatility,
        sharpe_ratio=ov.sharpe_ratio,
        sortino_ratio=ov.sortino_ratio,
        maximum_drawdown=ov.maximum_drawdown,
        maximum_drawdown_duration=ov.maximum_drawdown_duration,
        var_95=rk.var_95,
        cvar_95=rk.cvar_95,
        beta=rk.beta,
        alpha=rk.alpha,
        tracking_error=rk.tracking_error,
        information_ratio=rk.information_ratio,
        benchmark_return=bm.benchmark_cumulative_return,
        active_return=bm.active_return,
        holdings=holdings_list,
        sectors=sectors_list,
        concentration_hhi=conc_hhi,
        largest_holding_ticker=largest_ticker,
        largest_holding_weight=largest_weight,
        top_3_concentration=top_3,
        top_5_concentration=top_5,
        return_contributions=contrib_list,
        average_pairwise_correlation=avg_corr,
        highest_correlated_pair=cr.highest_correlated_pair,
        lowest_correlated_pair=cr.lowest_correlated_pair,
        warnings=warnings,
        metrics_available=metrics_used,
    )
