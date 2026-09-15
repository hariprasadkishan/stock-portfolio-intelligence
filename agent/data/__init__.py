"""Data ingestion and normalization package for Stock Portfolio Intelligence."""

from agent.data.fetcher import fetch_asset_metadata, fetch_market_data
from agent.data.ingestion import ingest_market_data, upsert_assets, upsert_market_prices
from agent.data.normalization import normalize_market_data
from agent.data.schemas import (
    AssetMetadata,
    IngestionSummary,
    MarketPriceRecord,
    ValidationResult,
)
from agent.data.validation import validate_and_deduplicate, validate_record

__all__ = [
    "fetch_asset_metadata",
    "fetch_market_data",
    "normalize_market_data",
    "validate_record",
    "validate_and_deduplicate",
    "upsert_assets",
    "upsert_market_prices",
    "ingest_market_data",
    "AssetMetadata",
    "MarketPriceRecord",
    "ValidationResult",
    "IngestionSummary",
]
