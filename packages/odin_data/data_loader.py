from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import polars as pl

from odin_data.config import settings
from odin_data.parquet_store import ParquetStore
from odin_data.postgres_store import PostgresStore
from odin_data.questdb import QuestDBClient
from odin_data.redis_cache import RedisCache
from odin_data.schema import validate_ohlc


@dataclass
class LoadStats:
    tier: str = "none"
    rows: int = 0
    latency_ms: float = 0.0
    cache_hit: bool = False


@dataclass
class DataLoader:
    parquet: ParquetStore = field(default_factory=ParquetStore)
    postgres: PostgresStore = field(default_factory=PostgresStore)
    redis: RedisCache = field(default_factory=RedisCache)
    questdb: QuestDBClient = field(default_factory=QuestDBClient)

    def load_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        use_redis: bool | None = None,
        use_questdb: bool | None = None,
    ) -> tuple[pl.DataFrame, LoadStats]:
        import time

        use_redis = settings.use_redis if use_redis is None else use_redis
        use_questdb = settings.use_questdb if use_questdb is None else use_questdb
        use_postgres = settings.use_postgres
        start_s = start.isoformat()
        end_s = end.isoformat()
        t0 = time.perf_counter()

        if use_redis and self.redis.available:
            key = self.redis.ohlc_key(symbol, timeframe, start_s, end_s)
            cached = self.redis.get_frame(key)
            if cached is not None and not cached.is_empty():
                stats = LoadStats(tier="redis", rows=cached.height, latency_ms=(time.perf_counter() - t0) * 1000, cache_hit=True)
                return validate_ohlc(cached), stats

        if use_postgres and self.postgres.ping():
            frame = self.postgres.read_ohlc(symbol, timeframe, start, end, settings.default_series)
            if frame is not None:
                if use_redis and self.redis.available:
                    key = self.redis.ohlc_key(symbol, timeframe, start_s, end_s)
                    self.redis.set_frame(key, frame)
                stats = LoadStats(
                    tier="postgres",
                    rows=frame.height,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
                return validate_ohlc(frame), stats

        frame = self.parquet.read_ohlc(symbol, timeframe, start, end)
        if frame is not None:
            if use_redis and self.redis.available:
                key = self.redis.ohlc_key(symbol, timeframe, start_s, end_s)
                self.redis.set_frame(key, frame)
            stats = LoadStats(tier="parquet", rows=frame.height, latency_ms=(time.perf_counter() - t0) * 1000)
            return frame, stats

        if use_questdb and self.questdb.ping():
            frame = self.questdb.fetch_ohlc(symbol, start, end, timeframe)
            if not frame.is_empty():
                self._writeback_months(symbol, timeframe, frame)
                if use_postgres and self.postgres.ping():
                    self.postgres.upsert_ohlc(frame, symbol, timeframe, settings.default_series, source="questdb")
                if use_redis and self.redis.available:
                    key = self.redis.ohlc_key(symbol, timeframe, start_s, end_s)
                    self.redis.set_frame(key, frame)
                stats = LoadStats(tier="questdb", rows=frame.height, latency_ms=(time.perf_counter() - t0) * 1000)
                return frame, stats

        frame = self._load_csv_fallback(symbol, start, end, timeframe)
        if not frame.is_empty():
            self._writeback_months(symbol, timeframe, frame)
            if use_postgres and self.postgres.ping():
                self.postgres.upsert_ohlc(frame, symbol, timeframe, settings.default_series, source="csv")
            if use_redis and self.redis.available:
                key = self.redis.ohlc_key(symbol, timeframe, start_s, end_s)
                self.redis.set_frame(key, frame)
        stats = LoadStats(
            tier="csv" if not frame.is_empty() else "none",
            rows=frame.height,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        return frame, stats

    def _writeback_months(self, symbol: str, timeframe: str, frame: pl.DataFrame) -> None:
        if frame.is_empty():
            return
        frame = validate_ohlc(frame)
        months = frame.with_columns(pl.col("timestamp").dt.strftime("%Y-%m").alias("month"))
        for month in months["month"].unique().sort():
            month_df = frame.filter(pl.col("timestamp").dt.strftime("%Y-%m") == month)
            self.parquet.write_ohlc_month(symbol, timeframe, month, month_df)
        self.parquet.rebuild_catalog(symbol, timeframe)

    def _load_csv_fallback(self, symbol: str, start: datetime, end: datetime, timeframe: str) -> pl.DataFrame:
        path = settings.raw_csv_path
        if not path.exists():
            return validate_ohlc(pl.DataFrame())

        frame = pl.read_csv(path, try_parse_dates=True)
        if "timestamp" not in frame.columns:
            return validate_ohlc(pl.DataFrame())

        frame = (
            frame.filter(pl.col("symbol") == symbol)
            .with_columns(pl.col("timestamp").cast(pl.Datetime(time_unit="us", time_zone="UTC")))
            .filter(pl.col("timestamp") >= start)
            .filter(pl.col("timestamp") < end)
            .sort("timestamp")
        )
        if timeframe == "5m" and not frame.is_empty():
            frame = self._resample_to_5m(frame)
        return validate_ohlc(frame) if not frame.is_empty() else validate_ohlc(pl.DataFrame())

    @staticmethod
    def _resample_to_5m(frame: pl.DataFrame) -> pl.DataFrame:
        return (
            frame.group_by_dynamic("timestamp", every="5m")
            .agg(
                pl.col("open").first(),
                pl.col("high").max(),
                pl.col("low").min(),
                pl.col("close").last(),
                pl.col("volume").sum(),
            )
            .sort("timestamp")
        )

    @staticmethod
    def default_range(days: int = 365) -> tuple[datetime, datetime]:
        end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days)
        return start, end
