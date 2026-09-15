"""Deterministic Portfolio Intelligence Analytics Layer.

Calculates:
1. Asset Allocation: Market values and decimal portfolio weights.
2. Sector Exposure: Aggregated sector weights and market values with explicit 'Unknown' handling.
3. Concentration Analytics: Herfindahl-Hirschman Index (HHI), largest holding, top-3, and top-5 weights.
4. Return Contribution: Asset-level weighted return contribution and percentage of total portfolio return.
5. Diversification / Correlation: Pairwise Pearson correlation matrix excluding diagonal self-correlation.
6. Portfolio Intelligence Summary: High-level dataclass bundling all intelligence analytics.

Mathematical Formulas:
- Market Value:
    MV_i = Shares_i \\times Price_i
    Total_MV = \\sum_{i=1}^n MV_i
- Portfolio Weight:
    w_i = \\frac{MV_i}{Total_MV}
- Sector Weight:
    w_{sector} = \\frac{\\sum_{i \\in sector} MV_i}{Total_MV}
- Herfindahl-Hirschman Index (HHI):
    HHI = \\sum_{i=1}^n w_i^2
- Asset Return Contribution:
    C_i = w_i \\times R_i
    R_{port} = \\sum_{i=1}^n C_i
    C_{\\%, i} = \\frac{C_i}{R_{port}}  (\\text{for } R_{port} \\neq 0)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from agent.analytics.types import (
    ConcentrationMetrics,
    DiversificationMetrics,
    HoldingAllocation,
    PortfolioIntelligenceSummary,
    ReturnContribution,
    SectorExposure,
)


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase snake_case."""
    col_map = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
    return df.rename(columns=col_map)


def calculate_asset_allocation(holdings: pd.DataFrame) -> pd.DataFrame:
    """Calculate current asset allocation, market values, and decimal portfolio weights.

    Parameters:
        holdings: pd.DataFrame containing at minimum:
            - 'ticker' (or 'symbol')
            - 'shares'
            - 'current_price' (or 'price', 'close_price', 'adj_close')
            - optionally 'sector'

    Returns:
        pd.DataFrame with columns:
            ['ticker', 'shares', 'current_price', 'market_value', 'portfolio_weight']
            (plus 'sector' if present in input)
        Sorted by 'market_value' descending.
    """
    empty_cols = ["ticker", "shares", "current_price", "market_value", "portfolio_weight"]
    if holdings is None or holdings.empty:
        return pd.DataFrame(columns=empty_cols)

    df = _normalize_column_names(holdings.copy())

    # Map column aliases
    ticker_col = next((c for c in ["ticker", "symbol"] if c in df.columns), None)
    shares_col = next((c for c in ["shares", "share_count", "quantity"] if c in df.columns), None)
    price_col = next(
        (c for c in ["current_price", "price", "close_price", "adj_close", "close"] if c in df.columns),
        None,
    )
    sector_col = next((c for c in ["sector"] if c in df.columns), None)

    if not ticker_col or not shares_col or not price_col:
        return pd.DataFrame(columns=empty_cols)

    # Standardize working columns
    df = df.rename(
        columns={
            ticker_col: "ticker",
            shares_col: "shares",
            price_col: "current_price",
        }
    )

    # Clean ticker symbols
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df = df[df["ticker"].str.len() > 0]

    # Clean numeric fields - drop invalid, negative, or zero values
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
    df["current_price"] = pd.to_numeric(df["current_price"], errors="coerce")

    valid_mask = (
        df["shares"].notna()
        & (df["shares"] > 0)
        & df["current_price"].notna()
        & (df["current_price"] > 0)
    )
    clean_df = df[valid_mask].copy()

    if clean_df.empty:
        return pd.DataFrame(columns=empty_cols)

    # Calculate market value
    clean_df["market_value"] = clean_df["shares"] * clean_df["current_price"]
    total_market_value = float(clean_df["market_value"].sum())

    if total_market_value <= 0.0 or np.isnan(total_market_value):
        clean_df["portfolio_weight"] = 0.0
    else:
        clean_df["portfolio_weight"] = clean_df["market_value"] / total_market_value

    clean_df = clean_df.sort_values(by="market_value", ascending=False).reset_index(drop=True)

    result_cols = ["ticker", "shares", "current_price", "market_value", "portfolio_weight"]
    if sector_col and sector_col in clean_df.columns:
        result_cols.append(sector_col)

    return clean_df[result_cols]


def calculate_sector_exposure(
    allocation_df: pd.DataFrame,
    sector_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Calculate portfolio exposure grouped by sector.

    Parameters:
        allocation_df: pd.DataFrame produced by calculate_asset_allocation or containing
                       ['ticker', 'market_value'] and optionally ['sector'].
        sector_map: Optional dictionary mapping ticker symbol to sector name.

    Returns:
        pd.DataFrame with columns:
            ['sector', 'market_value', 'portfolio_weight']
        Sorted by 'market_value' descending.
    """
    empty_cols = ["sector", "market_value", "portfolio_weight"]
    if allocation_df is None or allocation_df.empty:
        return pd.DataFrame(columns=empty_cols)

    df = _normalize_column_names(allocation_df.copy())
    if "market_value" not in df.columns:
        if "shares" in df.columns and "current_price" in df.columns:
            df["market_value"] = df["shares"] * df["current_price"]
        else:
            return pd.DataFrame(columns=empty_cols)

    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    # Determine sector for each asset
    def _resolve_sector(row: pd.Series) -> str:
        ticker = row.get("ticker", "")
        sector_val = row.get("sector")
        if pd.notna(sector_val) and str(sector_val).strip() and str(sector_val).strip().lower() != "none":
            return str(sector_val).strip()
        if sector_map and ticker in sector_map:
            mapped = sector_map[ticker]
            if pd.notna(mapped) and str(mapped).strip() and str(mapped).strip().lower() != "none":
                return str(mapped).strip()
        return "Unknown"

    df["resolved_sector"] = df.apply(_resolve_sector, axis=1)

    total_portfolio_value = float(df["market_value"].sum())
    if total_portfolio_value <= 0.0 or np.isnan(total_portfolio_value):
        return pd.DataFrame(columns=empty_cols)

    # Group by resolved sector
    grouped = (
        df.groupby("resolved_sector", as_index=False)["market_value"]
        .sum()
        .rename(columns={"resolved_sector": "sector"})
    )

    grouped["portfolio_weight"] = grouped["market_value"] / total_portfolio_value
    grouped = grouped.sort_values(by="market_value", ascending=False).reset_index(drop=True)

    return grouped[["sector", "market_value", "portfolio_weight"]]


def calculate_concentration_metrics(
    weights: Union[pd.Series, Dict[str, float], pd.DataFrame],
) -> ConcentrationMetrics:
    """Calculate portfolio concentration metrics including Herfindahl-Hirschman Index (HHI).

    Formula:
        HHI = \\sum_{i=1}^n w_i^2

    Parameters:
        weights: pd.Series of decimal weights, dictionary mapping ticker -> weight,
                 or DataFrame with columns ['ticker', 'portfolio_weight'].

    Returns:
        ConcentrationMetrics dataclass.
    """
    clean_weights: Dict[str, float] = {}

    if isinstance(weights, pd.DataFrame):
        df = _normalize_column_names(weights)
        t_col = next((c for c in ["ticker", "symbol"] if c in df.columns), None)
        w_col = next((c for c in ["portfolio_weight", "weight", "weights"] if c in df.columns), None)
        if t_col and w_col:
            for _, r in df.iterrows():
                t = str(r[t_col]).strip().upper()
                w = pd.to_numeric(r[w_col], errors="coerce")
                if pd.notna(w) and w > 0:
                    clean_weights[t] = float(w)
    elif isinstance(weights, pd.Series):
        for idx, w in weights.items():
            t = str(idx).strip().upper()
            w_val = pd.to_numeric(w, errors="coerce")
            if pd.notna(w_val) and w_val > 0:
                clean_weights[t] = float(w_val)
    elif isinstance(weights, dict):
        for t, w in weights.items():
            t_str = str(t).strip().upper()
            w_val = pd.to_numeric(w, errors="coerce")
            if pd.notna(w_val) and w_val > 0:
                clean_weights[t_str] = float(w_val)

    if not clean_weights:
        return ConcentrationMetrics(
            hhi=0.0,
            largest_holding_ticker=None,
            largest_holding_weight=0.0,
            top_3_weight=0.0,
            top_5_weight=0.0,
            total_holdings_count=0,
        )

    # Normalize weights so they sum to 1.0
    weight_sum = sum(clean_weights.values())
    if weight_sum > 0:
        normalized_weights = {k: v / weight_sum for k, v in clean_weights.items()}
    else:
        normalized_weights = clean_weights

    sorted_weights = sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True)
    sorted_vals = [w for _, w in sorted_weights]

    hhi = float(sum(w ** 2 for w in sorted_vals))
    largest_ticker = sorted_weights[0][0] if sorted_weights else None
    largest_weight = float(sorted_vals[0]) if sorted_vals else 0.0

    top_3_weight = float(min(1.0, sum(sorted_vals[:3])))
    top_5_weight = float(min(1.0, sum(sorted_vals[:5])))

    return ConcentrationMetrics(
        hhi=round(hhi, 6),
        largest_holding_ticker=largest_ticker,
        largest_holding_weight=round(largest_weight, 6),
        top_3_weight=round(top_3_weight, 6),
        top_5_weight=round(top_5_weight, 6),
        total_holdings_count=len(sorted_weights),
    )


def calculate_return_contributions(
    weights: Union[Dict[str, float], pd.Series],
    asset_returns: Union[Dict[str, float], pd.Series],
) -> pd.DataFrame:
    """Calculate asset-level return contributions and percentage contribution to total portfolio return.

    Formulas:
        Contribution_i = Weight_i * Return_i
        Portfolio_Return = \\sum Contribution_i
        Contribution_Pct_i = Contribution_i / Portfolio_Return  (if Portfolio_Return != 0)

    Returns:
        pd.DataFrame with columns:
            ['ticker', 'portfolio_weight', 'asset_return', 'contribution', 'contribution_pct']
        Sorted by 'contribution' descending.
    """
    empty_cols = ["ticker", "portfolio_weight", "asset_return", "contribution", "contribution_pct"]
    if not weights or not asset_returns:
        return pd.DataFrame(columns=empty_cols)

    # Convert to standard dictionaries
    w_dict = {str(k).strip().upper(): float(v) for k, v in dict(weights).items() if pd.notna(v)}
    r_dict = {str(k).strip().upper(): float(v) for k, v in dict(asset_returns).items() if pd.notna(v)}

    # Match overlapping tickers
    common_tickers = sorted(list(set(w_dict.keys()).intersection(set(r_dict.keys()))))
    if not common_tickers:
        return pd.DataFrame(columns=empty_cols)

    rows: List[Dict[str, Any]] = []
    total_contribution = 0.0

    for t in common_tickers:
        w = w_dict[t]
        r = r_dict[t]
        contrib = w * r
        total_contribution += contrib
        rows.append(
            {
                "ticker": t,
                "portfolio_weight": w,
                "asset_return": r,
                "contribution": contrib,
            }
        )

    df_result = pd.DataFrame(rows)

    # Calculate contribution percentage if total return is non-zero
    if abs(total_contribution) > 1e-12:
        df_result["contribution_pct"] = df_result["contribution"] / total_contribution
    else:
        df_result["contribution_pct"] = None

    df_result = df_result.sort_values(by="contribution", ascending=False).reset_index(drop=True)
    return df_result[empty_cols]


def calculate_diversification_metrics(
    returns_matrix: pd.DataFrame,
) -> DiversificationMetrics:
    """Calculate asset return correlation matrix and off-diagonal pairwise summary statistics.

    Excludes diagonal self-correlations (1.0) when computing pairwise average, min, and max.

    Parameters:
        returns_matrix: pd.DataFrame where columns = ticker symbols and index = dates.

    Returns:
        DiversificationMetrics dataclass.
    """
    if returns_matrix is None or returns_matrix.empty:
        return DiversificationMetrics(
            correlation_matrix=pd.DataFrame(),
            average_pairwise_correlation=None,
            highest_pairwise_correlation=None,
            highest_correlation_pair=None,
            lowest_pairwise_correlation=None,
            lowest_correlation_pair=None,
            total_pairs_count=0,
        )

    # Drop columns that are completely empty
    clean_matrix = returns_matrix.dropna(how="all", axis=1)
    tickers = list(clean_matrix.columns)

    if len(tickers) < 2:
        corr_mat = clean_matrix.corr(method="pearson") if len(tickers) == 1 else pd.DataFrame()
        return DiversificationMetrics(
            correlation_matrix=corr_mat,
            average_pairwise_correlation=None,
            highest_pairwise_correlation=None,
            highest_correlation_pair=None,
            lowest_pairwise_correlation=None,
            lowest_correlation_pair=None,
            total_pairs_count=0,
        )

    # Pearson correlation matrix using pairwise complete observations (no forward fill)
    corr_matrix = clean_matrix.corr(method="pearson")

    # Extract upper-triangle off-diagonal pairwise values
    pairwise_values: List[Tuple[float, Tuple[str, str]]] = []

    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            t_i = tickers[i]
            t_j = tickers[j]
            c_val = corr_matrix.loc[t_i, t_j]
            if pd.notna(c_val) and not np.isinf(c_val):
                pairwise_values.append((float(c_val), (str(t_i), str(t_j))))

    if not pairwise_values:
        return DiversificationMetrics(
            correlation_matrix=corr_matrix,
            average_pairwise_correlation=None,
            highest_pairwise_correlation=None,
            highest_correlation_pair=None,
            lowest_pairwise_correlation=None,
            lowest_correlation_pair=None,
            total_pairs_count=0,
        )

    corrs = [val for val, _ in pairwise_values]
    avg_corr = float(np.mean(corrs))

    highest_val, highest_pair = max(pairwise_values, key=lambda x: x[0])
    lowest_val, lowest_pair = min(pairwise_values, key=lambda x: x[0])

    return DiversificationMetrics(
        correlation_matrix=corr_matrix,
        average_pairwise_correlation=round(avg_corr, 6),
        highest_pairwise_correlation=round(highest_val, 6),
        highest_correlation_pair=highest_pair,
        lowest_pairwise_correlation=round(lowest_val, 6),
        lowest_correlation_pair=lowest_pair,
        total_pairs_count=len(pairwise_values),
    )


def compute_portfolio_intelligence(
    holdings_df: pd.DataFrame,
    asset_returns: Optional[Union[pd.Series, Dict[str, float]]] = None,
    returns_matrix: Optional[pd.DataFrame] = None,
    sector_map: Optional[Dict[str, str]] = None,
) -> PortfolioIntelligenceSummary:
    """Compute complete Portfolio Intelligence summary combining allocation, exposure, concentration, and diversification.

    Parameters:
        holdings_df: DataFrame containing ticker, shares, current_price, and optional sector.
        asset_returns: Optional periodic returns for return contribution calculation.
        returns_matrix: Optional historical returns DataFrame for correlation analysis.
        sector_map: Optional dictionary mapping ticker to sector.

    Returns:
        PortfolioIntelligenceSummary dataclass.
    """
    # 1. Asset allocation
    alloc_df = calculate_asset_allocation(holdings_df)
    total_val = float(alloc_df["market_value"].sum()) if not alloc_df.empty else 0.0

    allocations: List[HoldingAllocation] = []
    if not alloc_df.empty:
        for _, r in alloc_df.iterrows():
            allocations.append(
                HoldingAllocation(
                    ticker=str(r["ticker"]),
                    shares=float(r["shares"]),
                    current_price=float(r["current_price"]),
                    market_value=float(r["market_value"]),
                    portfolio_weight=float(r["portfolio_weight"]),
                    sector=str(r["sector"]) if "sector" in r and pd.notna(r["sector"]) else None,
                )
            )

    # 2. Sector exposure
    sector_df = calculate_sector_exposure(alloc_df, sector_map=sector_map)
    sector_exposures: List[SectorExposure] = []
    if not sector_df.empty:
        for _, r in sector_df.iterrows():
            sector_exposures.append(
                SectorExposure(
                    sector=str(r["sector"]),
                    market_value=float(r["market_value"]),
                    portfolio_weight=float(r["portfolio_weight"]),
                )
            )

    # 3. Concentration metrics
    concentration = calculate_concentration_metrics(alloc_df)

    # 4. Return contributions
    return_contributions: List[ReturnContribution] = []
    portfolio_return: Optional[float] = None
    contrib_df = pd.DataFrame()

    if asset_returns is not None and not alloc_df.empty:
        weights_dict = dict(zip(alloc_df["ticker"], alloc_df["portfolio_weight"]))
        contrib_df = calculate_return_contributions(weights_dict, asset_returns)
        if not contrib_df.empty:
            portfolio_return = float(contrib_df["contribution"].sum())
            for _, r in contrib_df.iterrows():
                return_contributions.append(
                    ReturnContribution(
                        ticker=str(r["ticker"]),
                        portfolio_weight=float(r["portfolio_weight"]),
                        asset_return=float(r["asset_return"]),
                        contribution=float(r["contribution"]),
                        contribution_pct=float(r["contribution_pct"]) if pd.notna(r["contribution_pct"]) else None,
                    )
                )

    # 5. Diversification metrics
    if returns_matrix is not None and not returns_matrix.empty:
        diversification = calculate_diversification_metrics(returns_matrix)
    else:
        diversification = DiversificationMetrics(
            correlation_matrix=pd.DataFrame(),
            average_pairwise_correlation=None,
            highest_pairwise_correlation=None,
            highest_correlation_pair=None,
            lowest_pairwise_correlation=None,
            lowest_correlation_pair=None,
            total_pairs_count=0,
        )

    return PortfolioIntelligenceSummary(
        total_market_value=round(total_val, 4),
        allocations=allocations,
        sector_exposures=sector_exposures,
        concentration=concentration,
        return_contributions=return_contributions,
        diversification=diversification,
        portfolio_return=round(portfolio_return, 6) if portfolio_return is not None else None,
        allocation_df=alloc_df,
        sector_df=sector_df,
        contribution_df=contrib_df,
    )
