"use client";

import React from "react";
import { PortfolioRisk } from "@/lib/types";
import { formatPercent, formatRatio } from "@/lib/formatters";
import { Shield, HelpCircle } from "lucide-react";

interface RiskAnalyticsProps {
  risk: PortfolioRisk;
}

interface MetricItem {
  id: string;
  name: string;
  value: string;
  definition: string;
  category: "Tail Risk" | "Volatility & Drawdown" | "Risk-Adjusted" | "Benchmark Sensitivity";
}

export function RiskAnalytics({ risk }: RiskAnalyticsProps) {
  const metrics: MetricItem[] = [
    {
      id: "volatility",
      name: "Annualized Volatility",
      value: formatPercent(risk.volatility, 2),
      definition: "Annualized standard deviation of daily logarithmic returns (scaled by sqrt(252)).",
      category: "Volatility & Drawdown",
    },
    {
      id: "sharpe",
      name: "Sharpe Ratio",
      value: formatRatio(risk.sharpe, 2),
      definition: "Ratio of annualized excess portfolio return over the risk-free rate to annualized volatility.",
      category: "Risk-Adjusted",
    },
    {
      id: "sortino",
      name: "Sortino Ratio",
      value: formatRatio(risk.sortino, 2),
      definition: "Ratio of excess portfolio return to downside standard deviation (penalizing only negative volatility).",
      category: "Risk-Adjusted",
    },
    {
      id: "mdd",
      name: "Maximum Drawdown",
      value: formatPercent(risk.max_drawdown, 2),
      definition: "Greatest peak-to-trough equity decline observed over the valuation history.",
      category: "Volatility & Drawdown",
    },
    {
      id: "mdd_duration",
      name: "Max Drawdown Duration",
      value: `${risk.max_drawdown_duration} trading days`,
      definition: "Duration in business days from peak valuation to reaching the lowest trough.",
      category: "Volatility & Drawdown",
    },
    {
      id: "var_95",
      name: "Historical VaR (95%)",
      value: formatPercent(risk.var_95, 2),
      definition: "Historical estimate of the loss threshold at the 95% confidence level over a 1-day horizon.",
      category: "Tail Risk",
    },
    {
      id: "cvar_95",
      name: "Historical CVaR (95%)",
      value: formatPercent(risk.cvar_95, 2),
      definition: "Expected Shortfall: average loss incurred given that losses exceed the 95% VaR threshold.",
      category: "Tail Risk",
    },
    {
      id: "beta",
      name: "Portfolio Beta",
      value: formatRatio(risk.beta, 2),
      definition: "Measures sensitivity of portfolio returns relative to benchmark return swings (Cov(Rp, Rb) / Var(Rb)).",
      category: "Benchmark Sensitivity",
    },
    {
      id: "alpha",
      name: "Jensen's Alpha",
      value: formatPercent(risk.alpha, 2, true),
      definition: "Annualized excess return generated above the Capital Asset Pricing Model (CAPM) expected return.",
      category: "Benchmark Sensitivity",
    },
    {
      id: "tracking_error",
      name: "Tracking Error",
      value: formatPercent(risk.tracking_error, 2),
      definition: "Annualized standard deviation of active return differentials between portfolio and benchmark.",
      category: "Benchmark Sensitivity",
    },
    {
      id: "information_ratio",
      name: "Information Ratio",
      value: formatRatio(risk.information_ratio, 2),
      definition: "Mean active return divided by tracking error, measuring consistency of outperformance.",
      category: "Benchmark Sensitivity",
    },
  ];

  return (
    <section aria-labelledby="risk-analytics-heading" className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-indigo-400" />
          <h2 id="risk-analytics-heading" className="text-lg font-semibold text-slate-100">
            Quantitative Risk Analytics
          </h2>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Deterministic Formulations
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-6 max-w-3xl">
        Statistical risk metrics computed across chronological daily returns. Tooltips provide theoretical definitions without prescriptive or subjective investment ratings.
      </p>

      {/* Grid of 11 risk metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {metrics.map((item) => (
          <div
            key={item.id}
            className="bg-[#0B0F17] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-lg p-3.5 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-xs text-slate-400 font-medium truncate" title={item.name}>
                  {item.name}
                </span>
                <div className="group relative cursor-help">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 transition-colors shrink-0" />
                  <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block w-56 p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-[11px] text-slate-200 shadow-xl z-20 pointer-events-none">
                    <p className="font-semibold text-slate-100 mb-0.5">{item.name}</p>
                    <p className="text-slate-300">{item.definition}</p>
                  </div>
                </div>
              </div>

              <div className="text-lg md:text-xl font-bold font-mono text-slate-100">
                {item.value}
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-[#1F2937]/60 flex items-center justify-between text-[10px] text-slate-500">
              <span>{item.category}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
