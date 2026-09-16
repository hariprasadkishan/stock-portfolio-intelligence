# Power BI Institutional Dashboard Specification

This document details the multi-page report architecture, layout design, visual components, field mappings, and interactive features for the **Stock Portfolio Intelligence & Risk Analytics** Power BI Desktop dashboard.

---

## Dashboard Overview & Theme

- **Design Philosophy**: Institutional Financial Terminal aesthetic (clean dark slate/zinc background `#0B0F17`, high-contrast cards `#111827`, subtle grid borders `#1F2937`, restrained typography, tabular figures).
- **Target Audience**: Technical recruiters, investment analysts, quantitative researchers, portfolio managers.
- **Data Refresh**: Sourced directly from PostgreSQL analytical views (`vw_dim_*` and `vw_fact_*`).
- **Interactive Global Slicers**:
  - **Portfolio Slicer**: Dropdown bound to `vw_dim_portfolios[portfolio_name]`.
  - **Date Range Slicer**: Slider bound to `vw_dim_date[date]`.
  - **Sector Slicer**: Multi-select dropdown bound to `vw_dim_assets[sector]`.

---

## Page 1: Portfolio Overview

**Goal**: Deliver an immediate executive-level summary of capital balances, profitability, and fundamental risk-adjusted performance.

### 1.1 Header & Slicers (Top Banner)
- **Visual 1 (Title Text Box)**: "Institutional Portfolio Analytics Terminal" with dynamic subtitle `="Portfolio: " & SELECTEDVALUE(vw_dim_portfolios[portfolio_name], "All Portfolios") & " | Benchmark: " & SELECTEDVALUE(vw_dim_portfolios[benchmark_symbol], "N/A")`.
- **Visual 2 (Slicer - Dropdown)**: Field `vw_dim_portfolios[portfolio_name]`. Single-select enabled.
- **Visual 3 (Slicer - Date Slider)**: Field `vw_dim_date[date]`. Range slider mode.

### 1.2 Executive KPI Scorecard (Row 1)
| Visual # | Visual Type | Measure / Field | Purpose & Financial Meaning |
| :--- | :--- | :--- | :--- |
| **Visual 4** | Card (New) | `[Portfolio Value]` | Current total portfolio equity + cash balance. |
| **Visual 5** | Card (New) | `[Invested Capital]` | Total capital deployed across active holdings. |
| **Visual 6** | Card (New) | `[Absolute P&L]` | Dollar profit/loss relative to initial capital. Conditional formatting (Green if $>0$, Red if $<0$). |
| **Visual 7** | Card (New) | `[Percentage P&L]` | Percentage return on initial capital. |
| **Visual 8** | Card (New) | `[Portfolio Return]` | Cumulative portfolio return over active history. |
| **Visual 9** | Card (New) | `[Annualized Return (CAGR)]` | Geometric compound annual return. |
| **Visual 10** | Card (New) | `[Annualized Volatility]` | Annualized standard deviation ($\sigma \times \sqrt{252}$). |
| **Visual 11** | Card (New) | `[Sharpe Ratio]` | Risk-adjusted excess return per unit of volatility. |

### 1.3 Primary Visuals (Row 2 & 3)
- **Visual 12: Primary Performance Chart**
  - **Type**: Line Chart
  - **Data Source**: `vw_fact_portfolio_performance` JOIN `vw_dim_date`
  - **X-Axis**: `vw_dim_date[date]`
  - **Y-Axis**: `vw_fact_portfolio_performance[total_value]` (Portfolio Equity), `vw_fact_portfolio_performance[benchmark_value]` (Benchmark Index)
  - **Tooltip**: `vw_fact_portfolio_performance[daily_return_pct]`, `vw_fact_portfolio_performance[cumulative_return_pct]`
  - **Purpose**: Visualizes chronological equity curve progression against benchmark market tracking.

- **Visual 13: Asset Allocation Quick Donut**
  - **Type**: Donut Chart
  - **Data Source**: `vw_fact_portfolio_holdings`
  - **Legend**: `vw_fact_portfolio_holdings[ticker]`
  - **Values**: `[Holding Market Value]`
  - **Tooltip**: `[Portfolio Weight %]`
  - **Purpose**: High-level visual representation of asset concentration.

---

## Page 2: Performance & Benchmark

**Goal**: Analyze relative performance, active return generation (alpha spread), and benchmark sensitivity.

### 2.1 Visual Components
- **Visual 1: Cumulative Return Comparison**
  - **Type**: Line Chart
  - **X-Axis**: `vw_dim_date[date]`
  - **Y-Axis**: `[Portfolio Return]`, `[Benchmark Return]`
  - **Formatting**: Portfolio line (Solid Blue `#3B82F6`), Benchmark line (Dashed Purple `#A855F7`).
  - **Purpose**: Tracks cumulative outperformance/underperformance over time.

- **Visual 2: Active Return Spread (Alpha Trend)**
  - **Type**: Clustered Column Chart
  - **X-Axis**: `vw_dim_date[year_month]`
  - **Y-Axis**: `[Active Return]`
  - **Conditional Color**: Green (`#10B981`) if $>0$, Red (`#F43F5E`) if $<0$.
  - **Purpose**: Identifies specific calendar months of positive alpha generation vs benchmark drag.

- **Visual 3: Benchmark Factor Scorecard Matrix**
  - **Type**: Matrix Visual
  - **Rows**: Metric Name (Beta, Jensen's Alpha, Tracking Error, Information Ratio, Correlation, Covariance)
  - **Values**: Sourced from `vw_fact_portfolio_risk_metrics`
  - **Purpose**: Institutional comparative factor table with precise statistical definitions.

---

## Page 3: Risk Analytics

**Goal**: Provide quantitative tail-risk, drawdown, and downside volatility diagnostics without subjective rating labels.

### 3.1 Visual Components
- **Visual 1: Risk Scorecard Cards**
  - `[Annualized Volatility]`, `[Sharpe Ratio]`, `[Sortino Ratio]`, `[Maximum Drawdown]`, `[Max Drawdown Days]`.

- **Visual 2: Tail Risk (VaR & CVaR) Callout Gauges**
  - **Type**: KPI Card / Gauge
  - **Values**: `[Historical VaR 95%]`, `[Historical CVaR 95%]`
  - **Subtext**: "1-Day horizon at 95% historical confidence level."
  - **Purpose**: Quantifies maximum expected loss under standard market stress vs expected shortfall during tail events.

- **Visual 3: Drawdown Underwater Chart**
  - **Type**: Area Chart
  - **X-Axis**: `vw_dim_date[date]`
  - **Y-Axis**: Drawdown percentage (0% to negative peak)
  - **Color**: Rose gradient (`#F43F5E` to `#0B0F17`)
  - **Purpose**: Visualizes recovery cycles and severity of underwater periods.

- **Visual 4: Educational Definition Cards**
  - Multi-row card providing objective statistical definitions for Beta, VaR, CVaR, Sortino, and Tracking Error.

---

## Page 4: Holdings & Exposure

**Goal**: Granular visibility into position weights, cost bases, industry sector diversification, and concentration indexes.

### 4.1 Visual Components
- **Visual 1: Sector Exposure Horizontal Bar Chart**
  - **Type**: Clustered Bar Chart (Horizontal)
  - **Y-Axis**: `vw_fact_portfolio_holdings[sector]`
  - **X-Axis**: `[Sector Weight %]`
  - **Data Label**: Formatted as percentage (`12.5%`)
  - **Note**: Explicitly preserves `"Unknown"` sector category for unclassified instruments.

- **Visual 2: Concentration KPI Cards**
  - `[HHI (Concentration)]`: Herfindahl index value (e.g. `0.3420`).
  - `[Largest Holding Weight]`: Weight of single largest position.
  - `[Top 3 Concentration]`: Combined weight of top 3 assets.
  - `[Top 5 Concentration]`: Combined weight of top 5 assets.

- **Visual 3: Detailed Holdings Matrix**
  - **Type**: Table / Matrix Visual
  - **Columns**:
    1. Ticker (`vw_fact_portfolio_holdings[ticker]`)
    2. Asset Name (`vw_fact_portfolio_holdings[asset_name]`)
    3. Sector (`vw_fact_portfolio_holdings[sector]`)
    4. Shares (`vw_fact_portfolio_holdings[shares]`)
    5. Cost Basis (`vw_fact_portfolio_holdings[cost_basis]`)
    6. Avg Cost / Share (`vw_fact_portfolio_holdings[avg_cost_per_share]`)
    7. Latest Price (`vw_fact_portfolio_holdings[latest_price]`)
    8. Market Value (`vw_fact_portfolio_holdings[market_value]`)
    9. Unrealized P&L (`vw_fact_portfolio_holdings[unrealized_pnl]`)
    10. Portfolio Weight (`vw_fact_portfolio_holdings[portfolio_weight]`)
  - **Sorting**: By Market Value descending.

---

## Page 5: Contribution & Diversification

**Goal**: Decompose portfolio return drivers and evaluate pairwise asset correlation dynamics.

### 5.1 Visual Components
- **Visual 1: Return Contribution Diverging Bar Chart**
  - **Type**: Clustered Bar Chart (Horizontal, centered at 0)
  - **Y-Axis**: `vw_fact_portfolio_holdings[ticker]`
  - **X-Axis**: Return Contribution ($w_i \times R_i$)
  - **Conditional Formatting**: Emerald green for positive contributors ($>0$), rose red for drags ($<0$).
  - **Purpose**: Distinguishes which holdings drove outperformance vs dragged returns.

- **Visual 2: Correlation Heatmap Matrix**
  - **Type**: Matrix Visual
  - **Rows**: `vw_dim_assets[ticker]`
  - **Columns**: `vw_dim_assets[ticker]`
  - **Values**: Pairwise Pearson correlation coefficient $\rho_{i,j}$
  - **Conditional Background Color**:
    - $\rho \ge 0.7$: Deep Blue (`#2563EB`)
    - $\rho \approx 0.0$: Neutral Slate (`#1E293B`)
    - $\rho \le -0.2$: Warm Amber/Rose (`#BE123C`)
  - **Purpose**: Institutional correlation matrix identifying co-movement and diversification clusters.

- **Visual 3: Pairwise Summary Scorecards**
  - Average Pairwise Correlation
  - Highest Correlated Pair
  - Lowest Correlated Pair
