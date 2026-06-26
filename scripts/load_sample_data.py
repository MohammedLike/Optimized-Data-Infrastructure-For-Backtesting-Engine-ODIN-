"""Load full questdb-query sample CSV into Parquet, indicators, and PostgreSQL."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

import polars as pl

from odin_data.config import settings
from odin_data.postgres_store import PostgresStore
from services.nightly_etl.export import csv_sample_range, export_nifty_5m
from services.nightly_etl.precompute import precompute_nifty_5m


def main() -> None:
    csv_path = settings.raw_csv_path
    if not csv_path.exists():
        raise SystemExit(f"Sample CSV not found: {csv_path}")

    raw = pl.read_csv(csv_path, try_parse_dates=True)
    start, end = csv_sample_range()
    print(f"Loading sample CSV: {csv_path.name}")
    print(f"  Raw rows: {raw.height} (1m)")
    print(f"  Range: {start.isoformat()} -> {end.isoformat()}")

    print("\n1/3 Exporting NIFTY 5m to Parquet...")
    export_nifty_5m(start=start, end=end)

    print("\n2/3 Precomputing indicators...")
    precompute_nifty_5m()

    print("\n3/3 Syncing to PostgreSQL...")
    postgres = PostgresStore()
    if postgres.ping():
        postgres.init_schema()
        sys.path.insert(0, str(ROOT / "scripts"))
        from sync_postgres import sync_from_parquet

        sync_from_parquet(settings.default_symbol, settings.default_timeframe)
    else:
        print("  PostgreSQL not running — skipped (start with: docker compose -f infra/docker-compose.yml up -d postgres)")

    print("\nDone. Sample data loaded.")


if __name__ == "__main__":
    main()
