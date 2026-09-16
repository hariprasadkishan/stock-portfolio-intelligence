"use client";

import React from "react";
import { ConcentrationItem, PortfolioAllocation } from "@/lib/types";
import { formatPercent, formatRatio } from "@/lib/formatters";
import { Target, PieChart, Layers } from "lucide-react";

interface ConcentrationSectionProps {
  allocation: PortfolioAllocation;
}

export function ConcentrationSection({ allocation }: ConcentrationSectionProps) {
  const conc = allocation?.concentration;

  // Gracefully fallback to allocation list if concentration object is absent
  let hhi = conc?.hhi ?? 0.0;
  let largestTicker = conc?.largest_holding_ticker ?? null;
  let largestWeight = conc?.largest_holding_weight ?? 0.0;
  let top3 = conc?.top_3_weight ?? 0.0;
  let top5 = conc?.top_5_weight ?? 0.0;
  let count = conc?.total_holdings_count ?? (allocation?.allocations?.length || 0);

  if (!conc && allocation?.allocations && allocation.allocations.length > 0) {
    const sorted = [...allocation.allocations].sort(
      (a, b) => b.portfolio_weight - a.portfolio_weight
    );
    count = sorted.length;
    largestTicker = sorted[0]?.ticker || null;
    largestWeight = sorted[0]?.portfolio_weight || 0.0;
    top3 = sorted.slice(0, 3).reduce((acc, curr) => acc + curr.portfolio_weight, 0);
    top5 = sorted.slice(0, 5).reduce((acc, curr) => acc + curr.portfolio_weight, 0);
    hhi = sorted.reduce((acc, curr) => acc + Math.pow(curr.portfolio_weight, 2), 0);
  }

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-semibold text-slate-100">
            Portfolio Concentration Analytics
          </h2>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Total Positions: {count}
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-6 max-w-3xl">
        Objective mathematical concentration measures. Herfindahl-Hirschman Index (HHI = Σ w_i²) quantifies capital concentration across active holdings.
      </p>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* HHI Score */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Herfindahl Index (HHI)
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100">
            {formatRatio(hhi, 4)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Σ (weights)² (range: 1/N to 1.0)</div>
        </div>

        {/* Largest Single Holding */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Largest Position
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl md:text-2xl font-bold font-mono text-slate-100">
              {largestTicker || "None"}
            </span>
            <span className="text-sm font-semibold font-mono text-blue-400">
              {formatPercent(largestWeight, 2)}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Single largest portfolio weight</div>
        </div>

        {/* Top 3 Concentration */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Top 3 Holdings Concentration
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100">
            {formatPercent(top3, 2)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Combined weight of top 3 assets</div>
        </div>

        {/* Top 5 Concentration */}
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-4">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Top 5 Holdings Concentration
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100">
            {formatPercent(top5, 2)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Combined weight of top 5 assets</div>
        </div>
      </div>
    </div>
  );
}
