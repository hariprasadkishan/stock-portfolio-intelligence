"use client";

import React from "react";
import { PortfolioContributions } from "@/lib/types";
import { formatPercent, formatRatio } from "@/lib/formatters";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import { GitCommit, TrendingUp, TrendingDown } from "lucide-react";

interface ReturnContributionProps {
  contributions: PortfolioContributions;
}

export function ReturnContribution({ contributions }: ReturnContributionProps) {
  const items = contributions?.contributions || [];

  if (items.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 text-center text-slate-400">
        No return contribution data available.
      </div>
    );
  }

  const chartData = items.map((c) => ({
    ticker: c.ticker,
    contribution: c.contribution * 100, // percentage points
    assetReturn: c.asset_return * 100,
    weight: c.portfolio_weight * 100,
    contributionPct: c.contribution_pct,
  }));

  const pReturn = contributions.portfolio_return;
  const isTotalPositive = pReturn !== null && pReturn >= 0;

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-slate-100">
              Return Contribution Breakdown
            </h2>
          </div>
          {pReturn !== null && (
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <span className="text-slate-400">Total Return:</span>
              <span
                className={`font-semibold px-2 py-0.5 rounded ${
                  isTotalPositive
                    ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/50"
                    : "bg-rose-950/60 text-rose-400 border border-rose-800/50"
                }`}
              >
                {formatPercent(pReturn, 2, true)}
              </span>
            </div>
          )}
        </div>

        <p className="text-xs text-slate-400 mb-6">
          Weighted contribution of each holding to total portfolio returns (w_i × R_i). Diverging bars distinguish positive drivers from performance drags.
        </p>

        {/* Diverging Bar Chart */}
        <div className="h-64 w-full mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" horizontal={false} />
              <XAxis
                type="number"
                stroke="#64748B"
                fontSize={11}
                tickFormatter={(v) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`}
              />
              <YAxis
                type="category"
                dataKey="ticker"
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0B0F17",
                  borderColor: "#374151",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#E2E8F0",
                }}
                formatter={(value: any, name: string) => [
                  `${Number(value) > 0 ? "+" : ""}${Number(value).toFixed(2)}%`,
                  "Contribution",
                ]}
              />
              <ReferenceLine x={0} stroke="#475569" strokeWidth={1.5} />
              <Bar dataKey="contribution" radius={[2, 2, 2, 2]}>
                {chartData.map((entry) => (
                  <Cell
                    key={`cell-${entry.ticker}`}
                    fill={entry.contribution >= 0 ? "#10B981" : "#F43F5E"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabular exact details */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-[#0B0F17] text-slate-400 uppercase font-mono text-[10px] border-y border-[#1F2937]">
            <tr>
              <th scope="col" className="py-2 px-3">Ticker</th>
              <th scope="col" className="py-2 px-3 text-right">Asset Return</th>
              <th scope="col" className="py-2 px-3 text-right">Weight</th>
              <th scope="col" className="py-2 px-3 text-right">Contribution</th>
              <th scope="col" className="py-2 px-3 text-right">Share of P&L</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1F2937]/50 font-mono">
            {items.map((c) => {
              const isPos = c.contribution >= 0;
              const isRetPos = c.asset_return >= 0;
              return (
                <tr key={c.ticker} className="hover:bg-[#1F2937]/30 transition-colors">
                  <td className="py-2 px-3 font-semibold text-slate-100 flex items-center gap-1.5">
                    {isPos ? (
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
                    )}
                    {c.ticker}
                  </td>
                  <td
                    className={`py-2 px-3 text-right font-medium ${
                      isRetPos ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {formatPercent(c.asset_return, 2, true)}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-300">
                    {formatPercent(c.portfolio_weight, 2)}
                  </td>
                  <td
                    className={`py-2 px-3 text-right font-semibold ${
                      isPos ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {formatPercent(c.contribution, 2, true)}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-400">
                    {c.contribution_pct !== null && c.contribution_pct !== undefined
                      ? `${(c.contribution_pct * 100).toFixed(1)}%`
                      : "N/A"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
