"""Seed Parquet data and indicator files from CSV for local development."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from services.nightly_etl.export import csv_sample_range, export_nifty_5m
from services.nightly_etl.precompute import precompute_nifty_5m


def main() -> None:
    start, end = csv_sample_range()
    print(f"Seeding NIFTY 5m Parquet from CSV ({start.date()} to {end.date()})...")
    export_nifty_5m(start=start, end=end)
    print("Precomputing indicators...")
    precompute_nifty_5m()
    print("Done.")


if __name__ == "__main__":
    main()
