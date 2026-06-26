"""Sync precomputed indicators from Parquet into PostgreSQL (OHLC stays in QuestDB)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.config import settings
from odin_data.parquet_store import ParquetStore
from odin_data.postgres_store import PostgresStore
from odin_indicators.compute import precompute_all


def sync_indicators(symbol: str, timeframe: str) -> None:
    store = ParquetStore()
    postgres = PostgresStore()
    catalog = store.catalog.get_range(symbol, timeframe)
    if catalog[0] is None or catalog[1] is None:
        raise SystemExit(f"No Parquet catalog for {symbol}/{timeframe}. Run export + precompute first.")

    start, end = catalog
    indicators = store.read_indicators(symbol, timeframe, start, end)
    if indicators is None or indicators.is_empty():
        ohlc = store.read_ohlc(symbol, timeframe, start, end)
        if ohlc is None or ohlc.is_empty():
            raise SystemExit(f"No Parquet OHLC for {symbol}/{timeframe}")
        print("No indicator Parquet found; computing from OHLC...")
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
    sync_indicators(symbol, timeframe)


if __name__ == "__main__":
    main()
