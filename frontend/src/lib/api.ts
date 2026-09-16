/**
 * Centralized API client for Portfolio Analytics & Intelligence.
 * Strictly communicates with backend FastAPI endpoints without performing financial logic.
 */

import {
  AnalystResponse,
  DashboardSummary,
  PortfolioAllocation,
  PortfolioBenchmark,
  PortfolioContributions,
  PortfolioCorrelation,
  PortfolioListItem,
  PortfolioOverview,
  PortfolioPerformance,
  PortfolioRisk,
  PortfolioSectors,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export const DEFAULT_PORTFOLIO_ID =
  process.env.NEXT_PUBLIC_DEFAULT_PORTFOLIO_ID || "";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errorJson = await res.json();
      if (errorJson?.detail) {
        errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Body not JSON
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export async function fetchPortfolios(): Promise<PortfolioListItem[]> {
  try {
    const res = await fetch(`${API_BASE}/api/portfolio`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    return await handleResponse<PortfolioListItem[]>(res);
  } catch (err: any) {
    // Gracefully return empty list if server is offline
    console.warn("Could not fetch portfolios list:", err?.message || err);
    return [];
  }
}

export async function fetchDashboard(
  portfolioId: string,
  riskFreeRate: number = 0.0
): Promise<DashboardSummary> {
  const url = `${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/dashboard?risk_free_rate=${riskFreeRate}`;
  const res = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<DashboardSummary>(res);
}

export async function fetchOverview(portfolioId: string): Promise<PortfolioOverview> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/overview`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioOverview>(res);
}

export async function fetchRisk(
  portfolioId: string,
  riskFreeRate: number = 0.0
): Promise<PortfolioRisk> {
  const res = await fetch(
    `${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/risk?risk_free_rate=${riskFreeRate}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    }
  );
  return handleResponse<PortfolioRisk>(res);
}

export async function fetchAllocation(portfolioId: string): Promise<PortfolioAllocation> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/allocation`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioAllocation>(res);
}

export async function fetchSectors(portfolioId: string): Promise<PortfolioSectors> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/sectors`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioSectors>(res);
}

export async function fetchContributions(portfolioId: string): Promise<PortfolioContributions> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/contributions`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioContributions>(res);
}

export async function fetchCorrelation(portfolioId: string): Promise<PortfolioCorrelation> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/correlation`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioCorrelation>(res);
}

export async function fetchBenchmark(
  portfolioId: string,
  riskFreeRate: number = 0.0
): Promise<PortfolioBenchmark> {
  const res = await fetch(
    `${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/benchmark?risk_free_rate=${riskFreeRate}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    }
  );
  return handleResponse<PortfolioBenchmark>(res);
}

export async function fetchPerformance(portfolioId: string): Promise<PortfolioPerformance> {
  const res = await fetch(`${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/performance`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  return handleResponse<PortfolioPerformance>(res);
}

export async function askPortfolioAnalyst(
  portfolioId: string,
  question: string
): Promise<AnalystResponse> {
  const url = `${API_BASE}/api/portfolio/${encodeURIComponent(portfolioId)}/ask`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    cache: "no-store",
    body: JSON.stringify({ question }),
  });
  return handleResponse<AnalystResponse>(res);
}
