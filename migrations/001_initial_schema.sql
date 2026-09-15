-- ==============================================================================
-- Migration: 001_initial_schema.sql
-- Project: Stock Portfolio Intelligence & Risk Analytics
-- Database: stock_portfolio_intelligence
-- ==============================================================================

-- 1. Assets Table
-- Tracks equities, ETFs, indices, and asset metadata
CREATE TABLE IF NOT EXISTS assets (
    ticker VARCHAR(16) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    asset_type VARCHAR(32) NOT NULL,
    sector VARCHAR(64),
    industry VARCHAR(128),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. Benchmarks Table
-- Reference market benchmarks for comparative risk & return analysis
CREATE TABLE IF NOT EXISTS benchmarks (
    symbol VARCHAR(16) PRIMARY KEY REFERENCES assets(ticker) ON UPDATE CASCADE ON DELETE RESTRICT,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 3. Portfolios Table
-- Portfolio containers with cash balances and strategy settings
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    base_currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    initial_cash NUMERIC(18, 4) NOT NULL CHECK (initial_cash >= 0),
    available_cash NUMERIC(18, 4) NOT NULL CHECK (available_cash >= 0),
    benchmark_symbol VARCHAR(16) REFERENCES benchmarks(symbol) ON UPDATE CASCADE ON DELETE RESTRICT,
    is_sandbox BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 4. Portfolio Holdings Table
-- Current position snapshot per portfolio
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(16) NOT NULL REFERENCES assets(ticker) ON UPDATE CASCADE ON DELETE RESTRICT,
    shares NUMERIC(18, 6) NOT NULL CHECK (shares >= 0),
    cost_basis NUMERIC(18, 4) NOT NULL CHECK (cost_basis >= 0),
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (portfolio_id, ticker)
);

-- 5. Portfolio Trades Table
-- Immutable double-entry transaction ledger
CREATE TABLE IF NOT EXISTS portfolio_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(16) NOT NULL REFERENCES assets(ticker) ON UPDATE CASCADE ON DELETE RESTRICT,
    trade_type VARCHAR(8) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    trade_date DATE NOT NULL,
    shares NUMERIC(18, 6) NOT NULL CHECK (shares > 0),
    price NUMERIC(18, 4) NOT NULL CHECK (price > 0),
    total_cost NUMERIC(18, 4) NOT NULL CHECK (total_cost > 0),
    cash_balance_after NUMERIC(18, 4) NOT NULL,
    strategy_interval VARCHAR(16) DEFAULT 'single_shot' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 6. Market Prices Table
-- Historical daily bar cache for portfolio assets and benchmark indices
CREATE TABLE IF NOT EXISTS market_prices (
    ticker VARCHAR(16) NOT NULL REFERENCES assets(ticker) ON UPDATE CASCADE ON DELETE CASCADE,
    price_date DATE NOT NULL,
    open_price NUMERIC(18, 4) CHECK (open_price > 0),
    high_price NUMERIC(18, 4) CHECK (high_price >= low_price),
    low_price NUMERIC(18, 4) CHECK (low_price > 0),
    close_price NUMERIC(18, 4) NOT NULL CHECK (close_price > 0),
    adj_close NUMERIC(18, 4) NOT NULL CHECK (adj_close > 0),
    volume BIGINT CHECK (volume >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (ticker, price_date)
);

-- 7. Portfolio Performance Snapshots Table
-- Time-series valuation curve comparing portfolio equity against benchmark
CREATE TABLE IF NOT EXISTS portfolio_performance_snapshots (
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    equity_value NUMERIC(18, 4) NOT NULL CHECK (equity_value >= 0),
    cash_balance NUMERIC(18, 4) NOT NULL CHECK (cash_balance >= 0),
    total_value NUMERIC(18, 4) NOT NULL CHECK (total_value >= 0),
    benchmark_value NUMERIC(18, 4),
    daily_return_pct NUMERIC(12, 6),
    cumulative_return_pct NUMERIC(12, 6),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (portfolio_id, snapshot_date)
);

-- 8. Portfolio Risk Metrics Table
-- Quantitative risk & factor scorecard
CREATE TABLE IF NOT EXISTS portfolio_risk_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    as_of_date DATE NOT NULL,
    lookback_window VARCHAR(16) DEFAULT 'INCEPTION' NOT NULL,
    annualized_return NUMERIC(10, 6),
    annualized_volatility NUMERIC(10, 6),
    sharpe_ratio NUMERIC(10, 4),
    sortino_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 6),
    max_drawdown_days INTEGER,
    beta NUMERIC(10, 4),
    alpha NUMERIC(10, 6),
    var_95_daily NUMERIC(10, 6),
    cvar_95_daily NUMERIC(10, 6),
    concentration_hhi NUMERIC(8, 4),
    calculated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_portfolio_risk_window UNIQUE (portfolio_id, as_of_date, lookback_window)
);

-- ==============================================================================
-- Indexes for High-Performance Time-Series and Analytics Queries
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_portfolios_created_at ON portfolios (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_holdings_portfolio ON portfolio_holdings (portfolio_id);
CREATE INDEX IF NOT EXISTS idx_holdings_ticker ON portfolio_holdings (ticker);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio_date ON portfolio_trades (portfolio_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON portfolio_trades (ticker);
CREATE INDEX IF NOT EXISTS idx_market_prices_ticker_date ON market_prices (ticker, price_date DESC);
CREATE INDEX IF NOT EXISTS idx_market_prices_date ON market_prices (price_date DESC);
CREATE INDEX IF NOT EXISTS idx_perf_snapshots_portfolio_date ON portfolio_performance_snapshots (portfolio_id, snapshot_date ASC);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_portfolio_date ON portfolio_risk_metrics (portfolio_id, as_of_date DESC);
