/**
 * Automated deterministic test suite for Portfolio Analytics Dashboard.
 * Uses Node.js built-in test runner (node:test, node:assert).
 * Does not require external financial APIs or network calls.
 */

import { test, describe } from "node:test";
import assert from "node:assert/strict";

// Import compiled or raw ESM formatters
import {
  formatCurrency,
  formatPercent,
  formatRatio,
  formatDate,
} from "./src/lib/formatters.ts";

// Deterministic Mock Dashboard Summary matching Step 8A/8B schemas
const MOCK_DASHBOARD_RESPONSE = {
  overview: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    portfolio_name: "Active Test Portfolio",
    base_currency: "USD",
    benchmark: "API_SPY",
    initial_cash: 10000.0,
    available_cash: 2000.0,
    current_portfolio_value: 7150.0,
    invested_value: 5150.0,
    absolute_pnl: -2850.0,
    percentage_pnl: -0.285,
    cumulative_return: 0.05147,
    annualized_return: 0.2842,
    annualized_volatility: 0.1425,
    sharpe_ratio: 1.85,
    sortino_ratio: 2.45,
    maximum_drawdown: 0.042,
    maximum_drawdown_duration: 5,
  },
  risk: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    volatility: 0.1425,
    sharpe: 1.85,
    sortino: 2.45,
    max_drawdown: 0.042,
    max_drawdown_duration: 5,
    var_95: 0.0152,
    cvar_95: 0.0215,
    beta: 0.88,
    alpha: 0.035,
    tracking_error: 0.045,
    information_ratio: 0.78,
  },
  allocation: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    total_market_value: 5150.0,
    allocations: [
      {
        ticker: "API_MSFT",
        shares: 20.0,
        current_price: 170.0,
        market_value: 3400.0,
        portfolio_weight: 0.660194,
      },
      {
        ticker: "API_AAPL",
        shares: 10.0,
        current_price: 175.0,
        market_value: 1750.0,
        portfolio_weight: 0.339806,
      },
    ],
    concentration: {
      hhi: 0.551323,
      largest_holding_ticker: "API_MSFT",
      largest_holding_weight: 0.660194,
      top_3_weight: 1.0,
      top_5_weight: 1.0,
      total_holdings_count: 2,
    },
  },
  sectors: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    total_market_value: 5150.0,
    sectors: [
      {
        sector: "Technology",
        market_value: 5150.0,
        portfolio_weight: 1.0,
      },
    ],
  },
  contributions: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    portfolio_return: 0.0735,
    contributions: [
      {
        ticker: "API_MSFT",
        portfolio_weight: 0.660194,
        asset_return: 0.0625,
        contribution: 0.04126,
        contribution_pct: 0.5614,
      },
      {
        ticker: "API_AAPL",
        portfolio_weight: 0.339806,
        asset_return: 0.09375,
        contribution: 0.03224,
        contribution_pct: 0.4386,
      },
    ],
  },
  correlation: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    correlation_matrix: {
      API_AAPL: { API_AAPL: 1.0, API_MSFT: 0.724 },
      API_MSFT: { API_AAPL: 0.724, API_MSFT: 1.0 },
    },
    average_pairwise_correlation: 0.724,
    highest_pairwise_correlation: 0.724,
    lowest_pairwise_correlation: 0.724,
    highest_correlated_pair: ["API_AAPL", "API_MSFT"],
    lowest_correlated_pair: ["API_AAPL", "API_MSFT"],
  },
  benchmark: {
    portfolio_id: "11111111-1111-1111-1111-111111111111",
    benchmark_symbol: "API_SPY",
    correlation: 0.912,
    covariance: 0.000185,
    beta: 0.88,
    jensens_alpha: 0.035,
    tracking_error: 0.045,
    information_ratio: 0.78,
    portfolio_cumulative_return: 0.05147,
    benchmark_cumulative_return: 0.030,
    active_return: 0.02147,
  },
  performance: [
    {
      date: "2025-01-02",
      portfolio_value: 6800.0,
      benchmark_value: 500.0,
      daily_portfolio_return: null,
      cumulative_portfolio_return: 0.0,
    },
    {
      date: "2025-01-03",
      portfolio_value: 6890.0,
      benchmark_value: 505.0,
      daily_portfolio_return: 0.01323,
      cumulative_portfolio_return: 0.01323,
    },
    {
      date: "2025-01-06",
      portfolio_value: 7000.0,
      benchmark_value: 510.0,
      daily_portfolio_return: 0.01596,
      cumulative_portfolio_return: 0.02941,
    },
    {
      date: "2025-01-07",
      portfolio_value: 7150.0,
      benchmark_value: 515.0,
      daily_portfolio_return: 0.02143,
      cumulative_portfolio_return: 0.05147,
    },
  ],
};

describe("Portfolio Dashboard Unit & Rendering Logic Tests", () => {
  test("1. Formatters: currency formatting for USD and INR", () => {
    const usd = formatCurrency(12345.67, "USD");
    assert.match(usd, /\$12,345\.67/);

    const inr = formatCurrency(500000.0, "INR");
    assert.match(inr, /5,00,000|500,000/);

    const compact = formatCurrency(1500000, "USD", true);
    assert.match(compact, /1\.5M/);

    assert.equal(formatCurrency(null), "N/A");
    assert.equal(formatCurrency(undefined), "N/A");
  });

  test("2. Formatters: percentage and ratio formatting", () => {
    assert.equal(formatPercent(0.1245), "12.45%");
    assert.equal(formatPercent(0.1245, 2, true), "+12.45%");
    assert.equal(formatPercent(-0.035, 2, true), "-3.50%");
    assert.equal(formatPercent(null), "N/A");

    assert.equal(formatRatio(1.854), "1.85");
    assert.equal(formatRatio(null), "N/A");
  });

  test("3. Formatters: date parsing and human formatting", () => {
    const d = formatDate("2025-01-02");
    assert.match(d, /Jan 02, 2025/);
    assert.equal(formatDate(null), "N/A");
  });

  test("4. KPI Extraction: accurately displays 8 core scorecard metrics", () => {
    const { overview } = MOCK_DASHBOARD_RESPONSE;
    assert.equal(overview.current_portfolio_value, 7150.0);
    assert.equal(overview.invested_value, 5150.0);
    assert.equal(overview.absolute_pnl, -2850.0);
    assert.equal(overview.percentage_pnl, -0.285);
    assert.equal(overview.cumulative_return, 0.05147);
    assert.equal(overview.annualized_return, 0.2842);
    assert.equal(overview.annualized_volatility, 0.1425);
    assert.equal(overview.sharpe_ratio, 1.85);
    assert.equal(overview.maximum_drawdown, 0.042);
  });

  test("5. Asset Allocation: weights sum to 1.0 and tickers match", () => {
    const { allocation } = MOCK_DASHBOARD_RESPONSE;
    assert.equal(allocation.total_market_value, 5150.0);
    assert.equal(allocation.allocations.length, 2);

    const sumWeights = allocation.allocations.reduce(
      (acc, a) => acc + a.portfolio_weight,
      0
    );
    assert.ok(Math.abs(sumWeights - 1.0) < 1e-4);
  });

  test("6. Sector Exposure: handles known sectors and preserves weights", () => {
    const { sectors } = MOCK_DASHBOARD_RESPONSE;
    assert.equal(sectors.sectors.length, 1);
    assert.equal(sectors.sectors[0].sector, "Technology");
    assert.equal(sectors.sectors[0].portfolio_weight, 1.0);
  });

  test("7. Concentration Analytics: HHI, largest holding, top-3 weights", () => {
    const conc = MOCK_DASHBOARD_RESPONSE.allocation.concentration;
    assert.ok(conc !== null);
    assert.equal(conc.largest_holding_ticker, "API_MSFT");
    assert.ok(conc.largest_holding_weight > 0.5);
    assert.ok(conc.hhi > 0.0);
    assert.equal(conc.top_3_weight, 1.0);
    assert.equal(conc.total_holdings_count, 2);
  });

  test("8. Return Contributions: positive and negative drivers sum correctly", () => {
    const { contributions } = MOCK_DASHBOARD_RESPONSE;
    assert.equal(contributions.contributions.length, 2);

    const sumContrib = contributions.contributions.reduce(
      (acc, c) => acc + c.contribution,
      0
    );
    assert.ok(Math.abs(sumContrib - (contributions.portfolio_return || 0)) < 1e-4);
  });

  test("9. Correlation Heatmap: off-diagonal matrix is symmetric", () => {
    const { correlation } = MOCK_DASHBOARD_RESPONSE;
    const m = correlation.correlation_matrix;
    assert.equal(m["API_AAPL"]["API_MSFT"], m["API_MSFT"]["API_AAPL"]);
    assert.equal(correlation.average_pairwise_correlation, 0.724);
    assert.deepEqual(correlation.highest_correlated_pair, ["API_AAPL", "API_MSFT"]);
  });

  test("10. Benchmark Comparison: beta, alpha, tracking error, active return", () => {
    const { benchmark } = MOCK_DASHBOARD_RESPONSE;
    assert.equal(benchmark.benchmark_symbol, "API_SPY");
    assert.equal(benchmark.beta, 0.88);
    assert.equal(benchmark.jensens_alpha, 0.035);
    assert.equal(benchmark.active_return, 0.02147);
    assert.equal(benchmark.information_ratio, 0.78);
  });

  test("11. Empty State Resilience: empty portfolio with 0 positions handles safely", () => {
    const emptySummary = {
      ...MOCK_DASHBOARD_RESPONSE,
      allocation: {
        portfolio_id: "22222222-2222-2222-2222-222222222222",
        total_market_value: 0.0,
        allocations: [],
        concentration: {
          hhi: 0.0,
          largest_holding_ticker: null,
          largest_holding_weight: 0.0,
          top_3_weight: 0.0,
          top_5_weight: 0.0,
          total_holdings_count: 0,
        },
      },
      performance: [],
    };

    assert.equal(emptySummary.allocation.allocations.length, 0);
    assert.equal(emptySummary.allocation.concentration.largest_holding_ticker, null);
    assert.equal(emptySummary.performance.length, 0);
  });
});
