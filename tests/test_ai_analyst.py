"""Comprehensive automated tests for AI Financial Analyst backend service and API."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from agent.ai_analyst.context import (
    PortfolioAnalyticsContext,
    build_portfolio_analytics_context,
)
from agent.ai_analyst.prompts import SYSTEM_PROMPT, build_analyst_user_prompt
from agent.ai_analyst.schemas import AnalystQuestion, AnalystResponse
from agent.ai_analyst.service import FinancialAnalystService
from agent.db import get_db_session
from agent.db.models import (
    Asset,
    Benchmark,
    MarketPrice,
    Portfolio,
    PortfolioHolding,
    PortfolioPerformanceSnapshot,
    PortfolioRiskMetric,
)
from agent.main import app

client = TestClient(app)

AI_P_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
AI_EMPTY_P_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
AI_NO_BM_P_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture(scope="module", autouse=True)
def setup_ai_analyst_fixtures():
    """Seed isolated deterministic portfolio fixtures for AI Analyst testing."""
    with get_db_session() as session:
        # Clean any prior records
        session.execute(
            text(
                "DELETE FROM portfolio_risk_metrics WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolio_performance_snapshots WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolio_holdings WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolios WHERE id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('AIA_AAPL', 'AIA_NVDA', 'AIA_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'AIA_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('AIA_AAPL', 'AIA_NVDA', 'AIA_SPY');"))
        session.commit()

        # 1. Assets
        aapl = Asset(ticker="AIA_AAPL", name="Apple Test Inc", asset_type="EQUITY", sector="Technology", currency="USD")
        nvda = Asset(ticker="AIA_NVDA", name="NVIDIA Test Corp", asset_type="EQUITY", sector="Semiconductors", currency="USD")
        spy = Asset(ticker="AIA_SPY", name="S&P 500 Test Index", asset_type="ETF", sector="Broad Market", currency="USD")
        session.add_all([aapl, nvda, spy])
        session.flush()

        # 2. Benchmark
        bm = Benchmark(symbol="AIA_SPY", name="S&P 500 Test Benchmark")
        session.add(bm)
        session.flush()

        # 3. Portfolios
        p_active = Portfolio(
            id=AI_P_ID,
            name="AI Analyst Active Fund",
            base_currency="USD",
            initial_cash=Decimal("10000.0000"),
            available_cash=Decimal("1500.0000"),
            benchmark_symbol="AIA_SPY",
        )
        p_empty = Portfolio(
            id=AI_EMPTY_P_ID,
            name="AI Analyst Empty Fund",
            base_currency="USD",
            initial_cash=Decimal("5000.0000"),
            available_cash=Decimal("5000.0000"),
            benchmark_symbol="AIA_SPY",
        )
        p_no_bm = Portfolio(
            id=AI_NO_BM_P_ID,
            name="AI Analyst Unbenchmarked Fund",
            base_currency="USD",
            initial_cash=Decimal("8000.0000"),
            available_cash=Decimal("8000.0000"),
            benchmark_symbol=None,
        )
        session.add_all([p_active, p_empty, p_no_bm])
        session.flush()

        # 4. Holdings for active portfolio
        h1 = PortfolioHolding(portfolio_id=AI_P_ID, ticker="AIA_AAPL", shares=Decimal("20.000000"), cost_basis=Decimal("3000.0000"))
        h2 = PortfolioHolding(portfolio_id=AI_P_ID, ticker="AIA_NVDA", shares=Decimal("50.000000"), cost_basis=Decimal("5500.0000"))
        session.add_all([h1, h2])
        session.flush()

        # 5. Market prices across 4 trading dates
        dates = [date(2025, 2, 3), date(2025, 2, 4), date(2025, 2, 5), date(2025, 2, 6)]
        prices_data = [
            (dates[0], 150.0, 110.0, 500.0),
            (dates[1], 155.0, 115.0, 502.0),
            (dates[2], 160.0, 120.0, 505.0),
            (dates[3], 165.0, 125.0, 510.0),
        ]
        for dt, p_a, p_n, p_s in prices_data:
            session.add(MarketPrice(ticker="AIA_AAPL", price_date=dt, close_price=Decimal(str(p_a)), adj_close=Decimal(str(p_a)), volume=100000))
            session.add(MarketPrice(ticker="AIA_NVDA", price_date=dt, close_price=Decimal(str(p_n)), adj_close=Decimal(str(p_n)), volume=200000))
            session.add(MarketPrice(ticker="AIA_SPY", price_date=dt, close_price=Decimal(str(p_s)), adj_close=Decimal(str(p_s)), volume=500000))

        session.commit()

    yield

    with get_db_session() as session:
        session.execute(
            text(
                "DELETE FROM portfolio_risk_metrics WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolio_performance_snapshots WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolio_holdings WHERE portfolio_id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(
            text(
                "DELETE FROM portfolios WHERE id IN "
                "('33333333-3333-3333-3333-333333333333', '44444444-4444-4444-4444-444444444444', '55555555-5555-5555-5555-555555555555');"
            )
        )
        session.execute(text("DELETE FROM market_prices WHERE ticker IN ('AIA_AAPL', 'AIA_NVDA', 'AIA_SPY');"))
        session.execute(text("DELETE FROM benchmarks WHERE symbol = 'AIA_SPY';"))
        session.execute(text("DELETE FROM assets WHERE ticker IN ('AIA_AAPL', 'AIA_NVDA', 'AIA_SPY');"))
        session.commit()


def _create_mock_llm_client(content: str = "Based on the supplied deterministic metrics, the portfolio generated positive excess return."):
    """Helper creating a mock OpenAI client returning given text content."""
    mock_choice = MagicMock()
    mock_choice.message.content = content

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ==============================================================================
# UNIT TESTS
# ==============================================================================

class TestContextBuilder:
    """Validates deterministic context assembly from database records."""

    def test_context_creation_active_portfolio(self):
        """Active portfolio context gathers all deterministic metrics accurately."""
        with get_db_session() as session:
            ctx = build_portfolio_analytics_context(session, AI_P_ID)

            assert isinstance(ctx, PortfolioAnalyticsContext)
            assert ctx.portfolio_id == str(AI_P_ID)
            assert ctx.portfolio_name == "AI Analyst Active Fund"
            assert ctx.benchmark_symbol == "AIA_SPY"
            assert ctx.initial_cash == 10000.0
            assert ctx.available_cash == 1500.0
            # 20 * 165 (3300) + 50 * 125 (6250) = 9550 invested + 1500 cash = 11050
            assert ctx.invested_value == 9550.0
            assert ctx.current_portfolio_value == 11050.0
            assert len(ctx.holdings) == 2
            assert len(ctx.sectors) == 2
            assert ctx.largest_holding_ticker == "AIA_NVDA"
            assert ctx.concentration_hhi is not None
            assert len(ctx.metrics_available) > 10

    def test_context_creation_empty_portfolio(self):
        """Empty portfolio handles 0 holdings gracefully without error."""
        with get_db_session() as session:
            ctx = build_portfolio_analytics_context(session, AI_EMPTY_P_ID)

            assert ctx.invested_value == 0.0
            assert ctx.current_portfolio_value == 5000.0
            assert ctx.holdings == []
            assert any("no active positions" in w.lower() for w in ctx.warnings)

    def test_context_unbenchmarked_portfolio(self):
        """Unbenchmarked portfolio records warning and omits benchmark returns."""
        with get_db_session() as session:
            ctx = build_portfolio_analytics_context(session, AI_NO_BM_P_ID)

            assert ctx.benchmark_symbol is None
            assert ctx.benchmark_return is None
            assert any("no benchmark symbol" in w.lower() for w in ctx.warnings)

    def test_context_to_prompt_text_formatting(self):
        """Prompt text includes critical numerical metrics and section titles."""
        with get_db_session() as session:
            ctx = build_portfolio_analytics_context(session, AI_P_ID)
            txt = ctx.to_prompt_text()

            assert "=== PORTFOLIO METADATA ===" in txt
            assert "=== QUANTITATIVE RISK METRICS ===" in txt
            assert "=== ASSET ALLOCATION & HOLDINGS ===" in txt
            assert "AIA_AAPL" in txt
            assert "AIA_NVDA" in txt


class TestInputValidation:
    """Validates user question length, whitespace, and schema constraints."""

    def test_empty_question_rejected(self):
        with pytest.raises(ValueError, match="empty or contain only whitespace"):
            AnalystQuestion(question="")

    def test_whitespace_only_question_rejected(self):
        with pytest.raises(ValueError, match="empty or contain only whitespace"):
            AnalystQuestion(question="    \n   \t  ")

    def test_oversized_question_rejected(self):
        long_q = "Why? " * 300  # 1500 chars
        with pytest.raises(ValueError, match="exceeds maximum allowed length"):
            AnalystQuestion(question=long_q)

    def test_valid_question_trimmed(self):
        q = AnalystQuestion(question="  What is the risk-adjusted return?   ")
        assert q.question == "What is the risk-adjusted return?"


class TestSystemPromptGuardrails:
    """Verifies system prompt strictly forbids hallucinations and investment advice."""

    def test_system_prompt_core_rules(self):
        assert "mathematically pre-computed, deterministic, and authoritative" in SYSTEM_PROMPT
        assert "Under NO circumstances should you calculate, estimate, reconstruct, or invent" in SYSTEM_PROMPT
        assert "Make personalized buy, sell, or hold recommendations" in SYSTEM_PROMPT
        assert "TEMPORAL DISTINCTION (CRITICAL)" in SYSTEM_PROMPT

    def test_build_analyst_user_prompt_combines_evidence(self):
        user_prompt = build_analyst_user_prompt("PORTFOLIO EVIDENCE: Value=10000", "Why was Beta low?")
        assert "PORTFOLIO EVIDENCE: Value=10000" in user_prompt
        assert "Why was Beta low?" in user_prompt


class TestFinancialAnalystService:
    """Tests service orchestration with injected mock LLM clients."""

    def test_service_successful_response(self):
        mock_client = _create_mock_llm_client("The portfolio Sharpe ratio of 1.85 reflects strong excess return per unit of volatility.")
        service = FinancialAnalystService(client=mock_client, model="mock-model")

        with get_db_session() as session:
            resp = service.ask(
                portfolio_id=str(AI_P_ID),
                question="How is my risk-adjusted performance?",
                session=session,
            )

            assert isinstance(resp, AnalystResponse)
            assert resp.question == "How is my risk-adjusted performance?"
            assert "Sharpe ratio of 1.85" in resp.answer
            assert resp.portfolio_id == str(AI_P_ID)
            assert "sharpe_ratio" in resp.metrics_used
            assert mock_client.chat.completions.create.called

    def test_service_empty_llm_response_raises_502(self):
        mock_client = _create_mock_llm_client("")
        service = FinancialAnalystService(client=mock_client, model="mock-model")

        with get_db_session() as session:
            with pytest.raises(Exception) as exc_info:
                service.ask(
                    portfolio_id=str(AI_P_ID),
                    question="Summarize the portfolio.",
                    session=session,
                )
            assert "502" in str(exc_info.value) or "empty or malformed" in str(exc_info.value)

    def test_service_llm_provider_failure_raises_502_without_secrets(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("OpenAI connection timeout with key sk-secret-12345")
        service = FinancialAnalystService(client=mock_client, model="mock-model")

        with get_db_session() as session:
            with pytest.raises(Exception) as exc_info:
                service.ask(
                    portfolio_id=str(AI_P_ID),
                    question="Summarize the portfolio.",
                    session=session,
                )
            err_msg = str(exc_info.value)
            assert "sk-secret-12345" not in err_msg
            assert "AI Analyst provider was unable to generate a response" in err_msg

    def test_service_unconfigured_provider_raises_503(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValueError("GROQ_API_KEY environment variable is not set.")
        service = FinancialAnalystService(client=mock_client, model="mock-model")

        with get_db_session() as session:
            with pytest.raises(Exception) as exc_info:
                service.ask(
                    portfolio_id=str(AI_P_ID),
                    question="Summarize the portfolio.",
                    session=session,
                )
            err_msg = str(exc_info.value)
            assert "AI Analyst provider is not configured" in err_msg

    def test_service_invalid_uuid_raises_400(self):
        service = FinancialAnalystService()
        with get_db_session() as session:
            with pytest.raises(Exception) as exc_info:
                service.ask(
                    portfolio_id="not-a-valid-uuid",
                    question="Summarize.",
                    session=session,
                )
            assert "400" in str(exc_info.value)
            assert "Must be a valid UUID format" in str(exc_info.value)

    def test_service_unknown_portfolio_raises_404(self):
        unknown_id = str(uuid.uuid4())
        mock_client = _create_mock_llm_client()
        service = FinancialAnalystService(client=mock_client)

        with get_db_session() as session:
            with pytest.raises(Exception) as exc_info:
                service.ask(
                    portfolio_id=unknown_id,
                    question="Summarize.",
                    session=session,
                )
            assert "404" in str(exc_info.value)


class TestApiEndpointAsk:
    """Integration tests for POST /api/portfolio/{id}/ask with mocked LLM."""

    @patch("agent.stock_analysis.get_llm_client")
    @patch("agent.stock_analysis.get_llm_model")
    def test_post_ask_success(self, mock_get_model, mock_get_client):
        mock_get_model.return_value = "mock-gpt"
        mock_get_client.return_value = _create_mock_llm_client(
            "Portfolio returns were primarily driven by AIA_NVDA which had a 62.5% allocation weight."
        )

        resp = client.post(
            f"/api/portfolio/{AI_P_ID}/ask",
            json={"question": "What drove my portfolio returns?"},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["question"] == "What drove my portfolio returns?"
        assert "AIA_NVDA" in data["answer"]
        assert data["portfolio_id"] == str(AI_P_ID)
        assert isinstance(data["metrics_used"], list)
        assert "asset_allocation" in data["metrics_used"]
        assert isinstance(data["warnings"], list)

    def test_post_ask_invalid_uuid(self):
        resp = client.post(
            "/api/portfolio/invalid-uuid-format/ask",
            json={"question": "Why did my portfolio lose money?"},
        )
        assert resp.status_code == 400
        assert "Must be a valid UUID format" in resp.json()["detail"]

    def test_post_ask_empty_question(self):
        resp = client.post(
            f"/api/portfolio/{AI_P_ID}/ask",
            json={"question": "   "},
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_post_ask_oversized_question(self):
        resp = client.post(
            f"/api/portfolio/{AI_P_ID}/ask",
            json={"question": "Explain " * 300},
        )
        assert resp.status_code == 422 or resp.status_code == 400

    def test_post_ask_nonexistent_portfolio(self):
        random_id = str(uuid.uuid4())
        resp = client.post(
            f"/api/portfolio/{random_id}/ask",
            json={"question": "What is the portfolio drawdown?"},
        )
        assert resp.status_code == 404
