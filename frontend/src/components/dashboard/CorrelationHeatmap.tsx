"use client";

import React from "react";
import { PortfolioCorrelation } from "@/lib/types";
import { formatRatio } from "@/lib/formatters";
import { Grid, Network, ArrowUpRight, ArrowDownRight } from "lucide-react";

interface CorrelationHeatmapProps {
  correlation: PortfolioCorrelation;
}

export function CorrelationHeatmap({ correlation }: CorrelationHeatmapProps) {
  const matrix = correlation?.correlation_matrix || {};
  const tickers = Object.keys(matrix);

  if (tickers.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 text-center text-slate-400">
        No correlation observations available.
      </div>
    );
  }

  const getHeatmapColor = (val: number | null | undefined, isDiagonal: boolean) => {
    if (isDiagonal) {
      return "bg-[#1F2937] text-slate-300 font-semibold border border-slate-700/50";
    }
    if (val === null || val === undefined || isNaN(val)) {
      return "bg-[#0B0F17] text-slate-500 border border-[#1F2937]";
    }

    // Correlation scale: -1.0 to +1.0
    if (val >= 0.8) return "bg-blue-600 text-white font-bold";
    if (val >= 0.5) return "bg-blue-700/80 text-blue-100 font-semibold";
    if (val >= 0.2) return "bg-blue-900/60 text-blue-200";
    if (val >= 0.0) return "bg-[#1E293B] text-slate-300";
    if (val >= -0.2) return "bg-amber-950/40 text-amber-200 border border-amber-900/40";
    if (val >= -0.5) return "bg-rose-900/50 text-rose-200";
    return "bg-rose-700 text-white font-bold";
  };

  const highPair = correlation.highest_correlated_pair;
  const lowPair = correlation.lowest_correlated_pair;

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">
            Asset Pairwise Return Correlation
          </h2>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Off-Diagonal Diversification
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-6">
        Pearson correlation matrix of asset daily returns. Summary statistics strictly exclude diagonal self-correlation (ρ = 1.0).
      </p>

      {/* Extrema Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-3.5">
          <div className="text-xs text-slate-400 font-medium mb-1">
            Average Pairwise Correlation
          </div>
          <div className="text-xl font-bold font-mono text-slate-100">
            {formatRatio(correlation.average_pairwise_correlation, 3)}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Mean across all distinct pairs</div>
        </div>

        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Highest Correlated Pair</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold font-mono text-slate-100">
              {highPair ? `${highPair[0]} / ${highPair[1]}` : "N/A"}
            </span>
            <span className="text-sm font-semibold font-mono text-blue-400">
              {formatRatio(correlation.highest_pairwise_correlation, 3)}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Strongest co-movement</div>
        </div>

        <div className="bg-[#0B0F17] border border-[#1F2937] rounded-lg p-3.5">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span>Lowest Correlated Pair</span>
            <ArrowDownRight className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold font-mono text-slate-100">
              {lowPair ? `${lowPair[0]} / ${lowPair[1]}` : "N/A"}
            </span>
            <span className="text-sm font-semibold font-mono text-amber-400">
              {formatRatio(correlation.lowest_pairwise_correlation, 3)}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Maximum diversification benefit</div>
        </div>
      </div>

      {/* Heatmap Matrix Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-center text-xs border-collapse">
          <thead>
            <tr>
              <th scope="col" className="p-2 text-left font-mono text-slate-400 text-[11px] bg-[#0B0F17] border border-[#1F2937]">
                Ticker
              </th>
              {tickers.map((t) => (
                <th
                  key={t}
                  scope="col"
                  className="p-2 font-mono font-semibold text-slate-200 text-xs bg-[#0B0F17] border border-[#1F2937] min-w-[70px]"
                >
                  {t}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tickers.map((rowTicker) => (
              <tr key={rowTicker}>
                <td className="p-2 text-left font-mono font-semibold text-slate-200 bg-[#0B0F17] border border-[#1F2937]">
                  {rowTicker}
                </td>
                {tickers.map((colTicker) => {
                  const val = matrix[rowTicker]?.[colTicker];
                  const isDiag = rowTicker === colTicker;
                  const cellClass = getHeatmapColor(val, isDiag);

                  return (
                    <td
                      key={`${rowTicker}-${colTicker}`}
                      className={`p-2 font-mono text-xs border border-[#1F2937]/80 transition-colors ${cellClass}`}
                      title={`${rowTicker} vs ${colTicker}: ${formatRatio(val, 4)}`}
                    >
                      {formatRatio(val, 2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-end gap-3 text-[10px] text-slate-400 font-mono">
        <span>Negative: <span className="inline-block w-3 h-3 bg-rose-700 align-middle rounded-sm"></span> -1.0</span>
        <span>Neutral: <span className="inline-block w-3 h-3 bg-[#1E293B] align-middle rounded-sm"></span> 0.0</span>
        <span>Positive: <span className="inline-block w-3 h-3 bg-blue-600 align-middle rounded-sm"></span> +1.0</span>
      </div>
    </div>
  );
}
