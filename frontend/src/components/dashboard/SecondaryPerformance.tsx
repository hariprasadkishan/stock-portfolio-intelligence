"use client";

import React from "react";
import { PortfolioBenchmark } from "@/lib/types";
import { formatPercent } from "@/lib/formatters";
import { Layers, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface SecondaryPerformanceProps {
  benchmark: PortfolioBenchmark;
}

export function SecondaryPerformance({ benchmark }: SecondaryPerformanceProps) {
  const pReturn = benchmark.portfolio_cumulative_return;
  const bReturn = benchmark.benchmark_cumulative_return;
  const activeReturn = benchmark.active_return;

  const isActivePositive = activeReturn !== null && activeReturn > 0;
  const isActiveNegative = activeReturn !== null && activeReturn < 0;

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Layers className="w-5 h-5 text-purple-400" />
        <h3 className="text-base font-semibold text-slate-100">
          Cumulative Return Distribution
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Portfolio Cumulative Return */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Portfolio Cumulative Return
          </div>
          <div className="text-xl font-bold font-mono text-slate-100">
            {formatPercent(pReturn, 2, true)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Total historical return</div>
        </div>

        {/* Benchmark Cumulative Return */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Benchmark Return ({benchmark.benchmark_symbol || "N/A"})
          </div>
          <div className="text-xl font-bold font-mono text-slate-100">
            {formatPercent(bReturn, 2, true)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Benchmark baseline return</div>
        </div>

        {/* Active Return (Alpha Spread) */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Active Return Spread</span>
            {isActivePositive ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            ) : isActiveNegative ? (
              <ArrowDownRight className="w-4 h-4 text-rose-400" />
            ) : (
              <Minus className="w-4 h-4 text-slate-400" />
            )}
          </div>
          <div
            className={`text-xl font-bold font-mono ${
              isActivePositive
                ? "text-emerald-400"
                : isActiveNegative
                ? "text-rose-400"
                : "text-slate-100"
            }`}
          >
            {formatPercent(activeReturn, 2, true)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Excess over benchmark</div>
        </div>
      </div>
    </div>
  );
}
