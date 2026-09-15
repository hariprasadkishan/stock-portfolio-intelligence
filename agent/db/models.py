"""SQLAlchemy ORM models for Stock Portfolio Intelligence & Risk Analytics."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agent.db.base import Base


class Asset(Base):
    """Assets Table: Tracks equities, ETFs, indices, and asset metadata."""

    __tablename__ = "assets"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), default="USD", server_default=text("'USD'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    benchmark: Mapped[Optional["Benchmark"]] = relationship(
        back_populates="asset", uselist=False
    )
    holdings: Mapped[List["PortfolioHolding"]] = relationship(
        back_populates="asset"
    )
    trades: Mapped[List["PortfolioTrade"]] = relationship(
        back_populates="asset"
    )
    market_prices: Mapped[List["MarketPrice"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(ticker='{self.ticker}', name='{self.name}', type='{self.asset_type}')>"


class Benchmark(Base):
    """Benchmarks Table: Reference market benchmarks for comparative risk & return analysis."""

    __tablename__ = "benchmarks"

    symbol: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("assets.ticker", onupdate="CASCADE", ondelete="RESTRICT"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="benchmark")
    portfolios: Mapped[List["Portfolio"]] = relationship(back_populates="benchmark")

    def __repr__(self) -> str:
        return f"<Benchmark(symbol='{self.symbol}', name='{self.name}')>"


class Portfolio(Base):
    """Portfolios Table: Portfolio containers with cash balances and strategy settings."""

    __tablename__ = "portfolios"
    __table_args__ = (
        CheckConstraint("initial_cash >= 0", name="chk_portfolios_initial_cash"),
        CheckConstraint("available_cash >= 0", name="chk_portfolios_available_cash"),
        Index("idx_portfolios_created_at", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_currency: Mapped[str] = mapped_column(
        String(3), default="USD", server_default=text("'USD'"), nullable=False
    )
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    available_cash: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    benchmark_symbol: Mapped[Optional[str]] = mapped_column(
        String(16),
        ForeignKey("benchmarks.symbol", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    is_sandbox: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    benchmark: Mapped[Optional["Benchmark"]] = relationship(back_populates="portfolios")
    holdings: Mapped[List["PortfolioHolding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    trades: Mapped[List["PortfolioTrade"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    performance_snapshots: Mapped[List["PortfolioPerformanceSnapshot"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )
    risk_metrics: Mapped[List["PortfolioRiskMetric"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Portfolio(id='{self.id}', name='{self.name}', cash={self.available_cash})>"


class PortfolioHolding(Base):
    """Portfolio Holdings Table: Current position snapshot per portfolio."""

    __tablename__ = "portfolio_holdings"
    __table_args__ = (
        CheckConstraint("shares >= 0", name="chk_holdings_shares"),
        CheckConstraint("cost_basis >= 0", name="chk_holdings_cost_basis"),
        Index("idx_holdings_portfolio", "portfolio_id"),
        Index("idx_holdings_ticker", "ticker"),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("assets.ticker", onupdate="CASCADE", ondelete="RESTRICT"),
        primary_key=True,
    )
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
    asset: Mapped["Asset"] = relationship(back_populates="holdings")

    def __repr__(self) -> str:
        return f"<PortfolioHolding(portfolio_id='{self.portfolio_id}', ticker='{self.ticker}', shares={self.shares})>"


class PortfolioTrade(Base):
    """Portfolio Trades Table: Immutable double-entry transaction ledger."""

    __tablename__ = "portfolio_trades"
    __table_args__ = (
        CheckConstraint("trade_type IN ('BUY', 'SELL')", name="chk_trades_trade_type"),
        CheckConstraint("shares > 0", name="chk_trades_shares"),
        CheckConstraint("price > 0", name="chk_trades_price"),
        CheckConstraint("total_cost > 0", name="chk_trades_total_cost"),
        Index("idx_trades_portfolio_date", "portfolio_id", text("trade_date DESC")),
        Index("idx_trades_ticker", "ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("assets.ticker", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    trade_type: Mapped[str] = mapped_column(String(8), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cash_balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    strategy_interval: Mapped[str] = mapped_column(
        String(16), default="single_shot", server_default=text("'single_shot'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="trades")
    asset: Mapped["Asset"] = relationship(back_populates="trades")

    def __repr__(self) -> str:
        return f"<PortfolioTrade(id='{self.id}', type='{self.trade_type}', ticker='{self.ticker}', shares={self.shares})>"


class MarketPrice(Base):
    """Market Prices Table: Historical daily bar cache for portfolio assets and benchmark indices."""

    __tablename__ = "market_prices"
    __table_args__ = (
        CheckConstraint("open_price > 0", name="chk_market_prices_open"),
        CheckConstraint("high_price >= low_price", name="chk_market_prices_high_low"),
        CheckConstraint("low_price > 0", name="chk_market_prices_low"),
        CheckConstraint("close_price > 0", name="chk_market_prices_close"),
        CheckConstraint("adj_close > 0", name="chk_market_prices_adj_close"),
        CheckConstraint("volume >= 0", name="chk_market_prices_volume"),
        Index("idx_market_prices_ticker_date", "ticker", text("price_date DESC")),
        Index("idx_market_prices_date", text("price_date DESC")),
    )

    ticker: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("assets.ticker", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    price_date: Mapped[date] = mapped_column(Date, primary_key=True)
    open_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    high_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    low_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    adj_close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="market_prices")

    def __repr__(self) -> str:
        return f"<MarketPrice(ticker='{self.ticker}', date='{self.price_date}', close={self.close_price})>"


class PortfolioPerformanceSnapshot(Base):
    """Portfolio Performance Snapshots Table: Time-series valuation curve comparing equity against benchmark."""

    __tablename__ = "portfolio_performance_snapshots"
    __table_args__ = (
        CheckConstraint("equity_value >= 0", name="chk_snapshots_equity"),
        CheckConstraint("cash_balance >= 0", name="chk_snapshots_cash"),
        CheckConstraint("total_value >= 0", name="chk_snapshots_total"),
        Index("idx_perf_snapshots_portfolio_date", "portfolio_id", text("snapshot_date ASC")),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, primary_key=True)
    equity_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    benchmark_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    daily_return_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    cumulative_return_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="performance_snapshots")

    def __repr__(self) -> str:
        return f"<PortfolioPerformanceSnapshot(portfolio_id='{self.portfolio_id}', date='{self.snapshot_date}', total={self.total_value})>"


class PortfolioRiskMetric(Base):
    """Portfolio Risk Metrics Table: Quantitative risk & factor scorecard."""

    __tablename__ = "portfolio_risk_metrics"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id", "as_of_date", "lookback_window", name="uq_portfolio_risk_window"
        ),
        Index("idx_risk_metrics_portfolio_date", "portfolio_id", text("as_of_date DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    lookback_window: Mapped[str] = mapped_column(
        String(16), default="INCEPTION", server_default=text("'INCEPTION'"), nullable=False
    )
    annualized_return: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    annualized_volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    sortino_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    max_drawdown_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    beta: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    alpha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    var_95_daily: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    cvar_95_daily: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    concentration_hhi: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="risk_metrics")

    def __repr__(self) -> str:
        return f"<PortfolioRiskMetric(portfolio_id='{self.portfolio_id}', date='{self.as_of_date}', sharpe={self.sharpe_ratio})>"
