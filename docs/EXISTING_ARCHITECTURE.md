# Existing Architecture Documentation

## 1. System Overview & Problem Solved
The **Stock Portfolio Analysis Agent** is a full-stack, conversational financial intelligence application. It allows users to simulate, analyze, and manage equity investment portfolios using natural language commands (such as *"Invest in Apple and Microsoft with $10k each since Jan 2023"*).

### Primary Problem Solved
Traditional portfolio backtesting and asset tracking tools require tedious manual data entry, symbol lookup, date selection, and parameter configuration. This application streamlines that workflow into an **interactive agentic experience**:
1. **Natural Language Understanding**: Interprets informal investment queries, extracting tickers, dollar amounts, start dates, and DCA/single-shot strategies.
2. **Automated Market Data Ingestion**: Automatically downloads real-world historical price data via Yahoo Finance.
3. **Simulation & Benchmark Comparison**: Simulates trade execution (single-shot lump sum or dollar-cost averaging), tracks cash depletion and share accumulation, calculates investment returns, and benchmarks performance against the S&P 500 (`SPY`).
4. **Qualitative Market Synthesis**: Generates AI-synthesized bull and bear theses for the selected assets.
5. **Real-Time Agent Observability**: Streams step-by-step execution logs (e.g., "Analyzing query", "Gathering Stock Data", "Calculating portfolio allocation", "Extracting Key insights") to the user interface via Server-Sent Events (SSE) before asking for user approval.

---

## 2. Complete Codebase Structure
The project is organized as a decoupled monorepo containing a Python backend agent and a Next.js React frontend:

```
stock-portfolio-analysis-agent/
├── .python-version               # Specifies Python version (3.12)
├── pyproject.toml                # Python project definition and dependencies (uv/pip)
├── uv.lock                       # Lockfile for reproducible Python dependencies
├── README.md                     # Setup instructions and documentation
├── agent/                        # Backend Application (FastAPI + CrewAI)
│   ├── .env.example              # Sample backend environment variables (OPENAI_API_KEY)
│   ├── __init__.py               # Python package initialization
│   ├── main.py                   # FastAPI application, AG-UI SSE streaming endpoint
│   ├── prompts.py                # System prompt templates and instructions
│   └── stock_analysis.py         # CrewAI Flow state machine, yfinance ingestion, simulation
└── frontend/                     # Frontend Application (Next.js App Router)
    ├── .env.example              # Sample frontend environment variables
    ├── next-env.d.ts             # Next.js TypeScript definitions
    ├── next.config.ts            # Next.js configuration
    ├── package.json              # NPM package definition and frontend dependencies
    ├── pnpm-lock.yaml            # PNPM dependency lockfile
    ├── postcss.config.mjs        # PostCSS configuration for Tailwind CSS v4
    ├── tsconfig.json             # TypeScript compiler settings
    └── src/
        ├── app/
        │   ├── api/
        │   │   └── copilotkit/
        │   │       └── route.ts  # Next.js API route proxying CopilotKit requests to FastAPI
        │   ├── components/
        │   │   ├── cash-panel.tsx          # Top bar: Total cash, invested amount, returns
        │   │   ├── component-tree.tsx      # Sidebar displaying UI layout hierarchy tree
        │   │   ├── generative-canvas.tsx   # Dashboard canvas rendering charts and insights
        │   │   ├── prompt-panel.tsx        # Left sidebar with CopilotChat interface
        │   │   ├── theme-provider.tsx      # Theme context (unused/commented)
        │   │   ├── tool-logs.tsx           # Real-time agent status badge tracker
        │   │   └── chart-components/
        │   │       ├── allocation-table.tsx# Table rendering asset breakdown & returns
        │   │       ├── bar-chart.tsx       # Recharts bar chart for individual ticker returns
        │   │       ├── insight-card.tsx    # Card component for Bull/Bear market theses
        │   │       ├── line-chart.tsx      # Recharts line chart comparing Portfolio vs SPY
        │   │       └── section-title.tsx   # Section header component
        │   ├── favicon.ico
        │   ├── globals.css                 # Global CSS and Tailwind directives
        │   ├── layout.tsx                  # Root layout wrapping app in CopilotKit provider
        │   └── page.tsx                    # Main client page, state hub & Copilot actions
        └── utils/
            └── prompts.ts                  # Client-side prompt templates for AI suggestions
```

---

## 3. Application Lifecycle & Startup Sequence

### Backend Startup (`agent/main.py`)
1. Executed via `uv run python agent/main.py`.
2. Python loads environment variables from `.env` via `load_dotenv()` in `stock_analysis.py`.
3. An instance of `FastAPI()` is created.
4. Uvicorn boots the ASGI server on `0.0.0.0:8000` (or configured `$PORT`) with development hot-reloading enabled.
5. Endpoint `/crewai-agent` is registered and waits for incoming POST requests formatted in the AG-UI / CopilotKit protocol (`RunAgentInput`).

### Frontend Startup (`frontend/`)
1. Executed via `npm run dev` (running Next.js 15 with Turbopack on `http://localhost:3000`).
2. App Router loads `layout.tsx`:
   - Configures Geist and Geist Mono Google fonts.
   - Imports CSS files (`globals.css`, `@copilotkit/react-ui/styles.css`).
   - Wraps children with `<CopilotKit runtimeUrl="/api/copilotkit" agent="crewaiAgent">`.
3. Main Page `page.tsx` (`OpenStocksCanvas`) mounts:
   - Initializes local React state: `totalCash = 1,000,000`, `investedAmount = 0`, empty portfolio lists.
   - Executes `useEffect` -> `getBenchmarkData()`, rendering default baseline placeholder data (AAPL + NVDA benchmark from Jan 2023 to Dec 2024).
   - Establishes hook connections: `useCoAgent` binds to backend agent state; `useCopilotAction` registers handlers for `render_standard_charts_and_table` and `render_custom_charts`.

---

## 4. Frontend Framework & Architecture
- **Framework**: [Next.js 15.3.4](https://nextjs.org) (App Router), [React 19](https://react.dev), TypeScript 5.
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com) with CSS variables.
- **Agentic UI Layer**: [CopilotKit](https://github.com/CopilotKit/CopilotKit) (`@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`).
- **Data Visualization**: [Recharts 3.0.2](https://recharts.org) for responsive SVG charting.
- **Icons**: [Lucide React](https://lucide.dev).

### Architecture Pattern: Generative Canvas with Human-in-the-Loop
The frontend does not automatically commit backend calculations to the main portfolio state. Instead, it uses CopilotKit's `renderAndWaitForResponse` pattern:
1. When the agent completes the allocation, it emits a `render_standard_charts_and_table` tool call.
2. The chat window displays an in-line micro-preview (small Line Chart, Bar Chart, and Allocation Table) along with **"Accept"** and **"Reject"** buttons.
3. If the user clicks **"Accept"**, local state (`currentState`, `totalCash`, `investedAmount`) is committed, updating the main **Generative Canvas** dashboard. If rejected, the portfolio remains untouched.

---

## 5. Backend Framework & Architecture
- **Web Framework**: [FastAPI 0.115](https://fastapi.tiangolo.com) + [Uvicorn 0.35](https://www.uvicorn.org).
- **Agent Orchestration**: [CrewAI 0.140](https://github.com/crewAIInc/crewAI) using `crewai.flow.flow.Flow` (State-Machine Flow).
- **Streaming Protocol**: [AG-UI Protocol](https://github.com/ag-ui-org/ag-ui) (`ag-ui-protocol` / `@ag-ui/client`) streaming events as Server-Sent Events (SSE).
- **Financial Data Processing**: `yfinance` (0.2.64), `pandas` (2.3.0), `numpy`.

### Agent Architecture: Event-Driven State Machine
Rather than an unstructured autonomous agent loop, the backend utilizes CrewAI's structured `Flow` with explicit stage transitions:
```
[start] ──> [chat] ──(if investment query)──> [simulation] ──> [allocation] ──> [insights] ──> [end]
               │
               └──(if general inquiry)─────────────────────────────────────────────> [end]
```
At each step, the workflow pushes real-time `StateDeltaEvent` updates to an async queue, allowing the client to watch progress live.

---

## 6. Entry-Point Files
1. **Backend Server Entry**: [`agent/main.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/main.py)
   - Exposes `app = FastAPI()`, contains `crewai_agent()` endpoint and `main()` Uvicorn launcher.
2. **Backend Logic Entry**: [`agent/stock_analysis.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/stock_analysis.py)
   - Contains `StockAnalysisFlow` definition and tool execution logic.
3. **Frontend Shell Entry**: [`frontend/src/app/layout.tsx`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/layout.tsx)
   - Root layout providing fonts and `<CopilotKit>` context.
4. **Frontend View Entry**: [`frontend/src/app/page.tsx`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/page.tsx)
   - Root client component hosting the `OpenStocksCanvas` page.
5. **Frontend Runtime Bridge**: [`frontend/src/app/api/copilotkit/route.ts`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/api/copilotkit/route.ts)
   - Next.js API route that proxies communication between the browser CopilotKit runtime and the FastAPI backend.

---

## 7. Important Files & Responsibilities

| File | Path | Responsibility |
|---|---|---|
| `main.py` | `agent/main.py` | FastAPI application, SSE event generator, state snapshotting, tool call event dispatching. |
| `stock_analysis.py` | `agent/stock_analysis.py` | CrewAI Flow workflow (`StockAnalysisFlow`), financial calculations, Yahoo Finance data retrieval, SPY benchmark math. |
| `prompts.py` | `agent/prompts.py` | Holds `system_prompt` (rules for ticker extraction and additive portfolio behavior) and `insights_prompt`. |
| `route.ts` | `frontend/src/app/api/copilotkit/route.ts` | Serverless CopilotRuntime handler bridging React client with FastAPI via `HttpAgent`. |
| `page.tsx` | `frontend/src/app/page.tsx` | Primary UI controller: state synchronization, CopilotKit actions (`render_standard_charts_and_table`), Accept/Reject flow. |
| `cash-panel.tsx` | `frontend/src/app/components/cash-panel.tsx` | Top metrics header: editable total cash, invested capital, portfolio value, 4-year return, allocation progress bar. |
| `generative-canvas.tsx` | `frontend/src/app/components/generative-canvas.tsx` | Main dashboard grid presenting Performance line chart, Allocation table, Returns bar chart, and Bull/Bear cards. |
| `tool-logs.tsx` | `frontend/src/app/components/tool-logs.tsx` | Live task execution badge list showing animated spinning or completed checkmarks. |
| `chart-components/*` | `frontend/src/app/components/chart-components/` | Visual chart primitives using Recharts (`line-chart.tsx`, `bar-chart.tsx`, `allocation-table.tsx`, `insight-card.tsx`). |
| `prompts.ts` | `frontend/src/utils/prompts.ts` | Prompts for dynamic LLM-driven query suggestions in the chat box. |

---

## 8. Important Classes and Functions

### Backend (`agent/`)
- `AgentState(CopilotKitState)` ([`agent/main.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/main.py#L51-L72)): Defines typed state containing `tools`, `messages`, `available_cash`, `investment_summary`, `investment_portfolio`, and `tool_logs`.
- `crewai_agent(input_data: RunAgentInput)` ([`agent/main.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/main.py#L77-L340)): Main FastAPI endpoint. Streams events via `StreamingResponse(event_generator(), media_type="text/event-stream")`.
- `StockAnalysisFlow(Flow)` ([`agent/stock_analysis.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/stock_analysis.py#L163-L1030)): CrewAI Flow orchestrating the entire lifecycle:
  - `start()`: Injects current portfolio holdings JSON into the system prompt.
  - `chat()`: Calls OpenAI with `extract_relevant_data_from_user_prompt` tool.
  - `simulation()`: Downloads historical quotes via `yfinance`.
  - `allocation()`: Computes single-shot/DCA purchases, cash depletion, SPY benchmark comparison, and prepares `render_standard_charts_and_table` tool call.
  - `insights()`: Calls OpenAI with `generate_insights` tool to obtain bull and bear market cases.
  - `end()`: Concludes workflow and returns state.
- `convert_tool_call(tc)` ([`agent/stock_analysis.py`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/agent/stock_analysis.py#L1036-L1053)): Converts OpenAI tool call objects into internal serializable dictionaries.

### Frontend (`frontend/src/`)
- `OpenStocksCanvas()` ([`frontend/src/app/page.tsx`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/page.tsx#L62-L311)): Core dashboard component.
- `useCopilotAction("render_standard_charts_and_table")` ([`frontend/src/app/page.tsx`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/page.tsx#L94-L177)): Intercepts the agent's rendering action, provides the interactive Accept/Reject prompt, and commits changes to React state.
- `CashPanel()` ([`frontend/src/app/components/cash-panel.tsx`](file:///Users/apple/Documents/stock-portfolio-intelligence/ai-engineering-hub/stock-portfolio-analysis-agent/frontend/src/app/components/cash-panel.tsx#L14-L183)): Header metrics calculator and in-place cash balance editor.

---

## 9. Stock Data Ingestion & Providers
- **Provider**: Yahoo Finance via the Python [`yfinance`](https://github.com/ranaroussi/yfinance) library.
- **Endpoint / Mechanism**:
  ```python
  data = yf.download(
      all_tickers,
      start=investment_date,
      end=datetime.today().strftime("%Y-%m-%d"),
      interval="3mo"  # Quarterly historical samples
  )
  ```
- **Benchmark Data**:
  ```python
  spy_prices = yf.download(
      "SPY",
      start=start_date,
      end=end_date,
      interval="1d",
      progress=False
  )["Close"]
  ```
  The daily SPY prices are reindexed to match the quarterly portfolio dates using forward-fill (`method="ffill"`).
- **Date Boundary Enforcement**: If the user specifies an investment start date older than 4 years, the backend automatically truncates it: `investment_date = f"{current_year - 4}-01-01"`.

---

## 10. AI Agent, LLM, and Tool Calling Mechanism
- **LLM Used**: `gpt-4o-mini` from OpenAI (`model="gpt-4o-mini"` called using the official `OpenAI` client).
- **Tools / Function Definitions**:
  1. **`extract_relevant_data_from_user_prompt`**:
     - Extract structured entities: `ticker_symbols` (array of strings), `investment_date` (ISO date string), `amount_of_dollars_to_be_invested` (array of numbers), `interval_of_investment` (e.g. `'single_shot'`, `'1mo'`, `'3mo'`), and `to_be_added_in_portfolio` (boolean).
  2. **`generate_insights`**:
     - Prompts the LLM to return structured positive (`bullInsights`) and negative (`bearInsights`) bullet points, each containing `title`, `description`, and an `emoji`.
  3. **`render_standard_charts_and_table`** (Synthetic Tool Call):
     - Created programmatically by Python code in `allocation()` and streamed to CopilotKit to trigger client-side rendering.

### Two-Layer Tool Calling Architecture
1. **Layer 1 (OpenAI Function Calling)**: Python backend sends tool definitions to OpenAI. OpenAI responds with `finish_reason: "tool_calls"`. Python parses the arguments.
2. **Layer 2 (AG-UI / CopilotKit Protocol)**: The Python backend packages the financial analysis and synthesizes a tool call named `render_standard_charts_and_table`, streaming `ToolCallStartEvent`, `ToolCallArgsEvent`, and `ToolCallEndEvent` over SSE. CopilotKit receives these events and renders the corresponding React component registered with `useCopilotAction`.

---

## 11. Financial Calculations & Metrics

### Financial Simulation Models
1. **Single-Shot (Lump-Sum) Purchase**:
   - Executes at the first historical period $t_0$.
   - Integer share purchase:
     $$\text{shares\_to\_buy}_i = \left\lfloor \frac{\text{allocated\_cash}_i}{P_{i, t_0}} \right\rfloor$$
   - Total cost: $\text{cost}_i = \text{shares\_to\_buy}_i \times P_{i, t_0}$
   - Cash deduction: $\text{total\_cash} = \text{total\_cash} - \text{cost}_i$
2. **Dollar-Cost Averaging (DCA)**:
   - Iterates through historical quarterly rows; attempts to purchase additional whole shares at each timestamp while cash is sufficient.
3. **SPY Benchmark Simulation**:
   - Total capital invested in the user's portfolio ($\sum \text{invested}_i$) is simulated as being invested in `SPY`:
     $$\text{spy\_shares} = \frac{\text{total\_invested}}{P_{\text{SPY}, t_0}}$$
     (Allows fractional shares).
4. **Time-Series Portfolio Valuation ($V_t$)**:
   - At each quarterly date $t$:
     $$V_t = \sum_{i} \left( \text{holdings}_{i} \times P_{i, t} \right)$$
     *(Cash is excluded from the chart curve to depict pure equity asset appreciation).*
5. **SPY Time-Series Valuation ($S_t$)**:
   - At each date $t$:
     $$S_t = \text{spy\_shares} \times P_{\text{SPY}, t}$$

### Output Metrics
- **Individual Return ($)**: $\text{holding\_value}_i - \text{invested}_i$
- **Individual Return (%)**: $\frac{\text{holding\_value}_i - \text{invested}_i}{\text{invested}_i} \times 100$
- **Allocation (%)**: $\frac{\text{invested}_i}{\text{total\_invested}} \times 100$
- **Total Portfolio Value ($)**: $\sum \text{holding\_value}_i + \text{remaining\_cash}$
- **Total Portfolio Return ($)**: $\sum \text{returns}_i$
- **4-Year Return**: $\text{currentPortfolioValue} - \text{investedAmount} - \text{totalCash}$
- **Insufficient Funds Detection**: Logs timestamp, ticker, share price, and available cash whenever cash is inadequate to purchase a single share.

---

## 12. State Management & Storage
- **Database**: **None**. There is no SQL database, no NoSQL database, and no file persistence.
- **SQL Usage**: **None**. No relational queries, ORMs, or migrations exist.
- **State Persistence**:
  - **Backend State**: Ephemeral in-memory object (`AgentState`) active only during the duration of the HTTP request.
  - **Frontend State**: Held in client-side React component state (`useState` inside `page.tsx` and CopilotKit internal session context).
  - **Impact**: Any browser refresh, tab closure, or server reboot clears all historical allocations and chat logs.

---

## 13. Error Handling & Testing Status

### Error Handling
- **Backend**:
  - Broad `try...except Exception as e` blocks wrap main execution blocks.
  - Unhandled exceptions are logged with `print(e)`.
  - In `agent/main.py`, exceptions during streaming yield a fallback text message: `"Something went wrong! Please try again."`.
  - In `simulation()`, if `yf.download` returns an empty DataFrame (invalid ticker or missing data), the flow terminates early returning `"end"`.
  - In `allocation()`, if SPY download fails, it silently falls back to `None` values for benchmark comparison.
- **Frontend**:
  - Basic React state fallbacks (`|| []`, optional chaining `?.`).
  - No global error boundary or retry mechanism for dropped SSE streams.

### Testing
- **Automated Tests**: **None**. No unit tests, no integration tests, no end-to-end tests exist anywhere in the repository.
- **Validation**: Performed manually by starting both servers and verifying functionality in the browser.

---

## 14. Key Limitations of the Current Project
1. **Zero Persistence**: Refreshing the browser resets the portfolio to default mock data ($1,000,000 cash, AAPL/NVDA baseline).
2. **Yahoo Finance Dependency**: Relies on unofficial Yahoo Finance scraping via `yfinance`, which is prone to rate-limiting, IP blocks, and schema breaks.
3. **Coarse Quarterly Simulation**: Historical simulation runs on 3-month quarterly intervals (`interval="3mo"`), missing intermediate volatility, dividend adjustments, and accurate execution prices.
4. **Whole-Share Only Math**: Stocks can only be bought in integer quantities (`allocated // price`), leaving uninvested cash residuals and creating discrepancies for high-priced stocks.
5. **Arbitrary 4-Year Lookback Restriction**: Enforces an artificial 4-year maximum backtesting horizon.
6. **No Real Portfolio Management**: Lacks rebalancing, tax-lot accounting, short positions, stop-loss simulation, dividend reinvestment (DRIP), or trading fee models.
7. **Single-User Architecture**: No user authentication, session security, or multi-tenant database partitioning.
8. **Fragile Event Filtering**: `main.py` relies on string-matching heuristics (e.g. checking for substrings like `'insights'` or `'processing'`) to suppress events and avoid UI flickering.
