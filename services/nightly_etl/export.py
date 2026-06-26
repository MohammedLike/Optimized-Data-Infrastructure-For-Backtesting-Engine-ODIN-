"""Export QuestDB (or CSV fallback) to Parquet for NIFTY 5m."""

from datetime import datetime, timedelta, timezone

import polars as pl

from odin_data.config import settings
from odin_data.data_loader import DataLoader
from odin_data.parquet_store import ParquetStore
from odin_data.questdb import QuestDBClient


def export_nifty_5m(days_back: int = 365 * 5, symbols: list[str] | None = None) -> None:
    symbols = symbols or [settings.default_symbol]
    timeframe = settings.default_timeframe
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    loader = DataLoader()
    store = ParquetStore()

    for symbol in symbols:
        if settings.use_questdb and loader.questdb.ping():
            frame = loader.questdb.fetch_ohlc(symbol, start, end, timeframe)
            source = "questdb"
        else:
            frame, _ = loader.load_ohlc(symbol, timeframe, start, end, use_redis=False, use_questdb=False)
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
