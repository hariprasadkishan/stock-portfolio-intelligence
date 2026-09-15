"""Deterministic tests for FastAPI Analytics & Dashboard API endpoints."""

from datetime import date
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient
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
)
from agent.main import app

client = TestClient(app)

TEST_P_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
EMPTY_P_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_TICKERS = ["API_AAPL", "API_MSFT", "API_SPY"]


@pytest.fixture(scope="module", autouse=True)
def setup_api_test_data():
    """Create deterministic test database records and clean up afterwards."""
    with get_db_session() as session:
        # 1. Clean any existing test fixtures
        session.execute(text("DELETE FROM portfolio_performance_snapshots WHERE portfolio_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM portfolio_holdings WHERE portfolio_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM portfolios WHERE id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('API_AAPL', 'API_MSFT', 'API_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'API_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('API_AAPL', 'API_MSFT', 'API_SPY');"))

        # 2. Insert test assets
        aapl = Asset(ticker="API_AAPL", name="Apple Test Inc.", asset_type="EQUITY", sector="Technology", currency="USD")
        msft = Asset(ticker="API_MSFT", name="Microsoft Test Corp.", asset_type="EQUITY", sector="Technology", currency="USD")
        spy = Asset(ticker="API_SPY", name="S&P 500 Test ETF", asset_type="ETF", sector="Broad Market", currency="USD")
        session.add_all([aapl, msft, spy])
        session.flush()

        # 3. Insert benchmark
        bm = Benchmark(symbol="API_SPY", name="S&P 500 Test Index")
        session.add(bm)
        session.flush()

        # 4. Insert portfolios
        p_active = Portfolio(
            id=TEST_P_ID,
            name="Active Test Portfolio",
            base_currency="USD",
            initial_cash=Decimal("10000.0000"),
            available_cash=Decimal("2000.0000"),
            benchmark_symbol="API_SPY",
        )
        p_empty = Portfolio(
            id=EMPTY_P_ID,
            name="Empty Test Portfolio",
            base_currency="USD",
            initial_cash=Decimal("5000.0000"),
            available_cash=Decimal("5000.0000"),
            benchmark_symbol="API_SPY",
        )
        session.add_all([p_active, p_empty])
        session.flush()

        # 5. Insert holdings for active portfolio
        h_aapl = PortfolioHolding(
            portfolio_id=TEST_P_ID,
            ticker="API_AAPL",
            shares=Decimal("10.000000"),
            cost_basis=Decimal("1500.0000"),
        )
        h_msft = PortfolioHolding(
            portfolio_id=TEST_P_ID,
            ticker="API_MSFT",
            shares=Decimal("20.000000"),
            cost_basis=Decimal("3000.0000"),
        )
        session.add_all([h_aapl, h_msft])
        session.flush()

        # 6. Insert market prices across 4 trading dates
        dates = [date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 7)]
        prices_data = [
            # date, AAPL, MSFT, SPY
            (dates[0], 160.0, 160.0, 500.0),
            (dates[1], 165.0, 162.0, 505.0),
            (dates[2], 170.0, 165.0, 510.0),
            (dates[3], 175.0, 170.0, 515.0),
        ]
        for d, p_a, p_m, p_s in prices_data:
            session.add(MarketPrice(ticker="API_AAPL", price_date=d, close_price=Decimal(str(p_a)), adj_close=Decimal(str(p_a)), volume=10000))
            session.add(MarketPrice(ticker="API_MSFT", price_date=d, close_price=Decimal(str(p_m)), adj_close=Decimal(str(p_m)), volume=10000))
            session.add(MarketPrice(ticker="API_SPY", price_date=d, close_price=Decimal(str(p_s)), adj_close=Decimal(str(p_s)), volume=10000))

        # 7. Insert performance snapshots
        snapshots = [
            PortfolioPerformanceSnapshot(portfolio_id=TEST_P_ID, snapshot_date=dates[0], equity_value=Decimal("4800.0000"), cash_balance=Decimal("2000.0000"), total_value=Decimal("6800.0000"), benchmark_value=Decimal("500.0000"), daily_return_pct=Decimal("0.0"), cumulative_return_pct=Decimal("0.0")),
            PortfolioPerformanceSnapshot(portfolio_id=TEST_P_ID, snapshot_date=dates[1], equity_value=Decimal("4890.0000"), cash_balance=Decimal("2000.0000"), total_value=Decimal("6890.0000"), benchmark_value=Decimal("505.0000"), daily_return_pct=Decimal("0.013235"), cumulative_return_pct=Decimal("0.013235")),
            PortfolioPerformanceSnapshot(portfolio_id=TEST_P_ID, snapshot_date=dates[2], equity_value=Decimal("5000.0000"), cash_balance=Decimal("2000.0000"), total_value=Decimal("7000.0000"), benchmark_value=Decimal("510.0000"), daily_return_pct=Decimal("0.015965"), cumulative_return_pct=Decimal("0.029412")),
            PortfolioPerformanceSnapshot(portfolio_id=TEST_P_ID, snapshot_date=dates[3], equity_value=Decimal("5150.0000"), cash_balance=Decimal("2000.0000"), total_value=Decimal("7150.0000"), benchmark_value=Decimal("515.0000"), daily_return_pct=Decimal("0.021429"), cumulative_return_pct=Decimal("0.051471")),
        ]
        session.add_all(snapshots)
        session.commit()

    yield

    with get_db_session() as session:
        session.execute(text("DELETE FROM portfolio_performance_snapshots WHERE portfolio_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM portfolio_holdings WHERE portfolio_id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM portfolios WHERE id IN ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222');"))
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('API_AAPL', 'API_MSFT', 'API_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'API_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('API_AAPL', 'API_MSFT', 'API_SPY');"))
        session.commit()


class TestPortfolioEndpoints:
    """Test API endpoints with valid, empty, and invalid inputs."""

    def test_openapi_docs_endpoint(self):
        """OpenAPI JSON and /docs return 200."""
        resp_json = client.get("/openapi.json")
        assert resp_json.status_code == 200
        schema = resp_json.json()
        assert "paths" in schema
        assert "/api/portfolio/{portfolio_id}/overview" in schema["paths"]
        assert "/api/portfolio/{portfolio_id}/dashboard" in schema["paths"]

        resp_docs = client.get("/docs")
        assert resp_docs.status_code == 200

    def test_invalid_uuid_returns_400(self):
        """Non-UUID string returns HTTP 400 Bad Request."""
        resp = client.get("/api/portfolio/not-a-uuid/overview")
        assert resp.status_code == 400
        assert "Invalid portfolio ID" in resp.json()["detail"]

    def test_nonexistent_portfolio_returns_404(self):
        """Random UUID not in DB returns HTTP 404 Not Found."""
        random_id = str(uuid.uuid4())
        resp = client.get(f"/api/portfolio/{random_id}/overview")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_overview_endpoint_success(self):
        """GET /api/portfolio/{id}/overview returns accurate portfolio metrics."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/overview")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert data["portfolio_name"] == "Active Test Portfolio"
        assert data["base_currency"] == "USD"
        assert data["benchmark"] == "API_SPY"
        assert data["initial_cash"] == 10000.0
        assert data["available_cash"] == 2000.0
        # Latest prices: AAPL = 175.0 (10 sh = 1750), MSFT = 170.0 (20 sh = 3400) -> invested = 5150
        assert data["invested_value"] == 5150.0
        assert data["current_portfolio_value"] == 7150.0
        assert data["absolute_pnl"] == -2850.0
        assert "annualized_volatility" in data
        assert "maximum_drawdown" in data

    def test_risk_endpoint_success(self):
        """GET /api/portfolio/{id}/risk returns computed risk metrics."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/risk?risk_free_rate=0.02")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert "volatility" in data
        assert "max_drawdown" in data
        assert "var_95" in data
        assert "cvar_95" in data
        assert "beta" in data
        assert "alpha" in data

    def test_allocation_endpoint_success(self):
        """GET /api/portfolio/{id}/allocation returns asset allocations."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/allocation")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert data["total_market_value"] == 5150.0
        assert len(data["allocations"]) == 2

        # MSFT (3400 / 5150 ~ 0.660194), AAPL (1750 / 5150 ~ 0.339806)
        tickers = {a["ticker"] for a in data["allocations"]}
        assert tickers == {"API_AAPL", "API_MSFT"}
        weights_sum = sum(a["portfolio_weight"] for a in data["allocations"])
        assert weights_sum == pytest.approx(1.0, rel=1e-5)

    def test_sectors_endpoint_success(self):
        """GET /api/portfolio/{id}/sectors returns aggregated sector weights."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/sectors")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert len(data["sectors"]) == 1
        assert data["sectors"][0]["sector"] == "Technology"
        assert data["sectors"][0]["portfolio_weight"] == pytest.approx(1.0)

    def test_contributions_endpoint_success(self):
        """GET /api/portfolio/{id}/contributions returns asset return contributions."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/contributions")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert len(data["contributions"]) == 2
        assert "portfolio_return" in data

    def test_correlation_endpoint_success(self):
        """GET /api/portfolio/{id}/correlation returns correlation matrix and stats."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/correlation")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert "correlation_matrix" in data
        assert "average_pairwise_correlation" in data
        assert "API_AAPL" in data["correlation_matrix"]

    def test_benchmark_endpoint_success(self):
        """GET /api/portfolio/{id}/benchmark returns benchmark comparison."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/benchmark")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert data["benchmark_symbol"] == "API_SPY"
        assert "beta" in data
        assert "jensens_alpha" in data
        assert "tracking_error" in data

    def test_performance_endpoint_success(self):
        """GET /api/portfolio/{id}/performance returns chronological observation curve."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/performance")
        assert resp.status_code == 200
        data = resp.json()

        assert data["portfolio_id"] == str(TEST_P_ID)
        assert data["observations_count"] == 4
        assert len(data["performance"]) == 4
        first_obs = data["performance"][0]
        assert first_obs["date"] == "2025-01-02"
        assert first_obs["portfolio_value"] == 6800.0

    def test_dashboard_endpoint_aggregation(self):
        """GET /api/portfolio/{id}/dashboard returns consolidated multi-dimensional payload."""
        resp = client.get(f"/api/portfolio/{TEST_P_ID}/dashboard?risk_free_rate=0.03")
        assert resp.status_code == 200
        data = resp.json()

        assert "overview" in data
        assert "risk" in data
        assert "allocation" in data
        assert "sectors" in data
        assert "contributions" in data
        assert "correlation" in data
        assert "benchmark" in data
        assert "performance" in data

        assert data["overview"]["portfolio_id"] == str(TEST_P_ID)
        assert data["allocation"]["total_market_value"] == 5150.0
        assert len(data["performance"]) == 4

    def test_empty_portfolio_graceful_handling(self):
        """Empty portfolio with no holdings returns zeroed/null metrics without error."""
        resp_overview = client.get(f"/api/portfolio/{EMPTY_P_ID}/overview")
        assert resp_overview.status_code == 200
        data_o = resp_overview.json()
        assert data_o["current_portfolio_value"] == 5000.0
        assert data_o["invested_value"] == 0.0

        resp_alloc = client.get(f"/api/portfolio/{EMPTY_P_ID}/allocation")
        assert resp_alloc.status_code == 200
        assert resp_alloc.json()["allocations"] == []

        resp_dash = client.get(f"/api/portfolio/{EMPTY_P_ID}/dashboard")
        assert resp_dash.status_code == 200
        assert resp_dash.json()["allocation"]["allocations"] == []
