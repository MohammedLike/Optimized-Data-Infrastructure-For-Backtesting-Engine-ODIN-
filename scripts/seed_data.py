"""Seed Parquet data and indicator files from CSV for local development."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from services.nightly_etl.export import export_nifty_5m
from services.nightly_etl.precompute import precompute_nifty_5m


def main() -> None:
    print("Seeding NIFTY 5m Parquet from CSV...")
    export_nifty_5m(days_back=30)
    print("Precomputing indicators...")
    precompute_nifty_5m()
    print("Done.")


if __name__ == "__main__":
    main()
