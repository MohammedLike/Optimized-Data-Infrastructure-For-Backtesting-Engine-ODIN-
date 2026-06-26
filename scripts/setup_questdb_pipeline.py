"""QuestDB-first pipeline: import OHLC → Parquet cache → indicators → PostgreSQL (indicators only)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from odin_data.config import settings
from odin_data.postgres_store import PostgresStore
from odin_data.questdb import QuestDBClient
from services.nightly_etl.export import csv_sample_range, export_nifty_5m
from services.nightly_etl.precompute import precompute_nifty_5m


def main() -> None:
    symbol = settings.default_symbol
    timeframe = settings.default_timeframe

    questdb = QuestDBClient()
    if not questdb.ping():
        raise SystemExit(
            "QuestDB is not reachable. Run:\n"
            "  docker compose -f infra/docker-compose.yml up -d questdb postgres"
        )

    print("1/5 Import sample CSV into QuestDB...")
    from import_csv_to_questdb import main as import_main

    import_main()

    print("\n2/5 Clear legacy OHLC rows from PostgreSQL...")
    postgres = PostgresStore()
    if postgres.ping():
        postgres.init_schema()
        cleared = postgres.clear_ohlc(symbol, timeframe)
        print(f"  Removed {cleared} rows from odin.ohlc_bars")
    else:
        print("  PostgreSQL not running — skipped")

    start, end = csv_sample_range()
    print(f"\n3/5 Export QuestDB to Parquet ({start.date()} to {end.date()})...")
    export_nifty_5m(start=start, end=end)

    print("\n4/5 Precompute indicators to Parquet...")
    precompute_nifty_5m()

    print("\n5/5 Sync indicators to PostgreSQL...")
    if postgres.ping():
        from sync_postgres import sync_indicators

        sync_indicators(symbol, timeframe)
    else:
        print("  PostgreSQL not running — skipped")

    q_rows = questdb.row_count(symbol=symbol, timeframe=timeframe)
    print(f"\nDone. QuestDB OHLC rows: {q_rows}")
    if postgres.ping():
        counts = postgres.row_counts(symbol, timeframe)
        print(f"PostgreSQL: ohlc={counts['ohlc']} (expected 0), indicators={counts['indicators']}")


if __name__ == "__main__":
    main()
