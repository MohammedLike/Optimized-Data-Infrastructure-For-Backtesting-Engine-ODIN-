"""In-process RAM cache for default backtest slices — makes every user's first click fast."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

import polars as pl


@dataclass
class HotStore:
    """Preloaded OHLC + indicator frames keyed by symbol/timeframe/date range."""

    _ohlc: dict[str, pl.DataFrame] = field(default_factory=dict)
    _indicators: dict[str, pl.DataFrame] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    @staticmethod
    def _key(symbol: str, timeframe: str, start: datetime, end: datetime) -> str:
        return f"{symbol}:{timeframe}:{start.isoformat()}:{end.isoformat()}"

    def put_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        frame: pl.DataFrame,
    ) -> None:
        if frame.is_empty():
            return
        with self._lock:
            self._ohlc[self._key(symbol, timeframe, start, end)] = frame

    def put_indicators(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        frame: pl.DataFrame,
    ) -> None:
        if frame.is_empty():
            return
        with self._lock:
            self._indicators[self._key(symbol, timeframe, start, end)] = frame

    def get_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame | None:
        with self._lock:
            return self._ohlc.get(self._key(symbol, timeframe, start, end))

    def get_indicators(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pl.DataFrame | None:
        with self._lock:
            return self._indicators.get(self._key(symbol, timeframe, start, end))

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._ohlc.keys())

    def clear(self) -> None:
        with self._lock:
            self._ohlc.clear()
            self._indicators.clear()


hot_store = HotStore()
