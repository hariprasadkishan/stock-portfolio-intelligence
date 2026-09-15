"""Normalization logic for market data fetched from yfinance or other dataframes."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
import pandas as pd


def _standardize_col_name(col: Any) -> str:
    """Standardize column names to snake_case without extra spaces."""
    if isinstance(col, tuple):
        col = "_".join(str(c) for c in col if c)
    s = str(col).strip().lower().replace(" ", "_")
    return s


def normalize_market_data(
    df: pd.DataFrame, default_ticker: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Normalize yfinance DataFrame into a list of raw price dictionaries.
    
    Handles:
    - yfinance MultiIndex columns (Price, Ticker) or (Ticker, Price)
    - Single-level DataFrames from ticker.history or test fixtures
    - DatetimeIndex or 'Date' / 'price_date' columns
    - Missing or optional OHLCV fields
    """
    if df is None or df.empty:
        return []

    processed_df = df.copy()

    # 1. Handle MultiIndex columns from yf.download
    if isinstance(processed_df.columns, pd.MultiIndex):
        col_names = [str(n).lower() if n else "" for n in processed_df.columns.names]
        if "ticker" in col_names:
            ticker_level = col_names.index("ticker")
            processed_df = processed_df.stack(level=ticker_level, future_stack=True).reset_index()
        elif len(processed_df.columns.levels) == 2:
            # Usually level 1 is ticker in yfinance download
            processed_df = processed_df.stack(level=1, future_stack=True).reset_index()
        else:
            # Flatten multiindex
            processed_df.columns = [_standardize_col_name(c) for c in processed_df.columns]
            processed_df = processed_df.reset_index()
    else:
        # Reset index if index contains Date/Timestamp
        if not any(c.lower() in ("date", "price_date") for c in processed_df.columns if isinstance(c, str)):
            processed_df = processed_df.reset_index()

    # 2. Map columns to standard field names
    raw_col_map = {col: _standardize_col_name(col) for col in processed_df.columns}
    processed_df = processed_df.rename(columns=raw_col_map)

    # Standard field mapping rules
    field_alias = {
        "date": "price_date",
        "price_date": "price_date",
        "timestamp": "price_date",
        "index": "price_date",
        "ticker": "ticker",
        "symbol": "ticker",
        "open": "open_price",
        "open_price": "open_price",
        "high": "high_price",
        "high_price": "high_price",
        "low": "low_price",
        "low_price": "low_price",
        "close": "close_price",
        "close_price": "close_price",
        "adj_close": "adj_close",
        "adjclose": "adj_close",
        "adjusted_close": "adj_close",
        "volume": "volume",
        "vol": "volume",
    }

    rename_dict = {}
    for col in processed_df.columns:
        if col in field_alias:
            rename_dict[col] = field_alias[col]

    processed_df = processed_df.rename(columns=rename_dict)

    # If ticker is missing from columns, apply default_ticker if available
    if "ticker" not in processed_df.columns and default_ticker:
        processed_df["ticker"] = default_ticker

    records: List[Dict[str, Any]] = []

    for _, row in processed_df.iterrows():
        # Extract date
        raw_date = row.get("price_date")
        parsed_date: Optional[date] = None
        if isinstance(raw_date, pd.Timestamp):
            parsed_date = raw_date.to_pydatetime().date()
        elif isinstance(raw_date, datetime):
            parsed_date = raw_date.date()
        elif isinstance(raw_date, date):
            parsed_date = raw_date
        elif isinstance(raw_date, str):
            try:
                parsed_date = pd.to_datetime(raw_date).date()
            except Exception:
                parsed_date = None

        record: Dict[str, Any] = {
            "ticker": str(row.get("ticker", "")).strip().upper() if row.get("ticker") is not None else "",
            "price_date": parsed_date,
            "open_price": row.get("open_price"),
            "high_price": row.get("high_price"),
            "low_price": row.get("low_price"),
            "close_price": row.get("close_price"),
            "adj_close": row.get("adj_close") if "adj_close" in row and pd.notna(row["adj_close"]) else row.get("close_price"),
            "volume": row.get("volume"),
        }
        records.append(record)

    return records
