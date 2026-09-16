-- ==============================================================================
-- Migration: 002_powerbi_views.sql
-- Project: Stock Portfolio Intelligence & Risk Analytics
-- Purpose: Curated analytical SQL views for Power BI reporting & semantic modeling
-- Target Database: stock_portfolio_intelligence
-- ==============================================================================

-- 1. Date Dimension View (vw_dim_date)
-- Dynamic calendar dimension spanning 2020 through 2030 for time-intelligence & slicers
CREATE OR REPLACE VIEW vw_dim_date AS
SELECT
    d::DATE AS date,
    EXTRACT(YEAR FROM d)::INT AS year,
    ('Q' || EXTRACT(QUARTER FROM d)::TEXT)::VARCHAR(2) AS quarter,
    EXTRACT(QUARTER FROM d)::INT AS quarter_number,
    TO_CHAR(d, 'YYYY-"Q"Q')::VARCHAR(7) AS year_quarter,
    TO_CHAR(d, 'YYYY-MM')::VARCHAR(7) AS year_month,
    TO_CHAR(d, 'Month')::VARCHAR(12) AS month_name,
    TO_CHAR(d, 'Mon')::VARCHAR(3) AS month_short,
    EXTRACT(MONTH FROM d)::INT AS month_number,
    EXTRACT(WEEK FROM d)::INT AS week_of_year,
    EXTRACT(DAY FROM d)::INT AS day_of_month,
    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
    TO_CHAR(d, 'Day')::VARCHAR(9) AS day_name,
    (EXTRACT(ISODOW FROM d) IN (6, 7)) AS is_weekend,
    (EXTRACT(ISODOW FROM d) NOT IN (6, 7)) AS is_trading_day
FROM generate_series('2020-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- 2. Asset Dimension View (vw_dim_assets)
-- Reference dimension for equities, ETFs, and indices with standardized categorization
CREATE OR REPLACE VIEW vw_dim_assets AS
SELECT
    a.ticker,
    a.name AS asset_name,
    a.asset_type,
    COALESCE(NULLIF(TRIM(a.sector), ''), 'Unknown') AS sector,
    COALESCE(NULLIF(TRIM(a.industry), ''), 'Unknown') AS industry,
    a.currency,
    a.created_at
FROM assets a;

-- 3. Portfolio Dimension View (vw_dim_portfolios)
-- Master dimension for portfolios, benchmark assignments, and capital baseline
CREATE OR REPLACE VIEW vw_dim_portfolios AS
SELECT
    p.id AS portfolio_id,
    p.name AS portfolio_name,
    p.description,
    p.base_currency,
    p.initial_cash,
    p.available_cash,
    p.benchmark_symbol,
    COALESCE(b.name, 'None') AS benchmark_name,
    p.is_sandbox,
    p.created_at,
    p.updated_at
FROM portfolios p
LEFT JOIN benchmarks b ON p.benchmark_symbol = b.symbol;

-- 4. Portfolio Performance Fact View (vw_fact_portfolio_performance)
-- Chronological time-series snapshots comparing portfolio valuation against benchmark
CREATE OR REPLACE VIEW vw_fact_portfolio_performance AS
SELECT
    pps.portfolio_id,
    p.name AS portfolio_name,
    pps.snapshot_date,
    pps.equity_value AS portfolio_value,
    pps.cash_balance,
    pps.total_value,
    p.benchmark_symbol,
    pps.benchmark_value,
    pps.daily_return_pct,
    pps.cumulative_return_pct,
    pps.created_at
FROM portfolio_performance_snapshots pps
JOIN portfolios p ON pps.portfolio_id = p.id;

-- 5. Portfolio Holdings Fact View (vw_fact_portfolio_holdings)
-- Current positions enriched with latest price, market value, unrealized P&L, and portfolio weight
CREATE OR REPLACE VIEW vw_fact_portfolio_holdings AS
WITH latest_prices AS (
    SELECT DISTINCT ON (ticker)
        ticker,
        price_date AS latest_price_date,
        COALESCE(adj_close, close_price) AS latest_price
    FROM market_prices
    ORDER BY ticker, price_date DESC
),
holdings_calc AS (
    SELECT
        ph.portfolio_id,
        ph.ticker,
        a.name AS asset_name,
        COALESCE(NULLIF(TRIM(a.sector), ''), 'Unknown') AS sector,
        COALESCE(NULLIF(TRIM(a.industry), ''), 'Unknown') AS industry,
        ph.shares,
        ph.cost_basis,
        CASE
            WHEN ph.shares > 0 THEN ROUND(ph.cost_basis / ph.shares, 4)
            ELSE 0.0000
        END AS avg_cost_per_share,
        lp.latest_price_date,
        COALESCE(
            lp.latest_price,
            CASE WHEN ph.shares > 0 THEN ph.cost_basis / ph.shares ELSE 0.0000 END
        ) AS latest_price,
        ROUND(
            ph.shares * COALESCE(
                lp.latest_price,
                CASE WHEN ph.shares > 0 THEN ph.cost_basis / ph.shares ELSE 0.0000 END
            ),
            4
        ) AS market_value,
        ph.updated_at
    FROM portfolio_holdings ph
    JOIN assets a ON ph.ticker = a.ticker
    LEFT JOIN latest_prices lp ON ph.ticker = lp.ticker
),
holdings_with_totals AS (
    SELECT
        hc.*,
        ROUND(hc.market_value - hc.cost_basis, 4) AS unrealized_pnl,
        CASE
            WHEN hc.cost_basis > 0 THEN ROUND((hc.market_value - hc.cost_basis) / hc.cost_basis, 6)
            ELSE 0.000000
        END AS unrealized_pnl_pct,
        SUM(hc.market_value) OVER (PARTITION BY hc.portfolio_id) AS total_holdings_value
    FROM holdings_calc hc
)
SELECT
    hwt.portfolio_id,
    hwt.ticker,
    hwt.asset_name,
    hwt.sector,
    hwt.industry,
    hwt.shares,
    hwt.cost_basis,
    hwt.avg_cost_per_share,
    hwt.latest_price_date,
    hwt.latest_price,
    hwt.market_value,
    hwt.unrealized_pnl,
    hwt.unrealized_pnl_pct,
    CASE
        WHEN hwt.total_holdings_value > 0 THEN ROUND(hwt.market_value / hwt.total_holdings_value, 6)
        ELSE 0.000000
    END AS portfolio_weight,
    hwt.updated_at
FROM holdings_with_totals hwt;

-- 6. Portfolio Trades Fact View (vw_fact_portfolio_trades)
-- Immutable transaction ledger with asset metadata and cash balance audit
CREATE OR REPLACE VIEW vw_fact_portfolio_trades AS
SELECT
    pt.id AS trade_id,
    pt.portfolio_id,
    pt.trade_date,
    pt.ticker,
    a.name AS asset_name,
    COALESCE(NULLIF(TRIM(a.sector), ''), 'Unknown') AS sector,
    pt.trade_type,
    pt.shares,
    pt.price,
    pt.total_cost,
    pt.cash_balance_after,
    pt.strategy_interval,
    pt.created_at
FROM portfolio_trades pt
JOIN assets a ON pt.ticker = a.ticker;

-- 7. Portfolio Risk Metrics Fact View (vw_fact_portfolio_risk_metrics)
-- Pre-computed deterministic risk and factor scorecard
CREATE OR REPLACE VIEW vw_fact_portfolio_risk_metrics AS
SELECT
    prm.id AS risk_metric_id,
    prm.portfolio_id,
    p.name AS portfolio_name,
    prm.as_of_date,
    prm.lookback_window,
    prm.annualized_return,
    prm.annualized_volatility,
    prm.sharpe_ratio,
    prm.sortino_ratio,
    prm.max_drawdown,
    prm.max_drawdown_days,
    prm.beta,
    prm.alpha,
    prm.var_95_daily,
    prm.cvar_95_daily,
    prm.concentration_hhi,
    prm.calculated_at
FROM portfolio_risk_metrics prm
JOIN portfolios p ON prm.portfolio_id = p.id;
