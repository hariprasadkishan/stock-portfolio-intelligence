"use client";

import React from "react";
import { PortfolioOverview } from "@/lib/types";
import { formatCurrency, formatPercent, formatRatio } from "@/lib/formatters";
import { TrendingUp, TrendingDown, DollarSign, ShieldAlert, BarChart3, Activity } from "lucide-react";

interface KPIGridProps {
  overview: PortfolioOverview;
}

export function KPIGrid({ overview }: KPIGridProps) {
  const curr = overview.base_currency || "USD";
  const isPnlPositive = overview.absolute_pnl >= 0;

  return (
    <section aria-labelledby="kpi-scorecard-heading">
      <h2 id="kpi-scorecard-heading" className="sr-only">
        Portfolio Executive Scorecard
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* 1. Current Portfolio Value */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Portfolio Value</span>
            <DollarSign className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatCurrency(overview.current_portfolio_value, curr)}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1 font-mono">
            Cash: {formatCurrency(overview.available_cash, curr, true)}
          </div>
        </div>

        {/* 2. Invested Value */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Invested Capital</span>
            <Activity className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatCurrency(overview.invested_value, curr)}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-mono">
            Initial: {formatCurrency(overview.initial_cash, curr, true)}
          </div>
        </div>

        {/* 3. Total P&L */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Profit & Loss</span>
            {isPnlPositive ? (
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            )}
          </div>
          <div
            className={`text-xl md:text-2xl font-bold font-mono tracking-tight ${
              isPnlPositive ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {isPnlPositive ? "+" : ""}
            {formatCurrency(overview.absolute_pnl, curr)}
          </div>
          <div className="text-xs font-mono mt-1">
            <span
              className={`inline-flex items-center px-1.5 py-0.2 rounded text-[11px] font-semibold ${
                isPnlPositive
                  ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/40"
                  : "bg-rose-950/60 text-rose-400 border border-rose-800/40"
              }`}
            >
              {formatPercent(overview.percentage_pnl, 2, true)}
            </span>
          </div>
        </div>

        {/* 4. Portfolio Return (Cumulative) */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Cumulative Return</span>
            <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatPercent(overview.cumulative_return, 2, true)}
          </div>
          <div className="text-xs text-slate-400 mt-1">Total valuation change</div>
        </div>

        {/* 5. CAGR (Annualized Return) */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>CAGR (Annualized)</span>
            <Activity className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatPercent(overview.annualized_return, 2, true)}
          </div>
          <div className="text-xs text-slate-400 mt-1">Geometric annual return</div>
        </div>

        {/* 6. Volatility (Annualized) */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Annual Volatility</span>
            <Activity className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatPercent(overview.annualized_volatility, 2)}
          </div>
          <div className="text-xs text-slate-400 mt-1">Annualized std deviation</div>
        </div>

        {/* 7. Sharpe Ratio */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Sharpe Ratio</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-slate-100 tracking-tight">
            {formatRatio(overview.sharpe_ratio, 2)}
          </div>
          <div className="text-xs text-slate-400 mt-1">Excess return / Volatility</div>
        </div>

        {/* 8. Maximum Drawdown */}
        <div className="bg-[#111827] border border-[#1F2937] hover:border-slate-700 transition-colors rounded-xl p-4 md:p-5 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Max Drawdown</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-xl md:text-2xl font-bold font-mono text-rose-400 tracking-tight">
            {formatPercent(overview.maximum_drawdown, 2)}
          </div>
          <div className="text-xs text-slate-400 mt-1 font-mono">
            {overview.maximum_drawdown_duration} trading days peak-to-trough
          </div>
        </div>
      </div>
    </section>
  );
}
