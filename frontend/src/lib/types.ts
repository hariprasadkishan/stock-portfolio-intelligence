/**
 * Strongly-typed data models for Portfolio Intelligence & Risk Analytics Dashboard.
 * Strictly mirrors the backend Pydantic API response models.
 */

export interface PortfolioOverview {
  portfolio_id: string;
  portfolio_name: string;
  base_currency: string;
  benchmark: string | null;
  initial_cash: number;
  available_cash: number;
  current_portfolio_value: number;
  invested_value: number;
  absolute_pnl: number;
  percentage_pnl: number;
  cumulative_return: number | null;
  annualized_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  maximum_drawdown: number;
  maximum_drawdown_duration: number;
}

export interface PortfolioRisk {
  portfolio_id: string;
  volatility: number | null;
  sharpe: number | null;
  sortino: number | null;
  max_drawdown: number;
  max_drawdown_duration: number;
  var_95: number | null;
  cvar_95: number | null;
  beta: number | null;
  alpha: number | null;
  tracking_error: number | null;
  information_ratio: number | null;
}

export interface AllocationItem {
  ticker: string;
  shares: number;
  current_price: number;
  market_value: number;
  portfolio_weight: number;
}

export interface ConcentrationItem {
  hhi: number;
  largest_holding_ticker: string | null;
  largest_holding_weight: number;
  top_3_weight: number;
  top_5_weight: number;
  total_holdings_count: number;
}

export interface PortfolioAllocation {
  portfolio_id: string;
  total_market_value: number;
  allocations: AllocationItem[];
  concentration?: ConcentrationItem | null;
}

export interface SectorItem {
  sector: string;
  market_value: number;
  portfolio_weight: number;
}

export interface PortfolioSectors {
  portfolio_id: string;
  total_market_value: number;
  sectors: SectorItem[];
}

export interface ContributionItem {
  ticker: string;
  portfolio_weight: number;
  asset_return: number;
  contribution: number;
  contribution_pct: number | null;
}

export interface PortfolioContributions {
  portfolio_id: string;
  portfolio_return: number | null;
  contributions: ContributionItem[];
}

export interface PortfolioCorrelation {
  portfolio_id: string;
  correlation_matrix: Record<string, Record<string, number | null>>;
  average_pairwise_correlation: number | null;
  highest_pairwise_correlation: number | null;
  lowest_pairwise_correlation: number | null;
  highest_correlated_pair: [string, string] | null;
  lowest_correlated_pair: [string, string] | null;
}

export interface PortfolioBenchmark {
  portfolio_id: string;
  benchmark_symbol: string | null;
  correlation: number | null;
  covariance: number | null;
  beta: number | null;
  jensens_alpha: number | null;
  tracking_error: number | null;
  information_ratio: number | null;
  portfolio_cumulative_return: number | null;
  benchmark_cumulative_return: number | null;
  active_return: number | null;
}

export interface PerformanceObservation {
  date: string;
  portfolio_value: number;
  benchmark_value: number | null;
  daily_portfolio_return: number | null;
  cumulative_portfolio_return: number | null;
  daily_benchmark_return: number | null;
  cumulative_benchmark_return: number | null;
}

export interface PortfolioPerformance {
  portfolio_id: string;
  observations_count: number;
  performance: PerformanceObservation[];
}

export interface DashboardSummary {
  overview: PortfolioOverview;
  risk: PortfolioRisk;
  allocation: PortfolioAllocation;
  sectors: PortfolioSectors;
  contributions: PortfolioContributions;
  correlation: PortfolioCorrelation;
  benchmark: PortfolioBenchmark;
  performance: PerformanceObservation[];
}

export interface PortfolioListItem {
  id: string;
  name: string;
  base_currency: string;
  benchmark_symbol: string | null;
}
