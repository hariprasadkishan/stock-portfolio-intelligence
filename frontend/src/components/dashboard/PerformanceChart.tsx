"use client";

import React, { useState } from "react";
import { PerformanceObservation } from "@/lib/types";
import { formatCurrency, formatPercent, formatDate } from "@/lib/formatters";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { TrendingUp, AlertCircle } from "lucide-react";

interface PerformanceChartProps {
  performance: PerformanceObservation[];
  baseCurrency?: string;
  benchmarkSymbol?: string | null;
}

export function PerformanceChart({
  performance,
  baseCurrency = "USD",
  benchmarkSymbol,
}: PerformanceChartProps) {
  const [viewMode, setViewMode] = useState<"value" | "return">("value");

  if (!performance || performance.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-8 text-center">
        <p className="text-sm text-slate-400">No historical performance observations available.</p>
      </div>
    );
  }

  const hasBenchmark = performance.some(
    (p) => p.benchmark_value !== null && p.benchmark_value !== undefined
  );

  const chartData = performance.map((p) => ({
    date: p.date,
    portfolioValue: p.portfolio_value,
    benchmarkValue: p.benchmark_value,
    portfolioReturn:
      p.cumulative_portfolio_return !== null && p.cumulative_portfolio_return !== undefined
        ? p.cumulative_portfolio_return * 100
        : null,
    benchmarkReturn:
      p.cumulative_benchmark_return !== null && p.cumulative_benchmark_return !== undefined
        ? p.cumulative_benchmark_return * 100
        : null,
  }));

  const isValueView = viewMode === "value";

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      {/* Top row: Title and view mode toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              Performance Over Time
            </h2>
            {!hasBenchmark && (
              <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-amber-950/40 text-amber-400 border border-amber-800/40">
                <AlertCircle className="w-3 h-3" />
                Benchmark curve unavailable
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological equity curve compared with benchmark tracking index
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="inline-flex rounded-lg bg-[#0B0F17] p-1 border border-[#374151] self-start sm:self-auto">
          <button
            onClick={() => setViewMode("value")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              isValueView
                ? "bg-[#1F2937] text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Value ({baseCurrency})
          </button>
          <button
            onClick={() => setViewMode("return")}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              !isValueView
                ? "bg-[#1F2937] text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Cumulative Return (%)
          </button>
        </div>
      </div>

      {/* Chart container */}
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              tickFormatter={(val) => formatDate(val)}
            />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) =>
                isValueView
                  ? formatCurrency(val, baseCurrency, true)
                  : `${val > 0 ? "+" : ""}${val.toFixed(1)}%`
              }
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0B0F17",
                borderColor: "#374151",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#E2E8F0",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
              }}
              labelFormatter={(label) => formatDate(String(label))}
              formatter={(value: any, name: string) => {
                if (value === null || value === undefined) return ["N/A", name];
                const num = Number(value);
                if (isValueView) {
                  return [formatCurrency(num, baseCurrency), name];
                }
                return [`${num > 0 ? "+" : ""}${num.toFixed(2)}%`, name];
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ paddingBottom: 12, fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey={isValueView ? "portfolioValue" : "portfolioReturn"}
              name="Portfolio"
              stroke="#3B82F6"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: "#3B82F6", stroke: "#93C5FD", strokeWidth: 2 }}
            />
            {hasBenchmark && (
              <Line
                type="monotone"
                dataKey={isValueView ? "benchmarkValue" : "benchmarkReturn"}
                name={benchmarkSymbol ? `Benchmark (${benchmarkSymbol})` : "Benchmark"}
                stroke="#A855F7"
                strokeWidth={1.75}
                strokeDasharray="4 4"
                dot={false}
                activeDot={{ r: 4, fill: "#A855F7", stroke: "#E9D5FF", strokeWidth: 2 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {!hasBenchmark && (
        <div className="mt-4 p-3 bg-[#0B0F17] rounded-lg border border-[#1F2937] text-xs text-slate-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Benchmark historical price data was not found for symbol{" "}
            <strong className="text-slate-300">{benchmarkSymbol || "N/A"}</strong>. Only portfolio valuation is plotted.
          </span>
        </div>
      )}
    </div>
  );
}
