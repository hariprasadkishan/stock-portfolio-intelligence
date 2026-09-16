"use client";

import React from "react";
import { PieChart, Info } from "lucide-react";

interface EmptyStateProps {
  portfolioName?: string;
  portfolioId?: string;
}

export function EmptyState({ portfolioName, portfolioId }: EmptyStateProps) {
  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-10 max-w-2xl mx-auto my-12 text-center">
      <div className="w-12 h-12 rounded-full bg-[#1F2937] flex items-center justify-center mx-auto mb-4 text-slate-400">
        <PieChart className="w-6 h-6" />
      </div>
      <h2 className="text-xl font-semibold text-slate-100 mb-2">
        Portfolio Has No Recorded Holdings
      </h2>
      <p className="text-sm text-slate-400 mb-4 max-w-md mx-auto">
        Portfolio <span className="text-slate-200 font-medium">{portfolioName || portfolioId}</span> is initialized with cash balance but currently contains zero active asset positions.
      </p>

      <div className="inline-flex items-center gap-2 px-3 py-2 text-xs text-slate-400 bg-[#0B0F17] rounded-lg border border-[#1F2937]">
        <Info className="w-4 h-4 text-blue-400" />
        Record trades or ingest historical market prices to generate deterministic analytics.
      </div>
    </div>
  );
}
