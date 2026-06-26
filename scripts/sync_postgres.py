"""Sync OHLC + indicators from Parquet (or QuestDB) into PostgreSQL."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

import polars as pl

from odin_data.config import settings
from odin_data.data_loader import DataLoader
from odin_data.parquet_store import ParquetStore
from odin_data.postgres_store import PostgresStore
from odin_indicators.compute import precompute_all


def sync_from_parquet(symbol: str, timeframe: str) -> None:
    store = ParquetStore()
    postgres = PostgresStore()
    catalog = store.catalog.get_range(symbol, timeframe)
    if catalog[0] is None or catalog[1] is None:
        raise SystemExit(f"No Parquet catalog for {symbol}/{timeframe}. Run scripts/seed_data.py first.")

    start, end = catalog
    ohlc = store.read_ohlc(symbol, timeframe, start, end)
    if ohlc is None or ohlc.is_empty():
        raise SystemExit(f"No OHLC Parquet data for {symbol}/{timeframe}")

    source = "questdb" if settings.use_questdb else "csv"
    ohlc_rows = postgres.upsert_ohlc(ohlc, symbol, timeframe, settings.default_series, source=source)
    print(f"Upserted {ohlc_rows} OHLC rows")

    indicators = store.read_indicators(symbol, timeframe, start, end)
    if indicators is None or indicators.is_empty():
        print("No indicator Parquet found; computing from OHLC...")
        computed = precompute_all(ohlc)
        indicators = ohlc.join(computed, on="timestamp", how="left")

    indicator_rows = postgres.upsert_indicators(indicators, symbol, timeframe)
    print(f"Upserted {indicator_rows} indicator rows")

    counts = postgres.row_counts(symbol, timeframe)
    print(f"PostgreSQL totals: {counts}")


def sync_from_questdb(symbol: str, timeframe: str, days_back: int = 365 * 5) -> None:
    from datetime import timedelta

    loader = DataLoader()
    postgres = PostgresStore()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)

    if not loader.questdb.ping():
        raise SystemExit("QuestDB is not reachable. Set USE_QUESTDB=true and verify QUESTDB_HOST/PORT.")

    ohlc = loader.questdb.fetch_ohlc(symbol, start, end, timeframe)
    if ohlc.is_empty():
        raise SystemExit(f"No QuestDB rows for {symbol}/{timeframe}")

    ohlc_rows = postgres.upsert_ohlc(ohlc, symbol, timeframe, settings.default_series, source="questdb")
    print(f"Upserted {ohlc_rows} OHLC rows from QuestDB")

    computed = precompute_all(ohlc)
    indicators = ohlc.join(computed, on="timestamp", how="left")
    indicator_rows = postgres.upsert_indicators(indicators, symbol, timeframe)
    print(f"Upserted {indicator_rows} indicator rows")

    counts = postgres.row_counts(symbol, timeframe)
    print(f"PostgreSQL totals: {counts}")


def main() -> None:
    symbol = settings.default_symbol
    timeframe = settings.default_timeframe
    postgres = PostgresStore()
    if not postgres.ping():
        raise SystemExit("PostgreSQL unavailable. Run scripts/init_database.py after starting postgres.")

    postgres.init_schema()

    if settings.use_questdb:
        sync_from_questdb(symbol, timeframe)
    else:
        sync_from_parquet(symbol, timeframe)


if __name__ == "__main__":
    main()
