"""Run nightly ETL: export OHLC, precompute indicators, invalidate Redis cache."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.config import settings
from odin_data.redis_cache import RedisCache
from services.nightly_etl.export import export_nifty_5m
from services.nightly_etl.precompute import precompute_nifty_5m


def main() -> None:
    print("=== ODIN Nightly ETL ===")
    export_nifty_5m()
    precompute_nifty_5m()

    cache = RedisCache()
    if cache.available:
        deleted = cache.invalidate_prefix(f"ohlc:{settings.default_symbol}:{settings.default_timeframe}:")
        deleted += cache.invalidate_prefix(f"ind:{settings.default_symbol}:{settings.default_timeframe}:")
        print(f"Invalidated {deleted} Redis keys")
    else:
        print("Redis unavailable — skip cache invalidation")

    print("Nightly ETL complete.")


if __name__ == "__main__":
    main()
