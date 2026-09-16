# Stock Portfolio Intelligence & Risk Analytics

An institutional-grade portfolio intelligence and risk analytics platform that unifies market data ingestion, PostgreSQL relational storage, deterministic quantitative analytics, interactive dashboards, Power BI reporting, and an evidence-grounded AI Financial Analyst.

---

## Overview

Modern portfolio management requires a clean separation between **mathematically verified computations** and **qualitative interpretation**. This platform bridges quantitative portfolio analytics with conversational AI by enforcing an uncompromised boundary:

- **Python, Pandas, and NumPy** perform all financial calculations deterministically.
- **PostgreSQL and SQLAlchemy** persist assets, trades, holdings, market prices, valuation snapshots, and risk scorecards.
- **FastAPI** serves standardized, sanitized REST APIs for both web dashboards and analytical consumers.
- **Next.js, TypeScript, and Tailwind CSS** provide an executive dashboard with interactive visual analytics.
- **Power BI SQL Views** expose star-schema dimensional models with pre-computed holding weights and valuations.
- **AI Financial Analyst** leverages configured Large Language Models (Groq / OpenAI) to explain pre-calculated metrics without ever calculating, guessing, or fabricating financial numbers.

This system is **not** a generic conversational chatbot. The LLM acts exclusively as an analytical interpreter of verified mathematical context.

---

## Architecture

The system operates across two parallel, decoupled analytical workflows:

```mermaid
flowchart TD
    subgraph Data & Persistence
        YF["Yahoo Finance (yfinance)"] -->|OHLCV Data| Ingestion["Market Data Ingestion\n(agent/data/)"]
        Ingestion -->|Validate & Deduplicate| PG[("PostgreSQL 16\n(stock_portfolio_intelligence)")]
        PG -->|SQLAlchemy ORM| Repo["Repository Layer\n(agent/api/repository.py)"]
    end

    subgraph Deterministic Analytics Engine
        Repo --> Analytics["Deterministic Analytics Engine\n(agent/analytics/)"]
        Analytics -->|Returns, Risk, Benchmark, Tail-Risk, Allocations| Endpoints["FastAPI Analytics Endpoints\n(/api/portfolio/*)"]
    end

    subgraph Web Application & AI
        Endpoints --> Dashboard["Next.js Portfolio Dashboard\n(/portfolio/dashboard)"]
        Endpoints --> AIContext["Analytics Context Builder\n(agent/ai_analyst/context.py)"]
        AIContext --> Prompt["System Prompt & Guardrails\n(agent/ai_analyst/prompts.py)"]
        Prompt --> LLM["LLM Provider (Groq / OpenAI)\n(agent/ai_analyst/service.py)"]
        LLM --> AIResponse["POST /api/portfolio/{id}/ask"]
        AIResponse --> UIAnalyst["AI Analyst UI Component\n(frontend/src/components/dashboard/AIAnalyst.tsx)"]
    end

    subgraph Business Intelligence Layer
        PG --> Views["7 PostgreSQL Analytical Views\n(vw_dim_* & vw_fact_*)"]
        Views --> PBIModel["Power BI Star Schema Model\n(docs/powerbi_setup.md)"]
        PBIModel --> PBIDAX["25+ DAX Measures\n(docs/powerbi_dax.md)"]
        PBIDAX --> PBIReport["5-Page BI Reporting Spec\n(docs/powerbi_dashboard.md)"]
    end
```

---

## Key Features

### Market Data Ingestion
- **Automated Data Retrieval**: Fetches historical OHLCV and adjusted close prices via `yfinance`.
- **Validation Engine**: Strictly rejects non-positive prices, high < low anomalies, future or malformed dates, and missing identifiers.
- **Idempotent Persistence**: Utilizes PostgreSQL `ON CONFLICT (ticker, price_date) DO UPDATE` to guarantee zero duplicate price rows.

### Quantitative Financial Analytics
- **Valuation & Returns**: Daily returns (forward-fill resilience), cumulative returns, annualized return (CAGR), ending portfolio valuation, and absolute/percentage P&L.
- **Risk Metrics**: Annualized volatility ($\sigma \times \sqrt{252}$), Sharpe ratio, Sortino ratio (downside deviation), maximum drawdown (MDD), and peak-to-trough drawdown duration.
- **Benchmark Comparative**: Pearson correlation, covariance, Beta ($\beta = \frac{\text{Cov}(R_p, R_b)}{\text{Var}(R_b)}$), annualized Jensen's Alpha ($\alpha = R_p - [R_f + \beta(R_b - R_f)]$), tracking error, and information ratio.
- **Tail-Risk Analytics**: Historical Value at Risk at 95% and 99% confidence intervals ($\text{VaR}_\alpha$), Conditional Value at Risk ($\text{CVaR}_\alpha$ / Expected Shortfall).
- **Portfolio Intelligence**: Exact asset allocation weights ($\sum w_i = 1.0$), sector exposures with explicit `'Unknown'` preservation, Herfindahl-Hirschman Index (HHI), largest holding concentration, top-3 and top-5 weights, weighted return contributions, and pairwise asset correlation matrices.

### AI Financial Analyst
- **Deterministic Grounding**: Natural-language inquiries are paired with a structured plain-text evidence block extracted from the deterministic analytics engine.
- **Strict Guardrails**: Prohibits calculating or inventing metrics, price projections, and buy/sell trading advice. Enforces a strict temporal distinction between historical sensitivity (e.g., historical Beta) and future expectations.
- **Provider Flexibility**: Supports Groq (`llama-3.3-70b-versatile`) and OpenAI (`gpt-4o-mini`) via a provider abstraction.
- **Transparent Provenance**: Each response returns the sanitized inquiry, narrative explanation, `metrics_used` array, and any data advisory `warnings`.

### Interactive Executive Dashboard
- **Executive Scorecard**: Real-time KPI grid covering portfolio valuation, invested capital, P&L, Sharpe, Sortino, volatility, and max drawdown.
- **Visual Analytics**: Interactive performance trajectories against benchmark indices, secondary active return distributions, asset allocation donuts, sector breakdown bars, return contribution charts, and asset correlation heatmaps.
- **Embedded AI Analyst**: Dedicated dashboard card with 5 clickable suggested inquiry chips, real-time character counting (1,000-character ceiling), loading feedback, line-break formatting, and quantitative metric tags.

### Power BI Analytics Layer
- **Analytical SQL Views**: 7 pre-built PostgreSQL views exposing dimensional models (`vw_dim_date`, `vw_dim_assets`, `vw_dim_portfolios`) and fact tables (`vw_fact_portfolio_performance`, `vw_fact_portfolio_holdings`, `vw_fact_portfolio_trades`, `vw_fact_portfolio_risk_metrics`).
- **DAX Measures**: Over 25 documented DAX formulas for dynamic filter-context evaluation in Power BI Desktop.
- *(Note: The analytical views and documentation are provided directly; the final `.pbix` report is authored in Power BI Desktop).*

---

## Database Design

The relational schema resides in PostgreSQL (`stock_portfolio_intelligence`), engineered for double-entry integrity and dimensional reporting:

```
[assets] 1 ────< [benchmarks] 1 ────< [portfolios] 1 ────< [portfolio_holdings]
   │                                         │
   └────────────< [market_prices]            ├──────────< [portfolio_trades]
                                             ├──────────< [portfolio_performance_snapshots]
                                             └──────────< [portfolio_risk_metrics]
```

### Base Tables (8)
1. **`assets`**: Master dimension of traded instruments (`ticker`, `name`, `asset_type`, `sector`, `industry`, `currency`).
2. **`benchmarks`**: Supported benchmark index assets (`symbol`, `name`).
3. **`portfolios`**: Portfolio entity records (`id`, `name`, `base_currency`, `initial_cash`, `available_cash`, `benchmark_symbol`).
4. **`portfolio_holdings`**: Current active positions (`portfolio_id`, `ticker`, `shares`, `cost_basis`).
5. **`portfolio_trades`**: Historical execution ledger (`portfolio_id`, `ticker`, `trade_type`, `shares`, `price`, `executed_at`).
6. **`market_prices`**: Daily historical market data (`ticker`, `price_date`, `open`, `high`, `low`, `close`, `adj_close`, `volume`).
7. **`portfolio_performance_snapshots`**: Daily portfolio valuation curve (`portfolio_id`, `snapshot_date`, `total_equity`, `cash_balance`, `total_value`, `daily_return`).
8. **`portfolio_risk_metrics`**: Pre-computed risk metrics (`portfolio_id`, `as_of_date`, `volatility`, `sharpe`, `sortino`, `max_drawdown`, `beta`, `alpha`, `var_95`, `cvar_95`, `hhi`).

### Power BI Analytical Views (7)
- **`vw_dim_date`**: Calendar dimension containing 4,018 trading and calendar days (2020 through 2030) with Year, Quarter, Month, Week, Day, and Trading Day flags.
- **`vw_dim_assets`**: Enriched asset dimension with explicit handling for missing sectors.
- **`vw_dim_portfolios`**: Container dimension linking portfolios with their benchmark metadata.
- **`vw_fact_portfolio_performance`**: Historical performance series with benchmark values and active returns.
- **`vw_fact_portfolio_holdings`**: Current positions enriched with latest prices, unrealized P&L, and window-partitioned portfolio weights.
- **`vw_fact_portfolio_trades`**: Transaction fact table with asset metadata.
- **`vw_fact_portfolio_risk_metrics`**: Risk scorecard fact table.

---

## Tech Stack

### Backend
- **Python 3.12**: Core runtime.
- **FastAPI (0.115+) & Uvicorn**: High-performance RESTful API layer.
- **SQLAlchemy 2.0 & Psycopg 3**: Object-relational mapping and connection pooling for PostgreSQL.
- **PostgreSQL 16**: Relational storage engine with native constraint verification.
- **Pandas (2.3+) & NumPy**: Deterministic quantitative calculation engine.
- **yfinance (0.2.64+)**: Market data collection.
- **Pydantic v2**: Data validation and schema enforcement.

### Artificial Intelligence
- **OpenAI Python SDK (1.0+)**: Structured completions interface.
- **Groq API**: High-throughput inference for `llama-3.3-70b-versatile`.
- **OpenAI API**: Inference support for `gpt-4o-mini`.

### Frontend
- **Next.js 15 (App Router)**: React application framework.
- **React 19**: Component architecture.
- **TypeScript 5**: Strict end-to-end type safety.
- **Tailwind CSS 4**: Responsive design system.
- **Recharts (3.0+)**: Vector chart visualization.
- **Lucide React**: Modern iconography.

### Testing & Verification
- **Pytest 9.1**: Backend test runner.
- **Node.js Test Runner (`node:test`)**: Zero-dependency frontend integration tests.

---

## Project Structure

```
stock-portfolio-analysis-agent/
├── agent/
│   ├── ai_analyst/               # AI Financial Analyst service
│   │   ├── __init__.py           # Package exports
│   │   ├── context.py            # Deterministic evidence context builder
│   │   ├── prompts.py            # System prompts, guardrails, and templates
│   │   ├── schemas.py            # Pydantic input/output models
│   │   └── service.py            # LLM provider orchestration & error handling
│   ├── analytics/                # Deterministic quantitative engine
│   │   ├── benchmark.py          # Beta, Alpha, correlation, covariance, tracking error
│   │   ├── portfolio.py          # Portfolio valuation and returns time series
│   │   ├── portfolio_intelligence.py # Allocation, sectors, HHI, contribution
│   │   ├── returns.py            # Daily, cumulative, and annualized returns (CAGR)
│   │   ├── risk.py               # Volatility, Sharpe, Sortino, max drawdown
│   │   ├── tail_risk.py          # Historical VaR and CVaR (Expected Shortfall)
│   │   └── types.py              # Analytics dataclasses and calculation types
│   ├── api/                      # FastAPI layer
│   │   ├── repository.py         # SQLAlchemy data access layer
│   │   ├── routes.py             # REST endpoints (/api/portfolio/*)
│   │   └── schemas.py            # Pydantic response models
│   ├── data/                     # Ingestion pipeline
│   │   ├── fetcher.py            # Yahoo Finance downloader
│   │   ├── ingestion.py          # Database upsert orchestration
│   │   ├── normalization.py      # DataFrame reshaping and typing
│   │   ├── schemas.py            # Ingestion dataclasses
│   │   └── validation.py         # Price, volume, and date validation rules
│   ├── db/                       # Database models and session management
│   │   ├── base.py               # SQLAlchemy declarative base
│   │   ├── models.py             # 8 PostgreSQL table models
│   │   └── session.py            # Connection engine and session maker
│   ├── main.py                   # FastAPI server entry point
│   ├── prompts.py                # Legacy simulation prompts
│   └── stock_analysis.py         # CrewAI simulation workflow & LLM helpers
├── docs/                         # Architecture & Power BI documentation
│   ├── DATA_FLOW.md              # End-to-end data flow specification
│   ├── EXISTING_ARCHITECTURE.md  # Core workflow documentation
│   ├── powerbi_dashboard.md      # 5-page Power BI report design
│   ├── powerbi_dax.md            # 25+ production DAX measures
│   └── powerbi_setup.md          # PostgreSQL Star Schema setup guide
├── frontend/                     # Next.js web application
│   ├── src/
│   │   ├── app/
│   │   │   ├── portfolio/dashboard/ # Main analytics dashboard page
│   │   │   ├── layout.tsx        # Root HTML layout
│   │   │   └── page.tsx          # Interactive simulation page
│   │   ├── components/
│   │   │   ├── dashboard/        # Modular dashboard cards (15 components)
│   │   │   │   ├── AIAnalyst.tsx # Embedded AI Analyst interface
│   │   │   │   ├── AssetAllocation.tsx
│   │   │   │   ├── BenchmarkComparison.tsx
│   │   │   │   ├── KPIGrid.tsx
│   │   │   │   ├── PerformanceChart.tsx
│   │   │   │   └── RiskAnalytics.tsx
│   │   │   └── portfolio/        # Re-exports for architectural flexibility
│   │   └── lib/
│   │       ├── api.ts            # Frontend API client
│   │       ├── formatters.ts     # Currency, percentage, and date utilities
│   │       └── types.ts          # TypeScript interfaces
│   ├── test_dashboard.test.mjs   # Node.js frontend test suite
│   ├── package.json
│   └── tsconfig.json
├── migrations/                   # PostgreSQL DDL migrations
│   ├── 001_initial_schema.sql    # 8 core relational tables and indices
│   └── 002_powerbi_views.sql     # 7 Power BI analytical SQL views
├── tests/                        # Automated backend test suite
│   ├── test_ai_analyst.py        # AI Analyst context, guardrails, and API tests
│   ├── test_api.py               # FastAPI endpoint tests
│   ├── test_benchmark.py         # Beta, Alpha, and benchmark tests
│   ├── test_ingestion.py         # Market data ingestion tests
│   ├── test_portfolio_analytics.py # Valuation and returns tests
│   ├── test_portfolio_intelligence.py # Allocation and concentration tests
│   ├── test_powerbi_views.py     # SQL view validation tests
│   ├── test_returns.py           # Return calculation tests
│   ├── test_risk.py              # Volatility, Sharpe, and drawdown tests
│   └── test_tail_risk.py         # VaR and CVaR tests
├── pyproject.toml                # Python dependencies and build config
└── README.md
```

---

## Setup

### Prerequisites
- **Python 3.12**
- **uv** (recommended Python package manager)
- **Node.js 20+** and **npm**
- **PostgreSQL 16**

---

### Step 1: Clone and Enter Repository
```bash
git clone <repository-url>
cd stock-portfolio-analysis-agent
```

### Step 2: Install Backend Dependencies
```bash
uv sync
```

### Step 3: Configure PostgreSQL
Ensure PostgreSQL is running locally, then create the project database:
```bash
createdb stock_portfolio_intelligence
```

### Step 4: Apply Database Migrations
Apply the initial schema and Power BI analytical views:
```bash
psql -d stock_portfolio_intelligence -f migrations/001_initial_schema.sql
psql -d stock_portfolio_intelligence -f migrations/002_powerbi_views.sql
```

### Step 5: Configure Backend Environment
Create `agent/.env` based on `agent/.env.example`:
```bash
cp agent/.env.example agent/.env
```
Edit `agent/.env`:
```ini
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/stock_portfolio_intelligence
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
PORT=8000
```
*(If using Groq, set `AI_PROVIDER=groq`, `GROQ_API_KEY=your-groq-api-key-here`, and `GROQ_MODEL=llama-3.3-70b-versatile`).*

### Step 6: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 7: Configure Frontend Environment
Create `frontend/.env.local` based on `frontend/.env.example`:
```bash
cp frontend/.env.example frontend/.env.local
```
*(No API keys belong in the frontend. Keep the default `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`).*

---

## Environment Variables

### Backend (`agent/.env`)
| Variable | Required | Default | Description |
|:---|:---:|:---:|:---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://localhost:5432/stock_portfolio_intelligence` | PostgreSQL connection string. |
| `AI_PROVIDER` | Yes | `openai` | Target LLM provider (`openai` or `groq`). |
| `OPENAI_API_KEY` | If OpenAI | — | API key for OpenAI endpoints. |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model identifier. |
| `GROQ_API_KEY` | If Groq | — | API key for Groq Cloud. |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model identifier. |
| `PORT` | No | `8000` | Backend HTTP server port. |

### Frontend (`frontend/.env.local`)
| Variable | Required | Default | Description |
|:---|:---:|:---:|:---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `http://localhost:8000` | Base URL for FastAPI analytics endpoints. |
| `NEXT_PUBLIC_DEFAULT_PORTFOLIO_ID`| No | `""` | Optional default portfolio UUID to load on dashboard launch. |
| `NEXT_PUBLIC_CREWAI_URL` | No | `http://localhost:8000/crewai-agent` | CopilotKit agent runtime endpoint. |

> **Security Note:** LLM API keys must remain strictly in `agent/.env`. The frontend code and client bundles contain zero private credentials.

---

## Running the Project

### Start Backend API Server
From the repository root:
```bash
uv run python agent/main.py
```
*The FastAPI server will start at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.*

### Start Frontend Dashboard
In a separate terminal:
```bash
cd frontend
npm run dev
```
*Open [http://localhost:3000/portfolio/dashboard](http://localhost:3000/portfolio/dashboard) to view the executive portfolio dashboard.*

---

## API Reference

All deterministic endpoints accept an ISO UUID `portfolio_id` parameter and optional query parameters:

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/portfolio` | List all available portfolios. |
| `GET` | `/api/portfolio/{id}/overview` | Executive KPI summary (value, cash, P&L, Sharpe, Sortino, drawdowns). |
| `GET` | `/api/portfolio/{id}/risk` | Quantitative risk scorecard (volatility, VaR 95%, CVaR 95%, Beta, Alpha). |
| `GET` | `/api/portfolio/{id}/allocation` | Holdings breakdown, market values, and portfolio weights. |
| `GET` | `/api/portfolio/{id}/sectors` | Sector exposure breakdown and weights. |
| `GET` | `/api/portfolio/{id}/contributions` | Weighted return contribution per holding. |
| `GET` | `/api/portfolio/{id}/correlation` | Pairwise asset return correlation matrix. |
| `GET` | `/api/portfolio/{id}/benchmark` | Active returns, Beta, Alpha, and benchmark comparisons. |
| `GET` | `/api/portfolio/{id}/performance` | Chronological portfolio and benchmark valuation snapshots. |
| `GET` | `/api/portfolio/{id}/dashboard` | **Consolidated single endpoint** aggregating all 8 analytics domains. |
| `POST`| `/api/portfolio/{id}/ask` | Query the **AI Financial Analyst** with evidence-grounded responses. |

### AI Analyst Request Example
```http
POST /api/portfolio/11111111-1111-1111-1111-111111111111/ask
Content-Type: application/json

{
  "question": "Why did my portfolio underperform the benchmark last month?"
}
```

### AI Analyst Response Example
```json
{
  "question": "Why did my portfolio underperform the benchmark last month?",
  "answer": "Over the analyzed historical window, your portfolio returned +5.15% against the benchmark return of +7.20%, resulting in an active return of -2.05%.\n\nThis underperformance was primarily driven by your 66.0% capital concentration in Technology assets, which experienced localized drawdowns. Although your portfolio Beta of 0.88 reflected lower sensitivity to broad market swings, negative return contributions from top holdings offset broader gains.",
  "portfolio_id": "11111111-1111-1111-1111-111111111111",
  "metrics_used": [
    "cumulative_return",
    "benchmark_cumulative_return",
    "active_return",
    "beta",
    "asset_allocation",
    "concentration_analytics",
    "return_contribution"
  ],
  "warnings": []
}
```

---

## Testing & Quality Assurance

The codebase maintains rigorous automated test suites across backend and frontend layers:

### Run Backend Unit & Integration Tests
```bash
uv run pytest -v
```
- **120 tests passed** covering data ingestion, mathematical returns, risk analytics, benchmark regressions, tail-risk quantiles, portfolio intelligence, Power BI SQL views, FastAPI routes, and AI Analyst guardrails.

### Run Python Syntax & Compilation Verification
```bash
uv run python -m py_compile agent/*.py agent/**/*.py tests/*.py
```

### Run Frontend Integration & Security Tests
```bash
cd frontend
npm test
```
- **23 tests passed** covering formatters, KPI extractions, asset allocations, concentration metrics, correlation symmetry, AI Analyst lifecycle states, input constraints, and automated AST secrets detection.

### Run TypeScript Verification
```bash
cd frontend
npx tsc --noEmit
```

### Run Production Build Verification
```bash
cd frontend
npm run build
```

---

## Power BI Integration

The reporting layer uses a star schema directly accessible by Power BI Desktop via standard PostgreSQL connectivity:

- **Dimensions**: `vw_dim_date`, `vw_dim_assets`, `vw_dim_portfolios`.
- **Facts**: `vw_fact_portfolio_performance`, `vw_fact_portfolio_holdings`, `vw_fact_portfolio_trades`, `vw_fact_portfolio_risk_metrics`.

Refer to the dedicated documentation suite in `docs/`:
1. [`docs/powerbi_setup.md`](docs/powerbi_setup.md): PostgreSQL gateway connection instructions and Star Schema relationship mappings.
2. [`docs/powerbi_dax.md`](docs/powerbi_dax.md): Production DAX formulas (Portfolio Value, Return %, Volatility, Sharpe, Sortino, VaR 95%, CVaR 95%, Beta, Alpha, and Concentration metrics).
3. [`docs/powerbi_dashboard.md`](docs/powerbi_dashboard.md): Comprehensive 5-page report layout specification for Power BI Desktop.

---

## AI Analyst Design Philosophy

```
  ┌─────────────────────────────────────────────────────────┐
  │  Python computes.                                       │
  │  PostgreSQL stores.                                     │
  │  FastAPI serves.                                        │
  │  The LLM explains.                                      │
  └─────────────────────────────────────────────────────────┘
```

The AI Financial Analyst does **not** estimate or recalculate financial metrics. When a user asks an analytical question:
1. The backend gathers verified, pre-computed metrics for that portfolio ID across all 8 domains.
2. The context builder constructs a structured evidence block containing exact valuation, return, risk, and concentration figures.
3. The system prompt instructs the model to act as a quantitative explainer, restricting it strictly to the provided numbers.
4. The response references exact data points and reports `metrics_used` to ensure auditability.

---

## Limitations

- **Market Data**: Ingestion relies on the public Yahoo Finance API (`yfinance`), which may be subject to network latency, upstream rate limits, or occasional schema variations.
- **Local Database**: Requires an active PostgreSQL 16 instance with permissions to create databases and views.
- **Power BI Reporting**: Analytical SQL views and DAX specifications are provided in the repository; final report rendering requires authoring inside Power BI Desktop.
- **AI Dependencies**: Response latency depends on the upstream Groq or OpenAI provider.
- **Analytical Scope**: The system provides historical quantitative risk analytics and performance reporting; it does not execute live market orders or make automated trading decisions.

---

## Future Improvements

- **Multi-Tenant Authentication**: Role-based access control (RBAC) and user-specific portfolio segregation.
- **Automated Ingestion Scheduling**: Asynchronous background workers (e.g., Celery or Temporal) for scheduled market close data refreshes.
- **Transaction Cost & Slippage Modeling**: Detailed trade accounting incorporating exchange fees, commissions, and bid-ask slippage.
- **Scenario & Stress Testing**: Historical crisis simulations (e.g., 2008 Financial Crisis, 2020 COVID shock).
- **Persistent Conversation Context**: Multi-turn dialogue caching for the AI Financial Analyst.

---

## Attribution

This project extends an MIT-licensed Stock Portfolio Agent foundation with a PostgreSQL-backed analytics engine, quantitative risk analysis, portfolio intelligence, Power BI reporting, and an evidence-grounded AI analyst.