"use client";

import React, { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  fetchDashboard,
  fetchPortfolios,
  DEFAULT_PORTFOLIO_ID,
} from "@/lib/api";
import { DashboardSummary, PortfolioListItem } from "@/lib/types";

import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { SecondaryPerformance } from "@/components/dashboard/SecondaryPerformance";
import { RiskAnalytics } from "@/components/dashboard/RiskAnalytics";
import { AssetAllocation } from "@/components/dashboard/AssetAllocation";
import { SectorExposure } from "@/components/dashboard/SectorExposure";
import { ReturnContribution } from "@/components/dashboard/ReturnContribution";
import { ConcentrationSection } from "@/components/dashboard/ConcentrationSection";
import { CorrelationHeatmap } from "@/components/dashboard/CorrelationHeatmap";
import { BenchmarkComparison } from "@/components/dashboard/BenchmarkComparison";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { ErrorState } from "@/components/dashboard/ErrorState";
import { EmptyState } from "@/components/dashboard/EmptyState";
import { AIAnalyst } from "@/components/dashboard/AIAnalyst";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [portfolioId, setPortfolioId] = useState<string>("");
  const [portfoliosList, setPortfoliosList] = useState<PortfolioListItem[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.0);

  // 1. Initial resolution of portfolios list & active portfolio ID
  useEffect(() => {
    let isMounted = true;

    async function initPortfolios() {
      const list = await fetchPortfolios();
      if (!isMounted) return;
      setPortfoliosList(list);

      const urlId = searchParams.get("portfolioId");
      if (urlId && urlId.trim()) {
        setPortfolioId(urlId.trim());
      } else if (DEFAULT_PORTFOLIO_ID && DEFAULT_PORTFOLIO_ID.trim()) {
        setPortfolioId(DEFAULT_PORTFOLIO_ID.trim());
      } else if (list.length > 0) {
        setPortfolioId(list[0].id);
      } else {
        // Fallback default ID
        setPortfolioId("11111111-1111-1111-1111-111111111111");
      }
    }

    initPortfolios();

    return () => {
      isMounted = false;
    };
  }, [searchParams]);

  // 2. Fetch dashboard data for active portfolio ID
  const loadDashboard = useCallback(
    async (pId: string, showRefreshSpinner = false) => {
      if (!pId) return;

      if (showRefreshSpinner) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const data = await fetchDashboard(pId, riskFreeRate);
        setDashboardData(data);
      } catch (err: any) {
        console.error("Dashboard fetch error:", err);
        setError(err?.message || "Failed to retrieve portfolio analytics from server.");
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [riskFreeRate]
  );

  useEffect(() => {
    if (portfolioId) {
      loadDashboard(portfolioId);
    }
  }, [portfolioId, loadDashboard]);

  // 3. Switch portfolio handler
  const handleSelectPortfolio = (newId: string) => {
    setPortfolioId(newId);
    router.push(`/portfolio/dashboard?portfolioId=${encodeURIComponent(newId)}`);
  };

  // 4. Render states
  if (isLoading && !dashboardData) {
    return (
      <main className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <LoadingSkeleton />
        </div>
      </main>
    );
  }

  if (error && !dashboardData) {
    return (
      <main className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <ErrorState message={error} onRetry={() => loadDashboard(portfolioId)} />
        </div>
      </main>
    );
  }

  if (!dashboardData) {
    return (
      <main className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <EmptyState portfolioId={portfolioId} />
        </div>
      </main>
    );
  }

  const { overview, risk, allocation, sectors, contributions, correlation, benchmark, performance } =
    dashboardData;

  const hasHoldings = allocation?.allocations && allocation.allocations.length > 0;

  return (
    <main className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Error notice if refresh failed while old data displayed */}
        {error && (
          <div className="bg-rose-950/50 border border-rose-800 text-rose-300 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between">
            <span>Notice: Refresh failed ({error}). Displaying cached analytics.</span>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-200 underline text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* 1. Header with metadata and switcher */}
        <DashboardHeader
          portfolioName={overview.portfolio_name}
          portfolioId={overview.portfolio_id}
          baseCurrency={overview.base_currency}
          benchmarkSymbol={overview.benchmark}
          portfoliosList={portfoliosList}
          selectedPortfolioId={portfolioId}
          onSelectPortfolio={handleSelectPortfolio}
          onRefresh={() => loadDashboard(portfolioId, true)}
          isRefreshing={isRefreshing}
        />

        {/* 2. Executive KPI Scorecard Grid */}
        <KPIGrid overview={overview} />

        {/* If portfolio is empty, show informative empty state below KPIs */}
        {!hasHoldings ? (
          <EmptyState
            portfolioName={overview.portfolio_name}
            portfolioId={overview.portfolio_id}
          />
        ) : (
          <>
            {/* 3. Primary Performance Chart (Line Chart over time) */}
            <PerformanceChart
              performance={performance}
              baseCurrency={overview.base_currency}
              benchmarkSymbol={overview.benchmark}
            />

            {/* 4. Secondary Cumulative & Active Returns Distribution */}
            <SecondaryPerformance benchmark={benchmark} />

            {/* 5. 2-Column: Asset Allocation & Sector Exposure */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AssetAllocation
                allocation={allocation}
                baseCurrency={overview.base_currency}
              />
              <SectorExposure
                sectors={sectors}
                baseCurrency={overview.base_currency}
              />
            </div>

            {/* 6. 2-Column: Return Contribution & Concentration Analytics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ReturnContribution contributions={contributions} />
              <ConcentrationSection allocation={allocation} />
            </div>

            {/* 7. Asset Pairwise Return Correlation Heatmap */}
            <CorrelationHeatmap correlation={correlation} />

            {/* 8. Dedicated Quantitative Risk Analytics Section */}
            <RiskAnalytics risk={risk} />

            {/* 9. Benchmark Comparative Analytics */}
            <BenchmarkComparison benchmark={benchmark} />
          </>
        )}

        {/* 10. AI Financial Analyst Experience */}
        <AIAnalyst
          portfolioId={overview.portfolio_id}
          portfolioName={overview.portfolio_name}
        />

        {/* Footer info note */}
        <footer className="pt-6 border-t border-[#1F2937] text-center text-xs text-slate-500 font-mono">
          Stock Portfolio Intelligence & Risk Analytics Terminal • Deterministic Formulation Layer
        </footer>
      </div>
    </main>
  );
}

export default function PortfolioDashboardPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#0B0F17] text-slate-100 p-4 md:p-8">
          <div className="max-w-7xl mx-auto">
            <LoadingSkeleton />
          </div>
        </main>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
