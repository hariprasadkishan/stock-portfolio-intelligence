"use client";

import React from "react";
import { PortfolioAllocation } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { PieChart as PieIcon } from "lucide-react";

interface AssetAllocationProps {
  allocation: PortfolioAllocation;
  baseCurrency?: string;
}

const PALETTE = [
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#8B5CF6", // Purple
  "#F59E0B", // Amber
  "#EC4899", // Pink
  "#06B6D4", // Cyan
  "#F97316", // Orange
  "#6366F1", // Indigo
  "#14B8A6", // Teal
  "#84CC16", // Lime
];

export function AssetAllocation({ allocation, baseCurrency = "USD" }: AssetAllocationProps) {
  const items = allocation?.allocations || [];

  if (items.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 text-center text-slate-400">
        No active asset allocations found.
      </div>
    );
  }

  const chartData = items.map((a, idx) => ({
    name: a.ticker,
    value: a.market_value,
    weight: a.portfolio_weight,
    color: PALETTE[idx % PALETTE.length],
  }));

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <PieIcon className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-slate-100">Asset Allocation</h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Total: {formatCurrency(allocation.total_market_value, baseCurrency)}
          </span>
        </div>

        {/* Donut chart visualization */}
        <div className="h-56 w-full mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="#111827" strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0B0F17",
                  borderColor: "#374151",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#E2E8F0",
                }}
                formatter={(val: any, name: string) => [
                  `${formatCurrency(Number(val), baseCurrency)} (${formatPercent(
                    chartData.find((d) => d.name === name)?.weight,
                    2
                  )})`,
                  name,
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabular breakdown */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-[#0B0F17] text-slate-400 uppercase font-mono text-[10px] border-y border-[#1F2937]">
            <tr>
              <th scope="col" className="py-2 px-3">Asset</th>
              <th scope="col" className="py-2 px-3 text-right">Shares</th>
              <th scope="col" className="py-2 px-3 text-right">Price</th>
              <th scope="col" className="py-2 px-3 text-right">Market Value</th>
              <th scope="col" className="py-2 px-3 text-right">Weight</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1F2937]/50 font-mono">
            {items.map((item, idx) => (
              <tr key={item.ticker} className="hover:bg-[#1F2937]/30 transition-colors">
                <td className="py-2 px-3 font-semibold text-slate-100 flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{ backgroundColor: PALETTE[idx % PALETTE.length] }}
                  />
                  {item.ticker}
                </td>
                <td className="py-2 px-3 text-right">{item.shares.toLocaleString()}</td>
                <td className="py-2 px-3 text-right">{formatCurrency(item.current_price, baseCurrency)}</td>
                <td className="py-2 px-3 text-right font-medium text-slate-100">
                  {formatCurrency(item.market_value, baseCurrency)}
                </td>
                <td className="py-2 px-3 text-right font-semibold text-blue-400">
                  {formatPercent(item.portfolio_weight, 2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
