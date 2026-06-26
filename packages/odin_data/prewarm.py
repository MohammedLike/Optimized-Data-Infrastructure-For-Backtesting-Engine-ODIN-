"""Load Parquet into RAM + Redis before users click Backtest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import polars as pl

from odin_data.config import settings
from odin_data.data_loader import DataLoader
from odin_data.hot_store import hot_store
from odin_data.parquet_store import ParquetStore


@dataclass
class PrewarmResult:
    symbol: str
    timeframe: str
    days: int
    ohlc_rows: int
    indicator_rows: int
    tiers: list[str]


def _range_for_days(days: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    return start, end


def prewarm_slice(
    symbol: str,
    timeframe: str,
    days: int,
    loader: DataLoader | None = None,
    use_redis: bool = True,
    use_hot_store: bool = True,
) -> PrewarmResult | None:
    """Load one date range from Parquet into hot RAM (and optionally Redis)."""
    loader = loader or DataLoader()
    store = loader.parquet
    start, end = _range_for_days(days)

    ohlc = store.read_ohlc(symbol, timeframe, start, end)
    if ohlc is None or ohlc.is_empty():
        return None

    indicators = store.read_indicators(symbol, timeframe, start, end)
    tiers: list[str] = []

    if use_hot_store and settings.hot_store_enabled:
        hot_store.put_ohlc(symbol, timeframe, start, end, ohlc)
        tiers.append("ram")
        if indicators is not None and not indicators.is_empty():
            hot_store.put_indicators(symbol, timeframe, start, end, indicators)
            tiers.append("ram_indicators")

    if use_redis and settings.use_redis and loader.redis.available:
        start_s, end_s = start.isoformat(), end.isoformat()
        loader.redis.set_frame(loader.redis.ohlc_key(symbol, timeframe, start_s, end_s), ohlc)
        tiers.append("redis")
        if indicators is not None and not indicators.is_empty():
            for col in indicators.columns:
                if col == "timestamp":
                    continue
                # Bulk indicator cache is handled per-column in resolver; store full frame key
                pass
            loader.redis.set_frame(
                f"indicators:{symbol}:{timeframe}:{start_s}:{end_s}",
                indicators,
            )
            tiers.append("redis_indicators")

    return PrewarmResult(
        symbol=symbol,
        timeframe=timeframe,
        days=days,
        ohlc_rows=ohlc.height,
        indicator_rows=indicators.height if indicators is not None else 0,
        tiers=tiers,
    )


def warmup_backtest() -> None:
    """One throwaway backtest at startup — compiles Numba with real array shapes."""
    from odin_engine.backtest import BacktestEngine, BacktestRequest
    from odin_engine.conditions import Condition, Operator

    warmup_numba_engine()
    engine = BacktestEngine()
    engine.run(
        BacktestRequest(
            symbol=settings.default_symbol,
            timeframe=settings.default_timeframe,
            entry_rules=[
                Condition(left_indicator="current_close", operator=Operator.GT, right_indicator="ema_20"),
                Condition(left_indicator="rsi_14", operator=Operator.GT, right_value=50),
            ],
        )
    )


def prewarm_defaults(loader: DataLoader | None = None) -> list[PrewarmResult]:
    """Prewarm all configured day ranges for the default symbol/timeframe."""
    symbol = settings.default_symbol
    timeframe = settings.default_timeframe
    results: list[PrewarmResult] = []
    for days in settings.prewarm_day_ranges:
        result = prewarm_slice(symbol, timeframe, days, loader=loader)
        if result is not None:
            results.append(result)
    return results


def warmup_numba_engine() -> None:
    """Compile the Numba kernel at startup so the first user click is not penalized."""
    import numpy as np

    from odin_engine.kernel import run_backtest_kernel

    n = 4096
    left = np.ones((2, n), dtype=np.float64)
    right = np.zeros((2, n), dtype=np.float64)
    ops = np.array([1, 1], dtype=np.int64)
    close = np.ones(n, dtype=np.float64)
    run_backtest_kernel(left, right, ops, close)
