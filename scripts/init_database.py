"""Initialize ODIN PostgreSQL schema."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.postgres_store import PostgresStore


def main() -> None:
    store = PostgresStore()
    if not store.ping():
        raise SystemExit(
            "Cannot connect to PostgreSQL. Start it with:\n"
            "  docker compose -f infra/docker-compose.yml up -d postgres  # port 47132\n"
            "Then set DATABASE_URL in .env"
        )
    store.init_schema()
    counts = store.row_counts("NIFTY", "5m")
    catalog = store.catalog_stats()
    print("PostgreSQL schema ready (odin.*)")
    print(f"Current NIFTY/5m rows: OHLC={counts['ohlc']}, indicators={counts['indicators']}, extensions={counts['extensions']}")
    if catalog["indicators"] == 0:
        print("Indicator catalog empty — run: python scripts/seed_indicator_catalog.py")
    else:
        print(f"Indicator catalog: {catalog['indicators']} indicators, {catalog['rules']} rule templates")


if __name__ == "__main__":
    main()
