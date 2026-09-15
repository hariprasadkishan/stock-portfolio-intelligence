"""Fetcher layer for retrieving market data and metadata via yfinance."""

from datetime import date, datetime
import logging
from typing import List, Optional, Union
import pandas as pd
import yfinance as yf

from agent.data.schemas import AssetMetadata

logger = logging.getLogger("agent.data.fetcher")


def _format_date(d: Optional[Union[str, date, datetime]]) -> Optional[str]:
    """Convert date/datetime/string into standard YYYY-MM-DD string."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, str):
        return d.strip()
    return str(d)


def fetch_asset_metadata(ticker: str) -> AssetMetadata:
    """Fetch ticker metadata from yfinance with resilient fallbacks."""
    clean_ticker = ticker.strip().upper()
    try:
        t = yf.Ticker(clean_ticker)
        info = None
        try:
            info = t.info
        except Exception as e:
            logger.debug("Failed to retrieve full info for %s: %s", clean_ticker, e)

        if info and isinstance(info, dict):
            name = info.get("longName") or info.get("shortName") or clean_ticker
            asset_type = info.get("quoteType") or "EQUITY"
            sector = info.get("sector")
            industry = info.get("industry")
            currency = info.get("currency") or "USD"
        else:
            # Fallback to fast_info if available
            fast_info = getattr(t, "fast_info", None)
            currency = (
                fast_info.get("currency")
                if fast_info and hasattr(fast_info, "get")
                else "USD"
            )
            quote_type = (
                getattr(fast_info, "quoteType", "EQUITY")
                if fast_info
                else "EQUITY"
            )
            name = clean_ticker
            asset_type = quote_type or "EQUITY"
            sector = None
            industry = None

        return AssetMetadata(
            ticker=clean_ticker[:16],
            name=str(name)[:128],
            asset_type=str(asset_type).upper()[:32],
            sector=str(sector)[:64] if sector else None,
            industry=str(industry)[:128] if industry else None,
            currency=str(currency).upper()[:3] if currency else "USD",
        )
    except Exception as e:
        logger.warning("Error fetching metadata for %s: %s. Using default metadata.", clean_ticker, e)
        return AssetMetadata(
            ticker=clean_ticker[:16],
            name=clean_ticker,
            asset_type="EQUITY",
            sector=None,
            industry=None,
            currency="USD",
        )


def fetch_market_data(
    tickers: List[str],
    start_date: Union[str, date, datetime],
    end_date: Optional[Union[str, date, datetime]] = None,
) -> pd.DataFrame:
    """Fetch historical OHLCV and adjusted close data from yfinance."""
    if not tickers:
        return pd.DataFrame()

    clean_tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    if not clean_tickers:
        return pd.DataFrame()

    start_str = _format_date(start_date)
    end_str = _format_date(end_date)

    logger.info(
        "Requesting yfinance download for %d ticker(s): %s from %s to %s",
        len(clean_tickers),
        clean_tickers,
        start_str,
        end_str or "latest",
    )

    try:
        df = yf.download(
            clean_tickers,
            start=start_str,
            end=end_str,
            auto_adjust=False,
            progress=False,
        )
        return df
    except Exception as e:
        logger.error("yfinance download exception for tickers %s: %s", clean_tickers, e)
        return pd.DataFrame()
