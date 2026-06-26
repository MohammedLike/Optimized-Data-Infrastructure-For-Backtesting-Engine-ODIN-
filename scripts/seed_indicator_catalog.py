"""Seed StrykeX indicator catalog and quant rule templates into PostgreSQL."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.postgres_store import PostgresStore
from odin_indicators.strykex_catalog import indicator_count, load_catalog, rule_count


def main() -> None:
    store = PostgresStore()
    if not store.ping():
        raise SystemExit(
            "PostgreSQL unavailable. Run:\n"
            "  docker compose -f infra/docker-compose.yml up -d postgres\n"
            "  python scripts/init_database.py"
        )

    store.init_schema()
    result = store.seed_indicator_catalog()
    stats = store.catalog_stats()

    print(f"Catalog source: {indicator_count()} indicators, {rule_count()} rules")
    print(f"Seeded: {result['indicators']} indicators, {result['rules']} rules")
    print(f"Database totals: {stats['indicators']} indicators, {stats['rules']} rules ({stats['implemented']} implemented)")

    # Sample output for RSI
    rsi = store.get_indicator_rules("rsi")
    if rsi is not None:
        print("\nSample — RSI entry/exit rules:")
        for row in rsi.iter_rows(named=True):
            print(f"  [{row['rule_purpose']}] {row['rule_name']}: {row['logic_notes']}")


if __name__ == "__main__":
    main()
