"""Data access repository for portfolio analytics retrieval."""

from datetime import date
from typing import Dict, List, Optional
import uuid
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from agent.db.models import (
    Asset,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioPerformanceSnapshot,
    PortfolioRiskMetric,
)


def get_portfolio(session: Session, portfolio_id: uuid.UUID) -> Optional[Portfolio]:
    """Retrieve portfolio by primary key."""
    return session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()


def get_portfolio_holdings(session: Session, portfolio_id: uuid.UUID) -> List[PortfolioHolding]:
    """Retrieve all open holdings for a portfolio."""
    return (
        session.query(PortfolioHolding)
        .filter(PortfolioHolding.portfolio_id == portfolio_id)
        .all()
    )


def get_assets_by_tickers(session: Session, tickers: List[str]) -> Dict[str, Asset]:
    """Retrieve metadata assets for a list of ticker symbols."""
    if not tickers:
        return {}
    clean_tickers = [t.strip().upper() for t in tickers if t]
    assets = session.query(Asset).filter(Asset.ticker.in_(clean_tickers)).all()
    return {a.ticker: a for a in assets}


def get_latest_market_prices(session: Session, tickers: List[str]) -> Dict[str, MarketPrice]:
    """Retrieve latest available market price record for each requested ticker."""
    if not tickers:
        return {}

    clean_tickers = [t.strip().upper() for t in tickers if t]

    # Find the most recent date for each ticker
    latest_dates_subquery = (
        session.query(
            MarketPrice.ticker.label("sub_ticker"),
            func.max(MarketPrice.price_date).label("max_date"),
        )
        .filter(MarketPrice.ticker.in_(clean_tickers))
        .group_by(MarketPrice.ticker)
        .subquery()
    )

    rows = (
        session.query(MarketPrice)
        .join(
            latest_dates_subquery,
            (MarketPrice.ticker == latest_dates_subquery.c.sub_ticker)
            & (MarketPrice.price_date == latest_dates_subquery.c.max_date),
        )
        .all()
    )
    return {r.ticker: r for r in rows}


def get_historical_market_prices(
    session: Session,
    tickers: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """Retrieve historical adjusted close price matrix (dates x tickers) as a DataFrame."""
    if not tickers:
        return pd.DataFrame()

    clean_tickers = [t.strip().upper() for t in tickers if t]
    query = session.query(
        MarketPrice.price_date,
        MarketPrice.ticker,
        MarketPrice.adj_close,
        MarketPrice.close_price,
    ).filter(MarketPrice.ticker.in_(clean_tickers))

    if start_date is not None:
        query = query.filter(MarketPrice.price_date >= start_date)
    if end_date is not None:
        query = query.filter(MarketPrice.price_date <= end_date)

    rows = query.order_by(MarketPrice.price_date.asc()).all()
    if not rows:
        return pd.DataFrame()

    data = []
    for r in rows:
        price_val = float(r.adj_close if r.adj_close is not None else r.close_price)
        data.append({"date": r.price_date, "ticker": r.ticker, "price": price_val})

    df = pd.DataFrame(data)
    matrix = df.pivot(index="date", columns="ticker", values="price")
    matrix.index = pd.to_datetime(matrix.index)
    return matrix


def get_performance_snapshots(
    session: Session,
    portfolio_id: uuid.UUID,
) -> List[PortfolioPerformanceSnapshot]:
    """Retrieve historical performance snapshots ordered chronologically."""
    return (
        session.query(PortfolioPerformanceSnapshot)
        .filter(PortfolioPerformanceSnapshot.portfolio_id == portfolio_id)
        .order_by(PortfolioPerformanceSnapshot.snapshot_date.asc())
        .all()
    )


def get_latest_risk_metrics(
    session: Session,
    portfolio_id: uuid.UUID,
) -> Optional[PortfolioRiskMetric]:
    """Retrieve the most recent computed risk metric record for a portfolio."""
    return (
        session.query(PortfolioRiskMetric)
        .filter(PortfolioRiskMetric.portfolio_id == portfolio_id)
        .order_by(PortfolioRiskMetric.as_of_date.desc(), PortfolioRiskMetric.calculated_at.desc())
        .first()
    )
