"use client";

import React from "react";
import { PortfolioBenchmark } from "@/lib/types";
import { formatPercent, formatRatio } from "@/lib/formatters";
import { Landmark, ArrowUpRight, ArrowDownRight, Scale } from "lucide-react";

interface BenchmarkComparisonProps {
  benchmark: PortfolioBenchmark;
}

export function BenchmarkComparison({ benchmark }: BenchmarkComparisonProps) {
  const symbol = benchmark?.benchmark_symbol || "N/A";
  const pReturn = benchmark?.portfolio_cumulative_return;
  const bReturn = benchmark?.benchmark_cumulative_return;
  const activeReturn = benchmark?.active_return;

  const isActivePos = activeReturn !== null && activeReturn !== undefined && activeReturn >= 0;

  const metrics = [
    {
      label: "Portfolio Return (Cum)",
      value: formatPercent(pReturn, 2, true),
      subtext: "Total portfolio gain/loss",
    },
    {
      label: `Benchmark Return (${symbol})`,
      value: formatPercent(bReturn, 2, true),
      subtext: "Index tracking baseline",
    },
    {
      label: "Active Return Spread",
      value: formatPercent(activeReturn, 2, true),
      subtext: "Excess return over index",
      highlight: isActivePos ? "text-emerald-400" : "text-rose-400",
    },
    {
      label: "Beta (β)",
      value: formatRatio(benchmark.beta, 2),
      subtext: "Sensitivity to benchmark",
    },
    {
      label: "Jensen's Alpha (α)",
      value: formatPercent(benchmark.jensens_alpha, 2, true),
      subtext: "Annualized CAPM alpha",
      highlight:
        benchmark.jensens_alpha !== null && benchmark.jensens_alpha >= 0
          ? "text-emerald-400"
          : "text-rose-400",
    },
    {
      label: "Correlation (ρ)",
      value: formatRatio(benchmark.correlation, 3),
      subtext: "Co-movement coefficient",
    },
    {
      label: "Covariance",
      value: formatRatio(benchmark.covariance, 6),
      subtext: "Joint variance of returns",
    },
    {
      label: "Tracking Error",
      value: formatPercent(benchmark.tracking_error, 2),
      subtext: "Standard deviation of active return",
    },
    {
      label: "Information Ratio",
      value: formatRatio(benchmark.information_ratio, 2),
      subtext: "Active return per tracking error",
    },
  ];

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-slate-100">
            Benchmark Comparative Analytics
          </h2>
        </div>
        <span className="text-xs px-2.5 py-1 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50 font-mono">
          Benchmark: {symbol}
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-6 max-w-3xl">
        Relative performance, sensitivity, and risk-adjusted metrics evaluated against benchmark index returns over the aligned trading window.
      </p>

      {/* Grid of benchmark statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-4">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-3.5 flex flex-col justify-between"
          >
            <div>
              <div className="text-xs text-slate-400 font-medium mb-1 truncate" title={m.label}>
                {m.label}
              </div>
              <div
                className={`text-lg md:text-xl font-bold font-mono tracking-tight ${
                  m.highlight || "text-slate-100"
                }`}
              >
                {m.value}
              </div>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 font-mono">{m.subtext}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
