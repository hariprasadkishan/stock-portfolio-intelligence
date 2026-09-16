"""Automated verification tests for Power BI analytical SQL views."""

from datetime import date
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import text

from agent.db import get_db_session
from agent.db.models import (
    Asset,
    Benchmark,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioPerformanceSnapshot,
    PortfolioRiskMetric,
    PortfolioTrade,
)

PBI_TEST_P_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")
PBI_TICKERS = ["PBI_AAPL", "PBI_MSFT", "PBI_SPY"]


@pytest.fixture(scope="module", autouse=True)
def setup_pbi_views_fixtures():
    """Create deterministic fixture records and tear down after tests."""
    with get_db_session() as session:
        # Clean any prior fixture
        session.execute(text("DELETE FROM portfolio_risk_metrics WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_performance_snapshots WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_trades WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_holdings WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolios WHERE id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('PBI_AAPL', 'PBI_MSFT', 'PBI_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'PBI_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('PBI_AAPL', 'PBI_MSFT', 'PBI_SPY');"))
        session.commit()

        # 1. Assets
        aapl = Asset(ticker="PBI_AAPL", name="Apple Test Inc", asset_type="EQUITY", sector="Technology", industry="Consumer Electronics", currency="USD")
        msft = Asset(ticker="PBI_MSFT", name="Microsoft Test Corp", asset_type="EQUITY", sector="Technology", industry="Software", currency="USD")
        spy = Asset(ticker="PBI_SPY", name="S&P 500 ETF", asset_type="ETF", sector="Broad Market", industry="Index Fund", currency="USD")
        session.add_all([aapl, msft, spy])
        session.flush()

        # 2. Benchmark
        bm = Benchmark(symbol="PBI_SPY", name="S&P 500 Test")
        session.add(bm)
        session.flush()

        # 3. Portfolio
        p = Portfolio(
            id=PBI_TEST_P_ID,
            name="Power BI Analytical Portfolio",
            base_currency="USD",
            initial_cash=Decimal("10000.0000"),
            available_cash=Decimal("2500.0000"),
            benchmark_symbol="PBI_SPY",
        )
        session.add(p)
        session.flush()

        # 4. Holdings: AAPL 10 @ $150, MSFT 20 @ $160
        h1 = PortfolioHolding(portfolio_id=PBI_TEST_P_ID, ticker="PBI_AAPL", shares=Decimal("10.000000"), cost_basis=Decimal("1500.0000"))
        h2 = PortfolioHolding(portfolio_id=PBI_TEST_P_ID, ticker="PBI_MSFT", shares=Decimal("20.000000"), cost_basis=Decimal("3200.0000"))
        session.add_all([h1, h2])
        session.flush()

        # 5. Market prices: AAPL $180, MSFT $200
        d = date(2025, 1, 15)
        mp1 = MarketPrice(ticker="PBI_AAPL", price_date=d, close_price=Decimal("180.0000"), adj_close=Decimal("180.0000"), volume=50000)
        mp2 = MarketPrice(ticker="PBI_MSFT", price_date=d, close_price=Decimal("200.0000"), adj_close=Decimal("200.0000"), volume=80000)
        session.add_all([mp1, mp2])
        session.flush()

        # 6. Performance Snapshot
        snap = PortfolioPerformanceSnapshot(
            portfolio_id=PBI_TEST_P_ID,
            snapshot_date=d,
            equity_value=Decimal("5800.0000"),
            cash_balance=Decimal("2500.0000"),
            total_value=Decimal("8300.0000"),
            benchmark_value=Decimal("500.0000"),
            daily_return_pct=Decimal("0.012500"),
            cumulative_return_pct=Decimal("0.052000"),
        )
        session.add(snap)

        # 7. Risk metrics
        rm = PortfolioRiskMetric(
            portfolio_id=PBI_TEST_P_ID,
            as_of_date=d,
            lookback_window="1Y",
            annualized_return=Decimal("0.185000"),
            annualized_volatility=Decimal("0.142000"),
            sharpe_ratio=Decimal("1.3028"),
            sortino_ratio=Decimal("1.8540"),
            max_drawdown=Decimal("0.045000"),
            max_drawdown_days=6,
            beta=Decimal("0.9200"),
            alpha=Decimal("0.034000"),
            var_95_daily=Decimal("0.014500"),
            cvar_95_daily=Decimal("0.021000"),
            concentration_hhi=Decimal("0.5400"),
        )
        session.add(rm)

        # 8. Trade
        tr = PortfolioTrade(
            portfolio_id=PBI_TEST_P_ID,
            ticker="PBI_AAPL",
            trade_type="BUY",
            trade_date=date(2025, 1, 10),
            shares=Decimal("10.000000"),
            price=Decimal("150.0000"),
            total_cost=Decimal("1500.0000"),
            cash_balance_after=Decimal("8500.0000"),
        )
        session.add(tr)
        session.commit()

    yield

    # Teardown
    with get_db_session() as session:
        session.execute(text("DELETE FROM portfolio_risk_metrics WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_performance_snapshots WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_trades WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolio_holdings WHERE portfolio_id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM portfolios WHERE id = '77777777-7777-7777-7777-777777777777';"))
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('PBI_AAPL', 'PBI_MSFT', 'PBI_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'PBI_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('PBI_AAPL', 'PBI_MSFT', 'PBI_SPY');"))
        session.commit()


def test_views_existence_in_information_schema():
    """All 7 Power BI analytical views exist in public schema."""
    expected_views = {
        "vw_dim_date",
        "vw_dim_assets",
        "vw_dim_portfolios",
        "vw_fact_portfolio_performance",
        "vw_fact_portfolio_holdings",
        "vw_fact_portfolio_trades",
        "vw_fact_portfolio_risk_metrics",
    }
    with get_db_session() as session:
        rows = session.execute(
            text("SELECT table_name FROM information_schema.views WHERE table_schema = 'public';")
        ).fetchall()
        existing = {r[0] for r in rows}
        assert expected_views.issubset(existing)


def test_dim_date_completeness():
    """vw_dim_date contains continuous trading days and calendar hierarchies."""
    with get_db_session() as session:
        row = session.execute(
            text("SELECT count(*), min(date), max(date) FROM vw_dim_date;")
        ).fetchone()
        assert row[0] >= 3650
        assert str(row[1]) == "2020-01-01"
        assert str(row[2]) == "2030-12-31"

        sample = session.execute(
            text("SELECT date, year, quarter, month_name, is_trading_day FROM vw_dim_date WHERE date = '2025-01-15';")
        ).fetchone()
        assert sample[1] == 2025
        assert sample[2] == "Q1"
        assert sample[4] is True


def test_fact_portfolio_holdings_valuation():
    """vw_fact_portfolio_holdings calculates market value, unrealized P&L, and weights."""
    with get_db_session() as session:
        rows = session.execute(
            text(
                f"SELECT ticker, shares, cost_basis, latest_price, market_value, unrealized_pnl, portfolio_weight "
                f"FROM vw_fact_portfolio_holdings WHERE portfolio_id = '{PBI_TEST_P_ID}' ORDER BY ticker;"
            )
        ).fetchall()

        assert len(rows) == 2
        # PBI_AAPL: 10 * 180 = 1800. Cost = 1500. Unrealized = +300
        aapl = rows[0]
        assert aapl[0] == "PBI_AAPL"
        assert float(aapl[4]) == 1800.0
        assert float(aapl[5]) == 300.0

        # PBI_MSFT: 20 * 200 = 4000. Cost = 3200. Unrealized = +800
        msft = rows[1]
        assert msft[0] == "PBI_MSFT"
        assert float(msft[4]) == 4000.0
        assert float(msft[5]) == 800.0

        # Weights: 1800 / 5800 ~ 0.310345, 4000 / 5800 ~ 0.689655
        total_weight = float(aapl[6]) + float(msft[6])
        assert total_weight == pytest.approx(1.0, rel=1e-4)


def test_fact_portfolio_performance_and_risk_views():
    """vw_fact_portfolio_performance and vw_fact_portfolio_risk_metrics map snapshot data correctly."""
    with get_db_session() as session:
        perf = session.execute(
            text(f"SELECT portfolio_value, total_value, daily_return_pct FROM vw_fact_portfolio_performance WHERE portfolio_id = '{PBI_TEST_P_ID}';")
        ).fetchone()
        assert float(perf[0]) == 5800.0
        assert float(perf[1]) == 8300.0
        assert float(perf[2]) == 0.0125

        risk = session.execute(
            text(f"SELECT sharpe_ratio, beta, var_95_daily FROM vw_fact_portfolio_risk_metrics WHERE portfolio_id = '{PBI_TEST_P_ID}';")
        ).fetchone()
        assert float(risk[0]) == 1.3028
        assert float(risk[1]) == 0.9200
        assert float(risk[2]) == 0.0145
