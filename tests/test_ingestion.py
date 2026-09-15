"""Tests for market data normalization, validation, deduplication, and database upserts."""

from datetime import date
from decimal import Decimal
import pandas as pd
import pytest
from sqlalchemy import text

from agent.data.normalization import normalize_market_data
from agent.data.schemas import AssetMetadata, MarketPriceRecord
from agent.data.validation import validate_and_deduplicate, validate_record
from agent.data.ingestion import upsert_assets, upsert_market_prices
from agent.db import get_db_session
from agent.db.models import Asset, MarketPrice


class TestNormalization:
    """Test normalization of various DataFrame shapes."""

    def test_multiindex_dataframe_normalization(self):
        """Test standard yf.download MultiIndex (Price, Ticker) format."""
        dates = pd.to_datetime(["2025-01-02", "2025-01-03"])
        cols = pd.MultiIndex.from_tuples(
            [
                ("Adj Close", "SPY"),
                ("Close", "SPY"),
                ("High", "SPY"),
                ("Low", "SPY"),
                ("Open", "SPY"),
                ("Volume", "SPY"),
                ("Adj Close", "AAPL"),
                ("Close", "AAPL"),
                ("High", "AAPL"),
                ("Low", "AAPL"),
                ("Open", "AAPL"),
                ("Volume", "AAPL"),
            ],
            names=["Price", "Ticker"],
        )
        data = [
            [574.8, 584.6, 591.1, 580.5, 589.4, 50000000, 242.1, 243.8, 245.0, 241.0, 244.0, 40000000],
            [582.0, 592.0, 592.6, 586.4, 587.5, 38000000, 241.6, 243.2, 244.5, 240.5, 243.0, 35000000],
        ]
        df = pd.DataFrame(data, index=dates, columns=cols)
        df.index.name = "Date"

        records = normalize_market_data(df)
        assert len(records) == 4

        tickers = {r["ticker"] for r in records}
        assert tickers == {"SPY", "AAPL"}

        dates_res = {r["price_date"] for r in records}
        assert date(2025, 1, 2) in dates_res
        assert date(2025, 1, 3) in dates_res

        # Check fields of one record
        spy_rec = next(r for r in records if r["ticker"] == "SPY" and r["price_date"] == date(2025, 1, 2))
        assert spy_rec["close_price"] == 584.6
        assert spy_rec["adj_close"] == 574.8
        assert spy_rec["volume"] == 50000000

    def test_flat_dataframe_normalization(self):
        """Test single-level DataFrame with default_ticker."""
        dates = pd.to_datetime(["2025-01-02", "2025-01-03"])
        df = pd.DataFrame(
            {
                "Open": [100.0, 102.0],
                "High": [105.0, 107.0],
                "Low": [99.0, 101.0],
                "Close": [104.0, 106.0],
                "Adj Close": [103.5, 105.5],
                "Volume": [100000, 150000],
            },
            index=dates,
        )
        df.index.name = "Date"

        records = normalize_market_data(df, default_ticker="MSFT")
        assert len(records) == 2
        assert records[0]["ticker"] == "MSFT"
        assert records[0]["price_date"] == date(2025, 1, 2)
        assert records[0]["close_price"] == 104.0

    def test_empty_dataframe(self):
        """Test that empty or None DataFrame returns empty list."""
        assert normalize_market_data(pd.DataFrame()) == []
        assert normalize_market_data(None) == []


class TestValidationAndDeduplication:
    """Test validation rules and duplicate prevention."""

    def test_valid_record(self):
        raw = {
            "ticker": "spy",
            "price_date": date(2025, 1, 2),
            "open_price": 589.39,
            "high_price": 591.13,
            "low_price": 580.50,
            "close_price": 584.64,
            "adj_close": 574.80,
            "volume": 50204000,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is True
        assert reason is None
        assert rec.ticker == "SPY"
        assert rec.close_price == Decimal("584.6400")
        assert rec.volume == 50204000

    def test_negative_close_price(self):
        raw = {
            "ticker": "SPY",
            "price_date": date(2025, 1, 2),
            "close_price": -10.50,
            "adj_close": 574.80,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "Close price must be positive" in reason

    def test_zero_close_price(self):
        raw = {
            "ticker": "SPY",
            "price_date": date(2025, 1, 2),
            "close_price": 0.0,
            "adj_close": 0.0,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "Close price must be positive" in reason

    def test_invalid_date(self):
        raw = {
            "ticker": "SPY",
            "price_date": "not-a-date",
            "close_price": 100.0,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "Invalid or missing date" in reason

    def test_missing_ticker(self):
        raw = {
            "ticker": "",
            "price_date": date(2025, 1, 2),
            "close_price": 100.0,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "Ticker is missing or empty" in reason

    def test_high_less_than_low(self):
        raw = {
            "ticker": "SPY",
            "price_date": date(2025, 1, 2),
            "open_price": 100.0,
            "high_price": 95.0,
            "low_price": 105.0,
            "close_price": 100.0,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "cannot be less than low price" in reason

    def test_negative_volume(self):
        raw = {
            "ticker": "SPY",
            "price_date": date(2025, 1, 2),
            "close_price": 100.0,
            "volume": -500,
        }
        is_valid, reason, rec = validate_record(raw)
        assert is_valid is False
        assert "Volume must be non-negative" in reason

    def test_duplicate_handling(self):
        """Ensure duplicate (ticker, price_date) pairs are detected and prevented."""
        raw_rows = [
            {
                "ticker": "SPY",
                "price_date": date(2025, 1, 2),
                "close_price": 584.0,
                "adj_close": 574.0,
            },
            {
                "ticker": "SPY",
                "price_date": date(2025, 1, 2),  # Duplicate date for same ticker
                "close_price": 585.0,
                "adj_close": 575.0,
            },
            {
                "ticker": "SPY",
                "price_date": date(2025, 1, 3),
                "close_price": 591.0,
                "adj_close": 581.0,
            },
        ]
        result = validate_and_deduplicate(raw_rows)
        assert len(result.valid_records) == 2
        assert result.duplicates_removed == 1
        assert len(result.validation_failures) == 0


class TestDatabaseUpsert:
    """Test PostgreSQL database upsert behavior."""

    @pytest.fixture(autouse=True)
    def cleanup_test_data(self):
        """Clean up test records before and after each test."""
        test_ticker = "TEST_ASSET"
        with get_db_session() as session:
            session.execute(text(f"DELETE FROM market_prices WHERE ticker = '{test_ticker}';"))
            session.execute(text(f"DELETE FROM assets WHERE ticker = '{test_ticker}';"))

        yield

        with get_db_session() as session:
            session.execute(text(f"DELETE FROM market_prices WHERE ticker = '{test_ticker}';"))
            session.execute(text(f"DELETE FROM assets WHERE ticker = '{test_ticker}';"))

    def test_upsert_idempotency_and_update(self):
        """Test inserting records and then re-upserting with updated values."""
        test_ticker = "TEST_ASSET"

        with get_db_session() as session:
            # 1. Upsert parent asset
            asset = AssetMetadata(
                ticker=test_ticker,
                name="Test Asset Corp",
                asset_type="EQUITY",
                currency="USD",
            )
            upsert_assets([asset], session)

            # 2. First insert: 2 rows
            r1 = MarketPriceRecord(
                ticker=test_ticker,
                price_date=date(2025, 1, 2),
                open_price=Decimal("100.0000"),
                high_price=Decimal("105.0000"),
                low_price=Decimal("98.0000"),
                close_price=Decimal("102.5000"),
                adj_close=Decimal("102.5000"),
                volume=10000,
            )
            r2 = MarketPriceRecord(
                ticker=test_ticker,
                price_date=date(2025, 1, 3),
                open_price=Decimal("102.5000"),
                high_price=Decimal("108.0000"),
                low_price=Decimal("101.0000"),
                close_price=Decimal("107.0000"),
                adj_close=Decimal("107.0000"),
                volume=12000,
            )

            ins, upd = upsert_market_prices([r1, r2], session)
            assert ins == 2
            assert upd == 0

            # Verify rows in DB
            rows = session.query(MarketPrice).filter(MarketPrice.ticker == test_ticker).all()
            assert len(rows) == 2

            # 3. Second run: Re-upsert with updated close price on same dates
            r1_mod = MarketPriceRecord(
                ticker=test_ticker,
                price_date=date(2025, 1, 2),
                open_price=Decimal("100.0000"),
                high_price=Decimal("105.0000"),
                low_price=Decimal("98.0000"),
                close_price=Decimal("103.7500"),  # Updated close price
                adj_close=Decimal("103.7500"),
                volume=15000,
            )
            r2_mod = MarketPriceRecord(
                ticker=test_ticker,
                price_date=date(2025, 1, 3),
                open_price=Decimal("102.5000"),
                high_price=Decimal("108.0000"),
                low_price=Decimal("101.0000"),
                close_price=Decimal("109.2500"),  # Updated close price
                adj_close=Decimal("109.2500"),
                volume=18000,
            )

            ins2, upd2 = upsert_market_prices([r1_mod, r2_mod], session)
            assert ins2 == 0
            assert upd2 == 2

            # Verify no duplicates were created
            rows_after = session.query(MarketPrice).filter(MarketPrice.ticker == test_ticker).all()
            assert len(rows_after) == 2

            # Verify updated price took effect
            updated_p1 = session.query(MarketPrice).filter(
                MarketPrice.ticker == test_ticker,
                MarketPrice.price_date == date(2025, 1, 2)
            ).one()
            assert updated_p1.close_price == Decimal("103.7500")
            assert updated_p1.volume == 15000
