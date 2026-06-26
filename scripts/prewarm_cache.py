"""Prewarm RAM + Redis after nightly ETL so every user's first backtest is fast."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT))

from odin_data.config import settings
from odin_data.prewarm import prewarm_defaults, warmup_backtest, warmup_numba_engine


def main() -> None:
    results = prewarm_defaults()
    if not results:
        raise SystemExit(
            "Nothing prewarmed. Run export + precompute first:\n"
            "  python -m services.nightly_etl.export\n"
            "  python -m services.nightly_etl.precompute"
        )
    warmup_backtest()
    print(f"Prewarmed {len(results)} slice(s) for {settings.default_symbol}/{settings.default_timeframe}:")
    for r in results:
        print(f"  {r.days}d - {r.ohlc_rows} OHLC rows, {r.indicator_rows} indicator rows -> {', '.join(r.tiers)}")


if __name__ == "__main__":
    main()
