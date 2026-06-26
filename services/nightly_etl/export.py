"""Export QuestDB (or CSV fallback) to Parquet for NIFTY 5m."""

from datetime import datetime, timedelta, timezone

import polars as pl

from odin_data.config import settings
from odin_data.data_loader import DataLoader
from odin_data.parquet_store import ParquetStore
from odin_data.questdb import QuestDBClient


def csv_sample_range() -> tuple[datetime, datetime]:
    """Min/max timestamp range from the local QuestDB sample CSV."""
    path = settings.raw_csv_path
    if not path.exists():
        raise FileNotFoundError(f"Sample CSV not found: {path}")
    frame = pl.read_csv(path, try_parse_dates=True)
    if frame.is_empty() or "timestamp" not in frame.columns:
        raise ValueError(f"No timestamps in sample CSV: {path}")
    ts = frame.with_columns(
        pl.col("timestamp").cast(pl.Datetime(time_unit="us", time_zone="UTC"))
    )["timestamp"]
    start = ts.min()
    end = ts.max() + timedelta(minutes=1)
    return start, end


def export_nifty_5m(
    days_back: int | None = None,
    symbols: list[str] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> None:
    symbols = symbols or [settings.default_symbol]
    timeframe = settings.default_timeframe
    if start is None or end is None:
        end = end or datetime.now(timezone.utc)
        start = start or (end - timedelta(days=days_back or 365 * 5))
    loader = DataLoader()
    store = ParquetStore()

    for symbol in symbols:
        if settings.use_questdb and loader.questdb.ping():
            frame = loader.questdb.fetch_ohlc(symbol, start, end, timeframe)
            source = "questdb"
        else:
            frame = loader._load_csv_fallback(symbol, start, end, timeframe)
            source = "csv"

        if frame.is_empty():
            print(f"No data exported for {symbol} {timeframe}")
            continue

        frame = frame.with_columns(pl.col("timestamp").dt.strftime("%Y-%m").alias("month"))
        for month in frame["month"].unique().sort():
            month_df = frame.filter(pl.col("month") == month).drop("month")
            path = store.write_ohlc_month(symbol, timeframe, month, month_df)
            print(f"Wrote {path}")

        store.rebuild_catalog(symbol, timeframe)
        print(f"Export complete for {symbol} from {source}: {frame.height} rows")


if __name__ == "__main__":
    export_nifty_5m()
