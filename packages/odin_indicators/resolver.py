from dataclasses import dataclass
from datetime import datetime
from typing import Any

import polars as pl

from odin_data.redis_cache import RedisCache
from odin_indicators.compute import compute_indicator, load_registry


@dataclass
class IndicatorResolver:
    redis: RedisCache
    symbol: str
    timeframe: str

    def resolve(
        self,
        name: str,
        ohlc: pl.DataFrame,
        start: datetime,
        end: datetime,
        precomputed: pl.DataFrame | None = None,
        params: dict[str, Any] | None = None,
        use_redis: bool = True,
    ) -> pl.Series:
        registry = load_registry()
        key_name = name if name in registry else self._map_strykex_name(name)
        start_s = start.isoformat()
        end_s = end.isoformat()
        resolved_params = {**registry.get(key_name, {}).get("params", {}), **(params or {})}

        if use_redis and self.redis.available:
            cache_key = self.redis.indicator_key(self.symbol, self.timeframe, key_name, resolved_params, start_s, end_s)
            cached = self.redis.get_frame(cache_key)
            if cached is not None and key_name in cached.columns:
                return self._join_series(ohlc, cached, key_name)

        if precomputed is not None and key_name in precomputed.columns:
            series = self._join_series(ohlc, precomputed, key_name)
        else:
            series = compute_indicator(ohlc, key_name, resolved_params)

        if use_redis and self.redis.available:
            cache_key = self.redis.indicator_key(self.symbol, self.timeframe, key_name, resolved_params, start_s, end_s)
            self.redis.set_frame(
                cache_key,
                pl.DataFrame({"timestamp": ohlc["timestamp"], key_name: series}),
            )

        return series

    @staticmethod
    def _join_series(ohlc: pl.DataFrame, source: pl.DataFrame, column: str) -> pl.Series:
        merged = ohlc.select("timestamp").join(
            source.select("timestamp", column),
            on="timestamp",
            how="left",
        )
        return merged[column].fill_null(strategy="forward").fill_null(0.0)

    @staticmethod
    def _map_strykex_name(name: str) -> str:
        normalized = name.lower().replace(" ", "_")
        mapping = {
            "current_close": "current_close",
            "rsi": "rsi_14",
            "ema_20": "ema_20",
            "ema_9": "ema_9",
        }
        return mapping.get(normalized, normalized)
