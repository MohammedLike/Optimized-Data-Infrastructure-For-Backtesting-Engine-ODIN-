from datetime import datetime
from pathlib import Path

import polars as pl

from odin_data.catalog import Catalog
from odin_data.config import settings
from odin_data.schema import validate_ohlc


class ParquetStore:
    def __init__(self, root: Path | None = None, catalog: Catalog | None = None) -> None:
        self.root = root or settings.parquet_dir
        self.catalog = catalog or Catalog()

    def _ohlc_dir(self, symbol: str, timeframe: str) -> Path:
        return self.root / "ohlc" / symbol / timeframe

    def _indicator_dir(self, symbol: str, timeframe: str) -> Path:
        return self.root / "indicators" / symbol / timeframe

    @staticmethod
    def month_key(ts: datetime) -> str:
        return ts.strftime("%Y-%m")

    def ohlc_path(self, symbol: str, timeframe: str, month: str) -> Path:
        return self._ohlc_dir(symbol, timeframe) / f"{month}.parquet"

    def indicator_path(self, symbol: str, timeframe: str, month: str) -> Path:
        return self._indicator_dir(symbol, timeframe) / f"{month}.parquet"

    def write_ohlc_month(self, symbol: str, timeframe: str, month: str, df: pl.DataFrame) -> Path:
        path = self.ohlc_path(symbol, timeframe, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        validate_ohlc(df).write_parquet(path)
        return path

    def write_indicator_month(self, symbol: str, timeframe: str, month: str, df: pl.DataFrame) -> Path:
        path = self.indicator_path(symbol, timeframe, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(path)
        return path

    def list_month_files(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[Path]:
        directory = self._ohlc_dir(symbol, timeframe)
        if not directory.exists():
            return []
        months = set()
        cursor = datetime(start.year, start.month, 1, tzinfo=start.tzinfo)
        while cursor <= end:
            months.add(self.month_key(cursor))
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)
        return [directory / f"{m}.parquet" for m in sorted(months) if (directory / f"{m}.parquet").exists()]

    def read_ohlc(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pl.DataFrame | None:
        files = self.list_month_files(symbol, timeframe, start, end)
        if not files:
            return None
        frame = (
            pl.scan_parquet(files)
            .filter(pl.col("timestamp") >= start)
            .filter(pl.col("timestamp") < end)
            .sort("timestamp")
            .collect()
        )
        if frame.is_empty():
            return None
        return validate_ohlc(frame)

    def read_indicators(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pl.DataFrame | None:
        directory = self._indicator_dir(symbol, timeframe)
        if not directory.exists():
            return None
        ohlc_dir = self._ohlc_dir(symbol, timeframe)
        months = set()
        if ohlc_dir.exists():
            for path in self.list_month_files(symbol, timeframe, start, end):
                months.add(path.stem)
        if not months:
            months = {p.stem for p in directory.glob("*.parquet")}
        files = [directory / f"{m}.parquet" for m in sorted(months) if (directory / f"{m}.parquet").exists()]
        if not files:
            return None
        frame = (
            pl.scan_parquet(files)
            .filter(pl.col("timestamp") >= start)
            .filter(pl.col("timestamp") < end)
            .sort("timestamp")
            .collect()
        )
        return frame if not frame.is_empty() else None

    def rebuild_catalog(self, symbol: str, timeframe: str) -> None:
        directory = self._ohlc_dir(symbol, timeframe)
        if not directory.exists():
            return
        months = sorted(p.stem for p in directory.glob("*.parquet"))
        if not months:
            return
        frames = [pl.read_parquet(directory / f"{m}.parquet") for m in months]
        combined = pl.concat(frames).sort("timestamp")
        self.catalog.update_symbol_timeframe(
            symbol,
            timeframe,
            months,
            combined["timestamp"].min(),
            combined["timestamp"].max(),
        )
