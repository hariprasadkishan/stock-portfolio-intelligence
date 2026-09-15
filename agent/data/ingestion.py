"""Market data ingestion orchestration into PostgreSQL."""

from datetime import date, datetime
import logging
from typing import List, Optional, Set, Tuple, Union
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from agent.db import get_db_session
from agent.db.models import Asset, MarketPrice
from agent.data.fetcher import fetch_asset_metadata, fetch_market_data
from agent.data.normalization import normalize_market_data
from agent.data.schemas import AssetMetadata, IngestionSummary, MarketPriceRecord
from agent.data.validation import validate_and_deduplicate

logger = logging.getLogger("agent.data.ingestion")


def upsert_assets(assets: List[AssetMetadata], session: Session) -> int:
    """Upsert asset metadata rows into the assets table."""
    if not assets:
        return 0

    values = [
        {
            "ticker": a.ticker,
            "name": a.name,
            "asset_type": a.asset_type,
            "sector": a.sector,
            "industry": a.industry,
            "currency": a.currency,
        }
        for a in assets
    ]

    stmt = insert(Asset).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker"],
        set_={
            "name": stmt.excluded.name,
            "asset_type": stmt.excluded.asset_type,
            "sector": stmt.excluded.sector,
            "industry": stmt.excluded.industry,
            "currency": stmt.excluded.currency,
        },
    )

    session.execute(stmt)
    session.flush()
    session.expire_all()
    return len(values)


def upsert_market_prices(
    records: List[MarketPriceRecord], session: Session
) -> Tuple[int, int]:
    """Upsert market price records into market_prices table.
    
    Returns:
        (rows_inserted, rows_updated_or_skipped)
    """
    if not records:
        return 0, 0

    tickers = list({r.ticker for r in records})
    min_date = min(r.price_date for r in records)
    max_date = max(r.price_date for r in records)

    existing_rows = session.query(MarketPrice.ticker, MarketPrice.price_date).filter(
        MarketPrice.ticker.in_(tickers),
        MarketPrice.price_date >= min_date,
        MarketPrice.price_date <= max_date,
    ).all()
    existing_keys: Set[Tuple[str, date]] = set(existing_rows)

    updated_count = sum(1 for r in records if (r.ticker, r.price_date) in existing_keys)
    inserted_count = len(records) - updated_count

    values = [
        {
            "ticker": r.ticker,
            "price_date": r.price_date,
            "open_price": r.open_price,
            "high_price": r.high_price,
            "low_price": r.low_price,
            "close_price": r.close_price,
            "adj_close": r.adj_close,
            "volume": r.volume,
        }
        for r in records
    ]

    stmt = insert(MarketPrice).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "price_date"],
        set_={
            "open_price": stmt.excluded.open_price,
            "high_price": stmt.excluded.high_price,
            "low_price": stmt.excluded.low_price,
            "close_price": stmt.excluded.close_price,
            "adj_close": stmt.excluded.adj_close,
            "volume": stmt.excluded.volume,
        },
    )

    session.execute(stmt)
    session.flush()
    session.expire_all()
    return inserted_count, updated_count


def ingest_market_data(
    tickers: Union[str, List[str]],
    start_date: Union[str, date, datetime],
    end_date: Optional[Union[str, date, datetime]] = None,
    session: Optional[Session] = None,
) -> IngestionSummary:
    """Ingest market data from yfinance into PostgreSQL.
    
    Parameters:
        tickers: Single ticker string or list of ticker strings
        start_date: Earliest date to fetch
        end_date: Latest date to fetch (defaults to today)
        session: Optional SQLAlchemy session. If None, manages its own transaction.
    """
    if isinstance(tickers, str):
        tickers_list = [tickers.strip().upper()]
    else:
        tickers_list = [t.strip().upper() for t in tickers if t and t.strip()]

    summary = IngestionSummary(tickers_requested=tickers_list)
    logger.info("Starting ingestion for %d tickers: %s", len(tickers_list), tickers_list)

    if not tickers_list:
        summary.errors.append("No valid ticker symbols provided.")
        return summary

    def _execute_ingestion(db_session: Session):
        # 1. Fetch & upsert asset metadata to satisfy foreign keys
        assets_to_upsert: List[AssetMetadata] = []
        for t in tickers_list:
            meta = fetch_asset_metadata(t)
            assets_to_upsert.append(meta)

        upsert_assets(assets_to_upsert, db_session)
        logger.info("Upserted metadata for %d asset(s)", len(assets_to_upsert))

        # 2. Fetch historical market data from yfinance
        df = fetch_market_data(tickers_list, start_date=start_date, end_date=end_date)
        if df.empty:
            summary.failed_tickers = list(tickers_list)
            msg = f"No market data returned by yfinance for tickers: {tickers_list}"
            logger.warning(msg)
            summary.errors.append(msg)
            return

        # 3. Normalize raw DataFrame into rows
        default_ticker = tickers_list[0] if len(tickers_list) == 1 else None
        raw_rows = normalize_market_data(df, default_ticker=default_ticker)
        summary.rows_fetched = len(raw_rows)
        logger.info("Normalized %d raw row(s) from yfinance payload", len(raw_rows))

        # 4. Validate & deduplicate rows
        val_result = validate_and_deduplicate(raw_rows)
        summary.rows_valid = len(val_result.valid_records)
        summary.rows_invalid = len(val_result.validation_failures)
        summary.duplicates_prevented = val_result.duplicates_removed
        summary.validation_failures = val_result.validation_failures

        if val_result.validation_failures:
            logger.warning(
                "Validation rejected %d row(s): %s",
                len(val_result.validation_failures),
                val_result.validation_failures[:5],
            )

        if not val_result.valid_records:
            summary.failed_tickers = list(tickers_list)
            logger.warning("No valid price rows to insert after validation.")
            return

        # 5. Persist to market_prices table with upsert
        inserted, updated = upsert_market_prices(val_result.valid_records, db_session)
        summary.rows_inserted = inserted
        summary.rows_updated_or_skipped = updated

        # 6. Categorize successful vs failed tickers
        tickers_with_data = {r.ticker for r in val_result.valid_records}
        summary.successful_tickers = sorted(list(tickers_with_data))
        summary.failed_tickers = sorted(list(set(tickers_list) - tickers_with_data))

        # Log comprehensive results
        logger.info(
            "Ingestion completed | Requested: %d | Successful: %s | Failed: %s | "
            "Inserted: %d | Updated/Skipped: %d | Validation Failures: %d | Duplicates Prevented: %d",
            len(summary.tickers_requested),
            summary.successful_tickers,
            summary.failed_tickers,
            summary.rows_inserted,
            summary.rows_updated_or_skipped,
            summary.rows_invalid,
            summary.duplicates_prevented,
        )

    if session is not None:
        _execute_ingestion(session)
    else:
        with get_db_session() as new_session:
            _execute_ingestion(new_session)

    return summary
