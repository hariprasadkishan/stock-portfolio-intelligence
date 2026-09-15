"""FastAPI routes exposing deterministic Portfolio Intelligence & Risk Analytics."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

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
)
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
    compute_risk_metrics,
)
from agent.analytics.tail_risk import (
    calculate_historical_cvar,
    calculate_historical_var,
)
from agent.api.repository import (
    get_assets_by_tickers,
    get_historical_market_prices,
    get_latest_market_prices,
    get_performance_snapshots,
    get_portfolio,
    get_portfolio_holdings,
)
from agent.api.schemas import (
    AllocationItem,
    ContributionItem,
    DashboardSummaryResponse,
    PerformanceObservation,
    PortfolioAllocationResponse,
    PortfolioBenchmarkResponse,
    PortfolioContributionsResponse,
    PortfolioCorrelationResponse,
    PortfolioOverviewResponse,
    PortfolioPerformanceResponse,
    PortfolioRiskResponse,
    PortfolioSectorsResponse,
    SectorItem,
    clean_float,
)
from agent.db.session import get_db

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Analytics"])


def _parse_uuid(portfolio_id: str) -> uuid.UUID:
    """Validate and parse portfolio UUID string."""
    try:
        return uuid.UUID(str(portfolio_id).strip())
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid portfolio ID '{portfolio_id}'. Must be a valid UUID format.",
        )


def _get_portfolio_or_404(session: Session, p_id: uuid.UUID):
    """Retrieve portfolio or raise HTTP 404."""
    p = get_portfolio(session, p_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{p_id}' not found.",
        )
    return p


def _build_holdings_dataframe(
    session: Session,
    p_id: uuid.UUID,
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Build standardized holdings DataFrame and sector map."""
    holdings = get_portfolio_holdings(session, p_id)
    if not holdings:
        return pd.DataFrame(), {}

    tickers = [h.ticker for h in holdings]
    latest_prices = get_latest_market_prices(session, tickers)
    assets_map = get_assets_by_tickers(session, tickers)

    rows = []
    sector_map = {}

    for h in holdings:
        ticker = h.ticker
        shares = float(h.shares)
        sector_val = assets_map[ticker].sector if ticker in assets_map else None
        sector_map[ticker] = sector_val or "Unknown"

        # Determine price
        price_val = 0.0
        if ticker in latest_prices:
            lp = latest_prices[ticker]
            price_val = float(lp.adj_close if lp.adj_close is not None else lp.close_price)
        elif shares > 0 and float(h.cost_basis) > 0:
            price_val = float(h.cost_basis) / shares

        rows.append(
            {
                "ticker": ticker,
                "shares": shares,
                "current_price": price_val,
                "sector": sector_map[ticker],
            }
        )

    return pd.DataFrame(rows), sector_map


def _get_or_compute_valuation_series(
    session: Session,
    p_id: uuid.UUID,
    portfolio,
    holdings_df: pd.DataFrame,
) -> Tuple[pd.Series, Optional[pd.DataFrame]]:
    """Retrieve valuation curve from performance snapshots or compute dynamically from prices."""
    snapshots = get_performance_snapshots(session, p_id)
    if snapshots:
        val_series = pd.Series(
            [float(s.total_value) for s in snapshots],
            index=pd.to_datetime([s.snapshot_date for s in snapshots]),
        )
        return val_series, None

    if holdings_df.empty:
        return pd.Series(dtype=float), None

    tickers = list(holdings_df["ticker"])
    price_matrix = get_historical_market_prices(session, tickers)
    if price_matrix.empty:
        return pd.Series(dtype=float), None

    holdings_dict = dict(zip(holdings_df["ticker"], holdings_df["shares"]))
    val_df = calculate_portfolio_value_series(
        holdings_dict, price_matrix, cash_balance=float(portfolio.available_cash)
    )
    if val_df.empty or "total_value" not in val_df.columns:
        return pd.Series(dtype=float), None

    return val_df["total_value"], val_df


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get(
    "/{portfolio_id}/overview",
    response_model=PortfolioOverviewResponse,
    summary="Portfolio Overview",
    description="Returns high-level portfolio valuation, cash balance, returns, and drawdown scorecard.",
)
def get_overview(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    alloc_df = calculate_asset_allocation(holdings_df)

    invested_val = float(alloc_df["market_value"].sum()) if not alloc_df.empty else 0.0
    avail_cash = float(p.available_cash)
    init_cash = float(p.initial_cash)
    current_val = invested_val + avail_cash

    abs_pnl = current_val - init_cash
    pct_pnl = (abs_pnl / init_cash) if init_cash > 0 else 0.0

    val_series, _ = _get_or_compute_valuation_series(db, p_uuid, p, holdings_df)

    cum_ret = None
    ann_ret = None
    ann_vol = None
    sharpe = None
    sortino = None
    mdd = 0.0
    mdd_days = 0

    if len(val_series) >= 2:
        analytics = compute_portfolio_analytics(val_series, initial_capital=init_cash)
        cum_ret = analytics.total_return_pct
        ann_ret = analytics.annualized_return
        ann_vol = analytics.annualized_volatility
        sharpe = analytics.sharpe_ratio
        sortino = analytics.sortino_ratio
        mdd = analytics.max_drawdown
        mdd_days = analytics.max_drawdown_duration_days
    elif len(val_series) == 1:
        cum_ret = pct_pnl

    return PortfolioOverviewResponse(
        portfolio_id=str(p.id),
        portfolio_name=p.name,
        base_currency=p.base_currency,
        benchmark=p.benchmark_symbol,
        initial_cash=round(init_cash, 4),
        available_cash=round(avail_cash, 4),
        current_portfolio_value=round(current_val, 4),
        invested_value=round(invested_val, 4),
        absolute_pnl=round(abs_pnl, 4),
        percentage_pnl=round(pct_pnl, 6),
        cumulative_return=clean_float(cum_ret),
        annualized_return=clean_float(ann_ret),
        annualized_volatility=clean_float(ann_vol),
        sharpe_ratio=clean_float(sharpe),
        sortino_ratio=clean_float(sortino),
        maximum_drawdown=round(mdd, 6),
        maximum_drawdown_duration=mdd_days,
    )


@router.get(
    "/{portfolio_id}/risk",
    response_model=PortfolioRiskResponse,
    summary="Portfolio Risk Analytics",
    description="Returns quantitative risk metrics: volatility, Sharpe, Sortino, MDD, VaR 95%, CVaR 95%, beta, and alpha.",
)
def get_risk(
    portfolio_id: str,
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate"),
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    val_series, _ = _get_or_compute_valuation_series(db, p_uuid, p, holdings_df)

    vol = None
    sharpe = None
    sortino = None
    mdd = 0.0
    mdd_days = 0
    var_95 = None
    cvar_95 = None
    beta = None
    alpha = None
    te = None
    ir = None

    if len(val_series) >= 2:
        daily_rets = calculate_daily_returns(val_series)
        risk_metrics = compute_risk_metrics(
            daily_rets, prices_or_values=val_series, risk_free_rate=risk_free_rate
        )
        vol = risk_metrics.annualized_volatility
        sharpe = risk_metrics.sharpe_ratio
        sortino = risk_metrics.sortino_ratio
        mdd = risk_metrics.max_drawdown
        mdd_days = risk_metrics.max_drawdown_duration_days

        var_95 = calculate_historical_var(daily_rets, confidence_level=0.95)
        cvar_95 = calculate_historical_cvar(daily_rets, confidence_level=0.95)

        if p.benchmark_symbol:
            b_matrix = get_historical_market_prices(db, [p.benchmark_symbol])
            if not b_matrix.empty and p.benchmark_symbol in b_matrix.columns:
                b_rets = calculate_daily_returns(b_matrix[p.benchmark_symbol])
                aligned = align_returns(daily_rets, b_rets)
                if len(aligned) >= 2:
                    bm_metrics = compute_benchmark_metrics(
                        aligned["portfolio"], aligned["benchmark"], risk_free_rate=risk_free_rate
                    )
                    beta = bm_metrics.beta
                    alpha = bm_metrics.alpha
                    te = bm_metrics.tracking_error
                    ir = bm_metrics.information_ratio

    return PortfolioRiskResponse(
        portfolio_id=str(p.id),
        volatility=clean_float(vol),
        sharpe=clean_float(sharpe),
        sortino=clean_float(sortino),
        max_drawdown=round(mdd, 6),
        max_drawdown_duration=mdd_days,
        var_95=clean_float(var_95),
        cvar_95=clean_float(cvar_95),
        beta=clean_float(beta),
        alpha=clean_float(alpha),
        tracking_error=clean_float(te),
        information_ratio=clean_float(ir),
    )


@router.get(
    "/{portfolio_id}/allocation",
    response_model=PortfolioAllocationResponse,
    summary="Asset Allocation",
    description="Returns current holdings, market values, and decimal portfolio weights.",
)
def get_allocation(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    alloc_df = calculate_asset_allocation(holdings_df)

    total_val = float(alloc_df["market_value"].sum()) if not alloc_df.empty else 0.0
    items = []

    if not alloc_df.empty:
        for _, r in alloc_df.iterrows():
            items.append(
                AllocationItem(
                    ticker=str(r["ticker"]),
                    shares=round(float(r["shares"]), 6),
                    current_price=round(float(r["current_price"]), 4),
                    market_value=round(float(r["market_value"]), 4),
                    portfolio_weight=round(float(r["portfolio_weight"]), 6),
                )
            )

    return PortfolioAllocationResponse(
        portfolio_id=str(p.id),
        total_market_value=round(total_val, 4),
        allocations=items,
    )


@router.get(
    "/{portfolio_id}/sectors",
    response_model=PortfolioSectorsResponse,
    summary="Sector Exposure",
    description="Returns aggregated portfolio market values and weights grouped by sector.",
)
def get_sectors(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, sector_map = _build_holdings_dataframe(db, p_uuid)
    alloc_df = calculate_asset_allocation(holdings_df)
    sector_df = calculate_sector_exposure(alloc_df, sector_map=sector_map)

    total_val = float(sector_df["market_value"].sum()) if not sector_df.empty else 0.0
    items = []

    if not sector_df.empty:
        for _, r in sector_df.iterrows():
            items.append(
                SectorItem(
                    sector=str(r["sector"]),
                    market_value=round(float(r["market_value"]), 4),
                    portfolio_weight=round(float(r["portfolio_weight"]), 6),
                )
            )

    return PortfolioSectorsResponse(
        portfolio_id=str(p.id),
        total_market_value=round(total_val, 4),
        sectors=items,
    )


@router.get(
    "/{portfolio_id}/contributions",
    response_model=PortfolioContributionsResponse,
    summary="Return Contributions",
    description="Returns asset-level contribution to total portfolio return and percentage contribution.",
)
def get_contributions(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    alloc_df = calculate_asset_allocation(holdings_df)

    if alloc_df.empty:
        return PortfolioContributionsResponse(
            portfolio_id=str(p.id),
            portfolio_return=None,
            contributions=[],
        )

    tickers = list(alloc_df["ticker"])
    price_matrix = get_historical_market_prices(db, tickers)

    # Compute asset returns over historical window
    asset_returns = {}
    if not price_matrix.empty and len(price_matrix) >= 2:
        for t in tickers:
            if t in price_matrix.columns:
                series = price_matrix[t].dropna()
                if len(series) >= 2:
                    asset_returns[t] = float((series.iloc[-1] - series.iloc[0]) / series.iloc[0])
                else:
                    asset_returns[t] = 0.0
    else:
        for t in tickers:
            asset_returns[t] = 0.0

    weights_dict = dict(zip(alloc_df["ticker"], alloc_df["portfolio_weight"]))
    contrib_df = calculate_return_contributions(weights_dict, asset_returns)

    items = []
    p_return = None

    if not contrib_df.empty:
        p_return = float(contrib_df["contribution"].sum())
        for _, r in contrib_df.iterrows():
            items.append(
                ContributionItem(
                    ticker=str(r["ticker"]),
                    portfolio_weight=round(float(r["portfolio_weight"]), 6),
                    asset_return=round(float(r["asset_return"]), 6),
                    contribution=round(float(r["contribution"]), 6),
                    contribution_pct=clean_float(r["contribution_pct"]),
                )
            )

    return PortfolioContributionsResponse(
        portfolio_id=str(p.id),
        portfolio_return=clean_float(p_return),
        contributions=items,
    )


@router.get(
    "/{portfolio_id}/correlation",
    response_model=PortfolioCorrelationResponse,
    summary="Asset Diversification and Correlation",
    description="Returns Pearson correlation matrix and pairwise summary statistics strictly excluding diagonal self-correlation.",
)
def get_correlation(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    if holdings_df.empty:
        return PortfolioCorrelationResponse(portfolio_id=str(p.id))

    tickers = list(holdings_df["ticker"])
    price_matrix = get_historical_market_prices(db, tickers)

    if price_matrix.empty or len(price_matrix) < 2:
        return PortfolioCorrelationResponse(portfolio_id=str(p.id))

    returns_matrix = price_matrix.pct_change().dropna(how="all")
    div_metrics = calculate_diversification_metrics(returns_matrix)

    # Convert correlation matrix to clean JSON serializable dict
    corr_dict: Dict[str, Dict[str, Optional[float]]] = {}
    if not div_metrics.correlation_matrix.empty:
        for row_t, row in div_metrics.correlation_matrix.iterrows():
            corr_dict[str(row_t)] = {
                str(col_t): clean_float(val) for col_t, val in row.items()
            }

    high_pair = list(div_metrics.highest_correlation_pair) if div_metrics.highest_correlation_pair else None
    low_pair = list(div_metrics.lowest_correlation_pair) if div_metrics.lowest_correlation_pair else None

    return PortfolioCorrelationResponse(
        portfolio_id=str(p.id),
        correlation_matrix=corr_dict,
        average_pairwise_correlation=clean_float(div_metrics.average_pairwise_correlation),
        highest_pairwise_correlation=clean_float(div_metrics.highest_pairwise_correlation),
        lowest_pairwise_correlation=clean_float(div_metrics.lowest_pairwise_correlation),
        highest_correlated_pair=high_pair,
        lowest_correlated_pair=low_pair,
    )


@router.get(
    "/{portfolio_id}/benchmark",
    response_model=PortfolioBenchmarkResponse,
    summary="Benchmark Analytics",
    description="Returns benchmark comparative statistics: beta, alpha, tracking error, and information ratio.",
)
def get_benchmark(
    portfolio_id: str,
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate"),
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    if not p.benchmark_symbol:
        return PortfolioBenchmarkResponse(
            portfolio_id=str(p.id),
            benchmark_symbol=None,
        )

    holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
    val_series, _ = _get_or_compute_valuation_series(db, p_uuid, p, holdings_df)

    if len(val_series) < 2:
        return PortfolioBenchmarkResponse(
            portfolio_id=str(p.id),
            benchmark_symbol=p.benchmark_symbol,
        )

    b_matrix = get_historical_market_prices(db, [p.benchmark_symbol])
    if b_matrix.empty or p.benchmark_symbol not in b_matrix.columns:
        return PortfolioBenchmarkResponse(
            portfolio_id=str(p.id),
            benchmark_symbol=p.benchmark_symbol,
        )

    p_rets = calculate_daily_returns(val_series)
    b_rets = calculate_daily_returns(b_matrix[p.benchmark_symbol])

    aligned = align_returns(p_rets, b_rets)
    if len(aligned) < 2:
        return PortfolioBenchmarkResponse(
            portfolio_id=str(p.id),
            benchmark_symbol=p.benchmark_symbol,
        )

    bm_metrics = compute_benchmark_metrics(
        aligned["portfolio"], aligned["benchmark"], risk_free_rate=risk_free_rate
    )

    p_cum = calculate_cumulative_returns(aligned["portfolio"], is_prices=False)
    b_cum = calculate_cumulative_returns(aligned["benchmark"], is_prices=False)

    p_total_cum = float(p_cum.iloc[-1]) if not p_cum.empty else None
    b_total_cum = float(b_cum.iloc[-1]) if not b_cum.empty else None
    active_cum = (p_total_cum - b_total_cum) if (p_total_cum is not None and b_total_cum is not None) else None

    return PortfolioBenchmarkResponse(
        portfolio_id=str(p.id),
        benchmark_symbol=p.benchmark_symbol,
        correlation=clean_float(bm_metrics.correlation),
        covariance=clean_float(bm_metrics.covariance),
        beta=clean_float(bm_metrics.beta),
        jensens_alpha=clean_float(bm_metrics.alpha),
        tracking_error=clean_float(bm_metrics.tracking_error),
        information_ratio=clean_float(bm_metrics.information_ratio),
        portfolio_cumulative_return=clean_float(p_total_cum),
        benchmark_cumulative_return=clean_float(b_total_cum),
        active_return=clean_float(active_cum),
    )


@router.get(
    "/{portfolio_id}/performance",
    response_model=PortfolioPerformanceResponse,
    summary="Performance Time Series",
    description="Returns chronological portfolio equity and benchmark valuation curves with daily and cumulative returns.",
)
def get_performance(
    portfolio_id: str,
    db: Session = Depends(get_db),
):
    p_uuid = _parse_uuid(portfolio_id)
    p = _get_portfolio_or_404(db, p_uuid)

    snapshots = get_performance_snapshots(db, p_uuid)
    observations: List[PerformanceObservation] = []

    if snapshots:
        for s in snapshots:
            d_str = s.snapshot_date.isoformat() if hasattr(s.snapshot_date, "isoformat") else str(s.snapshot_date)
            observations.append(
                PerformanceObservation(
                    date=d_str,
                    portfolio_value=float(s.total_value),
                    benchmark_value=clean_float(s.benchmark_value),
                    daily_portfolio_return=clean_float(s.daily_return_pct),
                    cumulative_portfolio_return=clean_float(s.cumulative_return_pct),
                )
            )
    else:
        # Dynamically compute time-series
        holdings_df, _ = _build_holdings_dataframe(db, p_uuid)
        val_series, _ = _get_or_compute_valuation_series(db, p_uuid, p, holdings_df)

        if not val_series.empty:
            daily_p_rets = calculate_daily_returns(val_series, dropna=False)
            cum_p_rets = calculate_cumulative_returns(val_series, is_prices=True)

            b_prices_series = pd.Series(dtype=float)
            b_daily_rets = pd.Series(dtype=float)
            b_cum_rets = pd.Series(dtype=float)

            if p.benchmark_symbol:
                b_matrix = get_historical_market_prices(db, [p.benchmark_symbol])
                if not b_matrix.empty and p.benchmark_symbol in b_matrix.columns:
                    b_prices_series = b_matrix[p.benchmark_symbol].reindex(val_series.index)
                    b_daily_rets = calculate_daily_returns(b_prices_series, dropna=False)
                    b_cum_rets = calculate_cumulative_returns(b_prices_series, is_prices=True)

            for dt, val in val_series.items():
                dt_obj = dt.date() if hasattr(dt, "date") else dt
                d_str = dt_obj.isoformat() if hasattr(dt_obj, "isoformat") else str(dt_obj)
                p_val = float(val)
                b_val = float(b_prices_series[dt]) if dt in b_prices_series and pd.notna(b_prices_series[dt]) else None
                dp_ret = float(daily_p_rets[dt]) if dt in daily_p_rets and pd.notna(daily_p_rets[dt]) else None
                cp_ret = float(cum_p_rets[dt]) if dt in cum_p_rets and pd.notna(cum_p_rets[dt]) else None
                db_ret = float(b_daily_rets[dt]) if dt in b_daily_rets and pd.notna(b_daily_rets[dt]) else None
                cb_ret = float(b_cum_rets[dt]) if dt in b_cum_rets and pd.notna(b_cum_rets[dt]) else None

                observations.append(
                    PerformanceObservation(
                        date=d_str,
                        portfolio_value=round(p_val, 4),
                        benchmark_value=clean_float(b_val),
                        daily_portfolio_return=clean_float(dp_ret),
                        cumulative_portfolio_return=clean_float(cp_ret),
                        daily_benchmark_return=clean_float(db_ret),
                        cumulative_benchmark_return=clean_float(cb_ret),
                    )
                )

    return PortfolioPerformanceResponse(
        portfolio_id=str(p.id),
        observations_count=len(observations),
        performance=observations,
    )


@router.get(
    "/{portfolio_id}/dashboard",
    response_model=DashboardSummaryResponse,
    summary="Dashboard Aggregation",
    description="Consolidated single endpoint aggregating overview, risk, allocation, sectors, contributions, correlation, benchmark, and performance.",
)
def get_dashboard(
    portfolio_id: str,
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate"),
    db: Session = Depends(get_db),
):
    overview_resp = get_overview(portfolio_id, db=db)
    risk_resp = get_risk(portfolio_id, risk_free_rate=risk_free_rate, db=db)
    allocation_resp = get_allocation(portfolio_id, db=db)
    sectors_resp = get_sectors(portfolio_id, db=db)
    contributions_resp = get_contributions(portfolio_id, db=db)
    correlation_resp = get_correlation(portfolio_id, db=db)
    benchmark_resp = get_benchmark(portfolio_id, risk_free_rate=risk_free_rate, db=db)
    performance_resp = get_performance(portfolio_id, db=db)

    return DashboardSummaryResponse(
        overview=overview_resp,
        risk=risk_resp,
        allocation=allocation_resp,
        sectors=sectors_resp,
        contributions=contributions_resp,
        correlation=correlation_resp,
        benchmark=benchmark_resp,
        performance=performance_resp.performance,
    )
