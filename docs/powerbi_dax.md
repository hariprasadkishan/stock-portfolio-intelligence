# Power BI DAX Measures & Analytics Layer

This document defines the production Data Analysis Expressions (DAX) measures library for the **Stock Portfolio Intelligence & Risk Analytics** Power BI semantic model.

---

## Architectural Principle: Deterministic Analytics vs. DAX Aggregation

To avoid calculation drift and redundant computational complexity, the system strictly enforces a clear division of responsibility:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AUTHORITATIVE DETERMINISTIC LAYER (Python / PostgreSQL)                 │
│ • Daily logarithmic/arithmetic return sequences                            │
│ • Volatility scaling (sqrt(252)) & downside semi-variance                  │
│ • Historical linear interpolation Value-at-Risk (VaR 95%) & CVaR (Expected Shortfall) │
│ • Aligned benchmark covariance, beta regression, tracking error & alpha     │
│ • Pairwise Pearson correlation matrices                                     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Pre-computed in analytical views
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. DYNAMIC FILTER-CONTEXT & AGGREGATION LAYER (Power BI / DAX)              │
│ • Context-sensitive scorecard selection (SELECTEDVALUE / LASTNONBLANKVALUE) │
│ • Slicer-driven market value & invested capital rollups                    │
│ • Dynamic portfolio & sector weights under user slicer selections          │
│ • Visual formatting ($ / %, currency locale switches)                     │
│ • Time Intelligence (MTD, QTD, YTD) based on DimDate                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Valuation & Capital Scorecards

### `[Portfolio Value]`
Returns the latest total portfolio equity plus cash value within the current filter context.
```dax
Portfolio Value = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_performance[snapshot_date],
            SUM(vw_fact_portfolio_performance[total_value])
        ),
        vw_fact_portfolio_performance[snapshot_date] <= _LastDate
    )
```
- **Format**: Currency (`$#,##0.00` or `₹#,##0.00`)
- **Type**: Decimal

### `[Invested Capital]`
Sum of total cost basis across active holdings in the current portfolio context.
```dax
Invested Capital = 
SUM(vw_fact_portfolio_holdings[cost_basis])
```
- **Format**: Currency (`$#,##0.00`)
- **Type**: Decimal

### `[Available Cash]`
Current uninvested cash balance in the portfolio container.
```dax
Available Cash = 
SELECTEDVALUE(vw_dim_portfolios[available_cash], 0)
```
- **Format**: Currency (`$#,##0.00`)
- **Type**: Decimal

### `[Initial Capital]`
Initial cash balance allocated at portfolio inception.
```dax
Initial Capital = 
SELECTEDVALUE(vw_dim_portfolios[initial_cash], 0)
```
- **Format**: Currency (`$#,##0.00`)
- **Type**: Decimal

### `[Absolute P&L]`
Dollar gain or loss computed as current total valuation minus initial capital baseline.
```dax
Absolute P&L = 
VAR _CurrentVal = [Portfolio Value]
VAR _InitCash = [Initial Capital]
RETURN
    IF(ISBLANK(_CurrentVal), BLANK(), _CurrentVal - _InitCash)
```
- **Format**: `+$#,##0.00;-$#,##0.00;$#,##0.00`
- **Type**: Decimal

### `[Percentage P&L]`
Percentage return on initial capital.
```dax
Percentage P&L = 
DIVIDE([Absolute P&L], [Initial Capital], BLANK())
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

---

## 2. Return & Benchmark Performance Measures

### `[Portfolio Return]`
Total cumulative portfolio return from inception to the selected date.
```dax
Portfolio Return = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_performance[snapshot_date],
            SELECTEDVALUE(vw_fact_portfolio_performance[cumulative_return_pct])
        ),
        vw_fact_portfolio_performance[snapshot_date] <= _LastDate
    )
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

### `[Benchmark Return]`
Total cumulative benchmark return over the aligned trading history.
```dax
Benchmark Return = 
VAR _FirstBench = 
    CALCULATE(
        FIRSTNONBLANKVALUE(
            vw_fact_portfolio_performance[snapshot_date],
            SELECTEDVALUE(vw_fact_portfolio_performance[benchmark_value])
        ),
        ALLSELECTED(vw_dim_date)
    )
VAR _LastBench = 
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_performance[snapshot_date],
            SELECTEDVALUE(vw_fact_portfolio_performance[benchmark_value])
        ),
        ALLSELECTED(vw_dim_date)
    )
RETURN
    IF(
        NOT ISBLANK(_FirstBench) && _FirstBench > 0,
        DIVIDE(_LastBench - _FirstBench, _FirstBench, BLANK()),
        BLANK()
    )
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

### `[Active Return]`
Active return spread (alpha spread) of the portfolio relative to the benchmark index.
```dax
Active Return = 
VAR _PortRet = [Portfolio Return]
VAR _BenchRet = [Benchmark Return]
RETURN
    IF(NOT ISBLANK(_PortRet) && NOT ISBLANK(_BenchRet), _PortRet - _BenchRet, BLANK())
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

### `[Annualized Return (CAGR)]`
Deterministic geometric compound annual growth rate retrieved from the risk scorecard.
```dax
Annualized Return (CAGR) = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[annualized_return])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

---

## 3. Quantitative Risk Measures

> [!NOTE]
> All quantitative risk parameters are deterministically computed in Python using 252-day business annualization and stored in `vw_fact_portfolio_risk_metrics`. DAX extracts these metrics dynamically based on the current portfolio and as-of date filter context.

### `[Annualized Volatility]`
Annualized standard deviation of daily logarithmic returns ($\sigma \times \sqrt{252}$).
```dax
Annualized Volatility = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[annualized_volatility])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Sharpe Ratio]`
Excess annualized return over the risk-free rate per unit of annualized volatility.
```dax
Sharpe Ratio = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[sharpe_ratio])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00`
- **Type**: Decimal

### `[Sortino Ratio]`
Excess return per unit of downside semi-deviation.
```dax
Sortino Ratio = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[sortino_ratio])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00`
- **Type**: Decimal

### `[Maximum Drawdown]`
Worst observed peak-to-trough decline over the portfolio history.
```dax
Maximum Drawdown = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[max_drawdown])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Max Drawdown Days]`
Duration in business days from peak equity to lowest trough.
```dax
Max Drawdown Days = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[max_drawdown_days])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `#,##0 "days"`
- **Type**: Integer

### `[Historical VaR 95%]`
Historical Value-at-Risk at 95% confidence over a 1-day horizon.
```dax
Historical VaR 95% = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[var_95_daily])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Historical CVaR 95%]`
Expected Shortfall (mean loss beyond 95% VaR threshold).
```dax
Historical CVaR 95% = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[cvar_95_daily])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

---

## 4. Benchmark Sensitivity Measures

### `[Beta]`
Sensitivity of portfolio returns relative to benchmark index movements.
```dax
Beta = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[beta])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `0.00`
- **Type**: Decimal

### `[Jensen's Alpha]`
Annualized excess return generated over CAPM expected return.
```dax
Jensen's Alpha = 
VAR _LastDate = MAX(vw_dim_date[date])
RETURN
    CALCULATE(
        LASTNONBLANKVALUE(
            vw_fact_portfolio_risk_metrics[as_of_date],
            SELECTEDVALUE(vw_fact_portfolio_risk_metrics[alpha])
        ),
        vw_fact_portfolio_risk_metrics[as_of_date] <= _LastDate
    )
```
- **Format**: `+0.00%;-0.00%;0.00%`
- **Type**: Percentage

---

## 5. Asset Allocation & Exposure Measures

### `[Holding Market Value]`
Sum of current position market values.
```dax
Holding Market Value = 
SUM(vw_fact_portfolio_holdings[market_value])
```
- **Format**: Currency (`$#,##0.00`)
- **Type**: Decimal

### `[Total Portfolio Market Value]`
All-positions market value ignoring asset filters, useful for calculating dynamic weights.
```dax
Total Portfolio Market Value = 
CALCULATE(
    SUM(vw_fact_portfolio_holdings[market_value]),
    ALL(vw_dim_assets)
)
```
- **Format**: Currency (`$#,##0.00`)
- **Type**: Decimal

### `[Portfolio Weight %]`
Dynamic weight of selected asset or position relative to the overall portfolio.
```dax
Portfolio Weight % = 
DIVIDE([Holding Market Value], [Total Portfolio Market Value], 0)
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Sector Weight %]`
Dynamic weight of selected industry sector relative to the overall portfolio.
```dax
Sector Weight % = 
DIVIDE(
    SUM(vw_fact_portfolio_holdings[market_value]),
    CALCULATE(SUM(vw_fact_portfolio_holdings[market_value]), ALL(vw_dim_assets[sector])),
    0
)
```
- **Format**: `0.00%`
- **Type**: Percentage

---

## 6. Concentration Analytics

### `[HHI (Concentration)]`
Herfindahl-Hirschman Index computed dynamically across holding weights:
$$\text{HHI} = \sum_{i=1}^n w_i^2$$
```dax
HHI (Concentration) = 
VAR _TotalVal = [Total Portfolio Market Value]
RETURN
    IF(
        _TotalVal > 0,
        SUMX(
            vw_fact_portfolio_holdings,
            VAR _Weight = DIVIDE(vw_fact_portfolio_holdings[market_value], _TotalVal, 0)
            RETURN _Weight * _Weight
        ),
        0
    )
```
- **Format**: `0.0000`
- **Type**: Decimal

### `[Largest Holding Weight]`
Weight of the single largest holding in the portfolio.
```dax
Largest Holding Weight = 
MAXX(
    ALL(vw_dim_assets[ticker]),
    [Portfolio Weight %]
)
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Top 3 Concentration]`
Combined weight of the top 3 holdings.
```dax
Top 3 Concentration = 
VAR _Top3 = 
    TOPN(
        3,
        ALL(vw_dim_assets[ticker]),
        [Holding Market Value],
        DESC
    )
RETURN
    CALCULATE(
        [Portfolio Weight %],
        KEEPFILTERS(_Top3)
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

### `[Top 5 Concentration]`
Combined weight of the top 5 holdings.
```dax
Top 5 Concentration = 
VAR _Top5 = 
    TOPN(
        5,
        ALL(vw_dim_assets[ticker]),
        [Holding Market Value],
        DESC
    )
RETURN
    CALCULATE(
        [Portfolio Weight %],
        KEEPFILTERS(_Top5)
    )
```
- **Format**: `0.00%`
- **Type**: Percentage

---

## 7. Time Intelligence Measures

### `[Portfolio Value MTD]`
Month-to-date portfolio valuation progression.
```dax
Portfolio Value MTD = 
TOTALMTD([Portfolio Value], vw_dim_date[date])
```

### `[Portfolio Value QTD]`
Quarter-to-date portfolio valuation progression.
```dax
Portfolio Value QTD = 
TOTALQTD([Portfolio Value], vw_dim_date[date])
```

### `[Portfolio Value YTD]`
Year-to-date portfolio valuation progression.
```dax
Portfolio Value YTD = 
TOTALYTD([Portfolio Value], vw_dim_date[date])
```
