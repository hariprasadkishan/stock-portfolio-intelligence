"""Validation and deduplication rules for normalized market data records."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple
import math
import pandas as pd

from agent.data.schemas import MarketPriceRecord, ValidationResult


def _to_decimal(val: Any) -> Optional[Decimal]:
    """Safely convert numeric value or float to Decimal rounded to 4 decimal places."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if pd.isna(val):
        return None
    try:
        # Convert float/int/str through rounded float to avoid representation artifacts
        flt = float(val)
        return Decimal(f"{flt:.4f}")
    except (ValueError, TypeError, InvalidOperation):
        return None


def _to_int(val: Any) -> Optional[int]:
    """Safely convert value to non-negative integer or None."""
    if val is None or pd.isna(val):
        return None
    try:
        flt = float(val)
        if math.isnan(flt) or math.isinf(flt):
            return None
        return int(round(flt))
    except (ValueError, TypeError):
        return None


def validate_record(raw: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[MarketPriceRecord]]:
    """Validate a single raw price dictionary.
    
    Returns:
        (is_valid, failure_reason, validated_record)
    """
    ticker = raw.get("ticker")
    if not ticker or not isinstance(ticker, str) or not ticker.strip():
        return False, "Ticker is missing or empty", None
    ticker = ticker.strip().upper()
    if len(ticker) > 16:
        return False, f"Ticker '{ticker}' exceeds maximum length of 16 characters", None

    price_date = raw.get("price_date")
    if not price_date or not isinstance(price_date, date):
        return False, f"Invalid or missing date for ticker '{ticker}': {price_date}", None

    # Close price validation (Mandatory, positive)
    close_dec = _to_decimal(raw.get("close_price"))
    if close_dec is None or close_dec <= 0:
        return False, f"Close price must be positive for {ticker} on {price_date}: got {raw.get('close_price')}", None

    # Adjusted close price validation (Mandatory in schema, positive)
    adj_dec = _to_decimal(raw.get("adj_close"))
    if adj_dec is None:
        adj_dec = close_dec
    if adj_dec <= 0:
        return False, f"Adjusted close must be positive for {ticker} on {price_date}: got {adj_dec}", None

    # Volume validation (Optional, non-negative if present)
    vol = _to_int(raw.get("volume"))
    if vol is not None and vol < 0:
        return False, f"Volume must be non-negative for {ticker} on {price_date}: got {vol}", None

    # Optional OHLC validations
    open_dec = _to_decimal(raw.get("open_price"))
    if open_dec is not None and open_dec <= 0:
        return False, f"Open price must be positive for {ticker} on {price_date}: got {open_dec}", None

    high_dec = _to_decimal(raw.get("high_price"))
    low_dec = _to_decimal(raw.get("low_price"))

    if low_dec is not None and low_dec <= 0:
        return False, f"Low price must be positive for {ticker} on {price_date}: got {low_dec}", None

    if high_dec is not None and low_dec is not None and high_dec < low_dec:
        return (
            False,
            f"High price ({high_dec}) cannot be less than low price ({low_dec}) for {ticker} on {price_date}",
            None,
        )

    record = MarketPriceRecord(
        ticker=ticker,
        price_date=price_date,
        open_price=open_dec,
        high_price=high_dec,
        low_price=low_dec,
        close_price=close_dec,
        adj_close=adj_dec,
        volume=vol,
    )
    return True, None, record


def validate_and_deduplicate(raw_records: List[Dict[str, Any]]) -> ValidationResult:
    """Validate a list of raw records and prevent duplicates on (ticker, price_date)."""
    valid_records: List[MarketPriceRecord] = []
    failures: List[str] = []
    seen_keys: Set[Tuple[str, date]] = set()
    duplicates_removed = 0

    for raw in raw_records:
        is_valid, reason, record = validate_record(raw)
        if not is_valid or record is None:
            failures.append(reason or "Unknown validation error")
            continue

        key = (record.ticker, record.price_date)
        if key in seen_keys:
            duplicates_removed += 1
            continue

        seen_keys.add(key)
        valid_records.append(record)

    return ValidationResult(
        valid_records=valid_records,
        validation_failures=failures,
        duplicates_removed=duplicates_removed,
    )
