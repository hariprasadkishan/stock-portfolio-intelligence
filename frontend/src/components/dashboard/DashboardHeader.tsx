"use client";

import React from "react";
import { PortfolioListItem } from "@/lib/types";
import { ChevronDown, RefreshCw, Briefcase, Landmark } from "lucide-react";

interface DashboardHeaderProps {
  portfolioName: string;
  portfolioId: string;
  baseCurrency: string;
  benchmarkSymbol?: string | null;
  lastUpdated?: string | null;
  portfoliosList: PortfolioListItem[];
  selectedPortfolioId: string;
  onSelectPortfolio: (id: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export function DashboardHeader({
  portfolioName,
  portfolioId,
  baseCurrency,
  benchmarkSymbol,
  lastUpdated,
  portfoliosList,
  selectedPortfolioId,
  onSelectPortfolio,
  onRefresh,
  isRefreshing = false,
}: DashboardHeaderProps) {
  return (
    <header className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left side: Portfolio title & metadata */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider bg-[#1F2937] text-slate-300 border border-slate-700">
              Institutional Terminal
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-medium bg-blue-950/50 text-blue-400 border border-blue-800/50">
              Currency: {baseCurrency.toUpperCase()}
            </span>
            {benchmarkSymbol && (
              <span className="px-2.5 py-0.5 rounded text-xs font-medium bg-purple-950/50 text-purple-400 border border-purple-800/50 flex items-center gap-1">
                <Landmark className="w-3 h-3" />
                Benchmark: {benchmarkSymbol}
              </span>
            )}
          </div>

          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">
              {portfolioName}
            </h1>
            <span className="text-xs font-mono text-slate-500 hidden sm:inline" title={portfolioId}>
              ID: {portfolioId.substring(0, 8)}...
            </span>
          </div>

          {lastUpdated && (
            <p className="text-xs text-slate-400">
              As of: <span className="text-slate-300 font-mono">{lastUpdated}</span>
            </p>
          )}
        </div>

        {/* Right side: Portfolio Selector & Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Portfolio Switcher Dropdown */}
          {portfoliosList.length > 0 && (
            <div className="relative">
              <label htmlFor="portfolio-switcher" className="sr-only">
                Select Portfolio
              </label>
              <div className="relative inline-block text-left">
                <select
                  id="portfolio-switcher"
                  value={selectedPortfolioId}
                  onChange={(e) => onSelectPortfolio(e.target.value)}
                  className="appearance-none bg-[#0B0F17] text-slate-200 text-sm font-medium pl-9 pr-8 py-2 rounded-lg border border-[#374151] hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                >
                  {portfoliosList.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.base_currency})
                    </option>
                  ))}
                </select>
                <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Refresh portfolio data"
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-200 bg-[#0B0F17] hover:bg-[#1F2937] rounded-lg border border-[#374151] hover:border-slate-500 transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-blue-400" : "text-slate-400"}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>
    </header>
  );
}
