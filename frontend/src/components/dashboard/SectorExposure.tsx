"use client";

import React from "react";
import { PortfolioSectors } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { Building2 } from "lucide-react";

interface SectorExposureProps {
  sectors: PortfolioSectors;
  baseCurrency?: string;
}

export function SectorExposure({ sectors, baseCurrency = "USD" }: SectorExposureProps) {
  const items = sectors?.sectors || [];

  if (items.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 text-center text-slate-400">
        No sector exposure data available.
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-slate-100">Sector Exposure</h2>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {items.length} {items.length === 1 ? "Sector" : "Sectors"}
          </span>
        </div>

        <p className="text-xs text-slate-400 mb-5">
          Industry grouping of invested capital. Assets with unclassified industry data appear as <strong className="text-slate-300">"Unknown"</strong>.
        </p>

        {/* Horizontal bar representation */}
        <div className="space-y-4">
          {items.map((sec) => {
            const pct = Math.max(0, Math.min(100, (sec.portfolio_weight || 0) * 100));
            const isUnknown = sec.sector.toLowerCase() === "unknown";

            return (
              <div key={sec.sector} className="space-y-1.5">
                <div className="flex justify-between items-baseline text-xs">
                  <span className={`font-medium ${isUnknown ? "text-slate-400 italic" : "text-slate-200"}`}>
                    {sec.sector}
                  </span>
                  <div className="flex items-center gap-3 font-mono">
                    <span className="text-slate-400">
                      {formatCurrency(sec.market_value, baseCurrency)}
                    </span>
                    <span className="font-semibold text-emerald-400 min-w-[50px] text-right">
                      {formatPercent(sec.portfolio_weight, 2)}
                    </span>
                  </div>
                </div>

                {/* Bar progress track */}
                <div className="h-2.5 w-full bg-[#0B0F17] rounded-full overflow-hidden border border-[#1F2937]">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isUnknown ? "bg-slate-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-6 pt-3 border-t border-[#1F2937] text-[11px] text-slate-500 flex justify-between">
        <span>Aggregate Market Exposure</span>
        <span className="font-mono text-slate-400">
          {formatCurrency(sectors.total_market_value, baseCurrency)}
        </span>
      </div>
    </div>
  );
}
