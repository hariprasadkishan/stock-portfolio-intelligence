"""Data transfer objects and schemas for market data ingestion."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class MarketPriceRecord:
    """Validated market price row ready for database persistence."""

    ticker: str
    price_date: date
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Decimal
    adj_close: Decimal
    volume: Optional[int]


@dataclass(frozen=True)
class AssetMetadata:
    """Metadata for an asset (equity, ETF, index)."""

    ticker: str
    name: str
    asset_type: str = "EQUITY"
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"


@dataclass
class ValidationResult:
    """Result of record validation and deduplication."""

    valid_records: List[MarketPriceRecord] = field(default_factory=list)
    validation_failures: List[str] = field(default_factory=list)
    duplicates_removed: int = 0


@dataclass
class IngestionSummary:
    """Comprehensive summary of an ingestion run."""

    tickers_requested: List[str]
    successful_tickers: List[str] = field(default_factory=list)
    failed_tickers: List[str] = field(default_factory=list)
    rows_fetched: int = 0
    rows_valid: int = 0
    rows_invalid: int = 0
    rows_inserted: int = 0
    rows_updated_or_skipped: int = 0
    duplicates_prevented: int = 0
    validation_failures: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
